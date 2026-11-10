# Undertale - MiaUI (RG35XX) Port

Undertale on the Anbernic RG35XX running MiaUI, using the open-source Butterscotch (Onion reimplementation) engine.

Needs the original (Non-H700) RG35XX with MiaUI v2.0.0, the release zip, and your own Undertale sourced from your own copy.

## Overview

This repo builds Undertale for the Anbernic RG35XX running MiaUI. It cross-compiles the open-source Butterscotch runner (a GameMaker engine reimplementation) for the handheld's ARM CPU, patches it for MiaUI's layout and controls, and packages everything into a ready-to-copy `.pak` folder.

The build is fully reproducible from source via Docker: run `build.bat` and the binaries land in `out/`. You need to provide your own copy of the game from Steam as they're not included in the repo or release.

## Install

1. Prepare your Undertale_MiaUI-release-v1.zip and Undertale Steam files
2. Extract the zip into PORTS/
3. Copy all of your game files (Steam Manage > Browse local files) into /PORTS/Undertale.pak/
4. Safely eject, boot, go to PORTS -> Undertale
5. Wait 1-3 minutes (yes its that long)
6. Thats all, you should be booted in the game now so enjoy!

## SD folder structure

```
Ports/
  Undertale.pak/          # MiaUI pak folder name
    launch.sh
    butterscotch
    libSDL-1.2.so.0
    libasound.so.2
    share/
    gamecontrollerdb.txt
    # Your Undertale Steam game files
```


## Build from source

Only needed if you change the engine or want fresh binaries

Prerequisites (Windows):

- Hardware Virtualization enabled in BIOS
- WSL 2 (Windows Subsystem for Linux 2)
- Docker Desktop (configured to use the WSL 2 engine)

Steps:

1. Open this folder and double-click `build.bat`
2. Wait for it to finish - success ends with `=== Built ===` plus a listing of `out/`
3. Fresh binaries land in `out/`: `butterscotch`, `libSDL-1.2.so.0`, ALSA libs (`libasound.so*`), `share/alsa/`, `gamecontrollerdb.txt`

What the build does (`Dockerfile`):

* Starts from `debian:bookworm`, installs compilers and build tools
* Cross-compiles alsa-lib for ARM (glibc) **first** - SDL 1.2's configure silently drops its ALSA driver without it, which surfaces on-device as "No available audio device"
* Cross-compiles SDL 1.2.15 with the fbcon video driver (`--enable-video-fbcon`, `--enable-alsa`) and hard-fails if the ALSA bootstrap string is missing
* Resets the vendored `upstream/` to the pinned commit, applies `patches/*.patch` (fails hard on any mismatch), then builds Butterscotch with `PLATFORM=cli BACKEND=sdl1 AUDIO_BACKEND=sdl1` and the software renderer
* Prints checks at the end: the binary's `INTERP` (want `/lib/ld-linux-armhf.so.3`) and its `NEEDED` libraries

To install your own build: copy `out/*` + `launch.sh` to SD `ROMS/Ports/Undertale.pak/`, then copy your game files into the same folder.

## MiaUI changes from upstream

MiaUI modifications (see `patches/`):

`launch.sh`: `ROMS/Ports/Undertale.pak/` layout, `SDL_VIDEODRIVER=fbcon` + `SDL_NOMOUSE=1`, CPU governor pinning to `performance` for full clock, and a `debug.log` probe dump.

## Debugging

If crashing open `ROMS/Ports/Undertale.pak/debug.log` and check/submit the error

## Credits

Thanks to:

* [cobaltgit](https://github.com/cobaltgit/Butterscotch) — Butterscotch GameMaker runner (AGPLv3, this port is forked from that repo, pinned at `92ed6b8`, vendored under `upstream/`)
* DSkywalk for [MiaUI](https://github.com/miaui-cfw/MiaUI-GPU-RG35XX)
* libsdl and ALSA upstreams for the bundled dependencies
* Tobias D. Fox — Undertale

## License

GPLv3 and AGPLv3 - the vendored Butterscotch upstream is AGPLv3 (see `upstream/LICENSE`). MiaUI-port attribution in `NOTICE.MiaUI`; upstream credits in `upstream/README.md`. Corresponding source for release binaries is this repo + `Dockerfile`/`build.bat` build instructions.
