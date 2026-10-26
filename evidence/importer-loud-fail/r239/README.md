# r239: signed orthogonal controls preserve images; cached shear residuals remain

Predeclare I, X/Y reflections, axis swap, 90-degree rotation, and horizontal/vertical shears±1. Transform original fill and ordered mask by S and child by inverse(S), retaining original translations, scale1/4 and camera. Negative determinants reverse local winding through S itself; never reverse vertices ad hoc or change active fillStyle1. Actual property readbacks and raw fields prove identical ordered stage geometry. Untouched nearest67 originals remain separate baselines.

40 native images / 2,621,440 raw RGBA pixels;3,680 source pixels and20 actual matrices verified. Independent FFDEC review confirms20 tags and preserved dormant styles.

- Original raw versus reencoded identity: **4/4 exact** in rawRGBA and independent black-composited output.
- All72 uncached factor pairs are exact. Cached shape56:36/36 exact; cached shape57:15/36 exact.
- Across all144pairs:123full images exact;9437146/9437184full pixels exact (38differences). Deep:78530/78552 (22differences).
- Identity versus each reflection, axis swap and90-degree rotation is exact. Cached shape57 I→H+1 has2full/1deep differences; H-1 is exact; V+1 has2/1; V-1 has1/1.
- Cache-state pairs:11/20full images exact,11differing pixels retained.

Raw maxRGBA delta2,7,0,0; black max2,6,0,0. Every pair remains in the report. Factor-family labels annotate source inputs; they never select a rendering path. These results constrain the tested factorizations only and do not identify a general cache decomposition or sampling origin.

## Reproduce

```sh
python3 -m tools.probes.build_jinye_signed_factorization --output /tmp/bvn-r239/native --ffdec /tmp/bvn-loud-fail/r02/ffdec/ffdec-cli.jar
python3 tools/probes/capture_native_player.py /tmp/bvn-r239/native /tmp/bvn-r239/native/native.log --player-app '/Users/fengkx/me/code/flash-player/Flash Player.app' --allow-window-activation --timeout 90
python3 -m tools.probes.analyze_jinye_signed_factorization --native evidence/importer-loud-fail/r239/native --output /tmp/bvn-r239/analysis.json
python3 -m unittest tools.tests.test_jinye_signed_factorization_controls tools.tests.test_jinye_signed_factorization_analysis
```

Focused7/7 and mandatory gates recorded. FullPython1059pass/2skip retained fromr235; exact sampler suites retained fromr229. No runtime or production edits, new roster/Web/54suite. Complete diagnostic46/54, historical production9/54. All admission false; AS/clip-action ownership open.

## Next discriminator

Keep original local geometry and I/H±1/V±1 factors fixed; move only final draw translation by predeclared integer offsets. Use baseline, X±1/X+16 andY±1/Y+16 with unchanged256² target after proving whole-mask containment. Require zero-offset baselines exact against this round. Compare corresponding pixels by input-defined integer translation, retaining full overlap, deep geometry, and outside-overlap transparency obligations in both raw/black planes and both cache states. This separates destination-origin sensitivity from persistent local shear differences without assuming cache allocation from getBounds or choosing coordinates from RGB.
