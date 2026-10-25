# r151 — original indexed Lanran cache and three complete images exact

The fixed indexed byte-weight rule from independent r150 controls now uses original locked bitmap tags7/9/11, their decoded raw texels, original fill metadata/contours, frame-selected placements, and unchanged cache allocation. The diagnostic verifies **format3** from the source tag before selecting the rule. Neither references nor production assets are converted.

At ticks0/8/11 (shapes8/12/8), each cache boundary, authored Blur output, and original pinned complete image is240000/240000 exact: **720000/720000 per layer, three complete images exact**. The previous bulk candidate's cache/channel errors disappear without per-fighter or output-selected arithmetic.

Tick4/frame5/shape10 still hard-rejects **Unproven fractional coverage** at eight nontransparent fringe footprints. The command deliberately exits1. No fallback image is supplied. `source_cpu_exact=false`, `gpu_binding_verified=false`, `production_admitted=false`.

[Summary and exact remaining sites](summary.json), [provenance](provenance.json), [acceptance](acceptance.json). Reuses immutable [r141 native boundaries](../r141/native/native.log.gz), [r142 authored source fixture](../r142/fixture.json), and original r21 complete images.

```sh
python3 -m tools.probes.analyze_indexed_component_cache --fixture evidence/importer-loud-fail/r142/fixture.json --native evidence/importer-loud-fail/r141/native --output /tmp/indexed-component
# Expected exit1: frame5 coverage remains unsupported.
python3 -m unittest tools.tests.test_indexed_component_cache
```

Next discriminator: spatially constant explicit byte sources under independently varied authored mask coordinates on the1/20 grid, retaining quarter-grid controls. This separates fractional coverage from sampling. Compare exact rational rectangle area globally before attempting varying-texture edges. Do not infer general coverage from the existing quarter-grid pass or enable production from these three CPU images.

Eight original live GPU images remain exact; these three CPU images are additional diagnostic evidence, not a production54 rerun. Production suite historical9/54; full AS ownership, remaining components, general affine/coverage are still open. Draft only; no merge/deploy/Worker.
