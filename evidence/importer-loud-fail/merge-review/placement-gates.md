# Placement / filter / blend / nested cached-timeline build gate review

No r251 pixel files were created; completed r250 files were left untouched. This review follows the revised fail-loud merge scope. Exact pixel parity and full AS/clip-action ownership proof remain explicitly deferred, not claimed complete.

## Actual build path

`build_online_manifest.make_documents()` loads every generated `timeline.json`, rejecting nonfinite JSON numbers, then runs `validate_timeline_blends`, `validate_build_controls`, and `validate_build_placements`; fighter caches additionally run `validate_cached_frame_calls`. `build_web.sh` copies these guards and their source-pinned catalogs into its isolated staging repository and invokes the same manifest entry point before/export/check. `.vercelignore` includes the placement, clip-action, blend and nested-control dependencies.

Source extraction `validate_placement` rejects unknown placement revisions/fields/active unsupported flags, missing selected attributes/children, malformed matrix/CXFORM numeric forms, and malformed clip-action metadata. `compile_filters` rejects unsupported or malformed filter records. Cached placement obligations compare authored filters/cache/blend/CXFORM with typed JSON equality, and check nested required frames/placements. Source clip-action intervals require exact metadata retention; this is NOT complete callback semantic ownership proof. Nested stop/play/goto controls are checked against source-pinned control catalogs by `visual_control_guard`.

## Concrete hole fixed

A source root `blend_mode` obligation could be dropped/changed in a cached wrapper because the wrapper path only validated unsupported fields, and the wrapper discovery catalog omitted blend mode. Ordinary nested placements already checked this field.

The focused fix uses shared typed source-vs-cache equality for wrapper filters and blend mode at the authored SWF/root/frame/depth location. The source audit now includes blend mode in first-placement wrapper obligations (one per character), so deleting the entire wrapper cannot bypass those recognized source blends. Later root MOVE/replacement ownership is not universally established by this first-placement catalog. Tests cover missing/changed/numeric-type substitution and missing entire wrapper, from source XML audit through cached validation.

Fresh exports of the five locked SWFs with root blend obligations verified their hashes and refreshed only `wrapper_obligations`. The catalog diff is exactly five additional blend fields; every previous wrapper identity/field remains identical:

- Kenshin root frame3 depth45: blend8.
- gangshou root frame6 depth2: blend8.
- shishio root frame83 depth2: blend4.
- yihuxuliu root frame64 depth2: blend6.
- main root frame56 depth69: blend13.

These are preservation obligations, not allowlists. No published wrapper currently intersects these five source sites; no gameplay output or generated runtime asset changed. Fresh source details: `wrapper-catalog-changes.json`.

## Verification

- `python3 -m unittest tools.tests.test_import_guards tools.tests.test_placement_tag_guards tools.tests.test_placement_audit_diagnostics tools.tests.test_clip_action_fields tools.tests.test_wrapper_filter_initialization`: **47/47 passed**.
- `python3 tools/importer/audit_frame_calls.py --output /tmp/bvn-merge/frame-calls-placement-review.json`: **26/26 compiled and cached contexts pass**, 1438 broad candidates retained.
- `python3 tools/importer/audit_shipped_placements.py --output /tmp/bvn-merge/shipped-placements.json`: **98/98 shipped timelines pass**, zero source placement issues (before five-field catalog refresh).
- `python3 tools/build_online_manifest.py --check`: **ONLINE_MANIFEST_OK**, 26 fighters /5 helpers /10 stages; no manifest rewrite.

Final refreshed-catalog placement verification: **98/98 passed, zero source issues**, recorded in `shipped-placements-final.json`. No runtime parity, full AS ownership, or universal sampler admission is inferred from these checks.
