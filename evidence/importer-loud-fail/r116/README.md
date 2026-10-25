# r116 — separate geometry bounds from translation before testing cache origins

Fresh native controls vary nine geometry minima, four widths, six integer scales, three child translations and two reveal alpha offsets: **1296 cases** with480 explicit source texels. Original800-pixel row y7 and the16-pixel column at its first occupied X are retained. The two alpha offsets1/255 have identical support in **648/648 paired groups**. This measures row/column support, not a full2D image or hidden cache allocation.

Three globally fixed expansion hypotheses are rejected: unexpanded transformed bounds432/1296; source-one-twip expansion656/1296; device-one-subpixel expansion784/1296. In particular, the attractive source-one-twip hypothesis from r115 does not generalize.

A fourth common construction separates geometry from translation: transform geometry into quarter-pixel integer bounds; floor the left bound and ceil the right bound independently; add separately floored node/draw translation; include the final right pixel. This explains **1296/1296** measured intervals. It was formulated after inspecting this grid and is therefore a **candidate requiring independent held-out controls**, not an admitted allocation algorithm. It never chooses a formula by RGB or a per-case padding value. Static cache-origin arithmetic and explicit materialization remain independent constraints.

## Reproduce

```sh
python3 tools/probes/build_flash_filter_probe.py --case bitmap-cache-support-grid --output /tmp/bvn-r116/native --ffdec /path/to/ffdec-cli.jar
python3 tools/probes/capture_native_player.py /tmp/bvn-r116/native /tmp/bvn-r116/native/native.log --player-app '/path/to/Flash Player.app' --allow-window-activation --timeout 60
python3 -m tools.probes.analyze_bitmap_cache_support_grid --native evidence/importer-loud-fail/r116/native --output /tmp/support-grid.json
python3 -m unittest tools.tests.test_bitmap_cache_support_grid
```

[Summary and all rejected sites](summary.json), full readbacks in `analysis.json.gz`, [provenance](provenance.json), [acceptance](acceptance.json).

Next discriminator: retain this formula unchanged and capture fractional scales, fractional widths, independently varied child versus outer translations, including negative output origins using a safe whole-pixel shift. Compare geometry support before using it as a cache-only initializer. Then require all r101–r113 cache references, not only the new reveal images, to pass. Identity filter equality does not establish universal allocation equivalence.

`candidate_admitted=false`, `production_admitted=false`. Historical components9/54, no production/GPU advance. General affine/coverage and AS/clip-action ownership remain open. Draft only; no merge/deploy/Worker.

Validation: focused Python2/2; prior r115 full771 pass+2skip retained. Fresh caches26/26, fingerprint, protected, integrity/handoff/contracts green. No runtime change; roster/Web and GPU/component renders not rerun.
