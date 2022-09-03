# sprite-stack-to-voxel

A tool that converts a folder of images into a single magickavoxel .vox file.

## Setup

1. Create virtual environment and install requirements.

  ```
  python3 -m virtualenv venv
  source /venv/scripts/activate.bat // Windows
  source /venv/bin/activate // Mac/Linux
  pip install -r requirements.txt
  ```

2. Install setup.py for vox tools.

  ```
  python3 setup.py install
  ```

3. Add folders with images into the `/stacks` directory.

4. Run `convert-stack-to-vox.py`, providing the name of a folder in the `/stacks` directory as an argument. Output will be found in the `/vox` directory

  ```
  python3 convert-stack-to-vox.py -n folder-name
  ```
