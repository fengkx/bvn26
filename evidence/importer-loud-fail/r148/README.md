# r148 — direct native readback rejects the synthetic indexed bitmap

The unchanged r147 bitmap payload is exported as `indexedSource`. Native display controls run before `BitmapData.loadBitmap` and repeat afterward. AS input readbacks remain2275/2275 exact, but native loaded bitmap properties are **width−1,height−1,transparent−1**. The analyzer explicitly marks this an invalid bitmap and does not interpret its pixel-return values as source RGBA.

Display samples are **1152/1152 identical before/after** materialization, including all576 transparent indexed outputs. Thus the r147 outputs are not evidence for a sampling precision or alpha formula. The invalid native source gate stays closed.

The small binary-alpha bitmap payload is55 bytes and the generic tag encoder emitted a2-byte short header. Successful original/opaque controls had larger payloads with6-byte long headers. This is a hypothesis to isolate, not yet a confirmed cause in this round.

[Summary](summary.json), [native export/payload metadata](native/build.json), [provenance](provenance.json), [acceptance](acceptance.json).

```sh
python3 -m tools.probes.build_indexed_bitmap_readback --output /tmp/indexed-readback --ffdec /path/to/ffdec-cli.jar
python3 tools/probes/capture_native_player.py /tmp/indexed-readback/components/lanran /tmp/indexed-readback/components/lanran/native.log --player-app '/path/to/Flash Player.app' --allow-window-activation --timeout 90
python3 -m tools.probes.analyze_indexed_bitmap_readback --native evidence/importer-loud-fail/r148/native --output /tmp/indexed-readback.json
python3 -m unittest tools.tests.test_indexed_bitmap_readback
```

Next discriminator: change **only the bitmap tag header** from short to explicit long in a new scratch control, leaving its payload and every other tag unchanged. Require valid native dimensions and exact native texel readback before revisiting any arithmetic. Preserve the invalid control as a negative test; never rewrite its output as if it had been valid.

`native_indexed_source_verified=false`, `indexed_sampler_admitted=false`, `production_admitted=false`. Original source/production assets unchanged. Eight source-backed live original images exact; production54 historical9/54. Full AS ownership and general affine/coverage remain open. Draft only; no merge/deploy/Worker.
