# r59 — exact actual FilterGroup GPU diagnostic

The admitted r58 byte-domain construction now clears **72,576/72,576** pinned native nested-filter pixels (previously67,774; 4,802 differences removed). No references, tolerances, allowlists or production shaders changed. `production_admitted=false`.

The new diagnostic subclasses the original scene, preserving actual production FilterGroup allocation/padding, two filter boundaries, destination-copy ordering, non-unit opacity and post-filter CXFORM. It replaces336 diagnostic materials, including96 buffer composites. The independently constructed reciprocal table uploads as RF and is read back byte-exact. Long-row prefix arithmetic uses the shared new diagnostic include; scalar/tail arithmetic remains unchanged. Original r38 files and their failing regression fixtures remain reproducible.

## Reproduction

```sh
python3 -m tools.probes.run_native_nested_filters \
  --godot /path/to/Godot \
  --native evidence/importer-loud-fail/r38/native \
  --output /tmp/bvn-r59/render
python3 -m unittest tools.tests.test_native_nested_filters tools.tests.test_nested_filters
```

See [render comparison](render/comparison.json), [source/native/readback hashes](render/provenance.json), [GPU log](render/godot.log), and [acceptance](acceptance.json). Pinned native input and intermediate filter buffers remain exact. All six rerun regression commands exited0: ordinary composition4032 and Yulong4/4; explicit nested composition124416; leaf6/6; Glow4/4; samplerGPU71824; CPU sampler suites. Logs and comparison summaries are retained under `regressions/`; the runner records exact command paths.

## Admission boundary and next experiment

This proves the bounded nested-filter fixture, not arbitrary GPU arithmetic or global production eligibility. Next run the same shader helper against all old/signed/amplified consumed-operand controls; GPU multiply/add contraction may differ for transforms absent from this fixture. Do not infer native ISA execution routing from exact output. Static construction evidence remains r58; execution routing remains unverified.

Production remains off. Component suite remains historical9/54 and was not remeasured. General coverage/affine, production eligibility, remaining visual differences and full AS/clip-action ownership still block merge. No full roster/Web export rerun: production runtime is unchanged. Draft only; no merge/deploy/Worker.
