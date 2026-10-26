# r16 — Yulong wrapper filter initialization

The Yulong `root/frame_1/depth_1` blocker is resolved without changing the placement guard. Fresh XML extraction retains the authored **0×0 BlurFilter, passes1** in both the source slice and production timeline. This specific root filter is not the inner Glow from the wider pixel inventory.

The original BODY345 frame1 unconditionally calls `resColor()`, which clears `_this.filters`. Base profiles now compile a source-hashed initialization record using the existing strict form initialization recognizer. The generic fighter startup executes the existing color/filter reset before first display. Authored filters remain in the timeline; the clear flag is rollback state. Missing/changed cached reset records and changed/conditional source resets fail with the SWF/sprite/frame location. No allowlist, pixel tolerance, or stability deviation was added.

[Source-first review](source-first.md), [native log](native.log), and [probe build hashes](native-build.json). Native Flash Debugger32 observes filter1 with zero radii before initialization, then filter0 at BODY frames2/3. The production Godot fixture verifies both player slots and full rollback. These are exact lifecycle observations; unresolved inner-filter/component pixel parity is not claimed.

## Acceptance

Final results: replay **227/227 (130,334 states)**; Python **476 passed +2 skipped**; GPU **7/7**, Godot **22/22**; protected/integrity/handoff/contracts and fingerprint unit **8/8** pass. Full local **build_web.sh exits0**, with import/export error scans, post-export fingerprint and `WEB_BUILD_METADATA_OK` all green. See [acceptance summary](acceptance-summary.json) and [Web build log](build-web.log). The build uses a modified-worktree snapshot based on924565fa; this is not a remote Vercel run or a production deployment. Cache acceptance remains26/26; shipped placement closures98/98. The pinned inventory still has34 unsupported source placements outside those admitted closures. This turn revalidates closures against that inventory; it does not rescan all62 SWFs.

The online manifest is regenerated now that all shipped closure guards pass. Its larger input-list diff includes accumulated form assets previously blocked from fingerprint generation. No selection catalog or Worker file changes.

Remaining merge blockers:34 source placements, exact color/order/XG_rush/component pixels, and full AS/clip-action semantic ownership audit. GPU color/order measurement completion does not imply those open pixel groups became exact. Draft PR remains open; no production deploy or merge.

## Reproduce

```sh
python3 tools/probes/build_wrapper_filter_probe.py --output "$OUT/native" --ffdec "$FFDEC"
python3 tools/probes/capture_native_player.py "$OUT/native" "$OUT/native/native.log" --player-app "$FLASH_APP" --allow-window-activation --timeout 40
python3 -m unittest discover -s tools/tests
"$GODOT" --headless --path godot --script res://tests/wrapper_filter_initialization_reference.gd --quit-after 1200 --log-file "$OUT/wrapper-engine.log"
python3 tools/importer/audit_frame_calls.py --output "$OUT/frame-calls.json"
python3 tools/importer/audit_shipped_placements.py --output "$OUT/placements.json"
python3 tools/build_online_manifest.py --check
python3 tools/test_online_manifest.py
python3 tools/test_importer_roster.py --godot "$GODOT" --output "$OUT/roster"
GODOT_BIN="$GODOT" TEMPLATE_DIR="$TEMPLATES" bash tools/build_web.sh
python3 tools/verify.py
python3 tools/check_handoff.py
python3 tools/validate_contracts.py
```

The placement inventory command intentionally exits1 for the34 unresolved locked-source issues even though shipped closures pass98/98. Python contracts require the existing jsonschema environment. Full GPU/Godot commands and outcomes are included under `godot/`; rerun with `GODOT="$GODOT" OUT="$OUT" python3 evidence/importer-loud-fail/r16/godot/commands.py`. The new fixture was corrected to use selection ID `石田` and scalar comparisons for JSON numeric fields; no runtime assertion or tolerance was relaxed.
