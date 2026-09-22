# Input decoupling evidence

2026-09-22. Input delivery refactor; no combat rule or source scheduling change.
Implementation and developer commands: [guide](../../docs/input-decoupling/IMPLEMENTATION.md).

## Source-first audit

1. **Frame/handler source.** `scripts/main.json::frame_7/DoAction.as` supplies
   configured P1/P2 key codes. `DefineSprite_1991/frame_1/DoAction.as` defines
   `renderSkip`: poll held J/N1 during steps 2–3, then move curtain to
   `skipintro`. The same script's `onKeyUp` uses fixed Enter/Up/Down, initializes
   Cancel on open and dispatches Title / Move List / resume. `frame_8/DoAction.as`
   owns conditional `stopMc/playMc` and `pauseGame2/resumeGame2`.
   `DefineButton2_2009` handles detail-page Enter press and mouse release.
   The complete source/timeline audit is retained in [pause-menu.md](../pause-menu.md)
   and [intro-source.json](../intro-source.json). Fighter key reads remain the
   compiled controller hooks, e.g. `scripts/fighter/minren.json::DefineSprite_764/frame_1/PlaceObject2_16_31/CLIPACTIONRECORD onClipEvent(enterFrame).as`,
   reached through `PlayerBodyDriver.Context.source_key`.
2. **Placement/lifetime.** Main `game_menu` is sprite 2010, depth 157; opening
   reuses it via visibility and gotoAndStop(1). Frames 2–9 have no frame script;
   frame 10 stops. This refactor changes neither placement nor callback lifetime,
   and preserves the button's press/release pairing. Controller hook placement
   and source callback registration are untouched.
3. **Exits.** Detail back goes to panel frame 1 without resume. Enter press on
   detail returns to frame 1; its subsequent release dispatches Cancel. Title
   exits to MENU and destroys the battle; Cancel resumes existing clips.
   Intro skip still follows the compiled curtain/Ready transitions.
4. **Invariants.** Preserve simultaneous absolute directions, held reads,
   remapped fighter buttons, fixed pause keys, both explicit slots, AI branch,
   immediate control delivery, source press/release ordering and conditional
   pause. Input log validation/keyboard isolation are engineering contracts,
   not claims about additional original gameplay behavior.
5. **Original same-input evidence.** Reused immutable shared-mode PVP and
   training-timer captures and CPU r13/r14/r15 captures. Source/native results
   below concern their measured fields only. No new Flash capture was needed
   to change the producer boundary; original pause-menu press/mouse timing
   remains unmeasured, as explicitly retained by its earlier evidence. This
   refactor does not declare that missing parity gate complete.

## Measured checks

Godot 4.7.2-stable official, native headless on macOS:

- `match_input_smoke.gd`: remapping J to Q, simultaneous left/right, independent
  P2 numpad input, release edges, JSON roundtrip, same-tick ordered controls,
  playback ignoring held real keys without clearing them, missing samples and
  slots/buttons, inconsistent edges, incomplete/endless/unsupported documents,
  and wrong runtime tick rejection.
- `match_input_scene_smoke.gd`: 330 display ticks / both actors exactly match
  through fresh setup, held intro skip, movement, attack/received damage, jump,
  pause, detail timeline, unmatched mouse release, release outside, paired back,
  Enter press→release resume, repeated pause and terminal Title/recreated scene.
  State comparison includes source frame, action, X/Y, facing, HP, energy, hits,
  pause state, intro step and pause-menu selection/frame. Random and clock
  consumers are separately replayed and completely consumed; callbacks run in
  the synchronous test schedule. Nondefault life/time are restored.
- Existing player controller, player visual, pause menu, Move List, intro,
  Vs Com, combat, menu and reference-input smoke checks pass. The visual and
  Vs Com tests read delivered input after its display update, then retain all
  their existing movement, child-frame and facing assertions.
- `tools/test_shared_modes.py`: PVP **602/602** actor states matched; training
  timer **602/602** matched. Original inputs and comparator are unchanged.

- Original CPU r13: **1166/1166** source boundaries; r14: **1084/1084**.
  Both completely consume random/clock tapes and match measured source fields.
  The r13 logical-adapter report is byte-for-byte identical to its preceding
  device-adapter report (parsed reports also compare equal).
- r15 remains a **preexisting failure** at display tick **2593**, expected
  fighter frames `[2, 2]`, actual `[1, 1]`. An isolated pre-change HEAD project
  restored main/session/pause and the old keyboard reference adapter while
  sharing unchanged assets. Its complete result equals the new result, including
  all 2854 consumed boundaries, geometry, inputs, state differences and tape
  positions. No thresholds or reference outputs were changed. The older r15
  success recorded elsewhere is not current acceptance evidence.
- Existing diagnostic export/replay: 400 ticks, 800 input records, 824 events,
  five random records; no event or final-snapshot differences. Result is
  `semantic_match_version_unverified` because this checkout's diagnostic build
  metadata is empty. This is compatibility evidence, not verified build identity.
- Final Web export passes and the in-app Chromium page boots with
  `M0_BOOT_OK`, `display_server=web`, 30 Hz; no browser error/warning logs.
  Full keyboard battle flow and Firefox/Safari were not verified in this run.
- `validate_contracts.py`: six schemas / six examples pass; the actual 330-tick
  captured document also passes the new schema. `verify.py`, `check_handoff.py`
  and `git diff --check` pass after updating hashes for reviewed changes.

Compact machine-readable results and runtime hashes: [results.json](results.json).
Temporary native reports/logs are under `/tmp/input-*`; exported artifacts are
in ignored `dist/web/`, not committed sources. No deployment was performed.

Reproduce native checks from the repository root:

```sh
/path/to/Godot --headless --path godot -s res://tests/match_input_smoke.gd
/path/to/Godot --headless --path godot -s res://tests/match_input_scene_smoke.gd
python3 tools/test_shared_modes.py --godot /path/to/Godot
/path/to/Godot --headless --path godot -s res://tests/intro_continuous_reference.gd -- /absolute/repo/evidence/ai/input-binary-r13/events.jsonl /tmp/r13.json combat-boundaries
```

The reference runner requires an absolute source path. Its process exit code
alone is insufficient: read the report's status, boundary count and tape
completion flags. For r15 use `match-flow-r15/events.jsonl` and retain its known
first difference instead of treating exit code zero as success.
Existing sandbox CA-certificate/editor-settings warnings and headless audio
ObjectDB/resource shutdown warnings are separate from script/assertion errors;
smoke markers and exit status are both checked. No clean-log or full audiovisual
parity claim is made.


## Review fix: mutually exclusive recording/playback

The new scene regression first failed on the reviewed implementation with
`Armed recording must reject playback before changing match state` (exit 1).
`start_input_playback` now rejects an armed recording before any setup or mode
mutation. The test verifies that the scene, actor identity, settings and pending
output path remain unchanged, and that the pending recording can still start.
It also checks rejection in the reverse direction, then completes the existing
330-tick two-player playback with real keyboard input held throughout.

After the fix, `MATCH_INPUT_SCENE_SMOKE_OK` and `MATCH_INPUT_SMOKE_OK` both pass
with exit 0 and no script errors. Red/green logs are `/tmp/input-mode-conflict-red.log`
and `/tmp/input-mode-fix-*.log`. Package, handoff and contract checks pass.
This follow-up changes only the developer mode-entry guard; earlier source/Web
results above retain their original evidence scope and runtime hashes.
