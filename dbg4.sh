#!/bin/sh
set -e
dpkg --add-architecture armhf
apt-get update -qq
apt-get install -y -qq libgbm-dev:armhf libegl-dev:armhf libdrm-dev:armhf libudev-dev:armhf > /tmp/apt.log 2>&1 || cat /tmp/apt.log
echo "--- dpkg -L libgbm-dev:armhf ---"
dpkg -L libgbm-dev:armhf | head -30
echo "--- dpkg -L libdrm-dev:armhf ---"
dpkg -L libdrm-dev:armhf | head -30
echo "--- dpkg -L libegl-dev:armhf ---"
dpkg -L libegl-dev:armhf | head -30
echo "--- dpkg -L libudev-dev:armhf ---"
dpkg -L libudev-dev:armhf | head -10
find /usr -name "gbm.h" -o -name "libdrm.pc" -o -name "gbm.pc" 2>/dev/null
