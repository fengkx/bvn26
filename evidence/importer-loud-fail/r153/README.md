# r153 — all four original Lanran CPU component images exact

Combine the independently measured indexed byte-weight sampler (r150) with non-tie quarter-rounded authored geometry (r152). Original format3 tags, raw texels, full source fixture/contours, timeline-selected frames, cache allocation and pinned native images remain unchanged.

All four ticks0/4/8/11 now match **960000/960000 pixels at each boundary**: source cache, authored Blur output and original complete image. Frame5's eight fringe footprints are resolved by the shared geometry rule, not special coordinates or a tolerance.

The new diagnostic explicitly rejects non-unit scale, non-quarter translation and coverage midpoint ties. It verifies indexed source storage before routing. Previous r142/r151 rejection controls are retained unchanged. `source_cpu_exact=true`, `gpu_binding_verified=false`, `production_admitted=false`.

[Summary](summary.json), [provenance](provenance.json), [acceptance](acceptance.json).

```sh
python3 -m tools.probes.analyze_indexed_twip_component --fixture evidence/importer-loud-fail/r142/fixture.json --native evidence/importer-loud-fail/r141/native --output /tmp/indexed-twip-component
python3 -m unittest tools.tests.test_indexed_twip_component
```

Next discriminator: feed original raw texels, retained fills/masks, geometry-derived coordinates/coverage into the live GPU sampler. Use actual FilterGroup allocation/padding and integer Blur/normal composition; compare all four same native cache/filter/final images. Never upload pre-rendered CPU or native input images as the rendered source.

Eight other original live GPU images remain exact; these four CPU images do not change production54 historical9/54. Full AS ownership, general affine/coverage and remaining components are open. Draft only; no merge/deploy/Worker.
