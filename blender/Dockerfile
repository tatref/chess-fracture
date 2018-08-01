FROM centos:7

RUN yum install -y bzip2 \
                   wget \
                   mesa-libGLU \
                   libXi \
                   libXrender \
                   xorg-x11-server-Xvfb \
                   xorg-x11-utils \
                   mesa-dri-drivers


COPY blender-2.79b-linux-glibc219-x86_64.tar.bz2 /work/


RUN mkdir /output && \
    cd /work && \
    tar xvjf blender-2.79b-linux-glibc219-x86_64.tar.bz2 && \
    rm -f blender-2.79b-linux-glibc219-x86_64.tar.bz2 && \
    cd blender-2.79b-linux-glibc219-x86_64/ && \
    wget https://bootstrap.pypa.io/get-pip.py && \
    2.79/python/bin/python3.5m get-pip.py && \
    2.79/python/bin/python3.5m -m pip install requests python-chess

COPY chess_fracture.py /work/chess_fracture.py
COPY chess_fracture_template.blend /work/chess_fracture_template.blend


VOLUME blend_files


WORKDIR /work/blender-2.79b-linux-glibc219-x86_64

CMD ./blender /work/chess_fracture_template.blend -noaudio --addons object_fracture_cell --python /work/chess_fracture.py
