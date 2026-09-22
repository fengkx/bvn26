# Lee callback exact r08

This run adds a same-input headless Godot callback comparison for eight source frame-action entries. It is bounded to `source_frame`, `entering`, decoded `action`, and decoded `ql`; it does not establish whole-character parity.

The source runs are `lee-callback-ground-hold-r05` (P1 Lee, P1 attack held from tick 10 through 259; P1 helper 我爱罗, P2 helper 魂) and `lee-callback-observer-hp1-r02` (P1 Ichigo, P2 Lee at health 1; P1 attack from tick 10 through 12; helpers 我爱罗/魂). Their original build files, instrumentation diffs, source output hashes, input/setup and callback target declarations are retained under `source-builds/`; original raw source traces remain under `evidence/characters/lee/original/`. The P2 recovery slot was taken from the actual captured build/raw, not inferred from the body frame number.

The exact cases were:

- Ground frame actions 235, 240, and 268: 12 source and 12 native boundary events, including four entries to 268.
- P2 recovery frame actions 1086, 1087, 1096, 1098, and 1112: 10 source and 10 native boundary events.

All 22 events matched on the four fields. The 1098 clip callback is a distinct `clip_action`; it is explicitly excluded and remains unmatched. The batch did not capture or compare clip callbacks.

Reproduce from the repo root:

```sh
/private/tmp/godot-4.7.2/Godot.app/Contents/MacOS/Godot \
  --headless --path godot \
  -s res://tests/lee_callback_exact_probe.gd -- --batch \
  /Users/fengkx/me/code/bvn2_6/evidence/characters/lee/godot/callback-exact-r08/paths.json \
  /Users/fengkx/me/code/bvn2_6/evidence/characters/lee/godot/callback-exact-r08/out
```

`comparison.json` contains per-event source/native rows, fixture/build/raw hashes and current runtime/runner hashes. `engine.log` is the full Godot stdout/stderr. The accepted 49-row derived index is `evidence/characters/lee/callback-exact-r01/pending-inventory-current-r08.json`; counts are 19 native-matched, 18 source-only, 10 remaining, 2 normal-input-unreachable. Those are callback-only classifications.
