# r157 — native ColorMatrix animation boundaries retain outer semantics

Fresh explicit authored/clear/cache/stage captures preserve original animation clocks, empty frames, restoration, all20 ColorMatrix property coefficients and effective transform/bounds. Native direct gray-stage images match **8/8 pinned images,1920000/1920000 pixels** across main and Yijiao. These are native boundary consistency checks, not runtime parity claims.

Yijiao's identity ColorMatrix leaves its materialized cache exact960000/960000. Cache versus uncached input differs367 pixels at tick0 and404 at tick52 (max channel delta2). Main's cache versus authored result differs4 pixels at tick0 (max1), while cache versus uncached input differs4/2 pixels with alpha delta255. Original main has arbitrary affine plus post-filter fixed RGB CXFORM; Yijiao has arbitrary affine, outer scale and blendMode5. Those fields remain in the cases and cannot be dropped.

The initial ordinary-over-gray reconstruction was invalid for Yijiao's blendMode5:43956/41058 differing pixels. A direct native gray-stage capture, retaining actual display composition, matches each original reference exactly. The invalid normal-composition comparison remains measured as a negative control; no fitted blend formula is admitted.

[Main measurements](main-summary.json), [Yijiao measurements](yijiao-summary.json), [provenance](provenance.json), [acceptance](acceptance.json). Full native readbacks are compressed under each source folder.

```sh
python3 -m tools.probes.build_matrix_component_boundaries --cases evidence/importer-loud-fail/r32/components/main/cases.json --case main-298-1-1 --output /tmp/matrix-main --ffdec /path/to/ffdec-cli.jar
python3 tools/probes/capture_native_player.py /tmp/matrix-main/components/main /tmp/matrix-main/components/main/native.log --player-app '/path/to/Flash Player.app' --allow-window-activation --timeout 90
python3 -m tools.probes.analyze_matrix_component_boundaries --native evidence/importer-loud-fail/r157/main --output /tmp/matrix-main.json
python3 -m unittest tools.tests.test_matrix_component_boundaries
```

Next discriminator: independent nearest affine input controls for main's fill67, using explicit coordinate-coded source bytes and transform readbacks. Isolate fully covered interior pixels geometrically before claiming polygon-edge coverage. Compare common exact/fixed inverse initializers, never choose from the observed RGB. Yijiao's smooth affine/outer-scale input and blend composition remain separate gates.

`source_sampler_admitted=false`, `production_admitted=false`. Diagnostics still cover24 original live/wrapper images; production54 historical9/54. Full AS ownership remains open. Draft only; no merge/deploy/Worker.
