#!/bin/sh
echo "--- dpkg ---"
dpkg -l | grep -E "libdrm|libgbm|libudev" || echo "no cross DRM pkgs"
echo "--- headers ---"
ls /usr/include/drm.h 2>&1
ls /usr/include/libdrm* 2>&1 | head -5
echo "--- sysroot ---"
ls /usr/arm-linux-gnueabihf/include/drm.h 2>&1
ls /usr/arm-linux-gnueabihf/include/libdrm* 2>&1 | head -5
echo "--- sdl drivers (strings) ---"
strings /opt/arm-sdl2-glibc/lib/libSDL2-2.0.so.0.2800.5 | grep -i kmsdrm | head -5
echo "--- sdl video drivers ---"
strings /opt/arm-sdl2-glibc/lib/libSDL2-2.0.so.0.2800.5 | grep -E "^kmsdrm$|^dummy$|^offscreen$" | head -10
