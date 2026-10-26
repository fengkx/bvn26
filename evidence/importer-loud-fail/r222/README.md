# r222 — independent smooth affine controls reject both fixed baselines

Six independently authored92×40 inputs (horizontal/vertical ramps and four corner impulses) retain Jinye's source-derived affine fill geometry and placement/root coefficients. Outer draw scales are the original normalization,1 and2; a geometry-defined camera keeps bitmap center(46,20) at(48,48). Explicit native input readbacks verify **22080/22080 source pixels**. Both cache states produce **72 native images,663552 RGBA pixels**, with transform/property readbacks retained.

This is explicitly the **Drawing API beginBitmapFill(false,true) domain**, not preserved SWF DefineShape fill65 bytes. `source_tag_equivalence_proved=false`; neither geometric agreement nor matching coefficients establishes API equivalence. Original source/native references remain unchanged.

Both fixed inverse-center constructions are rejected across all329280 geometry-selected interior samples: four-corner byte weights286547 exact; vertical-then-horizontal287378 exact. Maximum RGBA differences are[60,60,60,32]. At the original scale, interiors are opaque: horizontal ramps1670/2076 exact, vertical0/2076 (maxG3), and impulse differences reach60. Therefore changing only interpolation rounding order does not clear these controls. Larger scales retain alpha/coverage differences explicitly. Conditional centroid intervals are labeled with their operation/opacity assumptions; they are not coefficients chosen to match RGB.

[Full measured counterexamples/intervals](analysis.json.gz), [fixture](native/fixture.json), [native readbacks](native/native.log.gz), [acceptance](acceptance.json). `sampler_admitted=false`, `production_admitted=false`; no GPU or complete-wrapper admission advanced. Complete source-backed diagnostics remain46/54, historical production9/54 not rerun. Jinye4/Yijiao4, full AS/clip-action ownership and production binding remain open.

```sh
python3 -m tools.probes.build_jinye_affine_controls --output /tmp/jinye-affine --ffdec /path/to/ffdec-cli.jar
python3 tools/probes/capture_native_player.py /tmp/jinye-affine /tmp/jinye-affine/native.log --player-app '/path/to/Flash Player.app' --allow-window-activation --timeout 90
python3 -m tools.probes.analyze_jinye_smooth_controls --native evidence/importer-loud-fail/r222/native --output /tmp/jinye-affine-analysis.json
python3 -m unittest tools.tests.test_jinye_smooth_controls tools.tests.test_jinye_smooth_leaf tools.tests.test_jinye_jpeg_source tools.tests.test_orochimaru_wrapper
```

Fresh full Python discovery started during r219:986 tests,984 passed/2 skipped/0 failed,751.658s ([log](checks/python.log)); later additions have separate focused round tests. Production/runtime/import data unchanged, so no fresh roster/Web export or production54 rendering is claimed. Caches26/26 and fingerprint/integrity/handoff/contracts/protected-function checks remain required in acceptance.

Next discriminator, **not started**: compare synthetic lossless bitmap55 controls using unchanged original shape56/57 records and bitmap matrices against the same Drawing API controls. Retain identical input bytes, both cache states and geometry-derived sample selection. Establish or reject API equivalence before changing coordinate/footprint arithmetic, then reject any common model against old axis-aligned suites and original r221 leaf failures. No RGB-selected routes or tolerances.

Clean checkpoint at the user's weekly quota threshold: official read-only account rate-limit query reported89% used in the10080-minute window (**11% remaining**). Finish this in-flight round, update Draft PR and pause Goal; do not start r223. Draft only; no merge/deploy/Worker.
