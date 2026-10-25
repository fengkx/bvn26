# r80 — independent shadow gain and color-byte ordering

Both native APIs (`BitmapData.applyFilter` and filtered bitmap display) agree on all 16896 unblurred byte-ramp samples per API. Inputs are explicitly read back: **33792/33792** RGBA samples, spanning every source alpha byte, source-hidden and source-composited outputs. Property readbacks are retained. No production code changed.

One common construction clears the initial grid and a fresh held-out grid:

1. Consume filter alpha as its native byte getter (floor(requested alpha ×255)).
2. Premultiply the uniform filter RGB by that alpha byte, rounding to the nearest byte.
3. Floor source alpha × strength, then clamp to255.
4. Multiply this gain byte by each premultiplied color/alpha byte, divide by255, round to nearest.
5. For visible white source, compose `source + floor(shadow × (256-source)/256)`.

All predictions use exact rational/integer arithmetic. No epsilon, tolerance, fitted coefficient, output-selected route or instruction claim. Hidden-source is a diagnostic control, not new production flag support.

| Construction | Initial per API | Held-out per API |
|---|---:|---:|
| Continuous gain/color | 3520/4608 | 10802/12288 |
| Floored gain, late color multiplication | 4302/4608 | 11692/12288 |
| Rounded gain | 3502/4608 | 10382/12288 |
| Floored gain + prequantized color | **4608/4608** | **12288/12288** |

Initial grid: color0x51D3EF, alpha0.5/0.75/1, strength0.75/1/2.5. Held-out grid: source-authored colors1137375/16712064/0/16777215, alpha0.25/0.625, strength0.5/1.25/3. Both include hidden and visible source. The held-out capture was collected after defining the common construction; its parameters were not used to choose per-color formulas.

Using the already independently constrained **applyFilter** ties-even phase, grouped blur and consumed kernels, this construction also clears every unchanged r78 crossed control: **207360/207360**, up from190396/207360. Native input/blur controls and r79's display ties-away references remain intact. This does not license applying the applyFilter phase to display objects.

## Reproduce

```sh
# For each case: shadow-gain-paths, shadow-gain-colors
python3 tools/probes/build_flash_filter_probe.py --case shadow-gain-paths --output /tmp/bvn-r80/native --ffdec /path/to/ffdec-cli.jar
python3 tools/probes/capture_native_player.py /tmp/bvn-r80/native /tmp/bvn-r80/native/native.log --player-app '/path/to/Flash Player.app' --allow-window-activation --timeout 45
python3 -m tools.probes.analyze_shadow_gain_paths --native evidence/importer-loud-fail/r80/native --colors evidence/importer-loud-fail/r80/colors --output /tmp/bvn-r80/recheck.json
python3 -m unittest tools.tests.test_shadow_gain_paths tools.tests.test_shadow_phase_paths
```

[Summary](summary.json), complete per-coordinate rejected models in `analysis.json.gz`, [provenance](provenance.json), [acceptance](acceptance.json). Native captures and explicit property/input readbacks are under `native/` and `colors/`.

Next bind this common integer gain/color sequence and API-qualified phase to a **diagnostic GPU fixture**, retaining actual grouped filter allocation and source texture identity. Require exact r78 crossed outputs plus these held-out colors before any production change. Do not widen source-hidden support or treat applyFilter phase as display phase. Non-white source composition and general display-filter crossed parameters need their own controls before broader eligibility.

`candidate_passed=true`, `production_admitted=false`. No new GPU run this round. Components remain historical9/54. Full AS/clip-action ownership, PNG/coverage/affine/general composition eligibility remain separate blockers. Full roster/Web export and54 components were not rerun because production is unchanged. Draft only; no merge/deploy/Worker.
