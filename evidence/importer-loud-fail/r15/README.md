# PR48 r15 — Yihu full form graph and nested stage execution

Yihu638/frame1052 wankai now uses the shared production replacement graph:
638→1180→1672. Target image/sound/combat/controller packages and source-hashed
load/initialization contracts are committed. Frame-call caches reach **26/26**.

The native12/runtime17 discrepancy was an omitted nested frame script, not a
numeric rendering tolerance. Nested stage-writing clips now compile complete
unconditional scripts (root coordinates and flash) into source-bound events.
The retained child clock schedules their frame entry; the Fighter executes them
with its frame work. Replacement advances the newly placed subtree in the same
source display pass. Restoring/rendering display does not re-enter scripts.
The root Control's position is now captured by full rollback; previously restoring
only the shared root-value dictionary could accumulate a second displacement.

Full rollback initially exceeded180s while repeatedly copying inactive form
packages. Source profile/selected-target dictionaries are now immutable
checkpoint configuration; teardown replaces its references rather than clearing
shared packages. Pending replacement tick, transfer values, live BODY/callback
state and stage-action queues remain mutable checkpoint state. The production
fixture saves/restores the undefined-body pending window on both edges. The
complete battle checkpoint test now passes; the initial timeout is retained in
`godot-initial-timeout.log`. No assertion or timing semantics was relaxed.

Source-first answers: [source-first.md](source-first.md). Fresh native raw trace:
[native-stage/native.log](native-stage/native.log). Reproducible numeric fixture:
`tools/probes/fixtures/yihu-nested-stage.json`. Production fixture:
`godot/tests/yihu_form_graph_reference.gd`. The23 consecutive body/root samples
match exactly; both replacement edges, HP/QL, timer/live owner and rollback pass.

The generic compiler also exposes previously omitted stage scripts in other
retained contexts; see [nested-stage-inventory.json](nested-stage-inventory.json).
These were real drops, now consumed rather than allowlisted. Cached missing or
changed events are rejected with the nested source path. Unknown calls,
expressions, conditions and nonfinite numbers are regression-tested hard errors.

## Acceptance and remaining blockers

Final counts: roster227/227 (130,334 states); Python472 passed+2 skipped; GPU7/7;
Godot4/4 standard+9/9 additional+4/4 form gates+4/4 extra references. Natural
input activates7/7 form graphs. Protected/integrity/handoff/contracts pass;
fingerprint unit8/8. Details/logs: `acceptance-summary.json`.
`frame-calls.json` proves26/26 cache acceptance. `online.log` shows the next
**intentional build rejection**: Yulong root/frame1/depth1 cached wrapper filters
are missing. The local online-manifest build gets past all form loud-fails;
a Vercel rebuild should reach that same placement guard. No preview deployment
is claimed. A full local `build_web.sh` attempt also reports missing installed
Web export templates; `staged-manifest.log` instead executes the actual staging
copy commands and proves the same Yulong rejection in an isolated snapshot.
Runtime-fingerprint unit tests pass; generating the complete build
fingerprint remains blocked by this placement error.

`placements.json`:97/98 shipped timeline closures pass;34 pinned source placement
issues remain. This turn checks current closures against the reviewed catalog;
it does not redo the62-SWF raw scan. Exact component/color/order pixel parity and
full AS/clip-action ownership audit remain open. PR48 stays Draft. No merge,
production deployment, Worker changes, new ports, new allowlists or tolerance.

## Reproduce

```sh
python3 tools/probes/build_form_helper_probe.py --fighter yihu --observe-stage --ffdec "$FFDEC" --output "$OUT/native-stage"
python3 tools/probes/capture_native_player.py "$OUT/native-stage" "$OUT/native-stage/native.log" --player-app "$FLASH_APP" --allow-window-activation --timeout 40
"$GODOT" --headless --path godot --script res://tests/yihu_form_graph_reference.gd --log-file "$OUT/yihu-engine.log"
python3 tools/importer/prepare_form_graph.py --base godot/generated/fighters/yihu --target 2=godot/generated/forms/yihu-2 --target 3=godot/generated/forms/yihu-3 --report "$OUT/graph.json"
python3 tools/importer/audit_frame_calls.py --output "$OUT/frame-calls.json"
python3 tools/build_online_manifest.py --check
python3 -m unittest discover -s tools/tests
python3 tools/test_importer_roster.py --godot "$GODOT" --output "$OUT/roster"
```
