# r101 — cache rasterization retains the fractional draw phase

378 fresh independent native bitmap clips preserve480 explicit source texels. Fill/mask minima0/2/-4, child scale1/1.23333740234375/3, seven child translations and six outer integer/fractional draw origins vary independently. Cache flags, actual child matrix and source bounds are read back for each cached/uncached image.

- Common global uncached initializer: **37842/37842 interior RGB samples exact**.
- Snapping a fixed cached row to whole-pixel placement fails: floor/even/up variants each explain only224/378 complete rows. Fractional outer draw phase cannot simply be discarded.
- Local initialization that excludes the fractional outer draw phase:25266/37842 (or25206 with node-zero origin), rejected.
- Initialize in a local integer-origin raster **while retaining the complete consumed fractional draw translation**, then copy at that integer origin: **37842/37842 exact** for all three independently defined geometric-origin constructions: floor(consumed transformed bounds), floor(authored bounds + outer draw), and floor(node bounds)+floor(outer draw).

Those three constructions remain indistinguishable on this control grid. The report keeps them separate; no origin is selected from RGB and no production cache initializer is admitted. Complete row boundary pixels are retained in native logs and placement comparisons; the interpolation model score excludes one source texel at each authored edge to avoid claiming unproved fractional coverage.

## Reproduce

```sh
python3 tools/probes/build_flash_filter_probe.py --case bitmap-cache-origin --output /tmp/bvn-r101/native --ffdec /path/to/ffdec-cli.jar
python3 tools/probes/capture_native_player.py /tmp/bvn-r101/native /tmp/bvn-r101/native/native.log --player-app '/path/to/Flash Player.app' --allow-window-activation --timeout 60
python3 -m tools.probes.analyze_bitmap_cache_origin --native evidence/importer-loud-fail/r101/native --output /tmp/bvn-r101/analysis.json
python3 -m unittest tools.tests.test_bitmap_cache_origin
```

[Summary](summary.json), complete rejected-model coordinates in `analysis.json.gz`, [hashes](provenance.json), original capture under `native/`, [acceptance](acceptance.json).

Next discriminator: choose fractional mask minima and neighboring child translations that place authored and consumed lower bounds on opposite integer sides; vary inverse-scale families including5/7 and retain distant integer draw origins. Preserve source bytes/bounds/property readbacks and compare each fixed origin construction globally. Require old controls and source-bound cache images before full GPU wrapper binding. Do not pick a matching origin per output pixel.

`production_admitted=false`; historical54-suite9/54. r100 actual-cache-plus-blur720000/720000 remains exact; source cache allocation, complete GPU wrapper, general affine/coverage and AS ownership remain open. Draft only; no merge/deploy/Worker.

Fresh Python743 pass +2skip; caches26/26, fingerprint, protected, integrity, handoff/contracts green. Full roster/Web not rerun: production unchanged.
