# r213 — independent YCbCr contribution order clears unsubsampled controls

The diagnostic C helper asks libjpeg for JCS_YCbCr bytes with accurate integer IDCT and no fancy upsampling, bypassing RGB conversion. The independently captured native RGB is never used as helper input. Six unsubsampled32×32 controls retain every decoded component byte.

One shared sequence clears **6144/6144 RGB pixels**: R=Y+floor(1.402Cr), G=Y−floor(.344136Cb)−floor(.714136Cr), B=Y+floor(1.772Cb), with centered Cb/Cr and final byte clamping. These fixed conversion coefficients are not fitted to samples. Truncating contributions clears616/6144; floor-total38/6144; nearest-total77/6144. There is no RGB-dependent path. This is bounded evidence for the controls, not a universal decoder admission.

[Full comparisons](summary.json.gz), [decoded component bytes](planes/), [acceptance](acceptance.json).

```sh
cc -Wall -Wextra -Werror tools/probes/jpeg_ycbcr_dump.c -I/path/to/libjpeg/include -L/path/to/libjpeg/lib -ljpeg -o /tmp/jpeg-ycbcr
python3 -m tools.probes.analyze_jpeg_color_sequences --native evidence/importer-loud-fail/r212/native --dump /tmp/jpeg-ycbcr --output /tmp/jpeg-colors
```

Next discriminator: retain this color sequence and compare geometric chroma interpolation on4:2:0 controls. Derive component lattice from sampling factors, compare corner-aligned versus centered coordinates with fixed interpolation rounding, then reject any common construction against the original70308 JPEG3 pixels. Never choose geometry/rounding from RGB. Keep grayscale and unsubsampled controls exact. Production remains false; full component/AS gates remain open. Draft only.
