# Lee callback exact comparison r09

This is a bounded, same-source-run native Godot comparison for body frame-action callbacks. It compares only `source_frame`, `entering`, `action`, and decoded `ql`; it is not full-state, visual, or character parity. Both cases use Lee as P1, Ichigo as P2, helpers Gaara/Kon, explicit starting positions and energy, and the exact recorded input windows. The source and native records remain separate and immutable.

## Cases and results

- `defence-1070-p1`: P1 frame 1070 enter/exit, source run `lee-callback-defence-entry-r03`; native and source both report action 2 and ql 300.
- `held-jump-95-113-p1`: source capture runs 600 fight ticks. Frame 95 and 113 each enter/exit twice. Native observer runs the whole 600-tick fixture and reports the same 8 ordered events with action 0 and ql 300.

`comparison.json` records each event, all four field comparisons, the actual fixture/build/raw hashes, the source move case and build configuration, and the current Godot runtime file hashes. The source build metadata's own `status` field is retained verbatim; the paired raw must independently contain the same run id and terminal `done` marker. For the held-jump case, the prepared build's `move_case.frames` is 300, while the completed raw capture records 600 frames after Ready; the native fixture uses the observed 600-frame capture duration. It is not relabeled as frame 62 coverage: frame 62 never appeared in the source raw.

The first r09 native run stopped after its runner had observed each requested frame once. That omitted the second 95/113 occurrence present in the source capture. Its files are preserved under `partial-attempt-01/` and are not used by the current comparison. The accepted run sets `capture_callbacks_full_fixture` on this fixture so observation continues for all 600 fight ticks; it does not change combat inputs or runtime behavior.

## Reproduce

From the repository root, run the batch with the pinned Godot executable:

```sh
/private/tmp/godot-4.7.2/Godot.app/Contents/MacOS/Godot --headless --path godot --log-file /private/tmp/lee-callback-exact-r09-full-godot.log -s res://tests/lee_callback_exact_probe.gd -- --batch "$PWD/evidence/characters/lee/godot/callback-exact-r09/paths.json" "$PWD/evidence/characters/lee/godot/callback-exact-r09/out" > evidence/characters/lee/godot/callback-exact-r09/engine.log 2>&1
python3 evidence/characters/lee/godot/callback-exact-r09/compare_exact.py
python3 evidence/characters/lee/godot/callback-exact-r09/update_inventory.py
```

The source artifacts needed for comparison are archived at the paths referenced by `preflight.json`; generated SWFs stay outside the repository. `compare_exact.py` validates source raw/build/instrumentation hashes, build/run identity, main SWF hash, raw `done`, fixture inputs/helpers, and build configuration before comparing events.

Current inventory is `../../callback-exact-r01/pending-inventory-current-r09.json`; r09 adds three callback rows (1070, 95, 113) to the prior 49-row bounded inventory. Frame 128 still lacks a matching actual source build/raw capture; source-only history is not promoted. Frame 62 was not observed. Clip-action callbacks remain a separate kind and are not included here.
