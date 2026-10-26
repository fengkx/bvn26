# r241 — complete source Jinye CPU binding, still rejected

This round binds all authored Jinye leaf placements to one existing, globally fixed rejected sampler. It does not admit a renderer, increase component coverage, or change production code. **Active complete images remain 0/3 exact; the empty tick20 image is 1/4 total.**

## Source and boundary obligations

- Source bitmap55 is decoded from the locked JPEG3 bytes using the unchanged r218/r220 decoder. All three plane hashes must match r220 before rendering. Native images are used only after source decoding for comparison.
- The r220 inventory is regenerated and compared completely: 231 timeline events, 21 frames and up to11 depths. Frame selection is `1 + tick % 21`, checked against pinned native clocks at ticks0/10/20/23. All authored fill65 matrices, ordered quad masks, child transforms and the outer placement are retained.
- The single sampling model is the existing r229 `scaled_child_then_draw_quarters/minimum/HV`, with no per-leaf selection or coefficient fitting. Its isolated leaf failures reproduce r229: shape56 uncached/cached each17 changed pixels (maximum215); shape57 uncached2 and cached19 (maximum1).
- Fractional mask coverage uses one explicitly unproved diagnostic rule: exact polygon-square area, floored onto256 coverage steps. Cache allocation uses a separately labeled geometric floor/ceil bound with one-pixel padding, then recomputes the same sampler after local-origin rebasing. Neither is claimed to implement native Flash cache allocation or coverage.
- r220 contains complete uncached/cache/authored/stage observations, not explicit local/input buffers. Local/input comparisons therefore remain **unmeasured**, rather than being synthesized from native final images. Retained `getBounds` values are observations, not allocation evidence.
- Ratio40, dormant-style semantics and stream metadata have not gained new consumption proofs. The gate requires sampler, coverage, allocation, ratio, stream and local/input proof independently; an otherwise matching image cannot bypass them.

All PNG artifacts contain **premultiplied RGBA buffer bytes** in ordinary PNG containers. They are useful for byte inspection; a viewer interpreting them as straight-alpha previews may display dark fringes. Native r220 comparisons use black-composited RGB plus raw alpha, the same premultiplied encoding.

## Measured complete images

Each boundary contains240,000 RGBA pixels. Counts below are changed pixels; maximum delta is over all four channels. Full residual coordinates are retained in [wrapper/report.json](wrapper/report.json).

| Tick / source frame | Depths | Uncached changed / max | Cache changed / max | Stage changed / max |
|---|---:|---:|---:|---:|
|0 /1|11|131 /228|131 /229|129 /99|
|10 /11|11|272 /255|272 /255|270 /126|
|20 /21|0|0 /0|0 /0|0 /0|
|23 /3|11|209 /255|213 /255|212 /118|

The cache candidate also fails the authored-image boundary by the same cache counts. Empty tick20 proves removal/frame selection only; it does not admit the active wrapper or fractional coverage. Candidate source cache PNGs and final images are retained under `wrapper/tick*/`.

## Independent arithmetic rejection checks

[source-unit-audit.json](source-unit-audit.json) verifies that the raw source fill coefficients agree exactly with the existing XML-to16.16 recovery. Converting draw coefficients to float32 is only a tested precision hypothesis: it changes the examined fixed source coordinates by at most one 1/65536 unit, and is not an admitted explanation for the large shape56 error.

[phase-constraints.json](phase-constraints.json) retains6,104,000 rejection constraints from all200 r233 cases /436,000 native samples. Of112 coefficient/axis groups,48 have a nonempty common-phase interval and64 are contradictory. These intervals are rejection constraints, never selected coefficients. Even the existing scaled-child family has four contradictory groups; for example shape56, scale1, uncached Y requires phase≥2387 and≤2386 from two retained witnesses. Thus an arbitrary common phase cannot repair those fixed coefficients globally. No rendering experiment or GPU advancement is authorized by interval feasibility.

[inverse-translation-order.json](inverse-translation-order.json) rejects two independently fixed inverse-translation operation orders before any rendering change. On436,000 retained nearest-cell samples, exact-inverse-then-quantize remains409,816 exact; quantized-coefficients-then-dot-then-round gives409,798; separately rounded products then summed gives409,802. Their common-phase row groups are respectively12/16,12/16 and13/16 feasible, so none clears all old constraints. This rules out treating inverse-translation rounding order alone as the shared fix; no interval endpoint or fitted phase is selected.

## Reproduction and acceptance

From the repository root, using the unchanged source-plane decoder built for r215:

```sh
python3 -m tools.probes.run_jinye_wrapper_cpu \
  --dump /tmp/bvn-r215/jpeg-planes --output /tmp/bvn-r241/wrapper
# Expected exit1: active images and independent admission obligations fail.
python3 -m tools.probes.audit_jinye_source_units \
  --output /tmp/bvn-r241/source-unit-audit.json
python3 -m tools.probes.analyze_jinye_phase_constraints \
  --output /tmp/bvn-r241/phase-constraints.json
python3 -m tools.probes.analyze_jinye_inverse_translation_order \
  --output /tmp/bvn-r241/inverse-translation-order.json
python3 -m unittest tools.tests.test_jinye_wrapper_cpu \
  tools.tests.test_jinye_source_unit_audit tools.tests.test_jinye_phase_constraints \
  tools.tests.test_jinye_inverse_translation_order
```

Tests:13 passed. [provenance.json](provenance.json) pins the diagnostic sources and decoder executable. Runtime/production assets are unchanged; full gameplay/build acceptance is not claimed as rerun by this diagnostic. `candidate_admitted=false`, `gpu_advance_allowed=false`, `production_admitted=false`; no component-inventory increment. AS/clip-action ownership and the other production admission obligations remain separate blockers.

## Next concrete discriminator

Concentrate on the actual shape56 / first authored placement, whose17 isolated source-pixel failures remain upstream of wrapper composition. Hold its original source bitmap55, fill65, quad, child transform, outer transform and camera fixed. Compare native direct compound drawing with an **explicitly materialized native intermediate** of that same child before the outer draw, retaining the intermediate bytes and exact allocation origin. This is an API/boundary discriminator, not an assumption that `cacheAsBitmap` materializes that buffer. First require the direct path to reproduce the pinned r221/r220 boundary. Then test the one globally fixed candidate at that independently observed intermediate before interpreting the complete image. Do not use native intermediate pixels as Godot/source textures, choose a phase from feasible intervals, or repair shape56 by a per-leaf route.
