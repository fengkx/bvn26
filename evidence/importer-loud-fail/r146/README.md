# r146 — opaque indexed ramps retain eight-bit scalar weights

Independent synthetic source texels repeat8×8 horizontal-red/vertical-green ramps with constant blue73 and alpha255. The source is encoded as native format3 and separately materialized through AS; all2275 explicit source readbacks match. Original shape8 geometry/fill matrix is retained. Single-pixel clips cross scales1/1.25/3/5, independent quarter draw translations and source-relative positions. The original child is explicitly stopped at frame1 solely for this sampling control; AS-created frame0 is retained.

| Fixed fractional-weight precision | Indexed exact | AS exact |
|---|---:|---:|
|4 bits|335/576|335/576|
|5 bits|466/576|466/576|
|6 bits|552/576|552/576|
|8 bits|576/576|576/576|

The same independently defined initializer and global scalar byte-weight construction clear both **opaque** paths. Lower precision alone does not explain the original Lanran indexed-source counterexamples. No precision is selected from a locally matching pixel, and this all-opaque result does not admit the mixed-alpha indexed path.

[Summary with complete properties/native samples/counterexamples](summary.json), [provenance](provenance.json), [acceptance](acceptance.json).

```sh
python3 -m tools.probes.build_indexed_bitmap_scalar --output /tmp/indexed-scalar --ffdec /path/to/ffdec-cli.jar
python3 tools/probes/capture_native_player.py /tmp/indexed-scalar/components/lanran /tmp/indexed-scalar/components/lanran/native.log --player-app '/path/to/Flash Player.app' --allow-window-activation --timeout 90
python3 -m tools.probes.analyze_indexed_bitmap_scalar --native evidence/importer-loud-fail/r146/native --output /tmp/indexed-scalar.json
python3 -m unittest tools.tests.test_indexed_bitmap_scalar
```

Next discriminator: hold the geometry/transform/single-pixel grid fixed and replace only source texels with independently read binary-alpha four-corner impulses. Compare indexed/AS RGBA and retained fixed constructions globally; separate alpha/weight arithmetic from coordinate precision before any span experiment. Keep these opaque controls and original r144/r145 boundaries as strict rejection gates.

`indexed_sampler_admitted=false`, `production_admitted=false`. Original component errors unchanged. Eight source-backed live original images exact; production54 historical9/54. Full AS ownership and general coverage/affine remain open. Draft only; no merge/deploy/Worker.
