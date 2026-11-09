#!/bin/sh
# MiaUI pak launcher - install to /userdata/Ports/Undertale.pak/launch.sh
# MiaUI ROMs is EXT4 only (no FAT32), SD preserved read-only OS in /opt.
progdir=$(dirname "$0")
cd $progdir
HOME=$progdir
# Do NOT prepend bundled libasound.so here: the pack ships our SDL1.2-era
# alsa-lib which rejects the real card (atm7059link); system /usr/lib/libasound
# knows it (probe: bundled = "No available audio device", system = ok).
export LD_LIBRARY_PATH="$PWD:$LD_LIBRARY_PATH"
unset ALSA_CONFIG_PATH
unset ALSA_CONFIG_DIR
export SDL_VIDEODRIVER=fbcon
export SDL_FBDEV=/dev/fb0
export SDL_NOMOUSE=1
export SDL_AUDIODRIVER=alsa
# 'overclock.elf' only raises scaling_max_freq; governor stays 'userspace'
# pinned at CPU_SPEED_MENU (504 MHz), so gameplay initially ran at menu clock.
# Raise the ceiling to CPU_SPEED_PERF (1488000) and pin all cores there with
# the performance governor. 1.2 GHz (CPU_SPEED_GAME) measurably was not
# enough for the SW renderer's 30 FPS cadence -> game ran at ~<100% speed.
overclock.elf $CPU_SPEED_PERF 2>/dev/null
for i in 0 1 2 3; do
  echo performance > /sys/devices/system/cpu/cpu$i/cpufreq/scaling_governor 2>/dev/null
done
restore_cpu() {
  for i in 0 1 2 3; do
    echo userspace > /sys/devices/system/cpu/cpu$i/cpufreq/scaling_governor 2>/dev/null
    echo 504000 > /sys/devices/system/cpu/cpu$i/cpufreq/scaling_setspeed 2>/dev/null
  done
}
trap restore_cpu EXIT
sleep 1
{
  echo "=== Undertale MiaUI launch (SW, SDL1.2 fbcon) ==="
  cat /proc/fb
  ls -lh /dev/fb* /dev/dri/* 2>&1
  ls /dev/input/event* 2>&1
  ls -R /dev/snd 2>&1 | head -20
  cat /proc/meminfo 2>&1 | head -5
  ls -lh ./butterscotch ./lib*.so* ./data.win 2>&1
} > ./debug.log 2>&1
if [ ! -f "./data.win" ]; then
  echo "missing data.win - copy Undertale 1.08 (Windows) files here" >> ./debug.log
  sleep 3
  exit 1
fi
./butterscotch --renderer software --lazy-rooms --lazy-textures --lazy-audio --load-type load-per-chunk ./data.win >> ./debug.log 2>&1
RET=$?
echo "exit code $RET" >> ./debug.log
exit $RET
