# r238: exact axis factorization preserves the cached counterexample

Keep original Jinye fill, mask, child/outer transforms, scale 1/4 and the r236 camera. Predeclare S=I,diag(2,1),diag(1,2),diag(2,2); encode F'=SF, mask'=S mask, C'=C inverse(S). Integer source fields remain exact and display columns divided by two remain exact float32. No half-twip source fields are introduced. Preserve untouched nearest67 tags as separate identity baselines.

20 native images / 1,310,720 raw RGBA pixels, 3,680 source pixels and 10 actual matrices verified. Independent FFDEC parsing confirms all 10 tags, unchanged dormant styles, and exact ordered stage masks.

- Baseline: **4/4**, 262,144 full pixels exact.
- All axis-factor pairs: **24/24**, 1,572,864 full pixels and 13,092 deep pixels exact.
- Both raw getPixel32 RGBA and independently measured black-composited planes pass separately.
- Cache pairs: 5/10 exact. The same shape57 pixel (129,73) remains red106 uncached versus108 cached in all five versions; all five deep differences are retained.

The tested axis rescalings preserve output, unlike the tested shear factorizations in r236. This does not identify internal arithmetic or establish a general orientation rule. Original Jinye sampler failures remain. No model is selected from matching pixels and no production path is admitted.

## Reproduce

```sh
python3 -m tools.probes.build_jinye_axis_factorization --output /tmp/bvn-r238/native --ffdec /tmp/bvn-loud-fail/r02/ffdec/ffdec-cli.jar
python3 tools/probes/capture_native_player.py /tmp/bvn-r238/native /tmp/bvn-r238/native/native.log --player-app '/Users/fengkx/me/code/flash-player/Flash Player.app' --allow-window-activation --timeout 90
python3 -m tools.probes.analyze_jinye_axis_factorization --native evidence/importer-loud-fail/r238/native --output /tmp/bvn-r238/analysis.json
python3 -m unittest tools.tests.test_jinye_axis_factorization_controls tools.tests.test_jinye_axis_factorization_analysis
```

Focused 7/7 and mandatory gates recorded. Full Python 1059 pass/2 skip retained from r235; exact axis sampler suites retained from r229. The shared pure factorization comparator preserves this report byte-for-byte. No runtime changes or new roster/Web/54-component run. Complete diagnostic coverage46/54, historical production9/54. Candidate/GPU/production admission false; full AS/clip-action ownership remains open.

## Next discriminator

Keep the same original source and final stage geometry while testing predeclared signed orthogonal factors (X/Y reflections, axis swap, 90-degree rotation) alongside integer shears ±1. Preserve original vertex order through S and the original active fill style; do not reverse the polygon ad hoc. Prove exact raw fields, actual matrices, ordered stage mask, and original-tag identity baseline before comparing raw/black full/deep output. Distinguish orientation changes from nonorthogonal coupling before proposing further sampling arithmetic.
