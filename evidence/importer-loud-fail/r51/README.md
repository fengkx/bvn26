# r51 — fixed offset normalization does not resolve the paired witnesses

No new rendering, runtime change, coefficient fitting, tolerance or allowlist.
Consumed integer offsets and 1/256 multipliers remain mandatory. All1,302,912
previous RGB controls, including18,720 signed channels, are checked directly.

## Independent operation definitions

Instead of `f32(offset/255)`, use `f32(offset*f32(1/255))` or multiply by the
independently measured r41 reciprocal estimate of255. Combine each fixed choice
with the seven original reciprocal constructions and the three fixed source-first,
unit-gain and premultiplied-gain orders. No choice depends on observed output.
Original sequence bounds remain pinned; they are not reinterpreted as bounds on
these different operation sequences.

## Rejections

**0/42 models match both alpha49 witnesses.** The best total is
**1,274,875/1,302,912**, still rejected. Every model fails older controls.

Independent zero-source green controls provide a stronger isolated rejection:
rounded-reciprocal offset multiplication retains **3840/3840**, while the measured
reciprocal-estimate offset multiplication gives **3424/3840** in all21 combinations.
Thus that offset estimate cannot replace division, even if a combined transform
happens to improve. Rounded multiplication is not distinguished by these zero-source
controls, but does not solve the signed/old paired sites or the global suite.

The full compressed report retains all counted failures and paired outputs. No
old evidence or bounds changed. All admission flags remain false; native-buffer
43006/43200, nested GPU67774/72576 and historical components9/54 are unchanged.
Full AS/clip-action ownership is still a separate merge blocker.

## Reproduction and checks

```
python3 -m tools.probes.analyze_cxform_offset_normalization --output evidence/importer-loud-fail/r51/analysis.json.gz
python3 -m unittest tools.tests.test_cxform_offset_normalization
python3 -m unittest discover -s tools/tests
```

Analysis deliberately exits1. Provenance pins the tools and reused source readbacks.
See acceptance.json for fresh Python/integrity/handoff/contracts checks. Runtime,
cache inputs, old CPU/GPU probes and reference images are unchanged; latest full
cache/fingerprint/protected checks are r49, and exact rendering regressions are r48.
No full roster/Web export or rendering experiment was run.

## Next independent discriminator

All current float32 arithmetic comparisons assume round-to-nearest for intermediate
operations. Independently measure fixed floating-point rounding modes using an
explicit x86/Rosetta instruction probe (including actual mode readback), rather than
asserting what mode Flash uses. Compare each globally fixed mode at both alpha49
sites, then all old/signed controls. Do not infer an instruction or mode from a
local match. Preserve the old nearest-mode controls as strict regressions.
