# Lee callback exact comparison r14

This is the recorded P2 recovery-dash fixture from the same original SWF run `lee-callback-lifecycle-recovery-r01`, replayed for its full 900 ticks. It compares only observed P2 body frame-action rows 1134, 1144, 1158, 1159, and 1161 on `source_frame`, `entering`, decoded `action`, and decoded `ql`. The original fixture has P1 down+special at ticks 10–12 and P2 dash at ticks 76–79, with P1 Byakuya/P2 Lee and Soul helpers. The source clip event at 1133 is excluded from this body-only comparison and stays source-only.

Source produced ten ordered enter/exit rows and native reproduced all ten with zero differences. Three selected rows are opening observations (`fight_tick=-1` in the source log); the two recovery callbacks are source fight ticks 78 and 88. Godot ticks are preserved in the raw comparison but not equated to source clocks.

Reproduce from the repository root:

```sh
/private/tmp/godot-4.7.2/Godot.app/Contents/MacOS/Godot --headless --path godot --log-file /private/tmp/lee-callback-exact-r14-paired.log -s res://tests/lee_callback_exact_probe.gd -- --batch "$PWD/evidence/characters/lee/godot/callback-exact-r14/paths.json" "$PWD/evidence/characters/lee/godot/callback-exact-r14/out" > evidence/characters/lee/godot/callback-exact-r14/engine.log 2>&1
python3 evidence/characters/lee/godot/callback-exact-r14/compare_exact.py
python3 evidence/characters/lee/godot/callback-exact-r14/update_inventory.py
```
