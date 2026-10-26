# r87 — independent PNG draw boundaries preserve the same candidate bytes

A new64×64 PNG varies all RGB channels and alpha across both axes using fixed authored integer formulas. Every original decoded byte is verified4096/4096. The unchanged r86 candidate (opaque identity, partial-alpha integer product/256) predicts all four paths **4096/4096 each**:

- Loaded display object → transparent BitmapData → paired black readback.
- Loaded display object → direct opaque black BitmapData.
- Loaded display object →4096 separate single-pixel clip draws into transparent BitmapData.
- First materialized transparent BitmapData → second transparent BitmapData.

Direct-black RGB, single-pixel clips and redraw bytes all agree with the first materialization4096/4096. This rejects explanations that require the second black readback, an additional BitmapData draw or long-row-only behavior for these integer identity samples. It does **not** prove the internal decoder instruction sequence, fractional sampling, or SWF embedded bitmap behavior. The old r86 all-byte controls remain unchanged and strict.

## Reproduce

```sh
python3 tools/probes/build_png_draw_paths_probe.py --output /tmp/bvn-r87/native --ffdec /path/to/ffdec-cli.jar
python3 tools/probes/capture_native_player.py /tmp/bvn-r87/native /tmp/bvn-r87/native/native.log --player-app '/path/to/Flash Player.app' --allow-window-activation --timeout 45
python3 -m tools.probes.analyze_png_draw_paths --native evidence/importer-loud-fail/r87/native --output /tmp/bvn-r87/recheck.json
python3 -m unittest tools.tests.test_png_draw_paths tools.tests.test_png_decode
```

[Comparisons](analysis.json), exact `native/game/probe.png`, [source/readback hashes](provenance.json), [acceptance](acceptance.json). Source geometry, loaded dimensions/scales/opacity and all intermediate RGBA are retained. No references rewritten, no tolerance or output-selected arithmetic.

Next inspect **actual shipped DefineBitsLossless2 premultiplied bytes versus exported PNGs** for the failing54-component sources. Inventory which original texels survive each globally defined PNG/upload construction; keep raw source hashes and exact bitmap IDs. External PNG and embedded SWF bitmap paths must not be conflated. If an export loses recoverable premultiplied bytes, preserve those bytes in a diagnostic asset path and validate against native source components before changing production.

`bounded_external_png_passed=true`, `internal_decoder_attribution_proven=false`, `production_admitted=false`. No GPU/production change. Components historical9/54; general SWF/PNG export relationship, coverage/affine/implicit buffers and full AS/clip-action ownership remain open. Full roster/Web and54 components not rerun. Draft only; no merge/deploy/Worker.
