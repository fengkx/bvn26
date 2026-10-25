# r140 — original rotated Yulong component exact through live GPU FilterGroup

The source-proven shape266/bitmap148 quarter-turn fill remains intact, including both fill slots and the authored contour. Original raw texels create a live4×35 input viewport; shader byte interpolation and exact quarter-grid coverage have no epsilon. No native image, CPU-rendered input PNG or rotated replacement bitmap enters the GPU pipeline.

That live viewport texture feeds actual production FilterGroup nodes under the previously admitted integer-family diagnostic. Actual source bounds4×35, padded allocation8×39, two blur passes in X/Y order, Glow original-texture dependency, zero shadow offset and destination-copy-before-composite are asserted. Final ordinary composition uses the admitted integer diagnostic. Production defaults are unchanged.

All three integer-offset input/padded-input/Glow boundaries are exact:420 local pixels,936 padded input pixels,936 Glow pixels. Final native-composed canvases **720000/720000 exact**. The same two original54-suite pinned images are **2/2 exact**, **480000/480000 pixels**. Together with r130, source-backed live component diagnostics now cover **8 original images exactly**; this does not change the historical full production suite9/54, which was not rebound or rerun.

[GPU report](gpu/report.json), [fixture with original metadata](gpu/fixture.json), [source/readback hashes and command](gpu/provenance.json), [acceptance](acceptance.json). GPU logs and all buffer PNGs are retained under `gpu/`.

```sh
python3 -m tools.probes.run_yulong_rotated_live --godot /path/to/Godot --output /tmp/yulong-rotated-live
python3 -m unittest tools.tests.test_yulong_rotated_live
```

Next discriminator: use the generic native authored/clear/cache boundary harness on the next remaining static Blur component (Lanran640/frame732/depth32→sprite13), then inspect its original fill graph. Require source-derived input and exact pinned images before extending the shared live diagnostic. Keep all positive-axis/rotated source and sampler controls exact. No per-fighter runtime patches.

`live_rotated_glow_diagnostic_exact=true`, `production_admitted=false`. General affine/non-quarter coverage, arbitrary rotated long chunks, other components and full AS/clip-action ownership remain open. Draft, not merge-ready; no merge/deploy/Worker. No full roster/Web export rerun for these diagnostic-only changes.
