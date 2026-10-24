# r52 — independent hardware rounding modes do not resolve the witness

No Flash/Godot rendering or runtime changes. This is an independent x86/Rosetta
instruction experiment, not an inference about Flash's implementation.

## Explicit hardware controls

Compile the checked-in SSE intrinsic probe for x86_64 with contraction disabled,
no optimization and rounding-mode awareness. Feed all136,774 unique consumed-input
tuples represented by the1,302,912 old/signed native RGB controls. For each input,
set and read back MXCSR nearest/down/up/toward-zero bits; evaluate three globally
fixed integer-alpha / normalized-divide / normalized-multiply paths. Restore the
original CSR at program exit. Raw input/output streams and compile/run environment
are retained with hashes. No mode is selected from the observed pixel.

All **410,322 nearest-mode unique results** equal the existing CPU arithmetic
comparators exactly. This guards the experiment against a changed instruction
sequence or accidental loss of the old nearest-mode controls.

## Result

**0/12 models match both alpha49 witnesses.** Every mode/path returns12 at the old
positive witness where native is11. Integer-alpha paths match the signed12; the
normalized paths return11. Full old/signed scores remain rejected. Best total is
1,276,638/1,302,912 (`nearest/normalized_divide`), unchanged from the old sequence.
Changing rounding mode alone is not sufficient for these constructions.

All flags remain false. Native buffer43006/43200, unadvanced nested GPU67774/72576,
historical components9/54 and unresolved full AS ownership remain blockers.

## Reproduction

```
clang -arch x86_64 -O0 -ffp-contract=off -frounding-math tools/probes/cxform_rounding_modes.c -o /tmp/bvn-r52/rounding
python3 -m tools.probes.analyze_cxform_rounding_modes --executable /tmp/bvn-r52/rounding --output evidence/importer-loud-fail/r52
python3 -m unittest tools.tests.test_cxform_rounding_modes
```

Analysis deliberately exits1. See acceptance.json for targeted and integrity checks;
full Python remains r51, cache/fingerprint/protected r49, exact rendering r48.
No production, GPU gate or reference change.

## Next independent normalization construction

The normalized-alpha inverse can instead be constructed as `255 * estimate(alpha)`
from the integer alpha, while source normalization is independently measured.
This is algebraically equivalent in exact arithmetic but has different approximate
operations from estimating `alpha/255`. Define the sequence globally, preserve
all signed and old controls, and reject it globally even if the paired witnesses
match. Never replace actual source multiplication by a fitted per-alpha coefficient.
