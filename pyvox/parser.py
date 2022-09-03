import io
from struct import unpack_from as unpack, calcsize
import logging

from .models import Vox, Size, Voxel, Color, Model, Material

log = logging.getLogger(__name__)


class ParsingException(Exception):
    pass


def bit(val, offset):
    mask = 1 << offset
    return val & mask


class Chunk(object):
    def __init__(self, chunk_id, content=None, chunks=None):
        self.id = chunk_id
        self.content = content or b''
        self.chunks = chunks or []
        self.material = None

        if chunk_id == b'MAIN':
            if len(self.content):
                raise ParsingException('Non-empty content for main chunk')
        elif chunk_id == b'PACK':
            self.models = unpack('i', content)[0]
        elif chunk_id == b'SIZE':
            self.size = Size(*unpack('iii', content))
        elif chunk_id == b'XYZI':
            n = unpack('i', content)[0]
            log.debug('xyzi block with %d voxels (len %d)', n, len(content))
            self.voxels = []
            self.voxels = [Voxel(*unpack('BBBB', content, 4 + 4 * i)) for i in range(n)]
        elif chunk_id == b'RGBA':
            self.palette = [Color(*unpack('BBBB', content, 4 * i)) for i in range(255)]
            # Docs say:  color [0-254] are mapped to palette index [1-255]
            # hmm
            # self.palette = [ Color(0,0,0,0) ] + [ Color(*unpack('BBBB', content, 4*i)) for i in range(255) ]
        elif chunk_id == b'MATL':
            data = io.BytesIO(content)
            _id = self.unpack('i', data)[0]
            n_keys = self.unpack('i', data)[0]
            
            type = b'_diffuse'
            weight = 0.0
            props = {}
            for i in range(n_keys):
                key_len = self.unpack('i', data)[0]
                key = b''.join(self.unpack('s', data)[0] for j in range(key_len))
                value_len = self.unpack('i', data)[0]
                value = b''.join(self.unpack('s', data)[0] for j in range(value_len))
                if key == b'_weight':
                    weight = float(value.decode('ascii'))
                elif key == b'_type':
                    type = value
                else:
                    props[key.decode('ascii')] = value.decode('ascii')

            self.material = Material(id=_id, type=type, weight=weight, props=props)

        else:
            # raise ParsingException('Unknown chunk type: %s'%self.id)
            log.debug(f"Unknown chunk type {chunk_id}")
            pass

    def unpack(self, fmt, stream):
        size = calcsize(fmt)
        buf = stream.read(size)
        return unpack(fmt, buf)

class VoxParser(object):

    def __init__(self, filename):
        with open(filename, 'rb') as f:
            self.content = f.read()

        self.offset = 0

    def unpack(self, fmt):
        r = unpack(fmt, self.content, self.offset)
        self.offset += calcsize(fmt)
        return r

    def _parse_chunk(self):

        _id, n, m = self.unpack('4sii')

        log.debug("Found chunk id %s / len %s / children %s", _id, n, m)

        content = self.unpack('%ds' % n)[0]

        start = self.offset
        chunks = []
        while self.offset < start + m:
            chunks.append(self._parse_chunk())

        return Chunk(_id, content, chunks)

    def parse(self):

        header, version = self.unpack('4si')

        if header != b'VOX ':
            raise ParsingException("This doesn't look like a vox file to me")

        if version != 150:
            raise ParsingException("Unknown vox version: %s expected 150" % version)

        main = self._parse_chunk()

        if main.id != b'MAIN':
            raise ParsingException("Missing MAIN Chunk")

        chunks = list(reversed(main.chunks))
        if chunks[-1].id == b'PACK':
            models = chunks.pop().models
        else:
            models = 1

        log.debug("file has %d models", models)

        models = [self._parse_model(chunks.pop(), chunks.pop()) for _ in range(models)]

        if chunks and chunks[0].id == b'RGBA':
            palette = chunks.pop().palette
        else:
            palette = None

        materials = [c.material for c in chunks if c.material]
        return Vox(models, palette, materials)

    def _parse_model(self, size, xyzi):
        if size.id != b'SIZE':
            raise ParsingException('Expected SIZE chunk, got %s', size.id)
        if xyzi.id != b'XYZI':
            raise ParsingException('Expected XYZI chunk, got %s', xyzi.id)

        return Model(size.size, xyzi.voxels)


if __name__ == '__main__':
    import sys
    import coloredlogs

    coloredlogs.install(level=logging.DEBUG)

    VoxParser(sys.argv[1]).parse()
