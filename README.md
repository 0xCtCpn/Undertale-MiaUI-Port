# Undertale (Butterscotch onion-v2) for MiaUI RG35XX — Route B (GL)

Status: scaffolding, not tested. Do not claim it boots until a device log proves it.

MiaUI v2.0.0 (per `../agent.md` §4) is glibc 2.37 with GPU + GLES (SGX544) enabled.
Unlike Garlic (`../agent.md`), there is no musl/EGLIBC fight: target `arm-buildroot-linux-gnueabihf`
compatible, `INTERP /lib/ld-linux-armhf.so.3`, `GLIBC <=2.37`.

## Difference from Garlic build

| Garlic (`Port_Undertale/`) | MiaUI Route B (this folder) |
|---|---|
| musl cross, `/tmp/ld-musl-armhf.so.1` staged | glibc cross, standard INTERP |
| SDL1.2 + SW renderer only (SGX off) | SDL2 + Modern GL (GLES on SGX544) |
| `AUDIO_BACKEND=sdl1` (SDL audio) | `AUDIO_BACKEND=miniaudio` (ALSA via libasound) |
| FAT32 `ROMS/PORTS/*.sh` | EXT4 `/userdata/Emus/Undertale.pak/launch.sh` |

## Build

`build.bat` (needs Docker Desktop). Output in `out\`:
`butterscotch`, `libSDL2*.so*`, `libasound.so*`, `share/alsa/`, `gamecontrollerdb.txt`.

## Install (MiaUI)

1. Copy `out\*` + `launch.sh` to `/userdata/Emus/Undertale.pak/` (on the MiaUI SD).
2. Copy your own Undertale 1.08 (Windows) `data.win` + `.ogg` music into the same folder.
3. Run from Emus. Debug in `Undertale.pak/debug.log`.

## Notes

- SDL2 backend loads `gamecontrollerdb.txt` via `SDL_GameControllerAddMappingsFromFile`;
  the Garlic SDL1 `createFallbackMappings()` patch does not apply (different backend API).
  The upstream DB matches most Linux pads; RG35XX fallback for SDL2 requires a
  separate patch if the pad reports `valid=0`.
- If the GL context fails to init (`Failed to initialize GLAD` / `Could not set any video
  mode` in `debug.log`), fall back to Option A: glibc SDL1.2 + SW renderer (same toolchain,
  `BACKEND=sdl1`, `ENABLE_SW_RENDERER=ON`, GL off) — see `Port_Undertale/Dockerfile` pattern.
