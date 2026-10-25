# r174 — dominant off-diagonal controls reject diagonal priority

Eight independently specified reflected shears include off-diagonal magnitudes exceeding the diagonal, transposed axes and opposite signs. Explicit128×128 capture regions contain every nonzero pixel; **131072/131072 zero-phase full-image pixels** match across factor1/factor64 paths and48/48 scalar zero phases agree.

All6192 integer-phase samples test the same three global constructions. **Minimum(0,a,b):6192/6192 exact**. Negative diagonal priority:3480/6192; sum of negative components:4260/6192. Both alternatives are rejected. The minimum construction also retains60645/60645 prior observations, for66837 exact controls across these rounds. No coefficient or arithmetic path is selected from native RGB.

[Summary](summary.json), [failures](failures.json.gz), [native capture](native/native.log.gz), [provenance](provenance.json), [acceptance](acceptance.json).

```sh
python3 tools/probes/build_flash_filter_probe.py --case bitmap-affine-dominant-shear --output /tmp/dominant-shear --ffdec /path/to/ffdec-cli.jar
python3 tools/probes/capture_native_player.py /tmp/dominant-shear /tmp/dominant-shear/native.log --player-app '/path/to/Flash Player.app' --allow-window-activation --timeout 90
python3 -m tools.probes.analyze_affine_dominant_shear --native evidence/importer-loud-fail/r174/native --output /tmp/dominant-shear.json
python3 -m unittest tools.tests.test_affine_dominant_shear
```

Next discriminator: select pixel coordinates from independently calculated disagreements between exact-norm and rounded16.16-offset arithmetic, before reading their native RGB. Preserve actual source bytes and matrices; include adjacent coordinates as controls. On the fixed coordinate lattice, flooring the offset is mathematically equivalent to retaining the exact norm; rounding need not be. Verify this boundary distinction before GPU encoding. Do not infer native intermediate precision beyond distinguishable behavior.

`candidate_admitted=false`, `gpu_advance_allowed=false`, `production_admitted=false`. No production binding. Production54 historical9/54;24 original live/wrapper diagnostics exact. AS ownership remains open. Draft only.
