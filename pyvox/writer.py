from struct import pack

from pyvox.models import Vox, Voxel


class VoxWriter(object):

    def __init__(self, filename, vox: Vox):
        self.filename = filename
        self.vox: Vox = vox

    def _chunk(self, id, content, chunks=[]):

        res = b''
        for c in chunks:
            res += self._chunk(*c)

        return pack('4sii', id, len(content), len(res)) + content + res

    def _string(self, string: bytes):
        """ string packing: number of chars then one byte per char. """
        return pack('i', len(string)) + b''.join(pack('s', string[c:c+1]) for c in range(len(string)))

    def _dict(self, data: dict):
        """ dict packing: store the # of keys, then for each key/value strings. """
        ret = pack('i', len(data))
        for key, value in data.items():
            ret += self._string(key) + self._string(value)
        return ret

    def write(self):

        res = self.to_bytes()

        with open(self.filename, 'wb') as f:
            f.write(res)

    def to_bytes(self):

        res = pack('4si', b'VOX ', 150)

        chunks = []

        if len(self.vox.models):
            chunks.append((b'PACK', pack('i', len(self.vox.models))))

        for m in self.vox.models:
            chunks.append((b'SIZE', pack('iii', m.size.x, m.size.y, m.size.z)))
            chunks.append((b'XYZI', pack('i', len(m.voxels)) + b''.join(pack('BBBB', v.x, v.y, v.z, v.c) for v in m.voxels)))

        if not self.vox.default_palette:
            # The palette needs to contain 255 items of MagicaVoxel will overflow the read.
            chunks.append((b'RGBA', b''.join(pack('BBBB', c.r, c.g, c.b, c.a) for c in self.vox.palette) + b''.join(pack('BBBB', 0x00, 0x00, 0x00, 0xFF) for i in range(256 - len(self.vox.palette)))))

        for m in self.vox.materials:
            chunks.append((b'MATL', pack('i', m.id) + self._dict({
                b'_type': m.type,
                b'_weight': str(m.weight).encode('ascii'),
                **{ (b'_' + key.encode('ascii')): str(value).encode('ascii') for key, value in m.props.items() },
            })))

        # TODO materials

        res += self._chunk(b'MAIN', b'', chunks)

        return res
