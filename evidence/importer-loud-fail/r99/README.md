# r99 — authored filter output is integer-translation invariant; raw input is not

Seven independently attached original Jiraiya wrappers are drawn at destination X offsets-128/-17/-1/0/1/17/128. Each preserves authored scale, fill, mask and filter. Actual source bounds, child matrix, draw matrix and filter properties are read back. Both authored-filter and cleared-input images are captured as premultiplied RGBA.

- All seven authored-filter images equal the unchanged r93 reference shifted by the declared integer offset: **1680000/1680000 pixels exact**.
- Cleared-input images are not strictly translation invariant. Offsets-128/+128 differ from shifted r93 input at43/56 pixels respectively, max RGBA1. The other five offsets remain exact.
- The unchanged source-bound sampler plus independently measured nested translation consumption predicts **all seven cleared-input images1680000/1680000 exactly**, including those99 shifted-input counterexamples. No coordinate patch or per-pixel route added.

Thus the original filtered result does not simply inherit the global-coordinate input rasterization seen after removing its filter. This supports a distinct implicit materialization/copy boundary but does **not** identify its allocation origin. A rendered match alone is not a way to choose that origin. The r98 explicit-filter277-pixel residual remains unresolved.

A reusable bounded bitmap diagnostic now consumes actual fill/mask metadata and rejects nontransparent fractional-edge footprints. It centralizes the already measured half-even/geometry-only sampler for subsequent source-bound experiments; historical sampler/reference modules remain unchanged.

## Reproduce

```sh
python3 -m tools.probes.build_jiraiya_filter_boundary --output /tmp/bvn-r99/recheck --ffdec /path/to/ffdec-cli.jar --harness tools/probes/flash_filters/jiraiya-buffer-origin.as
python3 tools/probes/capture_native_player.py /tmp/bvn-r99/recheck/components/jiraiya /tmp/bvn-r99/recheck/components/jiraiya/native.log --player-app '/path/to/Flash Player.app' --allow-window-activation --timeout 90
python3 -m tools.probes.analyze_jiraiya_buffer_origin --native evidence/importer-loud-fail/r99/native --output /tmp/bvn-r99/results
python3 -m unittest tools.tests.test_jiraiya_buffer_origin
```

[Summary](summary.json), complete differing coordinates in `analysis.json.gz`, [hashes](provenance.json), original log/property readbacks under `native/`, fourteen images under `images/`, [acceptance](acceptance.json).

Next discriminator: independently toggle cache-only and zero-blur boundaries on the same authored shape, retain source bounds and `generateFilterRect` outputs, and compare their actual images across integer offsets. Do not infer materialization merely from cacheAsBitmap properties. Only after identifying a boundary should an explicit source-bound rectangle/placement construction be tested globally; no origin fitting to RGB.

`production_admitted=false`; historical54-suite9/54. Full authored filters, general affine/coverage, implicit cache behavior and AS ownership remain open. Draft only; no merge/deploy/Worker.

Fresh Python739 pass +2skip; caches26/26, fingerprint, protected, integrity, handoff/contracts green. Full roster/Web not rerun: production unchanged.
