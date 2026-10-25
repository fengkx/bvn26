# r204 — independently pinned packed arithmetic clears materialized matrix buffers

**554400/554400 RGBA pixels exact**, no channel tolerance: all r198–r203 rows, and both r197 original materialized images through applyFilter and display. This clears the previously ambiguous native input/output pairs with one construction selected by processed geometry and input alpha, never output RGB. It is CPU evidence only; the live GPU family remains10/12 until rerun with a diagnostic implementation. Production54 historical9/54; production admission false.

## Independent construction

Read-only inspection of the pinned Flash Player Debugger32 executable identifies matrix preparation at0x100016830 and packed row arithmetic at0x100017c5c. [Static evidence](static-binary.json) pins binary SHA, constants and instruction spans. This is **not verified runtime invocation**; no hardware execution route is inferred solely from matching pixels.

- Coefficients: float32 ×2048 then nearest-even integer conversion; offsets: float32 ×4 then nearest-even conversion plus2.
- Whole four-pixel processed prefix uses adjacent pairs. Both opaque: source byte shifted7. Otherwise integer reciprocal table `65280//alpha` (zero entry0), per-color product plus127 then logical shift1; alpha uses multiplier256. The127 and shift produce63/128 for an opaque target sharing a transparent pair, not an invented epsilon or exactly half a byte.
- Each signed coefficient/input product takes its high16 bits **before** summing; add the prepared offset and arithmetic shift2, clamp0–255.
- Remainder first converts premultiplied color using the integer table and127, shift8; then shift7. Its initialization differs from the paired path.
- Output premultiplication uses `(product + (product>>8) + 1)>>8`, a floor conversion. Nearest premultiplication left five original-buffer counterexamples and is rejected by the independently read constant1.

The diagnostic rejects nonidentity alpha rows, unreviewed coefficient ranges, unknown modes and invalid premultiplied bytes. General alpha-changing filters, saturation/overflow boundaries and runtime dispatch are not admitted. No production code or references changed.

| Native comparison | Exact RGBA pixels |
|---|---:|
| r200 nonbinary coefficient rows |18432/18432|
| r201 binary coefficient rows |18432/18432|
| r202 coefficient brackets |55296/55296|
| r203 offset brackets |19440/19440|
| r198 neighbor-alpha rows |114560/114560|
| r199 independently shifted spans |110592/110592|
| r197 two materialized sources ×two native APIs |217648/217648|

[All comparisons](summary.json), [provenance](provenance.json), [acceptance](acceptance.json).

```sh
python3 -m tools.probes.extract_matrix_binary_constants --binary '/path/to/Flash Player Debugger' --output /tmp/matrix-static.json
python3 -m tools.probes.analyze_matrix_packed_candidate --output /tmp/matrix-packed.json
python3 -m unittest tools.tests.test_matrix_packed_candidate
```

Next discriminator: independently sweep all source alphas with explicit byte readbacks across both paired and remainder spans, keeping the authored full matrix. Retain early r11/r12 vector scalar/ramp outputs and capture unfiltered inputs without changing their geometry or filtering API. Reject against all retained materialized buffers and earlier controls before GPU advancement. Then implement the same bounded arithmetic in the diagnostic FilterGroup, preserving original sources, allocation and post-CXFORM, and rerun the complete family. Full AS ownership remains a separate merge blocker. Draft only.
