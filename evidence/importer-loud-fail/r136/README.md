# r136 — transparent controls distinguish rotated bulk interpolation order

The exact r135 geometry/clip grid is recaptured with transparent source texels varying independently in both axes. Original source bytes, copyPixels permutation bytes and all transform/clip readbacks remain explicit. No target image supplies sampler input.

One geometric partition is tested: intersect the destination scan with the draw clip and fully covered source rectangle, split256-pixel work chunks, take the contiguous source-interior range `1≤u<3,1≤v<7`, and use its leading multiple of four as bulk. Remaining pixels retain scalar byte weights. Routing uses only geometry; neither native output nor the locally matching interpolation formula participates.

Both fixed bulk orders clear the independent ramps **22604/22604**. Transparent controls distinguish them: **H→V22604/22604**, V→H18819/22604 (maxΔ1). This bounded result does not establish general negative-scale/affine behavior, destination coverage or long chunks.

[Transparent summary](summary.json), [retained ramp regression](ramps-partition.json), [provenance](provenance.json), [acceptance](acceptance.json).

```sh
python3 tools/probes/build_flash_filter_probe.py --case bitmap-quarter-turn-transparent-spans --output /tmp/quarter-transparent --ffdec /path/to/ffdec-cli.jar
python3 tools/probes/capture_native_player.py /tmp/quarter-transparent /tmp/quarter-transparent/native.log --player-app '/path/to/Flash Player.app' --allow-window-activation --timeout 90
python3 -m tools.probes.analyze_quarter_turn_partition --native evidence/importer-loud-fail/r136/native --output /tmp/quarter-partition.json
python3 -m tools.probes.analyze_quarter_turn_partition --native evidence/importer-loud-fail/r135/native --ramps --output /tmp/quarter-ramp-partition.json
python3 -m unittest tools.tests.test_quarter_turn_partition
```

Next discriminator: hold this initializer/partition/order fixed; increase source height, use non-binary inverse scales3/5/7 and distant negative draw translations, and independently move clip starts/ends. Preserve all short transparent and ramp controls. Only after held-out geometry clears may original Yulong source input be compared. Long chunks, fractional coverage and general affine remain separate gates.

`partition_admitted=false`, `production_admitted=false`. Source-derived Yulong input and production binding not advanced. Original54 references unchanged; six earlier bounded live Blur images exact, full production54 historical9/54. Full AS/clip-action ownership remains open. Draft only; no merge/deploy/Worker.
