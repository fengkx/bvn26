# r196 — separate cache snapshots do not establish pointwise filter inputs

Original identity-state cache/authored observations contain21 distinct cached RGBA values but29 input/output pairs. **Eight cached values each correspond to two native outputs**, with full coordinates retained. All ambiguous inputs are opaque. No function of those readback bytes alone can reproduce both outputs.

Twenty globally fixed diagnostic constructions(coefficient float32 or fixed8/16 trunc/even, straight/premultiplied algebra, floor/nearest final conversion) all reject; best is477047/480000, the same2953-pixel gap. The float32 label describes coefficient storage; dot arithmetic in this rejection experiment uses Python real-precision floats, not a claimed native instruction sequence. No coefficient or path is selected from a matching pixel.

Crucially, the cache snapshot is observed with filters removed; it is **not an explicit readback of the internal source actually consumed by the native filter**. Therefore this finding does not yet prove row-dependent arithmetic, SIMD, or a particular cache mismatch. r195 local input matches that snapshot exactly, but cannot alone certify the filtered native path's intermediate input. Both possibilities stay open.

[Counts/counterexamples](summary.json), [all ambiguous coordinates](locations.json.gz), [provenance](provenance.json), [acceptance](acceptance.json).

```sh
python3 -m tools.probes.analyze_matrix_input_pairs --output /tmp/matrix-input-pairs.json
python3 -m unittest tools.tests.test_matrix_input_pairs
```

Next discriminator: explicitly copy the observed original cache bytes into a BitmapData, retain paired source readbacks, then apply the full authored ColorMatrix through applyFilter and through a materialized display clip. Compare each result with the original authored boundary and retain allocation/row-width differences; do not assume the two APIs or materializations are equivalent. Only then design row/byte arithmetic probes.

All admission flags remain false; no GPU/shader change. Main family remains10/12, identity2953 differing pixels,maxdelta1; production54 historical9/54. Full AS/clip-action ownership open. Draft only.
