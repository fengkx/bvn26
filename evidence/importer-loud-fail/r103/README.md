# r103 — width, painted span and reported bounds do not explain the prefix mismatch

384 independent native cases vary widths16/32/35/36/37/38/60/64, scale5/7, signed child phase and integer/fractional outer draw. Three constructions keep shared source texels identical:

1. Source bitmap width equals painted width.
2. Source bitmap stays64 wide while painted width changes.
3. Source bitmap stays64, painted span stays16, and alpha-zero geometry extends reported clip bounds to the tested width.

All3056 source texels are explicitly verified; actual bounds prove the third construction extends geometry while preserving the shared painted prefix. Both cached and uncached captures retain flag/property readbacks.

**No shared-prefix changes:** all384 width-prefix groups and256 mode-prefix groups are exact for both native paths. This includes widths36/37 crossing a256-pixel scaled extent at scale7. Therefore those width/bounds/span changes do not explain the first-interior-pixel failures; a new256-pixel route must not be inferred from the prior scale7 mismatch.

The unchanged uncached model matches **68544/68544** full-interior samples. The existing cache-origin model still matches only **53556/68544**, including failures already present in width16 controls. For example scale7/child0/outer256.5 predicts first-interior red163/green40 while native is154/39; child-0.95 at the same outer phase gives the opposite shift (native172/42). No one-sided correction or per-phase route is admitted.

## Reproduce

```sh
python3 tools/probes/build_flash_filter_probe.py --case bitmap-cache-width --output /tmp/bvn-r103/native --ffdec /path/to/ffdec-cli.jar
python3 tools/probes/capture_native_player.py /tmp/bvn-r103/native /tmp/bvn-r103/native/native.log --player-app '/path/to/Flash Player.app' --allow-window-activation --timeout 60
python3 -m tools.probes.analyze_bitmap_cache_width --native evidence/importer-loud-fail/r103/native --output /tmp/bvn-r103/analysis.json
python3 -m unittest tools.tests.test_bitmap_cache_width
```

[Summary](summary.json), complete prefix/model coordinates in `analysis.json.gz`, [hashes](provenance.json), original source/bounds/property readbacks under `native/`, [acceptance](acceptance.json).

Next discriminator: with the width16 source fixed, sweep signed child translations densely across quarter-consumption thresholds at scale5/7 and retain integer/fractional draw origins. Read native matrix inverse/forward intermediates at sufficient binary precision to compare globally defined operation orders. Keep the uncached control exact. Do not add a width selector, epsilon or locally fitted cache translation; reject any proposed normalization against all old origin/scale controls before GPU binding.

`production_admitted=false`; historical54-suite9/54. r100 actual-cache-plus-blur720000/720000 remains exact. Source cache normalization, full GPU wrapper, general affine/coverage and AS ownership remain open. Draft only; no merge/deploy/Worker.
