# HP-UX 9.05 on QEMU -M 715: runtime image.
# Build from the repository root:
#   docker build -f hpux905/Dockerfile -t hpux905-qemu .

FROM ubuntu:24.04 AS build
ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get update && apt-get install -y --no-install-recommends \
        build-essential git ca-certificates python3 python3-venv \
        ninja-build pkg-config libglib2.0-dev libpixman-1-dev libslirp-dev \
        flex bison bzip2 \
    && rm -rf /var/lib/apt/lists/*
COPY . /src
WORKDIR /src/build
RUN ../configure --target-list=hppa-softmmu --disable-docs --disable-werror \
        --enable-slirp --disable-gtk --disable-sdl --disable-opengl \
    && ninja qemu-system-hppa qemu-img
RUN mkdir -p /opt/hpux905/bin /opt/hpux905/share \
    && cp qemu-system-hppa qemu-img /opt/hpux905/bin/ \
    && strip /opt/hpux905/bin/* \
    && cp ../pc-bios/hppa-firmware.img /opt/hpux905/share/ \
    && cp -r ../pc-bios/keymaps /opt/hpux905/share/ \
    && cp ../hpux905/hpux905 ../hpux905/install.sh ../hpux905/con.py ../hpux905/step.py /opt/hpux905/ \
    && chmod +x /opt/hpux905/hpux905 /opt/hpux905/install.sh

FROM ubuntu:24.04
ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get update && apt-get install -y --no-install-recommends \
        libglib2.0-0t64 libpixman-1-0 libslirp0 python3-minimal \
    && rm -rf /var/lib/apt/lists/*
COPY --from=build /opt/hpux905 /opt/hpux905
RUN ! ldd /opt/hpux905/bin/qemu-system-hppa | grep 'not found'
VOLUME /data
EXPOSE 5900 4555
ENTRYPOINT ["/opt/hpux905/hpux905"]
CMD ["help"]
