#!/bin/sh
set -x
dpkg -L libdrm-dev:armhf | head -40
echo "---"
dpkg -L libgbm-dev:armhf | head -40
echo "---"
find /usr -name "drm.h" -o -name "gbm.h" -o -name "libdrm*.pc" -o -name "gbm.pc" -o -name "libudev.pc" 2>/dev/null
