# r133 — quarter-turn texel permutation is not native-equivalent

Fresh native Flash controls compare authored quarter-turn fill matrices with independently materialized `copyPixels` texel permutations. All48 materialized source texels retain paired premultiplied RGBA exactly. Source4×3 includes alpha0/64/128/255; original bytes and matrix/cache properties are read back. Scales1/1.25/2/3 and independent X/Y offsets0/.25/.5 are crossed with four turns and cache off/on:576 images,288 pairs.

Only **162/288 pairs**, **217324/221184 pixels** are exact. Identity-turn controls72/72 are exact. Both cache states have the same counts: turn1=18/36 pairs,maxΔ2; turn2=9/36,maxΔ2; turn3=18/36,maxΔ3. A geometric rectangle/texel permutation cannot substitute for the signed fill sampler. No candidate is admitted and no original reference changed.

[Summary](summary.json) retains every differing coordinate and both RGBA values, complete properties, source and permuted bytes. [Provenance](provenance.json), [acceptance](acceptance.json), native capture under `native/`.

## Reproduce

```sh
python3 tools/probes/build_flash_filter_probe.py --case bitmap-quarter-turn-equivalence --output /tmp/quarter-turn --ffdec /path/to/ffdec-cli.jar
python3 tools/probes/capture_native_player.py /tmp/quarter-turn /tmp/quarter-turn/native.log --player-app '/path/to/Flash Player.app' --allow-window-activation --timeout 90
python3 -m tools.probes.analyze_quarter_turn_equivalence --native evidence/importer-loud-fail/r133/native --output /tmp/quarter-turn-analysis.json
python3 -m unittest tools.tests.test_quarter_turn_equivalence
```

Next discriminator: repeat this fixed transform/geometry grid with opaque horizontal-red and vertical-green ramps plus a constant-blue channel. Compare interior coordinates separately from fractional coverage. Recover coordinate/weight constraints for reversed axes before considering any interpolation-order candidate; no RGB-selected path. Preserve this transparent-source suite as a rejection gate.

`quarter_turn_equivalence_admitted=false`, `production_admitted=false`. Six previous bounded live Blur images exact; full production54 historical9/54 not rerun. General affine/coverage, remaining component bindings and full AS/clip-action ownership remain open. Production unchanged; no full roster/Web rerun. Draft only; no merge/deploy/Worker.
