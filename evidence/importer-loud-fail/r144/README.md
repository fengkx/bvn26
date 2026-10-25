# r144 — identical source bytes distinguish SWF-tag and AS bitmap fill construction

The original Lanran wrapper/shape tags remain in the native probe. A separate AS drawing uses the exact original bitmap7 bytes, complete shape8 rectangle, fill matrix and copied child/draw/filter properties. All **2275/2275 source readback pixels** match the pinned decoded source. Local bounds and matrices match. The static AS-created clip reports frame0 while the original timeline reports frame1; both values are retained, not normalized or treated as timeline equivalence.

Original SWF-tag authored/clear/cache images each match the prior r141 native boundaries **240000/240000**. AS versus original tag differs: clear/cache **239338/240000** (maxRGBAΔ3/3/3/2), authored **239450/240000** (maxΔ1). Crucially, the unchanged r142 CPU cache is **240000/240000 exact against AS**, but still239338/240000 against the original tag. Thus the scalar AS controls cannot establish original SWF-tag sampling equivalence.

The source bitmap tag is DefineBitsLossless2 format3 (indexed palette), whereas AS BitmapData materializes a32-bit image. This is a discriminating hypothesis, not yet the proven cause. Original source, references and production assets remain unchanged.

[Summary](summary.json), [native bytes/images](images/), [provenance](provenance.json), [acceptance](acceptance.json).

```sh
python3 -m tools.probes.build_component_fill_api --output /tmp/component-fill-api --ffdec /path/to/ffdec-cli.jar
python3 tools/probes/capture_native_player.py /tmp/component-fill-api/components/lanran /tmp/component-fill-api/components/lanran/native.log --player-app '/path/to/Flash Player.app' --allow-window-activation --timeout 90
python3 -m tools.probes.analyze_component_fill_api --native evidence/importer-loud-fail/r144/native --output /tmp/component-fill-api-analysis
python3 -m unittest tools.tests.test_component_fill_api
```

Next discriminator: in a new scratch-only variant, replace **only** bitmap7's lossless format3 encoding with format5 containing the exact same decoded premultiplied RGBA bytes. Retain all shape/fill/placement/script tags byte-for-byte and prove that invariant. Compare the new native tag path to AS and the unchanged original references; never replace the original reference with the variant. This distinguishes source encoding/internal representation from fill-matrix geometry consumption.

`api_equivalence_verified=false`, `production_admitted=false`. Original Lanran input remains rejected; no source/reference rewriting or production admission. Eight source-backed live original images exact; production54 historical9/54. Full AS ownership and general affine/coverage remain open. Draft only; no merge/deploy/Worker.
