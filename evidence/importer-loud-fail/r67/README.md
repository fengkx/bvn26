# r67 — independent filter-property precision and public rectangle transitions

Three fresh native captures contain420 property/rectangle controls: a broad sweep around2,4,6,8,10,12; a fine sweep down to±2^-26 around those integers; and the same fine sweep around2.5,4.5,6.5,8.5,10.5,12.5. Glow and Blur are measured independently, with retained blurX/blurY property strings and actual public rectangle coordinates.

- Requested/property X/property Y strings agree **420/420**, including distinct logged values below float32 spacing. This is a claim about observed property precision, not arbitrary exact double-bit retention.
- Glow's public padding matches `round_to_nearest_even((value+1)/2)` on **210/210** controls.
- Blur's public padding matches `floor(value/2+0.75)` on **210/210** controls. Equivalent algebraic sequences are not distinguished by this evidence.
- Quantizing the retained input to float32 *before* these operations passes only **187/210** for each filter, **374/420** overall; that construction is rejected.

No RGB samples select a rectangle rule. These independent public-API controls explain why odd-kernel probes were insufficient, but do not establish internal cache allocation, an executed instruction/ISA, or a general production extent rule. The fine tests retain their actual emitted decimal property values; no epsilon/tolerance is applied to rectangle comparisons.

## Reproduce

Build/capture each checked-in probe using `build_flash_filter_probe.py` and `capture_native_player.py`:

- `filter-rectangle-precision` → `native/wide`
- `filter-rectangle-fine` → `native/fine`
- `filter-rectangle-half` → `native/half`

```sh
python3 -m tools.probes.analyze_filter_rectangle_precision \
  --native evidence/importer-loud-fail/r67/native --output /tmp/bvn-r67/analysis
# Expected exit1: public-API success cannot admit implicit cache allocation.
python3 -m unittest tools.tests.test_filter_rectangle_precision
```

[Analysis/counterexamples](analysis.json), [provenance](provenance.json), [acceptance](acceptance.json). Every capture pins the source hash and run identity; sequence, property fields and complete control coverage are checked. Original pixel/control references are unchanged.

## Remaining discriminator

The implicit cache still fails the fixed right-border hypothesis at the r66 kernel4/8 sites, despite exact explicit arithmetic/filter bytes. Public rectangle rounding must remain separate from any proposed conservative internal allocation. A future common construction must be tested globally against all old and held-out controls; do not replace the failed border with per-kernel constants or claim an internal route from public-API agreement alone.

No new GPU run, production/runtime edit, allowlist, channel tolerance or source/reference rewrite. Production remains disabled; components historical9/54 and full AS/clip-action ownership remain open. Full roster/Web export and unchanged graphical suites were not rerun; strict pinned regressions remain in Python. Draft only; no merge/deploy/Worker.
