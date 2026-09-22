# Lee callback exact comparison r12

This batch adds five same-source-run, full-duration headless comparisons for P1 Lee body frame-action callbacks. The bounded fields are `source_frame`, `entering`, decoded `action`, and decoded `ql`; this does not establish full-state or full-role parity.

Cases: exploratory ranged frame 320, conditioned up+attack frame 370, conditioned up+ranged frame 558, jump attack frame 128, and held jump+ranged frame 152. Each fixture is bound to its original run ID, raw events, actual source build/output hash, instrumentation, actor/helper selection, setup, and input tape in `preflight.json`. Original key-read audit passed for all five fixtures. Source timestamps are retained but are not compared to Godot physics ticks.

Reproduce from the repository root:

```sh
/private/tmp/godot-4.7.2/Godot.app/Contents/MacOS/Godot --headless --path godot --log-file /private/tmp/lee-callback-exact-r12-paired.log -s res://tests/lee_callback_exact_probe.gd -- --batch "$PWD/evidence/characters/lee/godot/callback-exact-r12/paths.json" "$PWD/evidence/characters/lee/godot/callback-exact-r12/out" > evidence/characters/lee/godot/callback-exact-r12/engine.log 2>&1
python3 evidence/characters/lee/godot/callback-exact-r12/compare_exact.py
python3 evidence/characters/lee/godot/callback-exact-r12/update_inventory.py
```

Observed result: 5/5 cases exact, 10 source and 10 native callback rows, zero field differences. These five rows increase the current-derived 49-entry callback inventory from 25 to 30 native-matched. Clip callbacks, other state fields, presentation, and full combat parity are outside this batch.
