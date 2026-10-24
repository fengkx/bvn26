# r60 — broad GPU byte-domain arithmetic is exact

The same diagnostic shader helper introduced in r59 clears **1,302,912/1,302,912 native channel controls**: old1,284,192 and signed18,720. These correspond to136,774 distinct consumed-input/target tuples. Signed alpha49/green25 and old upper-bound witnesses are included through the complete unchanged r48 dataset. No local coefficient, arithmetic path, reference or tolerance is selected from output RGB.

Inputs use consumed integer offsets and1/256 multipliers, uploaded as RGBAF without color conversion; opacity and the independently measured reciprocal table use RF. Every uploaded texture is read back byte-for-byte before rendering. The identical shared helper computes three replicated channels and alpha, and all four output channels must match. Duplicate native controls retain their original multiplicity. Padding pixels are explicitly outside the dataset, not failure exclusions.

## Reproduction and evidence

```sh
python3 -m tools.probes.run_native_cxform_controls \
  --godot /path/to/Godot --output /tmp/bvn-r60/render
python3 -m unittest tools.tests.test_native_cxform_gpu
```

[Comparison](render/comparison.json.gz), [source/native-control/readback hashes](render/provenance.json), [GPU log](render/godot.log), [acceptance](acceptance.json). Input binary files are stored losslessly gzipped. The complete native controls are regenerated from the unchanged prior captures, retaining explicit source readbacks and consumed operands. Tests reject a single-channel mutation and changed readback dimensions.

r59's actual FilterGroup72,576/72,576 gate and old failing fixtures remain pinned and are checked in the full Python suite. The shared shader was not edited after that graphical run. Its exact ordinary/nested composition, Yulong, leaf/Glow and sampler rendering regressions remain r59; no new runtime change or new Flash capture.

## Scope and next step

`production_admitted=false`. This validates broad arithmetic on this AppleM2/OpenGL backend, not all graphics backends or executed Flash ISA routing. General production binding, coverage/affine and component parity remain unproved; components are still historical9/54. Full AS/clip-action ownership is a separate merge blocker.

Next apply the now-exact shared arithmetic within a source-proven component diagnostic, preserving placement metadata, real PNG input, coverage and actual filter/composite nodes, then rerun pinned component images. Do not globally replace production CXFORM on the strength of these diagnostic gates. No merge/deploy/Worker.
