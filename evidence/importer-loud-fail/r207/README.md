# r207 — packed matrix GPU arithmetic exact before live binding

**401784/401784 native RGBA samples exact**, maxdelta0, through the diagnostic integer shader. All explicit rows from r198–r205, both r197 materialized input images and the retained r206 scalar/ramp samples pass. The geometry selects paired-prefix versus remainder arithmetic; no output RGB selects a route.

The GPU receives only explicit input RGBA bytes and source-derived packed matrix coefficients. Native output bytes are comparator inputs only. The fixture is batched into1024-row textures; original processed widths are separate metadata, so padding cannot silently change the span partition. CPU guards reject unsupported alpha rows/ranges before upload. The24 scalar and2048 ramp samples check only their captured offset, with repeated input context supplying the independently established span mode; no uncaptured pixels are claimed exact.

[runtime report](gpu/report.json), [engine log](gpu/godot.log), [source and input/readback hashes](gpu/provenance.json), [acceptance](acceptance.json). Large source/word scratch textures are deterministically regenerated, not committed. Every output PNG is retained.

```sh
python3 -m tools.probes.run_packed_matrix_rows --godot /path/to/Godot --output /tmp/matrix-packed-gpu
python3 -m unittest tools.tests.test_packed_matrix_rows
```

Next discriminator: bind this same include at the actual diagnostic FilterGroup ColorMatrix pass, preserving production allocation, live source texture, authored matrix, post-CXFORM and normal composition. Rerender the12 main owner-state images against unchanged pinned native images. Do not enable production based on standalone rows. Main family remains10/12 until rerendered; production54 historical9/54. Production admission false; AS ownership still open. Draft only.
