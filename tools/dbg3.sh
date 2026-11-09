#!/bin/sh
set -x
echo "--- apt-file search offline: dpkg-deb ---"
apt-get install -y apt-file 2>&1 | tail -2 || true
apt-file search gbm.h 2>&1 | head -20 || echo "apt-file failed"
echo "--- alternative: which packages provide gbm.h ---"
for p in libgbm-dev libgbm1 mesa-common libegl1-mesa-dev libglvnd-dev libgl-dev; do
  apt-cache show "$p" 2>/dev/null | grep -E "^Package|^Source" | head -2
done
echo "--- check libegl-dev file list via madison/depends ---"
apt-cache depends libegl-dev:armhf 2>&1 | head -20
echo "--- what did we actually install? ---"
dpkg -l | grep -E "armhf" | head -40
