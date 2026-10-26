# r235: exact native equivalence for independently factored dyadic fills

A synthetic source-tag control keeps final bitmap-to-stage mapping and stage mask identical while transferring a predeclared shear between fill and display. Source is R=2x,G=6y,B73,A255 (92x40). F=identity, C is horizontal or vertical shear1/2, S is identity/horizontal±2/vertical±2. Encode F'=S F, C'=C inverse(S), mask'=S mask. Drawscale1 or1/2, translation48,48,192x192target; both cache states. Forty native images, no original reference rewrite.

Actual emitted raw tag coefficients and20native property readbacks prove all group matrices/masks exactly equal. Independent FFDEC parsing confirms all5fill/mask records and b=rotateSkew0,c=rotateSkew1; this is not merely encoder/parser self-roundtrip. Source3680/3680verified;1474560nativepixels captured. Each output retains raw getPixel32 RGBA and a separately measured black-composited plane; raw RGB is not labeled premultiplied.

Both planes independently yield:

- **80/80** factorization comparisons exact:2949120/2949120fullpixels,132400/132400geometry-deep pixels; outside-deep also exact.
- **20/20** cache-state comparisons exact:737280/737280fullpixels,33100/33100deep; outside-deep exact.
- Raw deep coordinate codes264800/264800compatible, with no incompatible output excluded.

This proves bounded native factorization equivalence for these dyadic controls, not universal factorization invariance or a new sampler initializer. Original Jinye r232/r233 failures remain. No runtime/GPU code changes or admission.

## Reproduce

```sh
python3 -m tools.probes.build_jinye_factorization_controls --output /tmp/bvn-r235/native --ffdec /tmp/bvn-loud-fail/r02/ffdec/ffdec-cli.jar
python3 tools/probes/capture_native_player.py /tmp/bvn-r235/native /tmp/bvn-r235/native/native.log --player-app '/Users/fengkx/me/code/flash-player/Flash Player.app' --allow-window-activation --timeout 90
python3 -m tools.probes.analyze_jinye_factorization --native evidence/importer-loud-fail/r235/native --output /tmp/bvn-r235/analysis.json
python3 -m unittest tools.tests.test_jinye_factorization_controls tools.tests.test_jinye_factorization_analysis
```

Focused7/7 and mandatory checks recorded. FullPython **1059pass/2skip** (1061tests,608.422s); discovery began before final r235 additions, which are covered by focused7/7. Exact axis regressions retained at r229. No new roster/Web/54production run. Diagnosticcomplete46/54; historicalproduction9/54. All admission flags false; AS/clip-action ownership remains open.

## Next discriminator

Repeat exact factorization on original Jinye shape56/57 fill matrices and authored masks. Preserve original child/outer transforms where the predeclared C inverse(S) coefficients are independently proved exactly representable in float32; verify actual property readbacks and raw16.16/twip values. Drawscales1/8,1/4 and geometry-derived integer cameras bound complete masks within256x256. Keep an unchanged original nearest67 tag baseline and separately prove any identity reencoding before interpreting factorized images. Compare rawRGBA and black planes, full/deep/coverage scopes, both cache states; do not assume dyadic controls establish arbitrary fractional-source equivalence.
