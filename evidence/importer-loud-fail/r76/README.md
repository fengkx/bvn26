# r76 — independent multi-pass Glow and zero-offset DropShadow controls

540 new native `BitmapData.applyFilter` cases independently exercise outer Glow and zero-distance DropShadow at unit alpha/strength. Both retain source readbacks, reported blurX/blurY/quality/color/alpha/strength, and a separate materialized Blur control. The Blur control is **not** a readback of the other filters' hidden internal buffers.

| Gate / order | Exact RGBA samples |
|---|---:|
| Explicit inputs | **69120/69120** |
| Independent Blur controls | **69120/69120** |
| Glow, horizontal passes then vertical passes | **34560/34560** |
| Zero-offset DropShadow, same grouped order | **34560/34560** |
| Each family, alternating axes | 34221/34560 |
| Each family, reverse grouping | 33873/34560 |

The same common six-significant-bit kernel construction and per-axis byte truncation are used globally. Composition retains the independently supported source-over-glow byte rule: round the colored glow to bytes, then add `floor(glow*(256-source_alpha)/256)` to the original source. No coefficient or pass route is picked from observed RGB.

Controls span kernels1.5,3.99609375,7.99609375,8.25,16; alphas25/135; constant/impulse/ramp sources; each axis and both axes; quality1/2/3. Each family has339 alternating-order counterexamples, all both-axis quality2/3 with maximum channel delta1; reverse grouping has687 counterexamples per family, maximum delta2. The64×64 bitmap's central row and column are sampled, with shared center counted twice. Zero-distance DropShadow is intentionally isolated before nonzero offset composition; it does not establish arbitrary offset/strength/opacity behavior.

## Reproduce

```sh
python3 tools/probes/build_flash_filter_probe.py --case glow-shadow-multipass \
  --output /tmp/bvn-r76/native --ffdec /path/to/ffdec-cli.jar
python3 tools/probes/capture_native_player.py /tmp/bvn-r76/native /tmp/bvn-r76/native/native.log \
  --player-app '/path/to/Flash Player.app' --allow-window-activation --timeout 45
python3 -m tools.probes.analyze_glow_shadow_multipass \
  --native evidence/importer-loud-fail/r76/native --output /tmp/bvn-r76/analysis.json
python3 -m unittest tools.tests.test_glow_shadow_multipass
```

[All comparisons and negative controls](analysis.json), [native readbacks](native/native.log), [hashes](provenance.json), [acceptance](acceptance.json). This is fresh bounded CPU/native evidence, not a GPU or production admission gate.

Next carry these family controls into actual FilterGroup diagnostic nodes with the unchanged integer blur, actual group padding and original-source composition. Retain r74/r75 exact inputs and outputs. Independently cross multi-pass filtering with nonzero shadow offsets and non-unit filter strength/alpha before widening those claims. Preserve old DropShadow offset controls rather than inferring compositional equivalence.

`production_admitted=false`. Production alternating-axis code remains unchanged. No new GPU render this round; prior exact graphical readbacks remain pinned Python regressions. Components remain historical9/54. Full AS/clip-action ownership and general coverage/affine/production eligibility remain merge blockers. Full roster/Web and54 components were not rerun. Draft only; no merge/deploy/Worker.
