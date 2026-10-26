# r240: integer camera translation preserves the retained factorization images

Keep the original Jinye fill and ordered mask factorizations I/H±1/V±1 fixed. Vary only the final draw translation by predeclared offsets (0,0), (−1,0), (1,0), (16,0), (0,−1), (0,1), (0,16). The child/outer matrices and raw shape tags remain unchanged from r239. All whole-mask vertices remain within the 256² destination. Both cache states are retained independently.

140 native images / 9,175,040 raw RGBA pixels; 3,680 source pixels and 70 actual matrix readbacks verified. Independent review checks all 10 emitted shape tags, exact input-defined camera shifts, and actual typed matrix properties. Native decimal property recovery verifies transport encoding, not renderer arithmetic.

- Zero-offset baselines: **20/20 images exact** against r239, in both raw getPixel32 RGBA and independently black-composited output (1,310,720 pixels per plane).
- Shifted comparisons: **120/120 exact**, 7,680,000/7,680,000 overlapping pixels per plane. Deep geometry is 65,460/65,460 exact.
- Omitted strips are independently checked as transparent raw pixels / opaque black pixels; all are empty. Thus cropping the comparison does not hide differences.
- All source-relative correspondences are determined by the declared integer translation, never output RGB. All full/deep/outside-deep measurements remain in the report.

The r239 cached shear residuals survive these integer camera shifts. This bounded result rejects destination integer origin as their explanation; it does not establish a general cache allocation, fractional translation, affine initializer, or production sampler. No rendering model is tested or admitted here.

## Reproduce

```sh
python3 -m tools.probes.build_jinye_camera_controls --output /tmp/bvn-r240/native --ffdec /tmp/bvn-loud-fail/r02/ffdec/ffdec-cli.jar
python3 tools/probes/capture_native_player.py /tmp/bvn-r240/native /tmp/bvn-r240/native/native.log --player-app '/Users/fengkx/me/code/flash-player/Flash Player.app' --allow-window-activation --timeout 90
python3 -m tools.probes.analyze_jinye_camera_translation --native evidence/importer-loud-fail/r240/native --output /tmp/bvn-r240/reproduced.json
python3 -m unittest tools.tests.test_jinye_camera_controls tools.tests.test_jinye_camera_translation_analysis
```

Focused tests: 6/6 pass. The archived capture reproduces the analysis exactly; checks retain the independent review. Full Python 1059 pass/2 skip is retained from r235, sampler regressions from r229. No production runtime changes or fresh roster/Web/54-component run. Source-backed complete diagnostics remain 46/54; historical production remains 9/54. Candidate, GPU advance, and production admission remain false; AS/clip-action ownership remains open.

## Next discriminator

Bind the actual complete Jinye source graph using source-decoded bitmap55, authored fill65, masks, transforms, depths, and timeline clocks. Compare source-derived uncached/cache-candidate boundaries and final images against existing pinned native outputs, retaining every failure. Do not substitute native pixels as textures or infer cache allocation from bounds alone. This complete binding is the next bounded diagnostic (r241), not another synthetic matrix grid. Keep sampler, coverage, cache allocation, ratio/stream semantics, and independently captured local/input boundaries explicitly unproved until their own gates clear.
