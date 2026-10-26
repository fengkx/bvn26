# r197 — explicit materialization retains the native ColorMatrix ambiguity

Copy the original identity-state cache bytes into an explicit223×244 BitmapData. Paired readbacks prove the copy **108824/108824 RGBA exact** across active ticks0/8. Fresh cache/authored full images remain480000/480000 exact against r195, with clocks, source matrix, filter properties and restoration preserved.

Apply the full authored ColorMatrix to these known bytes using applyFilter. Separately attach the same BitmapData to a display clip and apply its filters. Each matches the original authored crop **108824/108824 exact**; the two APIs agree on every measured pixel. Their internal allocation is not assumed identical: the display clip's local bounds223×244 are retained, but its implicit cache may include additional border storage.

The same8 input values still map to two outputs in both materialized paths. This rules out the separate-cache-snapshot ambiguity for these measured bytes and confirms that a pointwise formula of source RGBA alone is insufficient here. It does not identify SIMD, neighborhood logic or an operation order.

[Exact comparisons/input-output groups](summary.json), [explicit source/native rows](native/native.log.gz), [provenance](provenance.json), [acceptance](acceptance.json).

```sh
python3 -m tools.probes.build_materialized_matrix_owner --output /tmp/materialized-matrix-owner --ffdec /path/to/ffdec-cli.jar
python3 tools/probes/capture_native_player.py /tmp/materialized-matrix-owner/frame3/components/main /tmp/materialized-matrix-owner/frame3/components/main/native.log --player-app '/path/to/Flash Player.app' --allow-window-activation --timeout 90
python3 -m tools.probes.analyze_materialized_matrix_owner --native evidence/importer-loud-fail/r197/native --output /tmp/materialized-matrix-owner.json
python3 -m unittest tools.tests.test_materialized_matrix_owner
```

Next discriminator: hold a target's verified opaque source bytes and full matrix fixed, vary only neighboring alpha within independently positioned four-pixel groups, and vary row width/group start. Retain all input readbacks and all output lanes. Determine whether neighboring alpha or row geometry changes target RGB before any arithmetic/partition implementation; no output-selected route.

`candidate_admitted=false`, `production_admitted=false`. Main family10/12, identity2953 pixels,maxdelta1; production54 historical9/54. No shader/production changes. Full AS ownership open. Draft only.
