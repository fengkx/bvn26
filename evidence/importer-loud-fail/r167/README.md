# r167 — prove compensated scale paths before phase amplification

Five independently fixed affine matrices are rendered with fill scales1/4/16/64/128, reciprocal child scales and corresponding authored rectangle dimensions. The effective linear matrices match exactly after float32 property readback reconstruction. Explicit source readbacks preserve all256 coordinate-coded texels.

All25 bounded64×64 native images match their factor1 controls: **102400/102400 pixels exact**. Native nonzero-alpha bounds lie wholly inside the captured region, so no nonzero exterior is omitted. The30 old r166 zero-phase observations also match exactly. This proves the bounded zero-phase decomposition, not a general affine sampler or arbitrary fill translation.

[Summary](summary.json), [native capture](native/native.log.gz), [provenance](provenance.json), [acceptance](acceptance.json).

```sh
python3 tools/probes/build_flash_filter_probe.py --case bitmap-affine-scale-split --output /tmp/scale-split --ffdec /path/to/ffdec-cli.jar
python3 tools/probes/capture_native_player.py /tmp/scale-split /tmp/scale-split/native.log --player-app '/path/to/Flash Player.app' --allow-window-activation --timeout 90
python3 -m tools.probes.analyze_affine_scale_split --native evidence/importer-loud-fail/r167/native --phase-native evidence/importer-loud-fail/r166/native --output /tmp/scale-split.json
python3 -m unittest tools.tests.test_affine_scale_split
```

Next discriminator: keep compensated scale64 fixed and sweep integer fill translations from-64 to64 on each axis. These values are exactly representable as twips; their effective source phases are1/64 apart. Require all old zero-phase observations and intersect every new coordinate interval with r166 consumed-twip bounds. Reject contradictory amplification; never choose an interval endpoint as a rendering coefficient.

`zero_phase_scale_paths_exact=true`; `affine_sampler_admitted=false`; `production_admitted=false`. Production54 remains historical9/54;24 source-backed live/wrapper diagnostic images exact. Full AS ownership remains open. Draft only.
