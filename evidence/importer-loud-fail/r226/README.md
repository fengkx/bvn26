# r226: deep-interior ramp gradients reject a constant byte-bias explanation

CPU analysis of pinned r225 native images only; no native reference or production changes. Membership depends on the authored convex quadrilateral: each complete pixel box expanded by two destination pixels must lie inside it. Both endpoints of a gradient pair must belong. This is a diagnostic subset; the complete r225 failure suite remains unchanged in [analysis.json.gz](../r225/analysis.json.gz), with its SHA and totals retained in this report.

All **581600** selected ramp samples satisfy native alpha255, constant blue73 and inactive-channel0. No sample was selected or removed using those readbacks. Twelve fixed models remain rejected. For scaled-child-quarter / minimum / vertical-horizontal, levels are **485718/581600**, horizontal differences **460310/562560**, vertical differences **438012/558252**.

The failures are not merely one constant output-byte correction. They do **not** uniquely identify wrong slope: a constant subpixel phase followed by quantization can also change adjacent byte differences. No fitted coordinate or RGB-selected route follows from these counts. Cache states, scale, source and independently observed unchanged-image buckets are annotated separately; buckets do not choose models.

## Reproduce

```sh
python3 -m tools.probes.analyze_jinye_deep_gradients --output /tmp/bvn-r226/analysis.json
python3 -m unittest tools.tests.test_jinye_deep_gradients tools.tests.test_jinye_translation_controls tools.tests.test_jinye_tag_controls tools.tests.test_jinye_affine_initializers tools.tests.test_smooth_affine_axis_reduction
```

Every level/gradient residual is retained in analysis.json.gz. Focused and mandatory checks are recorded under checks and acceptance.json. Full production roster/Web and54images were not rerun; production is unchanged. Diagnostic coverage remains46/54, historical production9/54. AS/clip-action ownership remains open. Candidate/GPU/production admission stayfalse.

## Next discriminator

Keep unchanged raw shape56/57, fill65, original draw scale and1, both cache states and original fixed matrices. Independently author four corner red impulses at (45,19), (46,19), (45,20), (46,20), amplitudes64/128/255, G0/B73/A255. Retain explicit source, matrix and cache bounds readbacks. Compare cross-amplitude responses under globally fixed weight/rounding orders; use intervals only to reject, never to choose coefficients or coordinate phases. At amplitude255 compare red against pinned r223 gray impulses as a separate channel-control check. Keep all old ramp/impulse and complete JPEG counterexamples before any model admission.
