# r168 — integer fill phase retains all older coordinate bounds

The independently verified r167 scale64 decomposition now uses integer fill translations from-64 to64 on X/Y. Integer values avoid the separately measured fractional-twip input truncation. All256 source texels, child/draw properties, declared fill scale/translation and paired pixel readbacks are preserved.

The30 zero-phase observations remain exact. All30 phase sweeps are monotone, their untouched coordinate channel is constant, and **30/30 refined intervals intersect the old r166 consumed-input bounds**. Bounds and native endpoint witnesses are recorded only as rejection constraints; no coefficient is chosen from them.

The common exact/fixed inverse center both match3370/3870: identity774/774; first rotation524/774; second rotation680/774; positive and negative horizontal shear696/774 each. Remaining differences are one source-index byte. This does not admit affine sampling or move the GPU gate.

[Summary/bounds](summary.json), [failures](failures.json.gz), [native readbacks](native/native.log.gz), [provenance](provenance.json), [acceptance](acceptance.json).

```sh
python3 tools/probes/build_flash_filter_probe.py --case bitmap-affine-integer-phase --output /tmp/integer-phase --ffdec /path/to/ffdec-cli.jar
python3 tools/probes/capture_native_player.py /tmp/integer-phase /tmp/integer-phase/native.log --player-app '/path/to/Flash Player.app' --allow-window-activation --timeout 90
python3 -m tools.probes.analyze_affine_integer_phase --native evidence/importer-loud-fail/r168/native --old-native evidence/importer-loud-fail/r166/native --output /tmp/integer-phase.json
python3 -m unittest tools.tests.test_affine_integer_phase
```

Next discriminator: independently vary signed horizontal versus vertical shear coefficients with fixed source bytes and geometry. Preserve zero-phase factor1/factor64 full-image equivalence before interpreting integer-phase sweeps. Check whether coordinate offsets follow the scan axis or transformed source axis; retain all earlier bounds and reject any common construction with a counterexample. Do not derive a rendering coefficient by selecting an interval endpoint.

`affine_sampler_admitted=false`, `production_admitted=false`.24 live/wrapper diagnostic images remain exact; production54 historical9/54. AS ownership remains a separate merge blocker. Draft only.
