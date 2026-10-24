# r71 — independent fractional BlurFilter axis controls

315 native `BitmapData.applyFilter` controls vary seven kernels, five source alphas, constant/impulse/ramp sources and horizontal/vertical/both-axis filters. Paired transparent and black readbacks preserve the actual premultiplied source and output bytes. **10080/10080 source pixels** agree with the explicit input construction. Filter property readbacks are retained; property precision is not assumed to equal consumed precision.

| Globally fixed arithmetic | Exact output RGBA pixels |
|---|---:|
| Rational weights and normalization | 9884/10080 |
| Truncate edge weights to 8 fraction bits | 8767/10080 |
| Truncate reciprocal to 16 fraction bits | 7947/10080 |
| Both preceding truncations | 7936/10080 |
| 8-bit edge weights, normalize by consumed weight sum | 9894/10080 |

**All candidates rejected.** No coefficient or arithmetic path is selected from output pixels. These are explicit BlurFilter controls, not an implicit Glow implementation admission. No GPU or production changes were made.

A useful single-axis counterexample is case54: kernel3.99609375, constant alpha25, horizontal only. At x6 native is `[2,2,2,2]`, rational predicts3; at x9 native is `[22,22,22,22]`, rational predicts21. Thus the new failures already occur in one axis, with opposing signs at different support positions; a global output bias cannot fix them. The 8-bit-weight renormalized candidate fails at the same two sites. The independent constant and impulse controls distinguish support-edge consumption from a uniform normalization error.

## Reproduce

```sh
python3 tools/probes/build_flash_filter_probe.py --case blur-fractional-axis \
  --output /tmp/bvn-r71/native --ffdec /path/to/ffdec-cli.jar
python3 tools/probes/capture_native_player.py /tmp/bvn-r71/native /tmp/bvn-r71/native/native.log \
  --player-app '/path/to/Flash Player.app' --allow-window-activation --timeout 45
python3 -m tools.probes.analyze_fractional_blur_axis \
  --native evidence/importer-loud-fail/r71/native --output /tmp/bvn-r71/analysis.json
python3 -m unittest tools.tests.test_fractional_blur_axis
```

Analysis exits normally after recording rejected models; this is not an admission gate. [All counterexamples](analysis.json), [native inputs/readbacks](native/native.log), [hashes](provenance.json), [checks](acceptance.json).

Next independently bracket consumed kernel precision with a fixed fine sweep around integer/half-integer kernels, reading properties and constant/impulse responses on each axis. Require a common consumption rule to retain all these controls and the original blur suite before considering runtime arithmetic. Do not infer consumed kernel precision from a locally matching output or change CXFORM to absorb pre-transform differences.

Production remains closed. The r70 actual GPU gate still has244 filtered/162 final differences; components remain historical9/54. General coverage/affine/production eligibility and full AS/clip-action ownership remain open. Full roster/Web and unchanged graphical gates were not rerun; their old pinned controls remain regression inputs. Draft only; no merge/deploy/Worker.
