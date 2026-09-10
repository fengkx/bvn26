# Sasuke original-vs-Godot diagnostic comparison r01

This is a diagnostic comparison of the retained 360-frame original-player capture against the generated Sasuke runtime. It is not a production selection-path parity result: the Godot side uses `godot/tests/sasuke_native_trace.gd` and directly instantiates `FighterRuntime`, because the shared controller alias compiler is still blocked on Sasuke's two placed input-controller instances.

## Inputs

- Original event trace: `native-probe-r01.events.jsonl.gz`; collected source rows: `/tmp/bvn-sasuke-probe-r01/collected.json/events.jsonl`.
- Godot trace: `/tmp/sasuke-native-r01.json`.
- Both traces contain 361 p1 rows (`tick=0..360`). The source setup is x=300, y=-25, energy=300, touch=true; the diagnostic fixture keeps the same floor reference and uses attack input for input ticks 10..12.

## Command

```sh
/tmp/godot-4.7.2/Godot.app/Contents/MacOS/Godot --headless --path godot -s res://tests/sasuke_native_trace.gd -- /tmp/sasuke-native-r01.json
```

The comparator uses `tools/probes/compare_mode_reference.py::source_rows` and compares every normalized p1 field in order.

## First difference

After normalizing the initial `touchFloor` setup transition, the first difference is tick 11: original `frame=203, action=0`; Godot `frame=204, action=1`. At ticks 8..10 both sides are frames 2..4, so this is the attack transition's one-frame observation/order mismatch. The original row observes the entered `砍1` frame before advancing; this direct diagnostic loop calls `enter_frame`, then advances, then observes. The fixture must be replayed through the production driver after controller alias compilation before treating this as an implementation defect.
