# Preserve complete stage roots under the missing-frame guard

Cursor's root-frame guard fix exposed ten cached stage slices omitting sprite1738/frame6/depth17. The guard remains unchanged. The stage generator now retains all23 source frames and their reachable definitions/assets. All ten catalog maps share `catalog/world`; the bundled `current_world` also retains the complete root. Catalog-selected frame numbers, stage IDs and music selection remain unchanged. Obsolete catalog-owned frame directories are retired only after successful materialization.

This is not a frame-scope allowlist or a guard exception. Removing an obligated root frame still fails. Whole-source retention makes the existing cache identity truthful without multiplying the complete bitmap set into ten directories. The shared result uses about13MB across generated stages rather than54MB for ten complete copies.

## Source and consumer evidence

- Source: locked main.swf SHA256 `707fac0ec6bb2af1a3d18dc308dd403cb556a0988144b0f6f10555382287f92d`, fresh pinned JPEXS export; sprite1738 has23 frames. Its sole root DoAction is frame1 `stop()`.
- Placement/MOVE: complete extracted display lists are retained, including frame6's obligation. `preservation.json` proves every prior catalog-selected frame is identical and every existing bitmap byte remains identical.
- Leaving labels: `main.gd::_load_selected_stage` chooses `initial_frame=stage.frame`, with autoplay=false. TimelinePreview indexes all frames but renders the selected frame; adding retained frames does not introduce automatic fallthrough.
- Invariants: all ten original map labels/spawn markers and source frame numbers remain; wrapper camera ownership remains with GameWorld; source-hidden marker definitions and externally replaced fighter/helper markers retain the existing compiler policy.
- Comparison: source/catalog-frame and asset-byte equality is verified, plus the actual TimelinePreview consumer is exercised for all ten stages. This is not a new native pixel-parity claim. Fresh extraction also restores existing compiler metadata absent from older caches (bitmap clip polygons; legacy current_world fill/placement annotations). Those are not stripped to mimic stale caches; exact production-image admission remains deferred.

## Reproduce

```sh
python3 tools/importer/export_swf_xml.py --ffdec-jar "$FFDEC" --output-dir "$WORKSPACE" game/main.swf
python3 tools/importer/build_stage_catalog.py --workspace "$WORKSPACE" --current-world-output godot/generated/stages/current_world
"$GODOT" --headless --path godot --editor --import --quit
python3 tools/build_online_manifest.py
python3 tools/importer/audit_shipped_placements.py --output "$OUT/placements.json"
"$GODOT" --headless --path godot --script "$PWD/tools/tests/stage_catalog_frames_smoke.gd"
```

Focused Python stage/guard tests pass54/54; complete source placement checks pass89/89 timelines with zero locked-source issues (98 became89 through deduplicating ten world slices to one). A real cached-world mutation deleting frame6 is also rejected at sprite1738/frame6/depth17. Final results: online manifest26 fighters/5 helpers/10 stages; local build_web exit0 and final fingerprint passed; roster227/227,130334 states; actual stage consumer10/10; fingerprint unit tests8/8; protected/integrity/handoff/contracts passed. See acceptance.json. The previous full Python/GPU run was not repeated for this generator/data-only change.

The first replay was stopped after detecting missing local Godot imports for moved texture paths; resources were imported before rerunning. An exploratory stage_sound smoke passed its assertions but reported an existing audio teardown resource warning; no audio/runtime change was retained. An in-progress Web snapshot was discarded while that test-only teardown experiment was reverted; the final Web run uses the unchanged test and final product source.

`production_admitted=false`. Jinye/Yijiao, complete sampler/production54 and full AS ownership remain accepted follow-ups. No merge, deployment or Worker action. Next action: Cursor/human review of root-frame rejection plus this complete-root packaging fix before merge.
