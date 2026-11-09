#!/bin/sh
set -x
find /usr -name "libdrm.pc" -o -name "gbm.pc" 2>/dev/null
ls /usr/lib/x86_64-linux-gnu/pkgconfig/ 2>&1 | head -20
ls /usr/lib/pkgconfig/ 2>&1 | head -20
ls /usr/share/pkgconfig/ 2>&1 | head -20
echo "--- pkg-config check (forced cross path) ---"
PKG_CONFIG_LIBDIR=/usr/arm-linux-gnueabihf/lib/pkgconfig PKG_CONFIG_PATH=/usr/arm-linux-gnueabihf/lib/pkgconfig pkg-config --modversion libdrm 2>&1
PKG_CONFIG_LIBDIR=/usr/arm-linux-gnueabihf/lib/pkgconfig pkg-config --modversion gbm 2>&1
echo "--- where are arm pkgconfigs? ---"
find /usr -path "*arm*lib/pkgconfig*" -name "*.pc" 2>/dev/null | head -20
echo "--- sysroot include check ---"
ls /usr/arm-linux-gnueabihf/include/drm/ | head -10
ls /usr/arm-linux-gnueabihf/include/ | grep -E "gbm|EGL" | head -10
