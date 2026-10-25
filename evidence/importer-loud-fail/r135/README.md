# r135 — independent clip changes expose rotated scan partition

The source is enlarged to4×8 with independently read horizontal-red/vertical-green ramps and constant blue73. Native90°/270° transforms retain scale1.25/2/3 and fractional X/Y offsets. Draw clipping varies start8/9 and length3/4/5/7/8/9/12/16 without changing source coordinates. All384 native images and input/property readbacks are retained.

Among2790 overlapping interior coordinate groups, **157 change output** solely with clip start/length. Fixed byte interpolation is **21354/22604 exact**, maximum channelΔ1; either universal separable order reaches19857/22604. Therefore signed scalar initialization alone is insufficient. Outside the draw clip is asserted transparent; fractional shape fringe/exterior is explicitly excluded from arithmetic claims.

[Summary](summary.json) includes changed-overlap observations and all fixed-order counterexamples. [Provenance](provenance.json), [acceptance](acceptance.json).

```sh
python3 tools/probes/build_flash_filter_probe.py --case bitmap-quarter-turn-spans --output /tmp/quarter-spans --ffdec /path/to/ffdec-cli.jar
python3 tools/probes/capture_native_player.py /tmp/quarter-spans /tmp/quarter-spans/native.log --player-app '/path/to/Flash Player.app' --allow-window-activation --timeout 90
python3 -m tools.probes.analyze_quarter_turn_spans --native evidence/importer-loud-fail/r135/native --output /tmp/quarter-spans.json
python3 -m unittest tools.tests.test_quarter_turn_spans
```

Next discriminator: keep this entire geometry/clip grid fixed and capture transparent source texels varying in both axes. Test a single source-interior four-pixel prefix partition with globally fixed H→V versus V→H operations. Independent ramps alone cannot separate these orders. Do not choose the partition or order from observed pixel values.

`initializer_admitted=false`, `interpolation_routing_admitted=false`, `production_admitted=false`. No production binding, no change to original reference images. Six previous live Blur images exact; historical full54 remains9/54. Coverage/affine and full AS ownership remain open. Draft only; no merge/deploy/Worker.
