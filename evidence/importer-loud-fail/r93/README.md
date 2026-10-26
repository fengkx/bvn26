# r93 — separate authored filter mutation from nested draw rasterization

Fresh Flash captures retain the original Jiraiya placement `342/frame766/depth27 → sprite275 → shape274 → bitmap273`. The existing raw-tag component builder preserves authored PlaceObject state and definitions. Five explicit draw boundaries retain transparent/black premultiplied readbacks and direct gray-background images, with actual child matrix/filter/cache properties before each mutation.

- Authored wrapper vs pinned54-suite image: **240000/240000 exact**.
- Clear child filters/cache **after** the authored draw:4976 RGBA pixels change, max channel deltas189/172/175/217.
- Reassign native BlurFilter(15,0,3): **240000/240000 exact** against original authored output.
- Clear again, advance one enterFrame: **240000/240000 exact** against the earlier cleared wrapper.
- Draw the child directly with independently read child matrix concatenated with normalization: **240000/240000 exact** against the r92 source-bound GPU leaf (padded only with transparent canvas).
- Draw the same cleared child through its parent wrapper versus direct child draw: **1767 differing pixels**, max RGBA48/44/43/52. The reported concatenated matrix is1.23333740234375,0,0,1.24481201171875,262.999878,162.9046024; no coordinate coefficient is fitted from these differences.

Therefore complete authored wrapper admission is still blocked even though the leaf is exact. Nested matrix consumption/raster initialization must be independently measured; filter-only tuning cannot be justified from direct-leaf success.

## Correction to the historical r22 input claim

All54 r22 “raster-input-only” native PNGs equal their original filtered counterparts byte-for-pixel, despite filter-property clear observations. Decoding the retained r22 Jiraiya log reproduces its PNG exactly, so this is not an image-file comparison typo. Those captures do **not** independently prove an unfiltered input boundary. r93 clears after an initial authored draw and observes a changed result. The reason for the r22 difference is not yet established; do not infer stale-cache invalidation or a constructor phase solely from these outputs. Original references remain unchanged.

## Reproduce

```sh
python3 -m tools.probes.build_jiraiya_filter_boundary --output /tmp/bvn-r93/recheck --ffdec /path/to/ffdec-cli.jar
python3 tools/probes/capture_native_player.py /tmp/bvn-r93/recheck/components/jiraiya /tmp/bvn-r93/recheck/components/jiraiya/native.log --player-app '/path/to/Flash Player.app' --allow-window-activation --timeout 60
python3 -m tools.probes.analyze_jiraiya_filter_boundary --native evidence/importer-loud-fail/r93/native --output /tmp/bvn-r93/results
python3 -m unittest tools.tests.test_jiraiya_filter_boundary
```

[Summary](summary.json), complete differing coordinates in `analysis.json.gz`, [hashes](provenance.json), native log gzip and property metadata under `native/`, all ten full readback images under `images/`, [acceptance](acceptance.json).

Next discriminator: fresh independent wrapper instances with clear-before-first-draw versus draw-before-clear, retaining initial and post-mutation property readbacks and next-frame observations. Separately compare nested matrix rounding with a direct composed draw using independent ramp/impulse coordinates; do not infer the transform path from whichever output matches. Retain the five current images unchanged as regression witnesses.

`production_admitted=false`;54-suite historical9/54. GPU leaf/old sampler gates remain exact; full AS ownership and general coverage/affine/implicit buffers remain unproven. Draft only; no merge/deploy/Worker.

Fresh Python726 pass +2skip; caches26/26, fingerprint, protected, integrity, handoff/contracts green. Full roster/Web not rerun: production unchanged.
