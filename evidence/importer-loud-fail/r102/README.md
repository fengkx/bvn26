# r102 — fractional-bound and scale7 controls reject all cache-origin candidates

1152 independent native clips vary nine signed/fractional mask minima, eight signed child translations, four outer draw origins and scales1.23333740234375/1.24481201171875/5/7. Source fill translation follows the authored mask minimum; original480 texels, actual matrices/bounds and cache-state readbacks are retained. No source/reference or old model is changed to green this expanded suite.

The existing **uncached** initializer remains **240900/240900 interior RGB samples exact**. All three previously exact cache constructions now reject:

| Fixed geometric origin | Exact /240900 | Maximum channel delta |
|---|---:|---:|
| Floor consumed transformed bounds |210078|10|
| Floor authored bounds + draw origin |210084|10|
| Floor node bounds + floor draw origin |210086|10|

Most failures occur at scale7; the remaining scale1.24481201171875 failures are small but still reject admission. The three candidates now produce distinguishable predictions, yet **none** passes. The report retains every failed coordinate and source property plus breakdown by scale and draw translation. No origin is picked from locally matching RGB.

One concrete scale7 witness: mask minimum0, child translation-0.95, outer draw256.5, sample x263 predicts red163/green40 but native is172/42 under the current local-origin model. Smaller±1 coordinate-quantization leftovers also remain at the other scale. These are separate measured counterexamples; no tolerance or per-scale splice is admitted.

## Reproduce

```sh
python3 tools/probes/build_flash_filter_probe.py --case bitmap-cache-crossing --output /tmp/bvn-r102/native --ffdec /path/to/ffdec-cli.jar
python3 tools/probes/capture_native_player.py /tmp/bvn-r102/native /tmp/bvn-r102/native/native.log --player-app '/path/to/Flash Player.app' --allow-window-activation --timeout 90
python3 -m tools.probes.analyze_bitmap_cache_crossing --native evidence/importer-loud-fail/r102/native --output /tmp/bvn-r102/analysis.json
python3 -m unittest tools.tests.test_bitmap_cache_crossing
```

[Summary](summary.json), all counterexamples in `analysis.json.gz`, [hashes](provenance.json), original capture under `native/`, [acceptance](acceptance.json).

Next discriminator: at fixed scale5/7 and phase, independently vary source bitmap width, painted bitmap span and cache bounds. Retain unique shared texels; use transparent geometry to extend bounds without extending painted span. Compare overlapping interior samples around widths35/36/37/38 (scaled spans near256), as well as16/32/60/64. Do not infer a span selector from whichever arithmetic matches. Source-width/ink-span/allocation effects must be separated before changing initialization or routing.

`production_admitted=false`; historical54-suite9/54. r100 measured-cache-plus-blur720000/720000 stays exact; source cache allocation, complete GPU wrapper, general affine/coverage and AS ownership remain open. Draft only; no merge/deploy/Worker.
