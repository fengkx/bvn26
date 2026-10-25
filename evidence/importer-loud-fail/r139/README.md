# r139 — independent quarter-grid coverage controls exact

Native2560 images cross80 explicitly read source byte/alpha combinations, normal/quarter-turn fills and independent quarter-pixel X/Y offsets0/.25/.5/.75. The source is spatially constant, separating rectangle coverage from interpolation and bulk partition. No input premultiplication formula is assumed: transparent/black paired readbacks provide actual bytes.

The fixed construction `floor(source_byte × exact rectangle area)` is **163840/163840 RGBA pixels exact**: interior18720/18720, fringe26880/26880, outside118240/118240. Coverage uses exact binary fractions, no epsilon or tolerance. Both orientations and all80 readback combinations remain in the evidence.

[Summary](summary.json), [provenance](provenance.json), [acceptance](acceptance.json).

```sh
python3 tools/probes/build_flash_filter_probe.py --case bitmap-quarter-coverage --output /tmp/quarter-coverage --ffdec /path/to/ffdec-cli.jar
python3 tools/probes/capture_native_player.py /tmp/quarter-coverage /tmp/quarter-coverage/native.log --player-app '/path/to/Flash Player.app' --allow-window-activation --timeout 90
python3 -m tools.probes.analyze_quarter_coverage --native evidence/importer-loud-fail/r139/native --output /tmp/quarter-coverage.json
python3 -m unittest tools.tests.test_quarter_coverage
```

Next discriminator: bind only the source-proven unit-quarter-turn Yulong component from r138 to a live GPU input buffer using retained original texels/matrix/mask and exact quarter coverage. Feed that live texture through actual FilterGroup allocation and integer Glow/normal composition, then compare the same two original pinned images. Validate buffer bounds and dependencies; do not globally enable arbitrary affine or production rendering from this pass.

`quarter_grid_constant_coverage_exact=true`, `general_coverage_admitted=false`, `production_admitted=false`. General polygon/affine coverage, long spans, other components and full AS/clip-action ownership remain separate blockers. Draft only; no merge/deploy/Worker.
