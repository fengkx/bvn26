# r209 — source-backed component coverage and original JPEG3 blocker

The case/tick inventory rechecks locked SWF hashes, pinned native hashes and actual RGBA bytes: **36/54 original images have exact source-backed complete diagnostics**. Remaining unbound images: Jinye4, Orochimaru10, Yijiao ColorMatrix4. This is not a fresh production render; historical production remains9/54 and `production_admitted=false`.

Orochimaru's five placements share wrapper342/shape341/bitmap340. The original bitmap is DefineBitsJPEG3 (tag35),186×378, with13265 JPEG bytes and70308 alpha bytes (30941 zero,39367 opaque). The authored clipped-unsmoothed fill, shape bounds, wrapper placement, all five outer transforms and Blur20 parameters are retained in [source inventory](orochimaru.json). The lossless-only binding correctly rejects the exact source site; no decoder or placement is silently substituted. The bounded XML preserves wrapper and shape metadata; raw tags are verified directly against locked SWF hashes.

[Complete image inventory](inventory.json), [acceptance](acceptance.json). Fresh full Python:965 tests,963 passed,2 skipped; focused inventory tests additionally cover newly added work. Production/runtime/import data unchanged; roster/Web and global production54 not rerun.

```sh
python3 -m tools.probes.inventory_component_diagnostics --output /tmp/component-inventory.json
python3 -m tools.probes.inventory_orochimaru_bitmap --xml evidence/importer-loud-fail/r209/orochimaru-bounded.xml --output /tmp/orochimaru-inventory.json
python3 -m unittest tools.tests.test_component_diagnostic_inventory
```

Next discriminator: load the unchanged original bitmap340 JPEG3 tag through native Flash BitmapData.loadBitmap, retain explicit full byte readbacks, then compare candidate JPEG decoding before touching sampling/filter math. Alpha is binary, so premultiplication cannot explain opaque RGB differences. Keep source/native pixels separate from diagnostic input generation; native bytes must never become replacement assets. AS/clip-action ownership, remaining component coverage and production admission still block merge. Draft only; no merge/deploy/Worker.
