# r214 — byte-plane bilinear chroma hypotheses rejected

The r213 fixed contribution-floor color conversion remains unchanged. Six4:2:0 controls compare whole-image corner-aligned and centered chroma coordinates, each with floor, nearest or unrounded bilinear weights. Component lattice bytes are independently decoded with integer IDCT; repeated2×2 values are explicitly asserted before extracting the lattice. All candidates fail nonconstant controls; constant controls remain exact. No geometry is selected from output RGB.

A sharper discriminator appears in quality100 chroma-edge case11: decoded Y/Cb/Cr at x10..13 are all[97,119,225], but native RGB is[228,33,82],[238,29,79],[244,27,79],[210,43,84]. Local bilinear interpolation of constant component bytes cannot produce this ringing. This does not prove an internal implementation; it rejects the tested byte-plane reconstruction family.

[All per-coordinate candidates](summary.json.gz), [component bytes](planes/), [acceptance](acceptance.json).

```sh
python3 -m tools.probes.analyze_jpeg_chroma_lattice --native evidence/importer-loud-fail/r212/native --dump /tmp/jpeg-ycbcr --output /tmp/jpeg-chroma
```

Next discriminator: independently reconstruct chroma at twice its decoded resolution directly from JPEG coefficients (scaled16×16 IDCT), retaining the original full-resolution Y and r213 conversion. Compare all controls and original JPEG3 before any admission. Do not infer a codec/SIMD path from RGB agreement alone. No per-pixel correction or production change. Components36/54 diagnostic,9/54 historical production; AS ownership still open. Draft only.
