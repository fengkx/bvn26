# Source-driven match opening

2026-09-08. Implemented for the currently playable Naruto/Ichigo base-form slice.
Original-player timing comparison remains pending; this is not full-content or
frame-parity acceptance. The user explicitly requested implementation from code
first and original-player comparison afterward.

## Source-first checklist

1. `scripts/main.json`, `DefineSprite_1991/frame_1/DoAction.as`: `kaichang`,
   `goStep`, `renderSkip`, initial `zhanting`, focus and menu lock. Poll interval
   is 500 ms. Steps are open curtain, P1 intro, P2 intro, ready playback.
   `DefineSprite_1882` has scripts only on frames 1, 2 and 127; `DefineSprite_1885`
   on 1, 10, 21, 29, 36 and 40. Full frame-level fighter scripts, empty frames,
   sound events and placement deltas are in [intro-source.json](intro-source.json).
2. The compiler preserves every source display-list placement, matrix, color
   transform, `placed_frame`, and `move` flag. Naruto's 1099–1178 and Ichigo's
   822–901 opening ranges reach bitmap animation clips, plus the shared body
   clips 2/3; no additional character-specific enterFrame motion was found in
   that reachable subtree. Common body callbacks remain gated by root zhanting.
3. Naruto frame 1160 and Ichigo frame 883 set `kcplayed=2`, then explicitly go
   to standing and play. They do not wait for the label end. `ready` unlocks at
   127 and naturally wraps from 132 to stopped frame 1. Skipping enters curtain
   frame 33; frame 36 resets both players/focus and starts the HUD entrance;
   frame 40 unlocks and goes to stopped frame 1.
4. Regressions assert these source transitions, input locking, the 500 ms first
   poll, separate P1/P2 completion, both skip paths and re-entry. Numerals use
   `roundshu.gotoAndStop(rounds+5)`; nested digit transitions stop on their
   authored fifth frame. Ready speech uses SOUNDINFO positions 50124, 50627,
   and 92879 at 44.1 kHz. Vector outlines are rasterized from the locked SWF,
   not drawn as shape bounding boxes. Upper HUD matrices use sprite 1815,
   frames 1–5, with the source `in` label at 2.
5. Native Godot rendered snapshots were inspected for both character intros,
   ROUND 1, READY and FIGHT. Original Flash Player access through computer-use
   failed twice with `timeoutReached`; no identical-input original-player
   replay was obtained. The source interval is advanced with the fixed-step
   duration; its phase relative to native Flash frame callbacks, nested-frame
   age, audio latency and raster/filter differences still require comparison.

## Implementation and validation

- Compiler: `tools/importer/build_intro.py`; production fields/assets:
  `godot/generated/main/intro/`. Source snippets remain in evidence only.
- `BattleIntro` controls the source stages, flags, polling, focus, HUD entrance
  and skip path. `IntroClip` draws original vector outlines and handles the
  source digit stops and segmented audio. Existing fighter action exits are reused.
- Current shared-worktree Python suite: 46 tests passed, including three intro
  source tests. `INTRO_SMOKE_OK`, `MENU_SMOKE_OK`, and `COMBAT_SMOKE_OK` observed,
  exit code 0. Intro smoke has no resource-leak or script-error output. Existing
  combat smoke still reports audio resource leaks at shutdown.
- Handoff and contract validation passed. Final `tools/verify.py` is blocked
  by a concurrent edit outside this change: hash mismatch for
  `tools/probes/as2/ai_reference/bootstrap.as`. Only STATUS/tasks hashes were
  refreshed here; the unrelated AI checksum was left to its owning change.
- Native Godot rendering succeeded; temporary captures are `/tmp/intro-49.png`,
  `/tmp/intro-124.png`, `/tmp/intro-209.png`, `/tmp/intro-244.png`, and
  `/tmp/intro-279.png`. They are development outputs, not shipped assets.
- Web release export regenerated `dist/web/index.html` and its resource pack.
  The sandboxed editor reported inability to save its global editor settings;
  the export completed. Headless checks also log the macOS certificate-store
  diagnostic; no intro GDScript errors remain.
- Other characters/forms and selecting P1/P2 roles remain outside the currently
  playable two-character slice. The legacy command-catalog cinematic gap has
  not been reclassified as full-content acceptance.

Rebuild:

```sh
python3 tools/importer/build_intro.py --workspace /tmp/main-pinned --ffdec-jar /tmp/ffdec-26.2.1/ffdec-cli.jar
python3 -m unittest discover -s tools/tests
# Use the configured Godot 4.7.2 executable.
godot --headless --path godot --script res://tests/intro_smoke.gd
```
