# Root-frame deletion guard: Cursor review follow-up

The placement build gate previously skipped a missing obligated frame when its sprite was the cached timeline root. Nested sprites already rejected missing obligations. The fix gives root placements the same missing-source-timeline-frame error; missing root clip-action frames flow into the existing dropped/changed-clip-actions error. Only sprites outside both the root and nested definitions remain skippable.

Negative controls delete only the obligated root frame, retaining other timeline content. Before the fix, filter/CXFORM and clip-action controls produce three expected test failures (no exception raised); after the fix the focused suite passes51/51. Out-of-slice controls still pass. No runtime, source SWF, cache, allowlist or reference change.

Validation:

- `python3 -m unittest tools.tests.test_qualified_visual_control_guard tools.tests.test_import_guards tools.tests.test_placement_tag_guards tools.tests.test_placement_audit_diagnostics tools.tests.test_clip_action_fields tools.tests.test_wrapper_filter_initialization`:51/51 passed.
- `python3 tools/verify.py`:passed.
- `python3 tools/check_handoff.py`:passed.
- `python3 tools/build_online_manifest.py --check`:**FAIL**, newly exposed retained-content obligation: `godot/generated/stages/catalog/frame_16/timeline.json: missing source timeline frame: game/main.swf sprite1738 frame6 depth17`.

The existing stage catalog cache selects frame16 and does not contain the obligated frame6. The guard is not weakened to accept that omission. Previous26/26/full-build evidence predates this stricter check and is not a passing result for this tip. Resolving the stage-cache/source-scope mismatch requires a separate follow-up before claiming the current build green; this checkpoint only implements the requested guard correction.

PR remains Ready for review as explicitly requested, not an assertion that the newly failing build is merge-approved. `production_admitted=false`; no merge/deploy/Worker action.
