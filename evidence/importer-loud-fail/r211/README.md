# r211 — six global JPEG constructions rejected

The original JPEG has4:2:0 component sampling (Y2×2,Cb/Cr1×1). All six documented libjpeg-turbo3.1.4.1 whole-image combinations remain inexact against unchanged r210 native bytes:

| IDCT | Fancy upsample exact/70308 | Simple upsample exact/70308 | Max RGB fancy/simple |
|---|---:|---:|---:|
| Integer |37022|36830|19/14|
| Fast integer |36118|35999|21/15|
| Float |37015|36829|19/14|

The source includes table/image EOI/SOI separation at byte572. Standalone djpeg correctly rejects the first table-only stream. The diagnostic removes only this four-byte pre-image seam after checking it precedes SOF/SOS; all entropy/table bytes remain unchanged. Pillow RGB bytes before/after this container normalization are identical. The native probe continues loading the untouched original SWF tag. No decode mode is chosen from individual output pixels.

[Commands, decoder executable/version and byte hashes](decoder/summary.json); each mode's complete coordinate differences and verbose JPEG metadata are retained alongside it. No production changes; complete diagnostics remain36/54, production historical9/54; production_admitted=false.

```sh
python3 -m tools.probes.compare_jpeg_decoder_modes --native evidence/importer-loud-fail/r210/native --djpeg /path/to/djpeg --output /tmp/jpeg-modes
```

Next discriminator: independently encoded grayscale, constant-color, and chroma-boundary controls with explicit native decoded bytes. Hold each encoded JPEG fixed across all decoder modes; compare grayscale first (no chroma), constant blocks (no AC variation), then chroma boundaries with/without subsampling. This separates IDCT, color conversion and interpolation without changing the original reference or selecting a per-pixel route. No candidate may enter component rendering until original bytes and controls are exact. AS ownership still open. Draft only; no merge/deploy/Worker.
