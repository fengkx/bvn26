# r94 — fresh-instance controls reject a simple first-draw explanation

Three independently attached original Jiraiya wrappers retain source placement/filter tags. Each records initial native Blur15×0/quality3, matrix and cache properties, clears filters/cache, and captures premultiplied RGBA. The only differing prior operation is:

1. No previous draw.
2. Full authored draw before clearing.
3. A1×1 transparent draw before clearing.

All three cleared images and all three next-enterFrame images equal the pinned r93 cleared wrapper **240000/240000 pixels each**. The authored control equals r93 authored240000/240000. Total **1680000/1680000** independent native RGBA pixels agree with the appropriate unchanged boundary reference. Initial filters1/cachetrue and cleared filters0/cachefalse are retained in property readbacks.

Thus a simple “first draw must occur before clearing” rule is **rejected** for this bounded wrapper. The r22 input-only observation remains unexplained; it must not be reused as an unfiltered proof. No cache-invalidation rule is invented or added to runtime. This experiment does not change the r93 nested-parent/direct-child discrepancy1767 pixels.

## Reproduce

```sh
python3 -m tools.probes.build_jiraiya_filter_boundary --output /tmp/bvn-r94/recheck --ffdec /path/to/ffdec-cli.jar --harness tools/probes/flash_filters/jiraiya-first-draw.as
python3 tools/probes/capture_native_player.py /tmp/bvn-r94/recheck/components/jiraiya /tmp/bvn-r94/recheck/components/jiraiya/native.log --player-app '/path/to/Flash Player.app' --allow-window-activation --timeout 60
python3 -m tools.probes.analyze_jiraiya_first_draw --native evidence/importer-loud-fail/r94/native --output /tmp/bvn-r94/results
python3 -m unittest tools.tests.test_jiraiya_first_draw
```

[Summary](summary.json), [native/readback hashes](provenance.json), original captures under `native/`, seven image readbacks under `images/`, [acceptance](acceptance.json).

Next discriminator: independent ramp/impulse bitmap controls with exact child matrix readbacks, varied outer draw translations around twip/quarter-pixel boundaries, and both nested-parent and direct-composed scalar draws. Constrain matrix consumption before changing the sampler or filter allocation. Separately reproduce the original r22 harness (including opaque destination and clock traversal) before attributing its unchanged outputs to a native rule.

`production_admitted=false`; historical54-suite9/54. Prior GPU71824/71824 and leaf6/6 remain strict readback regressions. Complete filtered components, general coverage/affine/implicit buffers and full AS ownership remain open. Draft only; no merge/deploy/Worker.

Fresh Python728 pass +2skip; caches26/26, fingerprint, protected, integrity, handoff/contracts green. Full roster/Web not rerun: production unchanged.
