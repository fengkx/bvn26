# r215 — coefficient-domain chroma clears controls; four original pixels remain

Scaled16×16 integer IDCT directly reconstructs each4:2:0 chroma block at output resolution. Original Y retains8×8 IDCT. Unsubsampled components retain8×8 throughout. Component dimensions/sampling factors/IDCT sizes are recorded by the helper; no resampling of decoded chroma bytes or RGB-selected routing occurs. r213 fixed color contribution arithmetic is unchanged.

All12 independent color controls clear **12288/12288 pixels**. Original Orochimaru JPEG3 improves37022→**70304/70308**; four pixels remain, max delta1:

| x,y | independently decoded Y,Cb,Cr | candidate RGB | native RGB |
|---|---|---|---|
|184,154|0,133,132|5,0,8|6,0,9|
|184,155|0,133,133|7,0,8|7,0,9|
|184,156|0,134,133|7,0,10|7,0,11|
|185,158|0,130,133|7,0,3|7,0,4|

Original alpha comes from the compressed source alpha stream, never from native expected output. No reference texture becomes an input asset. This bounded construction is still rejected; **production_admitted=false**. Four residuals cannot be dismissed by tolerance or edge patches.

[Measurements](summary.json), [component-plane bytes and helper logs](planes/), [acceptance](acceptance.json).

```sh
cc -Wall -Wextra -Werror tools/probes/jpeg_scaled_planes.c -I/path/to/libjpeg/include -L/path/to/libjpeg/lib -ljpeg -o /tmp/jpeg-planes
python3 -m tools.probes.analyze_jpeg_scaled_planes --dump /tmp/jpeg-planes --output /tmp/jpeg-scaled
```

Next discriminator: independently encode constant YCbCr controls around Y0/1/2 with the four residual chroma values and neighbors, plus high-luma controls; retain actual decoded component bytes. This separates low-luminance color treatment from partial-edge IDCT. Do not add a Y0 special case from these four outputs. If constants retain the existing rule, probe actual edge blocks and coefficient reconstruction independently. Original and all old controls remain rejection gates. Components36/54 diagnostic; production historical9/54; AS ownership open. Draft only.
