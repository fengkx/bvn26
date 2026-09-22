# Lee callback exact-body batch r01

This is a read-only source/native callback audit for source frames 8, 1083, 1219, and 1260. The original captures/builds remain unchanged under `evidence/characters/lee/original/`; the derived native fixtures add only `source_callback_targets` to the build-extracted move cases.

Run the headless batch with the project Godot 4.7.2 binary:

```sh
/private/tmp/godot-4.7.2/Godot.app/Contents/MacOS/Godot --headless --path godot \
  --log-file /private/tmp/lee-callback-exact-body-final-r01-godot.log \
  -s res://tests/lee_callback_exact_probe.gd -- --batch \
  "$PWD/evidence/characters/lee/godot/callback-exact-body-final-r01/paths.json" \
  "$PWD/evidence/characters/lee/godot/callback-exact-body-final-r01/out" \
  > evidence/characters/lee/godot/callback-exact-body-final-r01/engine.log 2>&1
```

`compare_fourbody.py` parses source AIREF/JSONL rows with the project parser and `decode_number`, compares callback sequences on `source_frame`, `entering`, `action`, and `ql`, and records `current_frame` separately. Full provenance and hashes are in `comparison-r01.json`.

The batch finished with `MOVE_CASE_BATCH_OK 2` and no script errors. Only the P1 kill fixture has a source/native same-input initial-state match. In that valid fixture, P1 frame 1219 and 1260 each have one matching enter/exit pair on all four accepted fields; frame 8 has repeated callback-count differences (source 248 rows, native 92), so that full sequence remains different. The P2 recovery source capture is invalid for the intended hp1 comparison: its source ready/state0 shows P2 hp 1000 and has no `source_state_precondition` event, while the derived native fixture applies P2 hp 1 before its first observation. Do not count its 8/1083/1219 rows as same-input matches or runtime failures.

The 738 stage-specific bounded check is recorded separately in `../callback-exact-stage-r01/provenance.json`; its full native replay output is not included in this four-body batch.
