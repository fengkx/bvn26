# Lee callback exact comparison r15

This run replays the complete 900-tick `lee-callback-lifecycle-recovery-r01` fixture in Godot. It compares P2 frame-action callbacks 1134 and 1144 on the same-source `source_frame`, `entering`, decoded `action`, and decoded `ql` fields. Separately, it observes the real P2 clip-action controller at source path `DefineSprite_518/frame_1133/PlaceObject2_18_30/CLIPACTIONRECORD onClipEvent(enterFrame).as`.

For the clip callback, the locked original-player raw has four ordered enter/exit pairs. It records instance `instance572`, child local frame 1, and parent frames 1134–1137. The native test-only proxy records the same eight ordered events and local/parent frames, plus placement at parent frame 1133 and removal at parent frame 1138. The source raw has no explicit clip-removal event, so native removal is reported as a native lifecycle observation, not a two-sided lifetime match. Parent x values are diagnostic only because the source callback tape does not record x.

`callback_trace_registry.gd` is test-only. It adopts the existing registry entries, proxies only the selected clip callback target through a weak delegate, and inherits the production `dispatch` implementation. The probe audits inherited registration IDs, method order, and `placed_tick` before and after installation. Dead delegates are removed during the same dispatch when detected, without emitting an observer event; `clear()` also releases proxy references. A focused smoke covers a delegate destroyed by an earlier callback in that same dispatch, plus clear behavior. The event reader normalizes both AIREF pipe rows and JSONL rows and rejects malformed or unknown encodings; its smoke asserts the same body and clip rows parse identically in both forms. No production registry or callback scheduling code was changed.

The body comparison and clip comparison have separate scopes. Neither implies full combat-state or full-character parity. The test-only proxy is a callback hook for these observed paths, not a generally transparent replacement registry: it records around a selected delegate call and retains weak delegate ownership. An emitted `exit` records return from the proxy-wrapped call; it does not prove the source clip remained alive after the call. R16 documents cases where source control flow removes a clip before an instrumented source-side exit marker appears.

Reproduce from the repository root:

```sh
/private/tmp/godot-4.7.2/Godot.app/Contents/MacOS/Godot --headless --path godot --log-file /private/tmp/lee-callback-exact-r15.log -s res://tests/lee_callback_exact_probe.gd -- --batch "$PWD/evidence/characters/lee/godot/callback-exact-r15/paths.json" "$PWD/evidence/characters/lee/godot/callback-exact-r15/out" > evidence/characters/lee/godot/callback-exact-r15/engine.log 2>&1
python3 evidence/characters/lee/godot/callback-exact-r15/compare_clip.py
python3 evidence/characters/lee/godot/callback-exact-r15/event_tape_smoke.py
/private/tmp/godot-4.7.2/Godot.app/Contents/MacOS/Godot --headless --path godot --log-file /private/tmp/callback-trace-registry-smoke.log -s res://tests/callback_trace_registry_smoke.gd
python3 evidence/characters/lee/godot/callback-exact-r15/update_inventory.py
```

The native run exited 0. It observed four source/native clip enter/exit pairs with zero differences on the five clip fields and four body-frame callback rows with zero differences on their four fields. The registry installation audit retained all 11 pre-existing registrations in the same ID/order/placement-phase sequence. Inventory r15 records 37 matched rows, 7 source-only rows, 2 remaining dynamic rows, and 3 statically unreachable rows. The 1288 source row comes from a later JSONL capture and is validated through the shared dual-format reader; it remains source-only pending native comparison.
