# r73 — exponent and multi-pass controls expose axis ordering

The unchanged six-binary-significant-bit kernel construction clears new exponent neighborhoods and quality1/2/3 **when all horizontal passes precede all vertical passes**. A single global order is compared against every case; no route is selected from individual RGB values.

| Gate / global pass order | Exact RGBA samples |
|---|---:|
| Explicit new source readbacks | **165888/165888** |
| Horizontal passes, then vertical passes | **165888/165888** |
| Alternating horizontal/vertical | 164159/165888 |
| Vertical passes, then horizontal passes | 162446/165888 |
| Retained r71 controls | **10080/10080** |
| Retained r72 controls | **72576/72576** |

The1296 new cases bracket kernels0.5,1,1.5,2,8.25,15.5,16,16.25 at±1/1024, vary alphas25/135, constant/impulse/horizontal-ramp sources, all axis combinations and qualities1/2/3. Source and result central rows/columns retain paired transparent/black native readbacks (shared center counted in both lines). Retained blurX/blurY/quality properties and the exact input grid are validated.

All1729 alternating-order differences occur at both-axis quality2/3; maximum channel delta1. Example case340: kernel1.4990234375, alpha25, impulse, quality2, row x31: alternating predicts2, native1. Case341 quality3 center predicts2, native3. The reverse grouped order also rejects, so this is not merely evidence for arbitrary grouping.

**The unchanged production `filter_group.gd` currently alternates axes inside the pass loop.** This fresh native evidence exposes a real multi-pass mismatch; it is not allowlisted or compensated. No production source, shader, allocation or reference was changed this round. The old242-case Blur suite has only horizontal blur and therefore cannot distinguish these two-axis orders; r72 retained all its kernel operands unchanged.

CPU convolution uses exact rational weights and per-axis byte truncation. A prefix-sum implementation retains all82656 previous samples before testing new controls. This is bounded observable behavior, not proof of executed native instructions, arbitrary clipping or all filter families.

## Reproduce

```sh
python3 tools/probes/build_flash_filter_probe.py --case blur-kernel-heldout \
  --output /tmp/bvn-r73/native --ffdec /path/to/ffdec-cli.jar
python3 tools/probes/capture_native_player.py /tmp/bvn-r73/native /tmp/bvn-r73/native/native.log \
  --player-app '/path/to/Flash Player.app' --allow-window-activation --timeout 45
python3 -m tools.probes.analyze_blur_kernel_heldout \
  --native evidence/importer-loud-fail/r73/native --output /tmp/bvn-r73/analysis.json
python3 -m unittest tools.tests.test_blur_kernel_heldout
```

[All comparisons](analysis.json), [native capture](native/native.log), [hashes](provenance.json), [acceptance](acceptance.json). Analysis output is bounded CPU evidence, not production admission.

Next carry the common kernel construction and grouped-axis order into isolated actual FilterGroup diagnostics. Require the same r70 native input/filter/final rows plus these multi-pass controls and old graphical regressions to remain exact before considering a production change. Verify Glow and DropShadow rather than assuming all families share BlurFilter ordering.

`production_admitted=false`. No new GPU render; r70 remains115596/115840 filtered and115678/115840 final. Components remain historical9/54. General coverage/affine/production eligibility and full AS/clip-action ownership remain open. Full roster/Web export and unchanged graphical gates were not rerun; pinned old controls remain regressions. Draft only; no merge/deploy/Worker.
