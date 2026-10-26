# r149 — header-only intervention restores valid indexed native input

Only bitmap7's tag header changes from2-byte short to6-byte explicit long. The55-byte payload is identical and **647 other tags are byte-identical**. Native `loadBitmap` now reports35×65/transparent=true and **2275/2275 decoded pixels match** the declared/AS source. The prior invalid r148 control remains unchanged as a negative test.

Display pixels are **1152/1152 identical before/after** native source materialization. Indexed and AS scalar outputs match576/576 in each epoch. The unchanged eight-bit coordinate/byte-weight construction independently matches **indexed1152/1152 and AS1152/1152**. The prior all-transparent result was a probe-encoding failure, not evidence for alpha interpolation.

A dedicated `native_lossless_tag.lossless2_tag` encoder emits explicit long headers even for short payloads; historical invalid-control builders remain reproducible and are not silently rewritten. Header/locked-source regression tests preserve payloads and prevent source mutation. This does not change production assets or the original Lanran format3 reference.

[Summary/intervention proof](summary.json), [native metadata](native/build.json), [provenance](provenance.json), [acceptance](acceptance.json).

```sh
python3 -m tools.probes.build_indexed_long_header --output /tmp/indexed-long --ffdec /path/to/ffdec-cli.jar
python3 tools/probes/capture_native_player.py /tmp/indexed-long/components/lanran /tmp/indexed-long/components/lanran/native.log --player-app '/path/to/Flash Player.app' --allow-window-activation --timeout 90
python3 -m tools.probes.analyze_indexed_header_control --native evidence/importer-loud-fail/r149/native --output /tmp/indexed-long.json
python3 -m unittest tools.tests.test_indexed_header_control
```

Next discriminator: continuous clips of lengths1/3/4/5/7/8/9/12/16/32 with independent start/transform changes. Retain direct native indexed source verification and before/after materialization controls. Compare the admitted positive-axis span route and fixed alternate bulk orders globally; original indexed component differences remain unresolved until one construction clears independent spans and original references together.

`native_indexed_source_verified=true`, `indexed_continuous_sampler_admitted=false`, `production_admitted=false`. Eight source-backed live original images exact; production54 historical9/54. Original Lanran still fails r142. Full AS ownership and general affine/coverage remain open. Draft only; no merge/deploy/Worker.
