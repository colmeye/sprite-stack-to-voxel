from pyvox.models import Vox, Color
from pyvox.writer import VoxWriter
from PIL import Image
import numpy as np
import glob
import argparse
import os


# Arguments
parser = argparse.ArgumentParser(description='Converts folder of images to a magickavoxel')
parser.add_argument('-n', '--name', help='Name of the folder within the /stacks folder', type=str, required=True)
args = vars(parser.parse_args())


# Init
final_list = []
palette_lookup = {}
palette = []
palette_counter = 1
image_paths = glob.glob(os.path.join( os.getcwd(), 'stacks', args['name'], '*.png' ))


# Populate palette lookup
for image_index, image_path in enumerate(image_paths):
  image = np.asarray(Image.open(image_path).convert('RGBA'))

  for row in image:
    for data in row:
      if (data[0], data[1], data[2], data[3]) not in palette_lookup:
        palette.append(Color(r=data[0], g=data[1], b=data[2], a=data[3]))
        palette_lookup[(data[0], data[1], data[2], data[3])] = len(palette) - 1

# Remove first element from palette, since palettes are 1 indexed
palette.pop(0)



for image_index, image_path in enumerate(reversed(image_paths)):
  
  original_image = np.asarray(Image.open(image_path).convert('RGBA'))
  formatted_list = np.delete(original_image, 0, 2)
  formatted_list = np.delete(formatted_list, 0, 2)
  formatted_list = np.delete(formatted_list, 0, 2)

  if len(final_list) == 0:
    # First image we're processing
    final_list = formatted_list
  else:
    # Not the first image, so concatenate to final list
    final_list = np.concatenate((final_list, formatted_list), axis = 2)

  # Number each piece on this new layer for the palette!
  for i, row in enumerate(final_list):
    for ii, data in enumerate(row):

        oi_data = original_image[i][ii]
        data[image_index] = palette_lookup[(oi_data[0], oi_data[1], oi_data[2], oi_data[3])]



# Face upright
final_list = np.moveaxis(final_list, 0, -1) 

# Save
vox = Vox.from_dense(final_list)
vox.palette = palette
VoxWriter( os.path.join( os.getcwd(), 'vox', args['name']+'.vox'), vox).write()
