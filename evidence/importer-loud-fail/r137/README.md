# r137 — fixed rotated partition survives distant larger-source controls

The r136 initializer/geometry/order is retained, replacing only independently authored source dimensions4×16 and source bounds. Native1080 images cross90°/270°, scales3/5/7, draw X8/−7.25/−48.5, draw Y6/6.25, clip starts0/1/8 and lengths3/4/5/7/8/9/12/16/24/32. Actual source and byte-preserving rotated source readbacks remain pinned.

Fixed geometric partition with H→V is **155624/155624 interior pixels exact**. V→H is110526/155624,maxΔ1 and rejected. This is a held-out test of the common construction; no parameter or per-pixel route changed after reading these outputs. Coverage fringes remain outside this claim; all target reads are retained.

[Summary](summary.json), [provenance](provenance.json), [acceptance](acceptance.json).

```sh
python3 tools/probes/build_flash_filter_probe.py --case bitmap-quarter-turn-heldout --output /tmp/quarter-heldout --ffdec /path/to/ffdec-cli.jar
python3 tools/probes/capture_native_player.py /tmp/quarter-heldout /tmp/quarter-heldout/native.log --player-app '/path/to/Flash Player.app' --allow-window-activation --timeout 90
python3 -m tools.probes.analyze_quarter_turn_heldout --native evidence/importer-loud-fail/r137/native --output /tmp/quarter-heldout.json
python3 -m unittest tools.tests.test_quarter_turn_heldout
```

Next discriminator: derive original Yulong shape266 input directly from source bitmap148 and its retained fill matrix/mask, preserving independent child/draw translation consumption. Compare full pinned cache input and identify fractional edge samples separately. Independently prove any required nontransparent fractional coverage before GPU binding; interior success is insufficient. Long256-pixel chunks and arbitrary affine remain unproven by this narrow canvas.

`partition_admitted=false`, `production_admitted=false`. No production path enabled. Full production54 remains historical9/54; six previous bounded live Blur images exact. General affine/coverage, other components and full AS/clip-action ownership remain open. Draft only; no merge/deploy/Worker.
