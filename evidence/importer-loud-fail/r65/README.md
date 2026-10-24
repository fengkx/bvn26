# r65 — declared transparent borders explain explicit spans, not implicit allocation

280 independent native controls vary transparent `(left,right)` borders over `(0,0),(0,1),(0,2),(0,3),(1,0),(2,0),(3,0)` for every r64 width/origin/opacity case. `copyPixels` preserves the materialized filter bytes; placement translation compensates the left border. Actual BitmapData width/height and Matrix translation properties are emitted before each draw.

- Input remains **44,800/44,800** exact against the unmodified implicit reference.
- Filtered pre-transform rows remain **44,800/44,800** exact.
- The unchanged scalar/long arithmetic with the independently declared bitmap extent predicts **44,800/44,800** final pixels.

| Explicit transparent border | Final pixels equal to implicit cache |
|---|---:|
| (0,0) | 6392/6400 |
| (0,1) | 6400/6400 |
| (0,2) | 6384/6400 |
| (0,3) | 6384/6400 |
| (1,0) | 6388/6400 |
| (2,0) | 6368/6400 |
| (3,0) | 6372/6400 |

These are globally fixed controls, not a per-pixel route selection. The `(0,1)` match is a discriminator, **not evidence sufficient to adopt an implicit right-border rule**. Extra-border and rounding constructions can coincide on this fixed-kernel/visible-edge sample. `implicit_extent_model_admitted=false`, `production_admitted=false`; the analysis intentionally exits1.

## Reproduce

```sh
python3 tools/probes/build_flash_filter_probe.py --case filter-border-extent \
  --output /tmp/bvn-r65/native --ffdec /path/to/ffdec-cli.jar
python3 tools/probes/capture_native_player.py /tmp/bvn-r65/native /tmp/bvn-r65/native/native.log \
  --player-app '/path/to/Flash Player.app' --allow-window-activation --timeout 45
python3 -m tools.probes.analyze_filter_borders \
  --native evidence/importer-loud-fail/r65/native --output /tmp/bvn-r65/analysis
python3 -m unittest tools.tests.test_filter_borders
```

[Full controls/sites](analysis.json), [provenance](provenance.json), [capture](native/native.log), [acceptance](acceptance.json). The initial scratch capture logged requested dimensions; a fresh capture logs actual object properties. All1121 stage/property events agree between those captures (excluding run id/sequence metadata). Only the actual-property capture is used here. Previous r62/r64 references remain unchanged.

## Next discriminator

Test the fixed right-border hypothesis on held-out kernel sizes and source widths, retaining explicit pre-transform readbacks and independently measured filter rectangles. Then distinguish border/rounding hypotheses with fractional or clipped cache boundaries. Do not choose a different border for a failing case, or promote a formula merely from current output agreement; the actual implicit allocation construction remains unverified.

No new GPU run or production/shader change. Components remain historical9/54 and AS/clip-action ownership remains open. Full roster/Web export and unchanged graphical suites were not rerun; old exact CPU/GPU readbacks remain strict Python regressions. Draft only; no merge/deploy/Worker.
