# r72 — bounded kernel consumption clears independent axis controls

A globally defined truncation of a positive kernel to **six binary significant bits**, followed by rational box weights and per-axis byte truncation, clears both the new native sweep and all r71 controls. It uses `frexp`/`ldexp`; there is no per-kernel table, RGB-selected path, epsilon or fitted coefficient.

| Model | r71 RGBA pixels | New RGBA pixels |
|---|---:|---:|
| Unconsumed exact kernel | 9884/10080 | 68492/72576 |
| Fixed four fractional bits | 10026/10080 | 71390/72576 |
| Six significant bits | **10080/10080** | **72576/72576** |

All10080 old and72576 new source readbacks are exact. The new1134 cases independently bracket seven centers (2.0625,3.5,3.9375,4,5.0625,7.9375,8) at offsets −17,−16,−15,−1,0,1,15,16,17 over1024. Constant and impulse sources, three alphas and horizontal/vertical/both-axis filters retain both central row and column readbacks (the shared center is counted in each sampled line). Filter properties retain the fine supplied values; consumed precision is inferred only within these observed bounds, not equated with property storage.

The former kernel3.99609375 counterexamples use consumed3.9375. Kernel7.99609375 uses7.875, explaining why fixed1/16 truncation failed. One common significant-bit construction covers both ranges and the held-out5.0625 neighborhood. No executed instruction/ISA or general filter implementation claim follows from this behavioral agreement.

The existing242-case Blur fixtures keep **all242 kernel operands unchanged** under this construction. This is an operand-invariance check, not a fresh GPU replay or proof that arbitrary multi-pass, large-kernel or implicit Glow cases are covered.

## Reproduce

```sh
python3 tools/probes/build_flash_filter_probe.py --case blur-kernel-consumption \
  --output /tmp/bvn-r72/native --ffdec /path/to/ffdec-cli.jar
python3 tools/probes/capture_native_player.py /tmp/bvn-r72/native /tmp/bvn-r72/native/native.log \
  --player-app '/path/to/Flash Player.app' --allow-window-activation --timeout 45
python3 -m tools.probes.analyze_blur_kernel_consumption \
  --native evidence/importer-loud-fail/r72/native --output /tmp/bvn-r72/analysis.json
python3 -m unittest tools.tests.test_blur_kernel_consumption
```

[Native controls](native/native.log), [all measured results and rejected-model sites](analysis.json), [hashes](provenance.json), [acceptance](acceptance.json). The analysis records a bounded CPU result; it is not production admission.

Next independently extend around smaller and larger exponent boundaries and multi-pass controls, then test the bounded construction through the actual GPU diagnostic against unchanged r70 native stages. Preserve source geometry/allocation and the admitted CXFORM implementation. Require all exact gates before any widening; do not change production from this CPU pass.

`production_admitted=false`. No runtime/shader modification, no new GPU render. r70 remains115596/115840 filtered and115678/115840 final. Components remain historical9/54. General coverage/affine/production eligibility and full AS/clip-action ownership remain open. Full roster/Web export and unchanged graphical gates were not rerun; pinned old controls remain regressions. Draft only; no merge/deploy/Worker.
