# r81 — common shadow bytes through actual diagnostic GPU buffers

The r80 construction now runs as an integer GPU diagnostic shader using production-created FilterGroup contents, passes, padding and texture dependencies. The fixture asserts source RGBA8 upload identity, allocation bounds, consumed blur operands, grouped H-then-V order, original source texture identity, API identity and final texture linkage. Production files and eligibility are unchanged.

All **1752 cases** clear every stage:

| Readback | Exact RGBA samples |
|---|---:|
| Source buffer | 241152/241152 |
| Grouped blur output | 241152/241152 |
| Shadow output | 241152/241152 |
| Raw final copy | 241152/241152 |

Coverage is unchanged r78 crossed native controls (207360 samples) plus both APIs for r80 original and independently held-out gain/color ramps (33792 samples). The native API is a source-authored fixture field, never selected from output pixels. The shader uses ties-even only for explicit applyFilter, ties-away for display; gain and prequantized color use common integer arithmetic. Source-hidden controls remain diagnostic-only. All tested strengths are exactly representable on the explicit1/256 input grid; the fixture rejects off-grid strengths rather than making a general consumption claim.

This is **raw final copy**, not ordinary scene/background composition. Inputs are explicit premultiplied white ramps/rectangles, not general decoded PNGs or affine coverage. The display controls here have zero shadow distance/blur; arbitrary display-filter crossed parameters are not established by the applyFilter controls. No global production admission follows from these bounded results.

## Reproduce

```sh
python3 -m tools.probes.run_integer_shadow_gpu --godot /path/to/Godot --output /tmp/bvn-r81/gpu
python3 -m unittest tools.tests.test_integer_shadow_gpu tools.tests.test_shadow_gain_paths tools.tests.test_shadow_phase_paths
python3 -m tools.probes.run_filter_regressions --godot /path/to/Godot --output /tmp/bvn-r81/regressions
```

[Readback comparisons](render/comparison.json), [source/native/GPU hashes](render/provenance.json), [acceptance](acceptance.json). Full readbacks are `render/rows.json.gz`; all37 batch inputs and clean GPU logs are retained. Godot4.7.2 Compatibility, AppleM2 OpenGL4.1 Metal90.5.

Next independently capture **non-white premultiplied source bytes** with non-unit gain/alpha, blur/offset, on both applyFilter and actual display boundaries. Keep source readbacks and API-specific phase fixed. This separates source-over composition and display-cache effects before widening eligibility. Include separate post-filter opacity/transparent-destination controls only after those source/filter outputs agree; do not infer final scene composition from raw copy.

`passed=true`, `production_admitted=false`. Historical components9/54 were not remeasured. Full AS/clip-action ownership and general PNG/coverage/affine/nested composition remain blockers. Full roster/Web export not rerun (production unchanged). Draft only; no merge/deploy/Worker.
