# r98 — explicit native blur agrees; implicit authored boundary still differs

The unchanged original Jiraiya wrapper is drawn with and without its authored Blur15×0/quality3. Both premultiplied RGBA readbacks retain the r93 references **240000/240000 exact**. The cleared input is materialized as native BitmapData, then used unchanged in two independent native operations:

1. `BitmapData.applyFilter` into a fresh transparent destination.
2. `attachBitmap` into a fresh clip, then native display `filters=[BlurFilter(15,0,3)]` and draw.

Plain attachBitmap/draw and input-after-filter readbacks are **240000/240000 exact**, proving the tested source bytes were retained and not mutated. The existing common integer blur, unchanged from prior independent blur controls, matches **both native filter outputs240000/240000**.

All three explicit results differ from the original authored wrapper at the same **277 pixels**, max RGBA delta **1/1/1/1**. This is a rejected complete-wrapper candidate, not permission for±1 tolerance. The evidence isolates an implicit materialization/raster/copy-boundary difference; it does not identify which internal stage differs. Changing blur arithmetic to fit the authored image would regress these independent native APIs.

## Reproduce

```sh
python3 -m tools.probes.build_jiraiya_filter_boundary --output /tmp/bvn-r98/recheck --ffdec /path/to/ffdec-cli.jar --harness tools/probes/flash_filters/jiraiya-materialized-blur.as
python3 tools/probes/capture_native_player.py /tmp/bvn-r98/recheck/components/jiraiya /tmp/bvn-r98/recheck/components/jiraiya/native.log --player-app '/path/to/Flash Player.app' --allow-window-activation --timeout 60
python3 -m tools.probes.analyze_jiraiya_materialized_blur --native evidence/importer-loud-fail/r98/native --output /tmp/bvn-r98/results
python3 -m unittest tools.tests.test_jiraiya_materialized_blur
```

[Summary](summary.json), all277 coordinates in `analysis.json.gz`, [hashes](provenance.json), original native log under `native/`, seven readback/candidate images under `images/`, [acceptance](acceptance.json).

Next discriminator: move the same complete wrapper by independent integer destination offsets, retaining authored-filter and cleared-input captures plus exact source bounds/matrix getters. Compare aligned outputs to distinguish origin-dependent raster initialization from a stable implicit cache/copy boundary. Then explicitly materialize any independently justified source-bound filter rectangle. Never choose a buffer origin by whichever rendered RGB happens to match.

`production_admitted=false`; historical54-suite9/54. GPU source leaf/old sampler gates remain exact, but the complete authored Blur wrapper is not admitted. General affine/coverage, implicit cache behavior and full AS ownership remain open. Draft only; no merge/deploy/Worker.

Fresh Python736 pass +2skip; caches26/26, fingerprint, protected, integrity, handoff/contracts green. Full roster/Web not rerun: production unchanged.
