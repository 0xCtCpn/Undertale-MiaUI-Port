# Patches

Each numbered patch modifies the vendored Butterscotch source in `upstream/` for MiaUI. They're applied in order by the `Dockerfile`:

| # | File | What it does |
|---|---|---|
| 001 | `001-rg35xx-fallback-mapping.patch` | Adds `createFallbackMappings()` — the shipped `gamecontrollerdb.txt` has no entry for the RG35XX pad, so a fallback mapping is created on boot. Face buttons are identity; the D-pad is remapped to the verified MiaUI indices (sdl 13–16). Button 12 is the system volume key and is never mapped. |
| 002 | `002-chunklog.patch` | Logs each `data.win` chunk as it's parsed (`logInfo`), so hangs in the loader are visible in `debug.log`. |
| 003 | `003-stage-markers.patch` | Prints `[stage]` markers to stderr at each engine init step (parse, VM create, platform init, renderer, audio). |
| 004 | `004-sdl-error.patch` | Includes `SDL_GetError()` in the SDL2 "Failed to initialize SDL" message. |
| 005 | `005-sdl1-error.patch` | Same as 004 but for the SDL1 backend (`sdl1.c`). |
| 006 | `006-fpslog.patch` | Per-frame phase timing — prints an `FPSLOG:` line every 300 frames via unbuffered `logError`, splitting the frame into input, simulation, and sleep phases. |
| 007 | `007-joyname-cache.patch` | **Performance fix.** Caches `SDL_JoystickName()` per slot. SDL 1.2's version opens the device and issues evdev ioctls on every call (~50 ms/frame on this pad), which was the root cause of a previous bug where the game was running at ~15 fps. |
| 008 | `008-exit-cursor.patch` | Select + Start held together quits cleanly; the fbcon stub cursor (which never moves and sits in a corner) is always hidden. |

## Applying

The `Dockerfile` resets `upstream/` to the pinned commit and applies `patches/*.patch` in filename order. Any mismatch fails the build hard.

To regenerate patches 001, 005–008 from the pristine pinned source, run:

```
docker run --rm -v <proj>:/mnt -v <proj>/patches:/patches undertale-miaui python3 /mnt/tools/gen_patches.py
```

See `tools/gen_patches.py` and `tools/insert_mapping.py` for the generation logic.
