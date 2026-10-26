# r181 — independent affine coverage controls reject simple point grids

Constant-color bitmap and vector rectangles retain explicit27621 source texels,33 independently fixed transforms and complete analytically bounded capture regions. Cases include the original main affine matrix/normalization, signed/sheared held-out matrices and independent child/draw translations. Bitmap/vector pairs match **80675/80675 pixels**. Native alpha uses precisely0,15,31,...,239,255.

All four common point-grid models remain rejected across161350 pixels. Consumed-transform lower4×4 grid is closest:158512/161350 exact,2838 failures,max channel delta64. Center grid:158398/161350,max80. Unquantized translation and upper-grid alternatives also fail. No per-pixel selection or edge rule is admitted.

An initial four-argument Math.min/max probe computed an incomplete ROI. The explicit nonzero-bounds guard rejected it before arithmetic analysis. The corrected probe uses nested two-argument calls. [Invalid capture](invalid-roi/) and original harness remain as a regression; its source path is rebased to the archived harness with the original source hash and original build metadata retained; no missing region is silently excluded.

[Summary/actual transform properties](summary.json), [all per-coordinate failures](failures.json.gz), [native capture](native/native.log.gz), [provenance](provenance.json), [acceptance](acceptance.json).

```sh
python3 tools/probes/build_flash_filter_probe.py --case affine-mask-coverage --output /tmp/affine-coverage --ffdec /path/to/ffdec-cli.jar
python3 tools/probes/capture_native_player.py /tmp/affine-coverage /tmp/affine-coverage/native.log --player-app '/path/to/Flash Player.app' --allow-window-activation --timeout 90
python3 -m tools.probes.analyze_affine_mask_coverage --native evidence/importer-loud-fail/r181/native --output /tmp/affine-coverage.json
python3 -m unittest tools.tests.test_affine_mask_coverage
```

Next discriminator: separate vertex quantization from scan-line boundary inclusion. Compare common exact/quarter-quantized vertices with a screen-space top-left half-open scan construction, retaining all33 transforms. Do not choose a construction from output RGB. If alternatives remain, independently capture authored fractional vertices before applying coverage to the15 unresolved main source pixels.

`coverage_admitted=false`, `production_admitted=false`. Production54 historical9/54;24 complete live/wrapper diagnostics exact. AS ownership remains open. Draft only.
