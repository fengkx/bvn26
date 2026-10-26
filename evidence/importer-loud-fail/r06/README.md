# Numeric goto consumer and source inventory, r06 (2026-10-23)

Draft PR #48 remains blocked. Fighter cache acceptance advances **21/26 → 22/26**.
Rukia's original `533/frame_141: gotoAndPlay(130)` now enters absolute frame 130
through the frame-action FIFO and synchronizes the child display/controller list.
It does not replay the label prefix at frame 127 or its frame-128 state writes.
Only Rukia's `frame_calls` cache changes; the earlier audited shine/shunbuxg and
conditional-stop rules are refreshed with it. Rukia's controller_scope_fields,
sensing and limits still differ from a full context rebuild; they retain their
existing owners and values, with exact differences in rukia-deferred-context.json.
This is frame-call cache acceptance, not complete context equivalence. No new
allowlist or port.

The new generic operation supports literal, retained numeric destinations within
the same label span. Missing frames, expression arguments, cross-label numeric
jumps and parent/form jumps still fail with SWF/path/line. Cross-label requests
need an action-metadata consumer in addition to a playhead change; they are not
silently treated as supported. The regression mutates both missing and cross-label
destinations and retains expression/child/parent rejection coverage.

## Source-first and native evidence

1. `rukia-source-review.json` records every frame 127..145, all DoAction and
   placement callbacks, including frames without scripts. Frame 128 writes
   `khit=1` and `动作=1`; frame 141 jumps to 130. The movement callback placed
   at 128 checks pause, moves using speed, and jumps to 跳砍2 if touch is true.
2. Placements retain their source `placed_frame` identity through 130..141.
   The numeric consumer uses the existing display-list/instance synchronization
   and queued frame-action path; it does not restart a label or create a fresh
   body. This probe measures playheads and skipped writes, not all child identity
   or callback scheduling combinations.
3. The loop is an explicit source goto, not inferred from the label's end_frame.
   In unpaused gameplay the retained touch callback can leave it at 跳砍2.
4. The test asserts native-captured playheads and that a numeric jump does not
   execute the skipped frame-128 khit assignment. No expected frame trace is
   synthesized from Godot. Missing/cross-label requests remain hard errors.
5. `build_numeric_goto_probe.py` attaches the original body 533 definition and
   pauses movement callbacks. Original definition bytes, including the frame-141
   action, are byte-identical after root-script import. Flash Debugger 32 captured
   **31/31 exact playheads** over two original 141→130 loops. Godot executes the
   real frame service, controller and runtime consumer against those rows. This
   isolated comparison is not full Rukia combat/input or pixel certification.

`numeric-native/` contains build hashes, the actual program, capture environment,
raw trace and parsed reference. `numeric-godot.json` / `numeric-godot.log` record
`NUMERIC_GOTO_REFERENCE_OK 31/31`. The packaged builder was rebuilt and recaptured
after its source-path/reuse cleanup; both captures yielded the identical trace.

## Still blocked

Four parent jumps replace the body and run a new form's load. The existing runtime
has no complete replacement-form assets/controller/combat/lifecycle consumer.
They remain exact hard errors; no disabled-action exception was added:

| SWF | Sprite/frame | Target body on parent frame 2 |
|---|---|---|
| daitu | 458/1309 | 1138 |
| minren | 764/1382 | 1293 |
| Sasuke | 603/1232 | 1019 |
| yihu | 638/1055 | 1180 |

`goto-blockers.json` preserves exact source/hash and target load scripts. Clearing
these requires full replacement-instance ownership, not interpreting parent frame
2 as body frame 2 or merely stopping the old body. **26/26 is not achieved.**

A fresh **62-SWF scan** still finds **34 unsupported placements**: blend 7 Kenshin
(1), blend 13 minrenx (1), qilabi (30), main (1), and main sprite 1504/frame 1
DropShadow (1). `locked-swf-audit.json` retains all exact sites and source hashes;
large placement-obligation arrays are omitted with their counts retained.
`audit_shipped_placements.py` reproducibly checks all **89/89** shipped closures
and maps all source errors to them. None of those 34 lies in a retained closure,
but the inventory command still exits 1: out-of-slice does not mean harmless.
No blend/filter consumer was changed or newly allowlisted this turn.

Overall build/fingerprint still fails at Yihu 638/1055. Compatibility output
remains stale; it was not regenerated through a guard bypass. Full AS/clip-action
ownership and deferred context-field review remain incomplete. Canonical color
comparison is still 3/5 exact (64/128 differing channels, maximum 1); order is
2/4 exact (one differing channel in each Glow group). Strict comparator reports
were rerun and remain failures. No tolerance changed. XG_rush pixel mismatch and
real component parity (previous 9/54 images) were not recaptured this turn.

## Acceptance

- Python: **383 run, 381 passed, 2 skipped**; `python-final.log`. The initial run
  caught a case-sensitive assertion typo in the new test; corrected and rerun.
- GPU: **7/7 existing asserted subsets**; Blur **242/242, 37,280 alphas** and
  blend **38/38** under its pre-existing assertion contract. This is not a claim
  that the still-failing complete color/order comparisons pass.
- Godot player/controller/retained clocks/clip placement: **4/4**.
- Numeric goto native reference: **31/31**, no tolerance.
- PROTECTED_FUNCTION_OK: original 1,086 bytes and SHA unchanged.
- Whole-roster replay: **227/227**, **130,334 states**, unchanged native baselines;
  roster-report.json / roster.log.
- Integrity after reviewed hashes, handoff and contracts: **pass**; manifest-review.json
  records every changed covered file. Placement catalog matches the fresh scan exactly.
- Cache **22/26**, shipped placement/control **89/89**, locked placements **34
  unresolved**, overall build/fingerprint **FAIL**.

## Reproduce

Use local FFDEC, FLASH_APP, GODOT and a fresh OUT directory:

```sh
python3 tools/probes/build_numeric_goto_probe.py --ffdec "$FFDEC" --output "$OUT/native"
python3 tools/probes/capture_native_player.py "$OUT/native" "$OUT/native/native.log" \
  --player-app "$FLASH_APP" --allow-window-activation --timeout 40
"$GODOT" --headless --path godot --script res://tests/numeric_goto_reference.gd \
  -- "$OUT/numeric-godot.json"
python3 tools/importer/audit_frame_calls.py --output "$OUT/frame-calls.json"
python3 tools/importer/audit_shipped_placements.py --output "$OUT/placements.json"
python3 tools/importer/audit_importer.py --ffdec "$FFDEC" --output "$OUT/locked-swfs.json"
python3 tools/test_importer_roster.py --godot "$GODOT" --output "$OUT/roster"
python3 tools/build_online_manifest.py --check
```

The audit/build commands intentionally return nonzero while these blockers remain.
No source edits under game/ or scripts/, merge, deployment or new ports.
