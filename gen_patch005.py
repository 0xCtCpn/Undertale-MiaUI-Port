#!/usr/bin/env python3
"""Apply patch 001 to upstream, then edit the SDL_Init error line (patch 005's
change) and emit a regenerated 005 patch via git diff so 005's hunk headers
match the post-001 file (line numbers shifted by 001's insertions)."""
import sys

UPSTREAM = "/build/upstream"
S1 = UPSTREAM + "/src/backends/sdl1.c"
P001 = "/patches/001-rg35xx-fallback-mapping.patch"

import subprocess

r = subprocess.run(["git", "-C", UPSTREAM, "apply",
                    "--ignore-whitespace", "--whitespace=nowarn", P001],
                   capture_output=True, text=True)
if r.returncode != 0:
    print("001 apply failed:", r.stderr)
    sys.exit(1)

src = open(S1, "r", encoding="utf-8").read()
old = 'logError("Failed to initialize SDL\\n");'
new = 'logError("Failed to initialize SDL: %s\\n", SDL_GetError());'
if old not in src:
    print("005 target line not found")
    sys.exit(1)
src = src.replace(old, new, 1)
open(S1, "w", encoding="utf-8").write(src)

diff = subprocess.run(["git", "-C", UPSTREAM, "diff", "--", "src/backends/sdl1.c"],
                      capture_output=True, text=True)
if diff.returncode != 0:
    print("git diff failed:", diff.stderr)
    sys.exit(1)

# Strip the 001 portion (it is already the standalone 001 patch): the diff
# includes everything since the pristine state, so to get *only* the 005
# change, restore the file to the 001-applied state first.
restored = subprocess.run(["git", "-C", UPSTREAM, "checkout",
                           "--", "src/backends/sdl1.c"],
                          capture_output=True, text=True)
r = subprocess.run(["git", "-C", UPSTREAM, "apply",
                    "--ignore-whitespace", "--whitespace=nowarn", P001],
                   capture_output=True, text=True)
if r.returncode != 0:
    print("001 re-apply failed:", r.stderr)
    sys.exit(1)

src = open(S1, "r", encoding="utf-8").read()
src = src.replace(old, new, 1)
open(S1, "w", encoding="utf-8").write(src)

diff = subprocess.run(["git", "-C", UPSTREAM, "diff", "--", "src/backends/sdl1.c"],
                      capture_output=True, text=True)
open("/patches/005-sdl1-error.patch", "w", encoding="utf-8", newline="\n").write(diff.stdout)

# Restore pristine upstream for cleanliness and verify the chain end-to-end.
subprocess.run(["git", "-C", UPSTREAM, "checkout", "--", "src/backends/sdl1.c"])
ok = True
for p in ["001-rg35xx-fallback-mapping.patch", "005-sdl1-error.patch",
          "002-chunklog.patch", "003-stage-markers.patch", "004-sdl-error.patch"]:
    r = subprocess.run(["git", "-C", UPSTREAM, "apply",
                        "--ignore-whitespace", "--whitespace=nowarn", "/patches/" + p],
                       capture_output=True, text=True)
    print("APPLY", p, "OK" if r.returncode == 0 else "FAIL " + r.stderr)
    if r.returncode != 0:
        ok = False
        break
print("--- generated 005 ---")
print(open("/patches/005-sdl1-error.patch").read())
sys.exit(0 if ok else 1)
