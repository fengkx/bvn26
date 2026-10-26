# r250 — Frozen candidate on actual Jinye images

The r249 display-matrix candidate is unchanged. The original r241 renderer now accepts an explicit optional sampler-row provider, retaining default behavior. Default replay exactly reproduces every stored r241 complete-image and leaf measurement, including full failure lists. Geometry/coverage, source decoding, cache bounds, inverse/phase/HV sampling and compositing are unchanged. No native capture or production edit.

| Actual image | Differing pixels before → after | After max channel delta |
|---|---:|---:|
| Shape56 leaf, uncached |17 → **0**|0|
| Shape56 leaf, cached |17 →7|1|
| Shape57 leaf, uncached |2 →3|1|
| Shape57 leaf, cached |19 →20|1|
| Complete stage tick0 |129 →76|71|
| Complete stage tick10 |270 →11|62|
| Complete stage tick20 (empty) |0 →0|0|
| Complete stage tick23 |212 →26|57|

Leaf exactness rises **0/4→1/4**. Complete images remain **1/4**, with only the empty frame exact; active images remain **0/3**. Therefore the complete diagnostic inventory stays **46/54**. The two leaf regressions and all81 r249 cached-control counterexamples remain visible; no per-image model selection or admission.

Every remaining isolated-leaf mismatch is in that leaf's full-coverage interior; edges/outside are exact. Full-graph partitions are unions of leaf interiors: another contributing leaf may still have fractional coverage at such a pixel, so that classification alone cannot exclude coverage/compositing. Full per-coordinate RGBA differences, source-frame/depth information and partitions are retained in compressed reports.

The source inventory already rejects child placement fields beyond its matrix/character/move scope; the231 events here do not hide a dropped CXFORM, clipDepth or filter. This does not prove the separate global AS/clip-action ownership audit.

## Reproduction and checks

```sh
python3 -m tools.probes.run_jinye_static_wrapper --dump /path/to/source-JPEG-plane-helper --output /tmp/r250
python3 -m unittest tools.tests.test_jinye_static_wrapper tools.tests.test_flash_float_compose tools.tests.test_jinye_static_hierarchy tools.tests.test_jinye_wrapper_cpu
```

The diagnostic deliberately exits1 while its retained counterexamples/admission obligations remain. Native outputs are used only for comparison, never as source textures. Source decoder and r249 tool hashes are pinned. Focused tests **12/12** and independent report reconciliation pass. Mandatory cache/fingerprint/protected/integrity/handoff/contracts results are in `acceptance.json`; no fresh full Python/roster/Web/production54 run for these diagnostic-only changes.

## Follow-ups under the revised merge bar (2026-10-26)

The user now explicitly defers Jinye/Yijiao exactness, sampler admission, production54 and full AS/clip-action ownership from this PR's merge bar. Do not start another pixel experiment for this merge. The retained concrete residual map above is the follow-up starting point: three uncached Shape57 interior pixels, seven/twenty cached leaf pixels, and complete stage ticks0/10/23. A future fix must preserve all old controls and cannot choose paths from output RGB.

This PR instead verifies the wired importer/compiler hard-fail safety net and documents the remaining scopes honestly. Candidate/GPU/production admission remain false. The latter is an evidence flag, not a gameplay kill-switch: FilterGroup may still render through FighterRuntime/TimelinePreview, an explicit follow-up risk accepted under the new merge bar. Full AS ownership remains open; do not claim universal semantic coverage. Ready-for-review may follow the fail-loud audit, but never merge/deploy/Worker automatically.
