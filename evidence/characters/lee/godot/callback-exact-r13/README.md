# Lee callback exact comparison r13

This comparison replays the original 900-fight-tick P2 recovery fixture with P1 Byakuya and P2 Lee, the same recorded helpers and input tape, and selects only callbacks actually present in that raw capture. It compares `source_frame`, `entering`, decoded `action`, and decoded `ql`; display/fight clocks are retained but not compared, so this does not claim full recovery-state parity.

The selected source events include body callbacks at frames 1158, 1159, and 1161 during opening (`fight_tick=-1`) and the P2 fall callback at frame 1128 (`fight_tick=106`). Native reproduced all eight ordered enter/exit events with zero differences in the four selected fields. Native's local ticks are recorded separately. The P2 clip callback at frame 1133 from the distinct recovery-dash source fixture remains source-only and is not conflated with a body action.

Reproduce from the repository root:

```sh
/private/tmp/godot-4.7.2/Godot.app/Contents/MacOS/Godot --headless --path godot --log-file /private/tmp/lee-callback-exact-r13-paired.log -s res://tests/lee_callback_exact_probe.gd -- --batch "$PWD/evidence/characters/lee/godot/callback-exact-r13/paths.json" "$PWD/evidence/characters/lee/godot/callback-exact-r13/out" > evidence/characters/lee/godot/callback-exact-r13/engine.log 2>&1
python3 evidence/characters/lee/godot/callback-exact-r13/compare_exact.py
python3 evidence/characters/lee/godot/callback-exact-r13/update_inventory.py
```
