# r224: reject global affine smooth initializer transfers

No new native captures or production changes. r223 proves bounded original-tag/Drawing API equivalence; that does not prove smooth affine coordinate arithmetic.

Eight models are evaluated globally: declared composition or independently consumed child/draw quarter translations, fixed-center or r176 minimum-footprint offset, and four-corner byte weights or vertical-then-horizontal interpolation. All models retain every geometry-interior sample across both cache states. No model is selected from RGB.

The closest control model (quarter consumption / minimum / vertical-horizontal) is only **309642/329280**, maximum RGBA deltas **[28,28,28,32]**. The same model on original r221 JPEG leaves is **2610/2818**, maximum **[106,96,110,150]**. All eight are rejected. `analysis.json.gz` preserves every failure coordinate and all models; cache-local rebasing and compound-fill quarter consumption remain unproved.

Independent positive-axis reduction stays exact: scalar 16377/16377, retained sampler 71824/71824 (including repeat and transparent RGBA), Jiraiya 6/6 images / 589824 RGBA, spans 9360/9360. Only the clipped initializer is substituted; repeat and span routing are unchanged. This necessary reduction does not admit affine smoothing.

## Reproduce

```sh
python3 -m tools.probes.analyze_jinye_affine_initializers --native evidence/importer-loud-fail/r223/native --leaf-native evidence/importer-loud-fail/r221/native --dump /tmp/bvn-r215/jpeg-planes --output /tmp/bvn-r224/reproduce
python3 -m tools.probes.analyze_smooth_affine_axis_reduction --output /tmp/bvn-r224/axis.json
python3 -m unittest tools.tests.test_jinye_affine_initializers tools.tests.test_smooth_affine_axis_reduction
```

The JPEG helper is built from `tools/probes/jpeg_scaled_planes.c` against libjpeg-turbo, as recorded in r218/reference-environment. Inputs and native references are unchanged. Focused tests: 5/5. Mandatory checks are recorded in acceptance.json/checks. Full roster/Web and production component suite were not rerun: production is unchanged. Source-backed complete diagnostic coverage remains 46/54; historical production images 9/54. Full AS/clip-action ownership remains open. Candidate/GPU/production admission are all false.

## Next discriminator

Preserve actual fill65 and source quadrilaterals; independently sweep child versus draw translation around quarter boundaries with horizontal/vertical byte ramps and both cache states. Retain explicit input, matrix and local bounds readbacks. Distinguish compose-before-quantize from independent operand consumption before changing smooth weights. A cache-origin rebase needs independent source-local evidence; do not infer it from matching pixels. Reject any common model against all old axis and original JPEG controls.
