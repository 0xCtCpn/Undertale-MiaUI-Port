#!/bin/sh
set -x
echo "--- arm sysroot tree ---"
ls /usr/arm-linux-gnueabihf/ 2>&1
echo "--- find .pc under sysroot ---"
find /usr -name "*.pc" 2>/dev/null | head -40
echo "--- gbm.h location ---"
find /usr -name "gbm.h" 2>/dev/null
echo "--- libgbm pkg location (new image?) ---"
dpkg -L libgbm-dev:armhf 2>&1 | head -30
dpkg -L libgbm-dev 2>&1 | head -30
echo "--- pkg-config --variable ---"
pkg-config --variable=pc_path pkg-config 2>&1
