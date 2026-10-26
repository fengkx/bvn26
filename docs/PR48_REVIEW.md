# PR48 review map

PR48 targets `master` from `fix/importer-loud-fail`. Its acceptance bar is the wired fail-loud importer/compiler/build safety net. Exact production image parity and complete AS/clip-action semantic ownership remain deferred; see [known gaps](IMPORTER_KNOWN_GAPS.md). This document is a review guide, not a claim that every changed line has been independently verified.

## Review the product change first

Use the merge-base diff, not just the latest diagnostic commit:

```sh
git diff origin/master...HEAD -- tools/importer tools/build_online_manifest.py tools/build_web.sh .vercelignore data
git diff origin/master...HEAD -- godot ':!godot/generated' ':!godot/tests'
git diff origin/master...HEAD -- tools/tests godot/tests tools/test_importer_roster.py tools/test_online_manifest.py tools/test_integer_blends.py tools/test_drop_shadow.py
```

1. Import/build entry points: online manifest, staged web packaging, source-hash-pinned frame/placement/visual/form obligations. Check negative tests and stale-cache bypass rejection, not just a successful cache import.
2. Compiler/extraction: supported call arguments, finite values, timeline placement fields, nested controls, form graph helpers and source locations. Read the historical narrowly scoped Byakuya exception and the test proving admitted compilation without it.
3. Runtime: body/profile replacement, callbacks and intervals, live source references, wrapper transfer, rollback fields, then TimelinePreview/BlendGroup/FilterGroup and shaders. These are shipping changes, not merely diagnostic tools.
4. Generated assets and requirements: check source hashes, regenerated cache/profile relationships and required assets. Review them separately from handwritten code.

`production_admitted=false` is an evidence flag, **not a runtime kill switch**. FighterRuntime inherits TimelinePreview, whose `_compose_blend_group` creates FilterGroup for authored filters. The current runtime therefore includes filter/composition work while broader exact-image admission is incomplete. Do not describe the whole branch as runtime-unchanged because recent rounds only changed diagnostics.

## Review generated output and evidence separately

```sh
git diff --stat origin/master...HEAD -- godot/generated tools/importer/*requirements.json tools/importer/visual_control_owners.json
git diff --name-only origin/master...HEAD -- tools/probes evidence/importer-loud-fail
git diff origin/master...HEAD -- docs/STATUS.md evidence/reference-environment.md manifest.json
```

Evidence rounds contain native captures, source readbacks, candidate reports, failures and strict comparison receipts. Start with the round README/acceptance files and follow the exact reproduction paths and hashes. A rejected candidate remains rejected even if some controls pass. Archived captures and generated pixel logs can be collapsed in GitHub; retain Markdown summaries and all reproducible files in the repository. Do not replace or relocate evidence simply to reduce the displayed diff.

## Interpret gates accurately

`audit_importer.py` inventories every locked script as requiring complete semantic ownership review. Its full-audit exit remains nonzero while those obligations or skip sites remain. Selected call/cache validation, placement validation and clip-action structural validation do not establish ownership of every AS statement or event body.

Final acceptance must distinguish:

- Actual passing shipped-cache, placement, replay, protected, Python/Godot/GPU, build, fingerprint, integrity, handoff and contract checks on the final product/guard source (subsequent documentation-only commits do not change that source).
- Explicitly deferred full AS ownership and exact production component-image proofs.
- Unexpected failures, which remain blockers under the revised bar.

Never relabel the deferred audit as passed, widen a tolerance, replace a native reference, or infer a runtime consumer solely from a retained field or recognized call name.
