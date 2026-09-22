# Lee callback exact comparison r10

This is a same-source-run, headless Godot comparison for the P1 body frame-action at source frame 771. Only `source_frame`, `entering`, decoded `action`, and decoded `ql` are in scope; no full-state, visual, or character parity claim is made.

Source capture `lee-callback-air-super-738-771-r01` uses Lee P1 / Ichigo P2, Gaara/Kon, x=300/350, ql=300, jump at ticks 5–6 and special at ticks 20–23. The completed original capture spans 600 fight ticks. Source frame 771 enters/exits once at fight tick 91, action 0, ql 200; the matching current Godot fixture emitted the same two events. Source frame 738 has no body marker in the raw capture and remains unobserved; it is not counted.

`comparison.json` binds the actual source raw/build/instrumentation and native fixture/runtime hashes. `partial-attempt-01/` retains the first observer run, which also reported P2's same-numbered frame; the accepted run uses `source_callback_targets.slot` filtering in the read-only probe and contains only the requested P1 callback. The probe change does not affect production runtime or inputs.

Reproduce from the repository root:

```sh
/private/tmp/godot-4.7.2/Godot.app/Contents/MacOS/Godot --headless --path godot --log-file /private/tmp/lee-callback-exact-r10-air-super-filtered.log -s res://tests/lee_callback_exact_probe.gd -- --batch "$PWD/evidence/characters/lee/godot/callback-exact-r10/paths.json" "$PWD/evidence/characters/lee/godot/callback-exact-r10/out" > evidence/characters/lee/godot/callback-exact-r10/engine.log 2>&1
python3 evidence/characters/lee/godot/callback-exact-r10/compare_exact.py
python3 evidence/characters/lee/godot/callback-exact-r10/update_inventory.py
```
