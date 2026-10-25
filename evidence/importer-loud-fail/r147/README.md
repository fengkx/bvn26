# r147 — binary-alpha indexed controls require direct native source verification

The entire r146 geometry/transform/single-pixel grid is retained; only source texels change to a2×2 repeating binary-alpha four-corner pattern. AS source constructor readbacks match all2275 declared pixels. Format3 payload decoding independently matches those same bytes in Python.

AS eight-bit scalar weights remain **576/576 exact**. However, **all576 indexed display samples are transparent**, including coordinates whose declared indexed texels are opaque. No tested weight precision explains this and no math is admitted. Lower-precision match counts in the summary are merely incidental matches to transparent output, not candidate evidence.

Crucial boundary: the explicit source readbacks so far come from **AS BitmapData construction**; the actual Flash-decoded indexed bitmap has **not** been directly read. A valid encoded payload plus matching Python decode is insufficient to infer what Flash consumed. Do not interpret this as an interpolation rule or patch the output.

[Summary with native properties/outputs](summary.json), [provenance](provenance.json), [acceptance](acceptance.json).

```sh
python3 -m tools.probes.build_indexed_alpha_scalar --output /tmp/indexed-alpha --ffdec /path/to/ffdec-cli.jar
python3 tools/probes/capture_native_player.py /tmp/indexed-alpha/components/lanran /tmp/indexed-alpha/components/lanran/native.log --player-app '/path/to/Flash Player.app' --allow-window-activation --timeout 90
python3 -m tools.probes.analyze_indexed_alpha_scalar --native evidence/importer-loud-fail/r147/native --output /tmp/indexed-alpha.json
python3 -m unittest tools.tests.test_indexed_alpha_scalar
```

Next discriminator: export this same indexed bitmap and read its native `BitmapData.loadBitmap` bytes directly, retaining display samples **before and after** that materialization. Verify the exported bitmap payload is unchanged and compare native decoded pixels to declared/AS bytes. If loadBitmap changes display state, retain that as a separate observation; never treat the post-read path as the original reference.

`native_indexed_texels_read_back=false`, `indexed_sampler_admitted=false`, `production_admitted=false`. Original component errors remain unchanged. Eight bounded source-backed live original images exact; production54 historical9/54. Full AS ownership and general affine/coverage remain open. Draft only; no merge/deploy/Worker.
