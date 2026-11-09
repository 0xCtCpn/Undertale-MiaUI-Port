#!/bin/sh
echo "--- find gbm.h, EGL, udev ---"
find /usr -name "gbm.h" 2>/dev/null
find /usr -name "egl.h" 2>/dev/null | head -5
find /usr -name "libudev.h" 2>/dev/null
find /usr -name "drm.h" 2>/dev/null
echo "--- dpkg libgbm-dev files (head) ---"
dpkg -L libgbm-dev:armhf 2>/dev/null | head -20
echo "--- dpkg libudev-dev files (head) ---"
dpkg -L libudev-dev:armhf 2>/dev/null | head -10
echo "--- dpkg libegl-dev files (head) ---"
dpkg -L libegl-dev:armhf 2>/dev/null | head -10
echo "--- dpkg libdrm-dev files (head) ---"
dpkg -L libdrm-dev:armhf 2>/dev/null | head -10
