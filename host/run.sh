#!/bin/bash

set -eux


/opt/TurboVNC/bin/vncserver :$VNC_DISPLAY -localhost -nohttpd
