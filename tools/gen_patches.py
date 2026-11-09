#!/usr/bin/env python3
"""Regenerate patches 001, 005 and 006 against the PRISTINE pinned upstream.

The build image's /build/upstream has the patch layers applied, so first reset
to the pinned commit (92ed6b8...), then:
  1. insert_mapping.py edits -> git diff -> 001 (mapping fallback only)
  2. apply 001, stage it, make the 005 logError edit, git diff -> 005
  3. apply remaining patches (002/003/004), stage everything, make the
     006 fps-log edit in loop.c, git diff -> 006
  4. reset again, verify the full chain applies in order.
"""
import subprocess
import sys

UP = "/build/upstream"
PIN = "92ed6b8c3766361a201a69d202bcde5873cdad7e"
S1 = UP + "/src/backends/sdl1.c"
P001 = "/patches/001-rg35xx-fallback-mapping.patch"
P005 = "/patches/005-sdl1-error.patch"
P006 = "/patches/006-fpslog.patch"


def run(cmd, ok=True):
    r = subprocess.run(cmd, capture_output=True, text=True)
    if ok and r.returncode != 0:
        print("FAIL:", " ".join(cmd), "\n", r.stdout, "\n", r.stderr)
        sys.exit(1)
    return r


def reset_pristine():
    run(["git", "-C", UP, "reset", "--hard", PIN])
    run(["git", "-C", UP, "clean", "-fdx", "--", "src/"])
    r = run(["git", "-C", UP, "status", "--porcelain"])
    dirty = [l for l in r.stdout.splitlines() if "src/" in l]
    if dirty:
        print("upstream src still dirty:", dirty)
        sys.exit(1)
    head = run(["git", "-C", UP, "rev-parse", "HEAD"]).stdout.strip()
    if head != PIN:
        print("HEAD is", head)
        sys.exit(1)
    print("pristine at", head)


# ---- step 0: pristine
reset_pristine()
if "createFallbackMappings" in open(S1).read():
    print("sdl1.c not pristine!")
    sys.exit(1)

# ---- step 1: mapping-only 001
r = run(["python3", "/mnt/tools/insert_mapping.py"], ok=False)
print(r.stdout.strip(), r.stderr.strip())
diff = run(["git", "-C", UP, "diff", "--", "src/backends/sdl1.c"]).stdout
open(P001, "w", encoding="utf-8", newline="\n").write(diff)
print("001 written:", len(diff), "bytes")

# reset to pristine so 001 can be applied programmatically for step 2
run(["git", "-C", UP, "checkout", "--", "src/backends/sdl1.c"])

# ---- step 2: 005 relative to applied 001
run(["git", "-C", UP, "apply", "--ignore-whitespace", "--whitespace=nowarn", P001])
# Stage the 001-applied file so `git diff` below shows ONLY the 005 edit.
run(["git", "-C", UP, "add", "src/backends/sdl1.c"])
src = open(S1, "r", encoding="utf-8").read()
old = 'logError("Failed to initialize SDL\\n");'
new = 'logError("Failed to initialize SDL: %s\\n", SDL_GetError());'
if old not in src:
    print("005 target line not found")
    sys.exit(1)
open(S1, "w", encoding="utf-8", newline="\n").write(src.replace(old, new, 1))
diff = run(["git", "-C", UP, "diff", "--", "src/backends/sdl1.c"]).stdout
open(P005, "w", encoding="utf-8", newline="\n").write(diff)
print("005 written:", len(diff), "bytes")

# ---- step 3: apply remaining patches, then build 006 (fpslog) on loop.c
for p in ["002-chunklog.patch", "003-stage-markers.patch", "004-sdl-error.patch"]:
    run(["git", "-C", UP, "apply", "--ignore-whitespace", "--whitespace=nowarn",
         "/patches/" + p])
run(["git", "-C", UP, "add", "-A"])

LOOP = UP + "/src/loop.c"
src = open(LOOP, "r", encoding="utf-8").read()

TAIL_OLD = (
    "                uint64_t nextFrameTime = lastFrameTime + targetFrameTime;\n"
    "                platformSleepUntil(nextFrameTime);\n"
    "            }\n"
    "            lastFrameTime = nowNanos();\n"
    "        }\n"
    "\n"
    "        saveInputRecording();\n"
)
TAIL_NEW = (
    "                uint64_t nextFrameTime = lastFrameTime + targetFrameTime;\n"
    "                uint64_t _sleepT0 = nowNanos();\n"
    "                platformSleepUntil(nextFrameTime);\n"
    "                fpsPhSleep += (double) (nowNanos() - _sleepT0); fpsPhSleepN++;\n"
    "            }\n"
    "            lastFrameTime = nowNanos();\n"
    "            {\n"
    "                /* Onion diagnostics: real sim interval + phase split.\n"
    "                logError (stderr) is unbuffered/always visible. */\n"
    "                static uint64_t fpsPrevNs = 0;\n"
    "                static double fpsSumNs = 0, fpsMaxNs = 0;\n"
    "                static int fpsFrames = 0;\n"
    "                uint64_t fpsNow = nowNanos();\n"
    "                if (fpsPrevNs != 0) {\n"
    "                    double d = (double) (fpsNow - fpsPrevNs);\n"
    "                    fpsSumNs += d;\n"
    "                    if (d > fpsMaxNs) fpsMaxNs = d;\n"
    "                    fpsFrames++;\n"
    "                    if (fpsFrames == 300) {\n"
    "                        double inv = 1.0 / (fpsFrames > 0 ? fpsFrames : 1);\n"
    "                        logError(\"FPSLOG: avg_interval=%.2fms max=%.2fms avg_fps=%.2f frame=%d | pre=%.2f upd=%.2f/%.2f slot=%.2f/%.2f poll=%.2f/%.2f ev=%.2f/%.2f step=%.2f/%.2f swap=%.2fms sleep=%.2fms\\n\",\n"
    "                            fpsSumNs / fpsFrames / 1000000.0, fpsMaxNs / 1000000.0,\n"
    "                            300 * 1000000000.0 / fpsSumNs, runner->frameCount,\n"
    "                            fpsPhPre * inv / 1000000.0,\n"
    "                            fpsSdlUpdN > 0 ? fpsSdlUpdSum / fpsSdlUpdN / 1000000.0 : 0.0,\n"
    "                            fpsSdlUpdN > 0 ? fpsSdlUpdMax / 1000000.0 : 0.0,\n"
    "                            fpsSdlJsN > 0 ? fpsSdlJsSum / fpsSdlJsN / 1000000.0 : 0.0,\n"
    "                            fpsSdlJsN > 0 ? fpsSdlJsMax / 1000000.0 : 0.0,\n"
    "                            fpsSdlPollN > 0 ? fpsSdlPollSum / fpsSdlPollN / 1000000.0 : 0.0,\n"
    "                            fpsSdlPollN > 0 ? fpsSdlPollMax / 1000000.0 : 0.0,\n"
    "                            fpsPhEv * inv / 1000000.0, fpsPhEvMax / 1000000.0,\n"
    "                            fpsPhStep * inv / 1000000.0, fpsPhStepMax / 1000000.0,\n"
    "                            fpsPhSwapN > 0 ? fpsPhSwap / fpsPhSwapN / 1000000.0 : 0.0,\n"
    "                            fpsPhSleepN > 0 ? fpsPhSleep / fpsPhSleepN / 1000000.0 : 0.0);\n"
    "                        fpsFrames = 0; fpsSumNs = 0; fpsMaxNs = 0;\n"
    "                        fpsPhEv = 0; fpsPhEvN = 0; fpsPhEvMax = 0;\n"
    "                        fpsPhPre = 0; fpsPhPreN = 0;\n"
    "                        fpsPhStep = 0; fpsPhStepN = 0; fpsPhStepMax = 0;\n"
    "                        fpsPhSwap = 0; fpsPhSwapN = 0;\n"
    "                        fpsPhSleep = 0; fpsPhSleepN = 0;\n"
    "                        fpsSdlUpdSum = 0; fpsSdlUpdMax = 0; fpsSdlUpdN = 0;\n"
    "                        fpsSdlJsSum = 0; fpsSdlJsMax = 0; fpsSdlJsN = 0;\n"
    "                        fpsSdlPollSum = 0; fpsSdlPollMax = 0; fpsSdlPollN = 0;\n"
    "                    }\n"
    "                }\n"
    "                fpsPrevNs = fpsNow;\n"
    "            }\n"
    "        }\n"
    "\n"
    "        saveInputRecording();\n"
)
STEP_END_OLD = (
    "                Runner_handlePendingRoomChange(runner);\n"
    "            }\n"
    "\n"
    "            if (RunnerKeyboard_checkPressed(runner->keyboard, VK_BACKSPACE)) {\n"
)
EVENTS_OLD = (
    "            if (platformHandleEvents()) {\n"
    "                shouldWindowClose = true;\n"
    "                continue;\n"
    "            }\n"
)
EVENTS_NEW = (
    "            if (platformHandleEvents()) {\n"
    "                shouldWindowClose = true;\n"
    "                continue;\n"
    "            }\n"
    "            {\n"
    "                double _evd = (double) (nowNanos() - frameStartNow);\n"
    "                fpsPhEv += _evd; fpsPhEvN++;\n"
    "                if (_evd > fpsPhEvMax) fpsPhEvMax = _evd;\n"
    "            }\n"
)
BEGIN_OLD = (
    "            // Clear last frame's pressed/released state, then poll new input events\n"
    "            RunnerKeyboard_beginFrame(runner->keyboard);\n"
    "            RunnerGamepad_beginFrame(runner->gamepads);\n"
    "            RunnerMouse_beginFrame(runner->mouse);\n"
)
BEGIN_NEW = BEGIN_OLD + (
    "            fpsPhPre += (double) (nowNanos() - frameStartNow); fpsPhPreN++;\n"
)
STATICS_OLD = "        uint64_t lastFrameTime = nowNanos();\n"
STATICS_NEW = (
    "        uint64_t lastFrameTime = nowNanos();\n"
    "        /* Onion diagnostics (patch 006): counters shared with sdl1.c */\n"
    "        extern double fpsSdlUpdSum, fpsSdlUpdMax, fpsSdlUpdN;\n"
    "        extern double fpsSdlJsSum, fpsSdlJsMax, fpsSdlJsN;\n"
    "        extern double fpsSdlPollSum, fpsSdlPollMax, fpsSdlPollN;\n"
    "        __attribute__((used)) static double fpsPhEv = 0, fpsPhEvN = 0, fpsPhEvMax = 0;\n"
    "        __attribute__((used)) static double fpsPhPre = 0, fpsPhPreN = 0;\n"
    "        __attribute__((used)) static double fpsPhStep = 0, fpsPhStepN = 0, fpsPhStepMax = 0;\n"
    "        __attribute__((used)) static double fpsPhSwap = 0, fpsPhSwapN = 0;\n"
    "        __attribute__((used)) static double fpsPhSleep = 0, fpsPhSleepN = 0;\n"
)
STEP_END_NEW = (
    "                Runner_handlePendingRoomChange(runner);\n"
    "                {\n"
    "                    double _sd = (double) (nowNanos() - frameStartNow);\n"
    "                    fpsPhStep += _sd; fpsPhStepN++;\n"
    "                    if (_sd > fpsPhStepMax) fpsPhStepMax = _sd;\n"
    "                }\n"
)
if TAIL_OLD not in src:
    print("006 TAIL anchor not found in loop.c")
    sys.exit(1)
if STEP_END_OLD not in src:
    print("006 STEP_END anchor not found in loop.c")
    sys.exit(1)
if EVENTS_OLD not in src:
    print("006 EVENTS anchor not found in loop.c")
    sys.exit(1)
if BEGIN_OLD not in src:
    print("006 BEGIN anchor not found in loop.c")
    sys.exit(1)
if "uint64_t frameStartNow = nowNanos();" not in src:
    print("006 frameStartNow anchor not found in loop.c")
    sys.exit(1)
src = src.replace(TAIL_OLD, TAIL_NEW, 1)
src = src.replace(STEP_END_OLD, STEP_END_NEW, 1)
src = src.replace(EVENTS_OLD, EVENTS_NEW, 1)
src = src.replace(BEGIN_OLD, BEGIN_NEW, 1)
src = src.replace(STATICS_OLD, STATICS_NEW, 1)
open(LOOP, "w", encoding="utf-8", newline="\n").write(src)

# ---- 006 part 2: sdl1.c sub-phase timers inside platformHandleEvents
# zone "upd"  = SDL_JoystickUpdate() alone
# zone "slot" = our per-slot polling loop (GetButton/GetHat/GetAxis/Name)
# zone "poll" = the SDL_PollEvent loop (fbcon keyboard/mouse + rest)
S1_HAND_HANDLE = "bool platformHandleEvents(void) {"
S1_UPD = "    SDL_JoystickUpdate();\n"
S1_SLOT0 = "    g_runner->gamepads->connectedCount = 0;\n"
S1_JS_END = (
    "    }\n"
    "\n"
    "    SDL_Event e;\n"
    "    while (SDL_PollEvent(&e)) {\n"
)
S1_FUNC_END = (
    "    }\n"
    "\n"
    "    return false;\n"
)
s1src = open(S1, "r", encoding="utf-8").read()
checks = {
    "HAND_HANDLE": (s1src, S1_HAND_HANDLE),
    "UPD": (s1src, S1_UPD),
    "SLOT0": (s1src, S1_SLOT0),
    "JS_END": (s1src, S1_JS_END),
    "FUNC_END": (s1src, S1_FUNC_END),
}
for name, (txt, anchor) in checks.items():
    n = txt.count(anchor)
    if n != 1:
        print("006 anchor", name, "count", n, "in sdl1.c")
        sys.exit(1)
s1src = s1src.replace(S1_HAND_HANDLE,
    "/* Onion diagnostics (patch 006): shared with loop.c */\n"
    "double fpsSdlUpdSum = 0, fpsSdlUpdMax = 0, fpsSdlUpdN = 0;\n"
    "double fpsSdlJsSum = 0, fpsSdlJsMax = 0, fpsSdlJsN = 0;\n"
    "double fpsSdlPollSum = 0, fpsSdlPollMax = 0, fpsSdlPollN = 0;\n"
    + S1_HAND_HANDLE, 1)
s1src = s1src.replace(S1_HAND_HANDLE,
    S1_HAND_HANDLE + "\n    uint64_t _evt0 = nowNanos();", 1)
s1src = s1src.replace(S1_UPD,
    "    uint64_t _upd0 = nowNanos();\n"
    + S1_UPD +
    "    {\n"
    "        double _udd = (double) (nowNanos() - _upd0);\n"
    "        fpsSdlUpdSum += _udd; fpsSdlUpdN++;\n"
    "        if (_udd > fpsSdlUpdMax) fpsSdlUpdMax = _udd;\n"
    "    }\n", 1)
s1src = s1src.replace(S1_SLOT0,
    "    uint64_t _slot0 = nowNanos();\n" + S1_SLOT0, 1)
s1src = s1src.replace(S1_JS_END,
    "    {\n"
    "        double _jsd = (double) (nowNanos() - _slot0);\n"
    "        fpsSdlJsSum += _jsd; fpsSdlJsN++;\n"
    "        if (_jsd > fpsSdlJsMax) fpsSdlJsMax = _jsd;\n"
    "    }\n"
    + S1_JS_END, 1)
s1src = s1src.replace(S1_FUNC_END,
    "    {\n"
    "        double _pld = (double) (nowNanos() - _evt0);\n"
    "        fpsSdlPollSum += _pld; fpsSdlPollN++;\n"
    "        if (_pld > fpsSdlPollMax) fpsSdlPollMax = _pld;\n"
    "    }\n"
    + S1_FUNC_END, 1)
open(S1, "w", encoding="utf-8", newline="\n").write(s1src)

diff = run(["git", "-C", UP, "diff", "--", "src/loop.c", "src/backends/sdl1.c"]).stdout
open(P006, "w", encoding="utf-8", newline="\n").write(diff)
print("006 written:", len(diff), "bytes")

# ---- step 3.5: patch 007 — cache SDL_JoystickName (SDL 1.2 opens the device +
#      issues EVIOCGNAME/JSIOCGNAME ioctls EVERY call; our slot loop calls it
#      every frame -> ~50ms/frame on MiaUI keymatrix. ROOT CAUSE of ~15fps.)
P007 = "/patches/007-joyname-cache.patch"
run(["git", "-C", UP, "add", "-A"])
s1src = open(S1, "r", encoding="utf-8").read()
NAME_OLD = "            const char* name = SDL_JoystickName(slotIdx);\n"
NAME_NEW = (
    "            /* Onion perf fix (patch 007): SDL 1.2's SDL_JoystickName()\n"
    "             * open()s the device and issues EVIOCGNAME/JSIOCGNAME ioctls\n"
    "             * on EVERY call (~50ms on MiaUI keymatrix); we poll it every\n"
    "             * frame, so cache the result per slot index instead. */\n"
    "            static char joyNameCache[MAX_GAMEPADS][64];\n"
    "            static SDL_Joystick* joyNameJoy[MAX_GAMEPADS];\n"
    "            const char* name = NULL;\n"
    "            if (joyNameJoy[slotIdx] != joy) {\n"
    "                const char* n = SDL_JoystickName(slotIdx);\n"
    "                if (n != NULL) {\n"
    "                    strncpy(joyNameCache[slotIdx], n, sizeof(joyNameCache[slotIdx]) - 1);\n"
    "                    joyNameCache[slotIdx][sizeof(joyNameCache[slotIdx]) - 1] = '\\0';\n"
    "                } else {\n"
    "                    joyNameCache[slotIdx][0] = '\\0';\n"
    "                }\n"
    "                joyNameJoy[slotIdx] = joy;\n"
    "            }\n"
    "            if (joyNameCache[slotIdx][0] != '\\0') name = joyNameCache[slotIdx];\n"
)
if s1src.count(NAME_OLD) != 1:
    print("007 NAME anchor not unique in sdl1.c")
    sys.exit(1)
s1src = s1src.replace(NAME_OLD, NAME_NEW, 1)
open(S1, "w", encoding="utf-8", newline="\n").write(s1src)
diff = run(["git", "-C", UP, "diff", "--", "src/backends/sdl1.c"]).stdout
open(P007, "w", encoding="utf-8", newline="\n").write(diff)
print("007 written:", len(diff), "bytes")

# ---- step 3.6: patch 008 — clean exit combo + cursor hide
#      (a) Select(sdl 8)+Start(sdl 9) combo -> platformHandleEvents returns true
#          -> loop breaks -> platformExit() -> clean shutdown (launch.sh trap
#          restores CPU governor; minui returns to menu)
#      (b) SDLK_MENU keydown quits (if the MiaUI keymon forwards the MENU key
#          to SDL); KEYLOG prints every distinct keydown sym once so the next
#          session can identify the MENU key's actual code
#      (c) fbcon stub mouse cursor (never moves, top corner) hidden forever
P008 = "/patches/008-exit-cursor.patch"
run(["git", "-C", UP, "add", "-A"])
s1src = open(S1, "r", encoding="utf-8").read()

E8_F4 = (
    "                if (e.key.keysym.sym == SDLK_F4 && (e.key.keysym.mod & KMOD_ALT)) {\n"
    "                    return true;\n"
    "                }\n"
)
E8_F4_NEW = E8_F4 + (
    "                /* Onion (patch 008): one-time keydown log to identify the\n"
    "                 * MiaUI MENU key's SDL keycode on-device. */\n"
    "                {\n"
    "                    static int lastLoggedSym = -1;\n"
    "                    if (e.key.keysym.sym != lastLoggedSym) {\n"
    "                        logError(\"KEYLOG: sym=%d uni=%d\\n\",\n"
    "                            e.key.keysym.sym, e.key.keysym.unicode);\n"
    "                        lastLoggedSym = e.key.keysym.sym;\n"
    "                    }\n"
    "                }\n"
    "#ifdef SDLK_MENU\n"
    "                /* Onion (patch 008): hardware MENU key quits if it reaches SDL. */\n"
    "                if (e.key.keysym.sym == SDLK_MENU) {\n"
    "                    logError(\"KEYLOG: MENU key -> exit\\n\");\n"
    "                    return true;\n"
    "                }\n"
    "#endif\n"
)
if s1src.count(E8_F4) != 1:
    print("008 F4 anchor not unique in sdl1.c")
    sys.exit(1)
s1src = s1src.replace(E8_F4, E8_F4_NEW, 1)

# NOTE: with 006 applied there is an instrumentation block between the switch
# close and the while close, so anchor on the FUNCTION BOUNDARY instead:
# "    }\n    }\n\n    return false;\n}\n\nvoid platformSleepUntil..."
E8_QUIT = (
    "    }\n"
    "    }\n"
    "\n"
    "    return false;\n"
    "}\n"
    "\n"
    "void platformSleepUntil(uint64_t time) {\n"
)
E8_QUIT_NEW = (
    "    }\n"
    "    }\n"
    "\n"
    "    /* Onion (patch 008): exit combo for MiaUI RG35XX (no OS quit path):\n"
    "     * Select (sdl 8) + Start (sdl 9) held together closes the game. */\n"
    "    for (int i = 0; i < MAX_GAMEPADS; i++) {\n"
    "        SDL_Joystick* exj = openJoysticks[i];\n"
    "        if (!exj) continue;\n"
    "        if (SDL_JoystickNumButtons(exj) > 9 &&\n"
    "            SDL_JoystickGetButton(exj, 8) && SDL_JoystickGetButton(exj, 9))\n"
    "            return true;\n"
    "    }\n"
    "\n"
    "    return false;\n"
    "}\n"
    "\n"
    "void platformSleepUntil(uint64_t time) {\n"
)
if s1src.count(E8_QUIT) != 1:
    print("008 QUIT anchor not unique in sdl1.c")
    sys.exit(1)
s1src = s1src.replace(E8_QUIT, E8_QUIT_NEW, 1)

E8_REPEAT = "    SDL_EnableKeyRepeat(0, 0);\n"
if s1src.count(E8_REPEAT) != 1:
    print("008 REPEAT anchor not unique in sdl1.c")
    sys.exit(1)
s1src = s1src.replace(E8_REPEAT,
    E8_REPEAT + "\n"
    "    /* Onion (patch 008): fbcon draws a stub mouse cursor that never moves\n"
    "     * and sits in the corner; hide it for good. */\n"
    "    SDL_ShowCursor(SDL_DISABLE);\n", 1)

E8_CUR = (
    "    // SDL1.2 only supports showing/hiding\n"
    "    SDL_ShowCursor(cursorType == GML_CR_NONE ? SDL_DISABLE : SDL_ENABLE);\n"
)
E8_CUR_NEW = (
    "    // SDL1.2 only supports showing/hiding. Onion (patch 008): always hide —\n"
    "    // the GML game never uses a real cursor and fbcon's stub sits in a corner.\n"
    "    (void) cursorType;\n"
    "    SDL_ShowCursor(SDL_DISABLE);\n"
)
if s1src.count(E8_CUR) != 1:
    print("008 CURSOR anchor not unique in sdl1.c")
    sys.exit(1)
s1src = s1src.replace(E8_CUR, E8_CUR_NEW, 1)

open(S1, "w", encoding="utf-8", newline="\n").write(s1src)
diff = run(["git", "-C", UP, "diff", "--", "src/backends/sdl1.c"]).stdout
open(P008, "w", encoding="utf-8", newline="\n").write(diff)
print("008 written:", len(diff), "bytes")

# ---- step 4: fresh pristine, verify full ordered chain
reset_pristine()
order = ["001-rg35xx-fallback-mapping.patch", "005-sdl1-error.patch",
         "002-chunklog.patch", "003-stage-markers.patch", "004-sdl-error.patch",
         "006-fpslog.patch", "007-joyname-cache.patch", "008-exit-cursor.patch"]
for p in order:
    run(["git", "-C", UP, "apply", "--ignore-whitespace", "--whitespace=nowarn",
         "/patches/" + p])
    print("APPLY OK:", p)
print("--- 001 hunks ---")
for line in open(P001, encoding="utf-8"):
    if line.startswith("@@"):
        print(line.rstrip())
print("--- 005 hunks ---")
for line in open(P005, encoding="utf-8"):
    if line.startswith("@@"):
        print(line.rstrip())
print("--- 006 hunks ---")
for line in open(P006, encoding="utf-8"):
    if line.startswith("@@"):
        print(line.rstrip())
print("--- 007 hunks ---")
for line in open(P007, encoding="utf-8"):
    if line.startswith("@@"):
        print(line.rstrip())
print("--- 008 hunks ---")
for line in open(P008, encoding="utf-8"):
    if line.startswith("@@"):
        print(line.rstrip())
print("ALL_PATCHES_OK")
