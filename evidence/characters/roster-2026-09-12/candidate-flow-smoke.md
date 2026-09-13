# Production roster selection-to-battle flow smoke

The production `available.json` now exposes nine base fighters and four helpers. This Godot smoke loads the ordinary `main.tscn` scene and drives title, fighter, helper, map, intro, and battle states through `InputEventKey` on the normal 30 Hz physics path. It does not inject candidate mappings or call selection callbacks directly.

Sakura, base Rukia, and Yulong each enter their own source-derived opening, finish it naturally without an intro-skip input, and receive a J attack input that enters a source attack action. Each case selects Ino (`松本` → `jinye`) and presses O to activate that helper. The isolated test seeds P1 energy to 100 immediately before O because the compiled source command requires `energy_min: 100`; this controlled precondition is not a claim that the opening grants full energy. The selected Ino helper resource is used even where another source label is present in a fighter's summon event.

Command:

```sh
/private/tmp/bvn-toolchain-2026-09-12/Godot.app/Contents/MacOS/Godot \
  --headless --path godot \
  --script res://tests/roster_candidate_flow_smoke.gd \
  --log-file /private/tmp/roster-flow-public-9x4.log
```

Result: `ROSTER_CANDIDATE_FLOW_SMOKE_OK`. All three candidates completed the natural intro, entered an authored attack, and activated the selected Ino helper at source frame 2. The test is a native production-registry scene-flow check; it does not establish browser keyboard automation or full original Flash parity. The final verbose run exited successfully with no ObjectDB/resource leak warnings after audio players were stopped and their stream references cleared. Godot still reports the environment's macOS CA-certificate diagnostic.
