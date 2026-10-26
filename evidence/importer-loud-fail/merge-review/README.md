# Fail-loud-first review checkpoint (2026-10-26)

The user explicitly revised the merge bar: ship the enforced importer/compiler/build safety net, with exact-image and complete AS/clip-action ownership work retained as known follow-ups. No additional pixel experiment was started. r250 is committed as `19f3ba64` and retains its rejected residuals.

## Focused changes

- Explicit `this.stop/play/goto` now requires a nested DoAction owner and fails with the source location instead of escaping detection. Bare supported calls retain exact event checks.
- Source-pinned first root-wrapper obligations now retain blendMode, including whole-wrapper deletion; selected matching wrapper placements also compare it. This does not prove all later root MOVE/replacement ownership. Typed comparison also protects wrapper filters. Five source-hash-verified catalog fields were refreshed; no allowlist was added.
- [AS gate review](as-gates.md), [placement gate review](placement-gates.md), [catalog changes](wrapper-catalog-changes.json).
- [Known differences](../../../docs/IMPORTER_KNOWN_GAPS.md) and [review map](../../../docs/PR48_REVIEW.md) separate product changes from generated evidence. Evidence is retained; generated data is collapsed in GitHub using `.gitattributes`.

## Acceptance

Fresh passing checks: caches26/26, shipped timelines98/98, roster227/227 (130334 states), GPU7/7, headless Godot22/22, protected function, integrity, handoff, contracts, local Web export and final fingerprint. Focused guard tests50/50. Full Python ran1161 tests:1158 passed,2 skipped,1 historical-source hash failure. The r111 fixture now archives its exact original helper from c69642d9 with the original SHA256 unchanged; r243 had added three path-normalization lines to the live helper. All6 affected old/new profile tests pass on recheck. The entire suite was not repeated after this fixture-only fix; no known test failure remains. Native references were not rewritten.

Final machine-readable results are in `acceptance.json`; command logs are in `checks/`, Godot results in `godot/results.json`, and roster results in the roster archive. The full audit remains explicitly incomplete; selected passing gates are not a universal AS ownership proof.

Reproduction:

```sh
python3 -m unittest discover -s tools/tests
python3 tools/build_online_manifest.py --check
python3 tools/test_online_manifest.py
python3 tools/verify.py
python3 tools/check_handoff.py
python3 tools/validate_contracts.py
python3 tools/test_importer_roster.py --godot "$GODOT" --output "$OUT/roster"
GODOT="$GODOT" OUT="$OUT" python3 evidence/importer-loud-fail/r16/godot/commands.py
GODOT_BIN="$GODOT" TEMPLATE_DIR="$TEMPLATES" bash tools/build_web.sh
```

Initial local Web attempt stopped because the default export-template directory was empty; the final run explicitly binds the existing Godot4.7.2 template. The first handoff run caught the not-yet-written README link; the final run is after this document exists. Neither failure was hidden or bypassed. Seven graphical launches initially exited -6 before logs under the sandbox; rerunning those same GPU tests with native display access passed7/7. Headless checks passed22/22. Existing colors/order scripts retain their known residual measurements; a successful script exit does not claim those images are exact.

`production_admitted=false`; diagnostic images46/54; production images historical9/54. Jinye/Yijiao and full AS ownership remain follow-ups under the accepted bar. FilterGroup can already render in gameplay; the evidence flag is not a runtime kill switch.

## Next action

Human/Cursor review of the fail-loud/product diff before merge. Follow-up fidelity work should address the retained real-image residuals and production admission/AS ownership; no new orthogonal rejection suites are required to send this PR for review. No merge, deploy or Worker action is authorized here.
