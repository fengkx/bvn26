# r132 — source-owned Yulong fill graph retained

The full source table has two slots. Slot1 (bitmap65535) owns **zero** directed edges; slot2 (bitmap148,34×3) owns all **four** edges. Both slots, original style-change records and wrapper XML are retained. This is edge ownership evidence, not a harmless-behavior allowlist.

The active fill matrix is `(a,b,c,d,tx,ty)=(0,1,-1,0,3,0)` after converting source twips. Its transformed bitmap corners exactly match the authored3×34 contour. `rotateSkew0/1` are not transposed. Source/raw-tag/texel hashes are pinned. The existing positive-axis/single-fill extractor correctly rejects this graph; its guard is unchanged.

## Reproduce

```sh
python3 -m tools.probes.inspect_component_fill_graph --cases evidence/importer-loud-fail/r21/components/yulong/cases.json --case yulong-345-753-29 --output /tmp/yulong-fill-graph --ffdec /path/to/ffdec-cli.jar
python3 -m unittest tools.tests.test_component_fill_graph
```

[Summary](summary.json), [source shape](shape.xml), [source wrapper](wrapper.xml), [provenance](provenance.json), [acceptance](acceptance.json).

Next discriminator: independently compare quarter-turn bitmap fill matrices against byte-preserving texel permutations, retaining transparent source readbacks and varying scale, fractional translation and cache state. A geometric equivalence alone does not prove identical sampling arithmetic. No source-derived pixel binding or production admission follows from this inspection.

`source_derived_input_verified=false`, `production_admitted=false`. Six bounded live Blur images exact; historical production54 suite9/54 not rerun. Arbitrary affine/coverage, remaining components and full AS/clip-action ownership remain open. Draft only; no merge/deploy/Worker.
