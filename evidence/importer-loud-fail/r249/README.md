# r249 — Per-boundary float display composition explains uncached controls

One fixed, instruction-defined display hierarchy improves retained nearest source-code controls from **409816 to435919/436000**. All **218000/218000 uncached** samples are exact; cached samples are **217919/218000**, leaving **81** counterexamples. The same unchanged inverse/phase/HV sampler now matches the actual source-decoded r242 local JPEG boundary **15980/15980** in both cache settings, previously15979. Every interior, edge and outside partition is retained; no tolerance or correction table is used.

The candidate is still **rejected globally**. These are source-code/isolated-local results, not four complete Jinye image passes. Complete diagnostic coverage remains **46/54**, production coverage historical9/54, all candidate/GPU/production admission flags false. No new native capture or runtime change.

## Independent construction

The pinned native binary supplies384bytes/97instructions of generic float composition and57bytes/11instructions of a device-matrix constructor. The model follows separate binary32 products/additions, signed integer translation conversion before adding the parent integer translation, and bitwise cross-term dispatch including negative zero. Both-fixed inputs, unsupported flags, nonfinite/subnormal/underflow arithmetic and invalid integer conversions reject.

Source display matrices are composed at each hierarchy boundary, rather than first combining them exactly and rounding only once. The constructor seed uses the fixed instruction sequence `f32(f32(4)*f32(.05))`, followed by binary32 draw coefficients/products. Field value4, source routing and MXCSR round-to-nearest-even are **explicit hypotheses**, not proved by a numerical match or pinned instructions alone. Draw translation retains the previous truncation rule separately. The original exact raw16.16/twip fill mapping remains unchanged: r233 already disproved collapsing fill translation into quarter pixels.

The model definition was frozen before valid evaluation. A preliminary evaluator had a dimensional error converting quarter-pixels per twip into pixels per pixel; an identity-units test corrected linear×5/translation÷4 before interpreting results. The invalid scratch run is not counted as a candidate or improvement. See `float-compose-scope.md` and `float-compose-static.json` for precise instruction/assumption scope.

## Verification and reproduction

The evaluator requires the complete200 case/cache inventory, all436000 compatible samples, unchanged retained rows and baseline409816 count. It retains **every failing coordinate**, both models, source hashes and local partitions. Independent review recomputed the complete prediction/failure lists. Focused tests **7/7** cover units, unchanged fill precision, staged float versus fused arithmetic, signed rounding/integer-add placement, negative zero, and rejection bounds.

```sh
python3 -m tools.probes.model_flash_float_compose --binary '/path/to/Flash Player Debugger' --disassembly /path/to/pinned-player.asm --output /tmp/r249/float-compose-static.json
python3 -m tools.probes.analyze_jinye_static_hierarchy --dump /path/to/source-JPEG-plane-helper --output /tmp/r249/evaluation
python3 -m unittest tools.tests.test_flash_float_compose tools.tests.test_jinye_static_hierarchy
```

The `--dump` argument is the existing source JPEG decoder helper, never native output pixels. Decoder plane hashes remain pinned. `evaluation.json.gz` retains complete results; independent review and exact input/tool hashes are archived.

## Next discriminator

Freeze this candidate. Apply it to the existing r221 four actual JPEG leaf images and r241 complete Jinye four-image diagnostic, keeping coverage, cache bounds, inverse/phase/HV and compositing unchanged. Report complete images and geometric partitions before/after without adding any cache-specific correction. No new native capture is needed. This establishes how much of the real source-image mismatch remains beyond display composition.

The81 cached controls remain strict failures throughout. A later cache explanation must come from independently defined allocation-local inverse/rebase behavior and source boundaries, not fitted offsets. Do not add native debugger traps while r247/r248 completion/abort remains unexplained. Separate merge blockers remain Jinye4/Yijiao4, actual gameplay admission or production54 proof, and full AS/clip-action ownership.

Fresh mandatory cache/fingerprint/protected/integrity/handoff/contracts checks are separate from the rejected candidate. Full Python/roster/Web and production54 were not rerun for diagnostic-only changes. Keep Draft; no merge/deploy/Worker.
