@echo off
REM Build Undertale (Butterscotch onion-v2) for MiaUI RG35XX - requires Docker Desktop
REM Toolchain: glibc armhf cross (MiaUI SYSTEM is glibc 2.37, INTERP
REM /lib/ld-linux-armhf.so.3 - NO musl /tmp loader staging like Garlic).
REM Route B: SDL2 + Modern GL (GLES on SGX544) instead of SW renderer.
docker build --load -t undertale-miaui .
if errorlevel 1 (
  echo Build failed - check docker log above
  exit /b 1
)
if not exist out mkdir out
docker run --rm -v "%cd%/out:/out" undertale-miaui
echo.
echo === Built ===
dir out
echo.
echo Install (MiaUI EXT4, no FAT32):
echo 1. Copy out\butterscotch + libSDL2* + libasound* + share + gamecontrollerdb.txt to /userdata/Emus/Undertale.pak/
echo    Copy launch.sh there as launch.sh (chmod via /userdata mount)
echo 2. Copy your Undertale 1.08 (Windows) data.win + .ogg music into the same folder
echo 3. Reboot, Emus -^> Undertale
echo 4. Debug: read /userdata/Emus/Undertale.pak/debug.log
