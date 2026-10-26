# r75 — grouped multi-pass blur is exact through actual GPU buffer nodes

All1296 pinned r73 native controls now run through real production-created FilterGroup/Contents/FilterPass nodes. The diagnostic retains production buffer allocation and kernel clamps, changes blur operands through the common consumption construction, uses the unchanged r74 integer shader, and explicitly reconnects all horizontal passes before vertical passes.

| GPU/native stage | Exact RGBA samples |
|---|---:|
| Input buffer | **165888/165888** |
| Filtered output | **165888/165888** |
| Final raw byte copy | **165888/165888** |

Twenty-seven batches validate actual buffer size/origin, texture dependency chains, axis order and consumed operands. The full64×64 source bitmap bounds are preserved, including its transparent margins. Input images are constructed as explicit premultiplied RGBA8 bytes and uploaded with byte readback checks; the actual input buffer is independently compared against native paired transparent/black rows. The shared center is counted in both sampled lines, as in r73.

The final stage deliberately uses a `blend_disabled` byte-copy shader to match explicit native BitmapData output. It is **not** evidence for ordinary production composition, PNG decoding, arbitrary coverage or affine placement. Those separate boundaries must retain their own gates. No production code, native reference, tolerance or epsilon changed.

The original production-created pass nodes are reused; the diagnostic rewires their inputs and child order rather than supplying precomputed filtered images. Existing production remains alternating and therefore still has the r73 multi-pass mismatch until a justified production change is made. `production_admitted=false`.

## Reproduce

```sh
python3 -m tools.probes.run_grouped_blur_gpu --godot /path/to/Godot \
  --output /tmp/bvn-r75/render
python3 -m unittest tools.tests.test_grouped_blur_gpu
```

[Exact native comparison](render/comparison.json), [GPU rows/order/operands](render/rows.json.gz), [source and native hashes, commands](render/provenance.json), [acceptance](acceptance.json). Native r73 source and readbacks are unchanged; no new Flash capture. All27 fixtures/logs are under `render/batches/`.

Next capture independent multi-pass Glow/DropShadow controls before extending this BlurFilter order to those families. Then define and justify any production eligibility from source metadata and complete pixel gates; a diagnostic pass alone does not enable production. Preserve the r74 single-pass extent gate and older exact composition/sampler controls.

Fresh Python checks include pinned r71/r72/r73 CPU controls and r74 GPU readbacks. The unchanged old graphical gates were last rerun in r74, not re-rendered this round. Full roster/Web export and54 components were not rerun because production is unchanged. Components remain historical9/54; full AS/clip-action ownership and general production rendering eligibility remain merge blockers. Draft only; no merge/deploy/Worker.
