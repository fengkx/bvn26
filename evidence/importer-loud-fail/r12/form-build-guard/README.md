# r12 reviewed form graph admission

The production Daitu manifest passes fresh source compilation and the offline build contract. See `production-audit.json`: source `game/fighter/daitu.swf`, parent frames 1/2, base sprite 458 (282 pinned files), replacement sprite 1138 (421 pinned files). The freshly produced source contract equals the reviewed `frame_call_requirements.json` entry exactly.

The source audit recompiles full AI context, player BODY (including shared hurt hooks), player controller, and predicate code/metadata for both graph nodes. The build guard pins the complete package and manifest, source/load requirements, frame calls and parent initialization, validates asset paths, and rejects transitions outside the reviewed graph. Merely placing a manifest on disk does not admit form calls. Forms are included in the content fingerprint. Generated `.uid`/`.import` files and candidate/manifest files are excluded from package hashes to avoid editor-dependent and recursive hashes.

Compilation and graph closure do **not** establish native Flash parity. Native ordering, state transfer and live-reference acceptance remain separate runtime evidence reviewed for this PR. No new allowlist or tolerance was introduced.

Validation:

- `python3 -m unittest tools.tests.test_form_profile_guard tools.tests.test_import_guards tools.tests.test_parent_frame_state`: 39/39 (`guard-tests.log`).
- `python3 -m unittest tools.test_online_manifest`: 8/8 (`fingerprint-tests.log`).
- `python3 -m unittest tools.tests.test_build_web_pipeline`: 8/8 (`build-web-tests.log`).
- Direct `audit_form_manifest`, reviewed-contract equality, `validate_form_manifest`, and `validate_cached_frame_calls` against the production Daitu package: passed (`production-audit.json`, `production-audit.log`).
- Match root ownership fixture: `FORM_ROOT_OWNER_SMOKE_OK`, clean exit (`root-owner.log`). Shared helper power, keys, difficulty, root position, interval lifetime and match teardown are covered.

The remaining source/placement failures are intentionally not admitted by this graph; see the whole-roster acceptance and `../placements/` inventory.
