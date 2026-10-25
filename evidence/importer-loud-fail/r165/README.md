# r165 — integer translation redistribution preserves the native result

Child translations independently take-128/0/128 on X/Y, with exact compensating draw translations. Every group verifies identical linear coefficients, total source-to-device translation and sampled target position against r164. Raw source256 texels remain explicit.

All **40/40 groups** are invariant across nine decompositions (**360 observations**). The zero-child-translation path reproduces the old baseline **40/40**. Separate integer translation consumption therefore does not explain the initializer failures within this domain. Fractional fill consumption remains unproved.

[Summary/readbacks](summary.json), [native log](native/native.log.gz), [provenance](provenance.json), [acceptance](acceptance.json).

```sh
python3 tools/probes/build_flash_filter_probe.py --case bitmap-affine-translation-split --output /tmp/translation-split --ffdec /path/to/ffdec-cli.jar
python3 tools/probes/capture_native_player.py /tmp/translation-split /tmp/translation-split/native.log --player-app '/path/to/Flash Player.app' --allow-window-activation --timeout 90
python3 -m tools.probes.analyze_affine_translation_split --native evidence/importer-loud-fail/r165/native --baseline evidence/importer-loud-fail/r164/summary.json --output /tmp/translation-split.json
python3 -m unittest tools.tests.test_affine_translation_split
```

Next discriminator: signed fill-translation sweeps finer than1/20, with fixed geometry/child/draw matrices and source readbacks. Include identity controls to distinguish declared fill properties from consumed translation precision. Use observed source-index transitions to reject common constructions; do not infer an initializer from an unverified input-consumption assumption or select interval coefficients.

`affine_sampler_admitted=false`, `production_admitted=false`. All prior failures remain; production54 historical9/54;24 live/wrapper diagnostics exact; full AS ownership open. Draft only; no merge/deploy/Worker.
