# r64 — explicit filter bitmap is exact; implicit cache remains distinct

Fresh native controls explicitly allocate the measured `generateFilterRect` extent, run `applyFilter` into that bitmap, read the result, then apply the same ColorTransform through `BitmapData.draw`. The original implicit-cache capture is retained unchanged; equivalence is measured, never assumed.

| Comparison | Input | Filtered | Final |
|---|---:|---:|---:|
| Pinned actual-allocation GPU vs explicit native bitmap | 6400/6400 | 6400/6400 | **6400/6400** |
| Implicit native cache vs explicit native bitmap | 6400/6400 | 6400/6400 | **6392/6400** |

The same40 widths/origins/opacities and paired transparent/black readbacks are used. The eight differences are exactly the width17/33 right-edge sites from r62/r63. This independently demonstrates that explicit filter materialization and the implicit filter-cache path do not share all final span behavior, despite identical visible pre-transform bytes. It supports the admitted arithmetic/explicit allocation path while leaving implicit allocation/routing unresolved.

`passed=false`, `implicit_equivalence_passed=false`, `production_admitted=false`. Explicit-path success cannot substitute for implicit-cache fidelity. No production/shader edit, new allowlist, tolerance, reference rewriting or fitted route.

## Reproduce

```sh
python3 tools/probes/build_flash_filter_probe.py --case filter-explicit-extent \
  --output /tmp/bvn-r64/native --ffdec /path/to/ffdec-cli.jar
python3 tools/probes/capture_native_player.py /tmp/bvn-r64/native /tmp/bvn-r64/native/native.log \
  --player-app '/path/to/Flash Player.app' --allow-window-activation --timeout 30
python3 -m tools.probes.analyze_explicit_filter_extent \
  --native evidence/importer-loud-fail/r64/native --output /tmp/bvn-r64/analysis
# Expected exit1: implicit equivalence remains unproven and differs at8 pixels.
python3 -m unittest tools.tests.test_explicit_filter_extent
```

[Analysis/exact sites](analysis.json), [provenance](provenance.json), [native capture](native/native.log), [acceptance](acceptance.json). GPU comparisons reuse unchanged r62 actual-buffer readbacks, with hashes retained. No new GPU run is claimed.

## Next independent control

Vary explicit transparent left/right border extents while preserving all visible filtered bytes/world coordinates, and measure each declared bitmap size before applying the transform. Compare these native results with the implicit-cache result as a discriminator, not as a way to select a fitting padding rule. In particular, extra-border and width-rounding hypotheses can be observationally equivalent at the current nonzero edge; neither is admitted. Retain all old arithmetic and geometry controls before widening any route.

Components remain historical9/54; full AS/clip-action ownership and other visual gaps remain open. Full roster/Web export and unchanged graphical suites are not rerun; pinned exact CPU/GPU regressions are checked in Python. Draft only; no merge/deploy/Worker.
