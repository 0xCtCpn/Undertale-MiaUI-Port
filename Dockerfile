FROM debian:bookworm
ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get update && apt-get install -y \
    gcc-arm-linux-gnueabihf g++-arm-linux-gnueabihf make pkg-config git python3 curl ca-certificates \
    autoconf automake libtool cmake ninja-build patch file xz-utils bzip2 unzip zip \
    && rm -rf /var/lib/apt/lists/*
WORKDIR /build

# glibc cross target: arm-buildroot-linux-gnueabihf compatible (<=2.37).
# No musl, no /tmp loader staging needed on MiaUI (glibc 2.37 in SYSTEM).
RUN arm-linux-gnueabihf-gcc --version

COPY toolchain-glibc.cmake /build/toolchain-glibc.cmake
COPY upstream /build/upstream
COPY patches /build/patches

# Alsa-lib for ARM (glibc) FIRST: SDL 1.2 configure needs its headers/lib at
# configure time or it silently disables the ALSA audio driver (happened once:
# libSDL had no "ALSA PCM audio" bootstrap -> SDL_OpenAudio "No available
# audio device" on-device).
RUN curl -sSL --retry 3 --retry-all-errors https://www.alsa-project.org/files/pub/lib/alsa-lib-1.2.12.tar.bz2 -o alsa.tar.bz2 && \
    tar xjf alsa.tar.bz2 && cd alsa-lib-1.2.12 && \
    CC=arm-linux-gnueabihf-gcc CFLAGS="-march=armv7-a -mfpu=neon -mfloat-abi=hard -O2" \
    ./configure --host=arm-linux-gnueabihf --prefix=/opt/arm-alsa-glibc \
      --disable-python --disable-aload --without-debug && \
    make -j$(nproc) && make install

# SDL 1.2.15 (MiaUI has no GBM/DRM: system SDL2 can't pick kmsdrm either).
# Same flag set as Garlic build but glibc cross.
RUN git clone --depth 1 --branch release-1.2.15 https://github.com/libsdl-org/SDL-1.2.git SDL12 && \
    cd SDL12 && ./autogen.sh 2>/dev/null || autoreconf -fi; \
    PATH=/opt/arm-alsa-glibc/bin:$PATH CC=arm-linux-gnueabihf-gcc \
    CFLAGS="-march=armv7-a -mfpu=neon -mfloat-abi=hard -O2 -I/opt/arm-alsa-glibc/include" \
    LDFLAGS="-L/opt/arm-alsa-glibc/lib" \
    CPPFLAGS="-I/opt/arm-alsa-glibc/include" \
    ./configure --host=arm-linux-gnueabihf --prefix=/opt/arm-sdl12-glibc \
      --disable-video-x11 --disable-video-directfb --disable-video-ps2gs --disable-video-ps3 \
      --disable-video-ggi --disable-video-svga --disable-video-aalib --disable-video-dga \
      --enable-video-fbcon \
      --enable-alsa --disable-alsa-shared \
      --disable-oss --disable-esd --disable-pulseaudio --disable-arts --disable-nas \
      --disable-cdrom \
    && grep -m1 "SDL_VIDEO_DRIVER_FBCON" include/SDL_config.h && \
       grep -m1 "SDL_AUDIO_DRIVER_ALSA" include/SDL_config.h && \
       make -j$(nproc) && make install && \
       ls /opt/arm-sdl12-glibc/lib/libSDL*.so* && \
       grep -a -q 'ALSA PCM audio' /opt/arm-sdl12-glibc/lib/libSDL.so \
         && echo "SDL alsa driver OK" \
         || (echo "SDL built WITHOUT alsa audio driver"; exit 1)

# Patches + pin check (onion-v2 92ed6b8, 32bpp XRGB, SW path kept for fallback).
# NOTE: the host upstream tree may be left with patches applied (gen_patches
# leaves the verification chain applied; probes may too) — reset to the pin
# FIRST so the apply loop always starts from pristine.
RUN cd /build/upstream && \
    git rev-parse HEAD && \
    git reset --hard HEAD && \
    git clean -fd src/ && \
    test "$(git rev-parse HEAD)" = "92ed6b8c3766361a201a69d202bcde5873cdad7e" && \
    echo "onion-v2 pin OK" && \
    for p in /build/patches/*.patch; do \
      echo "applying $p" && \
      git apply --ignore-whitespace --whitespace=nowarn --verbose "$p" || { echo "FAILED $p"; exit 1; } ; \
    done && \
    git diff --stat

# Butterscotch MiaUI Option A: PLATFORM=cli BACKEND=sdl1 AUDIO_BACKEND=sdl1,
# SW only (same as Garlic, but glibc cross — no musl loader needed).
RUN cd /build/upstream && \
    cmake -B build -G Ninja \
      -DCMAKE_TOOLCHAIN_FILE=/build/toolchain-glibc.cmake \
      -DPLATFORM=cli -DBACKEND=sdl1 -DAUDIO_BACKEND=sdl1 \
      -DENABLE_SW_RENDERER=ON -DENABLE_LEGACY_GL=OFF -DENABLE_MODERN_GL=OFF \
      -DENABLE_WAD14=OFF -DENABLE_WAD16=ON -DENABLE_WAD17=OFF \
      -DENABLE_VM_GML_PROFILER=OFF -DENABLE_VM_TRACING=OFF \
      -DENABLE_VM_OPCODE_PROFILER=OFF -DENABLE_VM_STUB_LOGS=OFF \
      -DCMAKE_BUILD_TYPE=Release -DWERROR=OFF \
      -DSDL_INCLUDE_DIR=/opt/arm-sdl12-glibc/include \
      -DSDL_LIBRARY=/opt/arm-sdl12-glibc/lib/libSDL.so \
      -DCMAKE_C_FLAGS="-march=armv7-a -mfpu=neon -mfloat-abi=hard -O3 -DNDEBUG" \
      -DCMAKE_EXE_LINKER_FLAGS="-L/opt/arm-sdl12-glibc/lib -L/opt/arm-alsa-glibc/lib -lasound" \
    && cmake --build build -j$(nproc) \
    && ls -lh build/butterscotch

CMD mkdir -p /out && cp /build/upstream/build/butterscotch /out/ && \
    cp /build/upstream/vendor/gamecontrollerdb.txt /out/ 2>/dev/null || true; \
    cp /opt/arm-sdl12-glibc/lib/libSDL-1.2.so* /out/ 2>/dev/null || true; \
    cp /opt/arm-alsa-glibc/lib/libasound.so* /out/ 2>/dev/null || true; \
    mkdir -p /out/share && cp -r /opt/arm-alsa-glibc/share/alsa /out/share/ 2>/dev/null || true; \
    ls -lh /out/ && arm-linux-gnueabihf-readelf -l /out/butterscotch | grep INTERP; \
    arm-linux-gnueabihf-readelf -d /out/butterscotch | grep NEEDED
