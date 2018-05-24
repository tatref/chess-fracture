# Windows usage
## Blender / Python setup
Download `pip` from https://bootstrap.pypa.io/get-pip.py

Save the file next to `python` under `$blender/2.79/python/bin/`, where `$blender` is the install dir of blender, usually `C:/Program files/Blender`

Install pip
```
.\python.exe get-pip.py
```

Install `python-chess`
```
.\python.exe -m pip install python-chess
```

## Running
Set the `CHESS_FRACTURE_PGN_PATH` environnement variable.

Windows
```
set CHESS_FRACTURE_PGN_PATH=.\path\to\pgn\file.pgn
```

Linux
```
export CHESS_FRACTURE_PGN_PATH=/path/to/pgn/file.pgn
```

To create the simulation, run blender like so
```
blender.exe .\chess_fracture_template.blend --python .\chess_fracture.py
```


# Docker
## Requirements
### TurboVnc
An OpenGL accelerated X11 is required (seems that some features of Blender simply won't work with `--background`

See [../host/setup.sh](../host/setup.sh)

### Git lfs

### X11 permissions
```
DISPLAY=:1 xhost local:name
```

## Building the container
```
git lfs pull
docker build -t chess-fracture .
```

## Usage
```
# the DISPLAY on wich turbovnc is running (or regular X if on workstation)
VNC_DISPLAY=1

# output name (will end up under /var/lib/docker/volumes/blend_files/_data/)
PGN_NAME=my_awsome_game.blend

# input PGN (absolute path required)
CHESS_FRACTURE_PGN_PATH=/path/to/my_awsome_game.pgn

docker run --name chess-fracture1 \
           --security-opt label=type:container_runtime_t \
           --rm \
           --mount type=bind,src=$CHESS_FRACTURE_PGN_PATH,dst=/work/input.pgn,ro=true \
           --mount type=volume,src=blend_files,dst=/output \
           --mount type=bind,src=/tmp/.X11-unix/X$VNC_DISPLAY,dst=/tmp/.X11-unix/X$VNC_DISPLAY \
           -e DISPLAY=:$VNC_DISPLAY \
           -e PGN_NAME=$PGN_NAME \
           chess-fracture:latest
```

## Variables
- `CHESS_FRACTURE_PGN_PATH`: path to the PGN input file
- `PGN_NAME`: output name (`*.blend`)
- `CHESS_FRACTURE_FRAMES_PER_MOVE`
- `CHESS_FRACTURE_FRAGMENTS`
- `CHESS_FRACTURE_TEST`: early exit the python script for easier testing
