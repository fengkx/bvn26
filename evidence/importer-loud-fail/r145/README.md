# r145 — source encoding independently isolates indexed bitmap sampling

A new scratch-only native variant changes **only bitmap7's DefineBitsLossless2 format3 encoding to format5**. All2275 decoded premultiplied RGBA texels remain identical; **646 other tags are byte-identical**, including shape geometry, fill matrix, placement and observer scripts. Before/after SWF/tag hashes, decoded-byte hash and unchanged-tag hash are recorded. Locked source files reject writes and remain unchanged.

After this isolated intervention, native tag versus AS authored/clear/cache images each become **240000/240000 exact**. The unchanged CPU cache also becomes240000/240000 against the variant tag. Comparison with the **unchanged original format3 native reference** still differs at662 cache pixels (maxRGBAΔ3/3/3/2). Thus equivalent decoded texels do not imply equivalent Flash indexed/32-bit sampling. The original indexed path remains unimplemented; converting production assets to format5 would change Flash behavior and is not proposed.

[Summary and intervention proof](summary.json), [native build metadata](native/build.json), [provenance](provenance.json), [acceptance](acceptance.json). Original r141/r144 references are retained unchanged; the variant is a new experimental result, never a replacement reference.

```sh
python3 -m tools.probes.build_lossless_encoding_control --output /tmp/encoding-control --ffdec /path/to/ffdec-cli.jar
python3 tools/probes/capture_native_player.py /tmp/encoding-control/components/lanran /tmp/encoding-control/components/lanran/native.log --player-app '/path/to/Flash Player.app' --allow-window-activation --timeout 90
python3 -m tools.probes.analyze_lossless_encoding_control --native evidence/importer-loud-fail/r145/native --output /tmp/encoding-control-analysis
python3 -m unittest tools.tests.test_lossless_encoding_control
```

Next discriminator: native indexed-format synthetic ramp/four-corner controls with exactly matched decoded format5/AS inputs. Use single-pixel clips first to isolate fractional-coordinate/weight precision, retaining actual fill/child/draw property readbacks. Compare fixed independently defined weight precisions globally before testing original component counterexamples; only then explain continuous span routing. Never select a weight precision from the locally matching pixel.

`format5_variant_matches_as=true`, `original_indexed_sampling_admitted=false`, `production_admitted=false`. Original Lanran still rejects as r142 records. Eight source-backed live original images exact; production54 historical9/54. Full AS ownership, other visual paths and general affine/coverage remain open. Draft only; no merge/deploy/Worker.
