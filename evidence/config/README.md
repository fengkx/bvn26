# Config and timeout source parity — 2026-09-09

## Scope and source-first answers

Locked `game/main.swf` remains unchanged. `config-timeout-source.json` and generated metadata retain source paths and placement evidence. The native implementation covers Config navigation, difficulty, round time, life, storage, key configuration return, countdown, and timeout win/draw transitions. Normal is deliberately hidden until implemented; the initial selection is Vs Com.

1. **Frame scripts:** Config is root frame 16 / label 游戏设置, Sprite 836. Its six-row selector and option load/keyDown/enterFrame callbacks are extracted by `build_config_model.py`. Timer Sprite 1813 uses the original 1000 ms `time()` callback. Timeout Sprite 1848 frame scripts and nested callbacks are compiled without guessed durations.
2. **Placement and MOVE:** Config option clips occupy depths 1/6/11/28, selector depth 33. The key page at frame 5 replaces those placements. Timeout winner child load at frame 62 sets source X -0.3 or 203.8; its assets and placement lifetimes come from the SWF timeline.
3. **Leaving labels:** Config frame 1 stops. J on row 1 enters 键位设置; button 740 release returns to Config frame 1, without saving. K or row 6 saves and returns to MENU. Timeout branches at frame 54 to winner 62 or draw 212, jumps 199→340, schedules nextfight at 350, and naturally wraps to frame 1.
4. **Invariants:** AI levels are 5→1; time is 30/60/90/100 (100 means unlimited); HP is 1000→5000. Independent A/D guards intentionally allow internal cl=0 and N+1; only valid enterFrame values write settings. Preserve original `qualiy` storage spelling and LOW's `_root.quality` assignment bug: selecting LOW leaves the actual `_quality` unchanged. Countdown pauses when zhanting or either sw is set, and has no interval in unlimited/training. Timeout compares actual remaining HP, awards a win only to the higher-HP side, and resets time/HP for the next round.
5. **Original comparison:** Native Flash runs of unchanged original option callback bodies produce 161 snapshots, all matched by Godot. Native timeout traces match 230 winner and 221 draw snapshots up to the first nextfight, including winner counters, pause/state flags and timeline branches. The subsequent nextfight is injected and verified separately in Godot; this is not a complete wall-clock phase or physical keyboard dispatch oracle.

## Evidence and reproduction

- `original/options.log`, build metadata and instrumentation diff: original Config callback oracle.
- `timeout-p1/`, `timeout-draw/`: collected original traces, events, build metadata and instrumentation diffs.
- `native/timeout-*.json`: compared snapshots and continued native state observations.
- `native/checks.json`: native checks and existing r13/r14/r15 match replay results.
- `native/title.png`, `native/options.png`: inspected native screenshots (900×600).

Generate models with `python3 tools/importer/build_config_model.py` and `python3 tools/importer/build_timeout_model.py --workspace /tmp/bvn-main-ko` (the latter requires the pinned JPEXS workspace). Original probes are `tools/probes/build_config_reference.py` and `tools/probes/build_ai_reference.py --timeout-probe p1|draw`; use their CLI help for isolated output/workspace options.

Run Godot 4.7.2 headless with `--path godot --script res://tests/config_reference_smoke.gd`, `config_flow_smoke.gd`, and `timeout_reference.gd`. Timeout fixtures accept `-- p1|draw OUTPUT.json`. The flow check uses actual input dispatch, saves/reloads an isolated settings file, verifies configured AI/HP/time at fight entry, exercises pause/unlimited/training, and walks both menu directions for 700 ticks each without selecting Normal. Existing menu, player movement/visual and KO-resume checks pass; 67 Python tests pass. Existing r13/r14/r15 combat boundary replays still report `boundary_segment_observed_fields_match`.

## Remaining limits

Config is a native English layout, not a pixel reconstruction. Quality state and the original LOW bug are reproduced, but Flash vector antialiasing levels have no equivalent implemented in this prerendered-bitmap renderer; quality rendering parity is pending. Timeout winner HUD counts update, but the original badge blink is not implemented by the existing HUD. Some headless main-loop checks report existing resource cleanup warnings despite passing assertions. Native checks and successful Web export do not establish browser gameplay/pixel parity. M6-02 remains pending; full mode/character selection and complete flow acceptance are outside this slice.
