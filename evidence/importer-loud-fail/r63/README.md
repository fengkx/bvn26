# r63 — bitmap and vector inputs share the same remaining implicit-cache discriminator

Fresh native explicit bitmap controls match the pinned r62 vector controls at **all three stages:19,200/19,200 RGBA pixels**. This rejects a vector-only explanation for the eight final-stage counterexamples. The strict GPU comparison remains red: input6400/6400, filtered6400/6400, final6392/6400. `production_admitted=false`.

The source vector is drawn once into a transparent BitmapData of the authored integer width×64, with inverse integer translation. The vector child is removed, and the measured bitmap is attached at the same integer origin with smoothing disabled. Fill bytes are not synthesized from a straight-alpha approximation. Source, filtered and final stages use paired transparent/black native readbacks. All40 widths/origins/opacities, filter rectangles and stage bytes match r62. Source code and actual native capture are pinned; no r62 reference is rewritten.

This experiment does not identify the internal allocation width or select a new arithmetic route. Both native input types retain the same width17/33 right-edge results; the fixed GPU scalar tail differs at the same eight coordinates. Shared reciprocal/input-normalization arithmetic remains unchanged and previously admitted by r58–r60. No tolerance, allowlist, per-alpha/path splice or coordinate patch.

## Reproduce

```sh
python3 tools/probes/build_flash_filter_probe.py --case filter-bitmap-extent \
  --output /tmp/bvn-r63/native --ffdec /path/to/ffdec-cli.jar
python3 tools/probes/capture_native_player.py /tmp/bvn-r63/native /tmp/bvn-r63/native/native.log \
  --player-app '/path/to/Flash Player.app' --allow-window-activation --timeout 30
python3 -m tools.probes.analyze_bitmap_filter_extent \
  --native evidence/importer-loud-fail/r63/native --output /tmp/bvn-r63/analysis
# Expected exit1: native equivalence does not admit the inexact GPU route.
python3 -m unittest tools.tests.test_bitmap_filter_extent
```

[Analysis/sites](analysis.json), [provenance](provenance.json), [native capture](native/native.log), [acceptance](acceptance.json). No new GPU render: the unchanged actual allocation/readbacks from r62 are compared to the new native bitmap reference. Their source and readback hashes are retained.

## Next discriminating experiment

Materialize the filtered bitmap explicitly with declared dimensions and independently read back its bytes before applying the same transform. Vary transparent border extents while keeping the visible source bytes and world coordinates fixed; compare against the implicit-cache result without assuming that two materialized operations equal one combined operation. These controls can separate generic bitmap span behavior from implicit-filter cache allocation. Do not infer an extra border or rounded width from whichever formula matches output RGB.

Production remains disabled. Components remain historical9/54; full AS/clip-action ownership and other visual gaps are still open. No full roster/Web export or unchanged GPU graphical-suite rerun (production runtime and shader helpers unchanged); strict pinned readback regressions run in Python. Draft only; no merge/deploy/Worker.
