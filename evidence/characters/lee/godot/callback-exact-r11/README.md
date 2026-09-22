# Lee callback exact comparison r11

This headless batch compares P1 body frame-action callback rows against their exact source run. Scope is limited to `source_frame`, `entering`, decoded `action`, and decoded `ql`; it does not claim full-state or full-character parity.

- `super-953-p1`: source `lee-callback-ground-super-frame953-r01`, P1 Lee/P2 Ichigo, helpers Gaara/Kon, P1 down+special at ticks 10–12. Frame 953 enter/exit is observed at source fight tick 287 with action 0 and ql 0. Native emits the same two selected fields at Godot tick 594. The clock values are recorded but not compared by this callback-only report.
- `defence-1050-1057-p1`: source `lee-callback-defence-frame1057-r02`, same actors/helpers/setup, P1 down at ticks 10–12. Frame 1050 occurs twice (including the action transition from 0 to 2); frame 1057 occurs once. Native matches all six ordered events and four compared fields. Frame 1050 is included as contextual callback evidence but is not a row in the fixed 49-entry inventory.

Both source captures completed 600 fight ticks. Native fixtures observe the full duration to preserve repeated markers. `preflight.json` binds source raw/build/instrumentation hashes, actual output main-SWF hash, fixture hash, exact input setup, slot, and targets. The build metadata's status field is preserved as recorded; each raw independently matches the run id and contains a terminal done event.

Reproduce from the repository root:

```sh
/private/tmp/godot-4.7.2/Godot.app/Contents/MacOS/Godot --headless --path godot --log-file /private/tmp/lee-callback-exact-r11-paired.log -s res://tests/lee_callback_exact_probe.gd -- --batch "$PWD/evidence/characters/lee/godot/callback-exact-r11/paths.json" "$PWD/evidence/characters/lee/godot/callback-exact-r11/out" > evidence/characters/lee/godot/callback-exact-r11/engine.log 2>&1
python3 evidence/characters/lee/godot/callback-exact-r11/compare_exact.py
python3 evidence/characters/lee/godot/callback-exact-r11/update_inventory.py
```

Frame 738 was not emitted by its source raw and is not treated as covered. Clip callbacks are outside scope.
