# r55 — sequence-specific feasibility still leaves an unknown construction

No rendering or production change; no coefficients selected. Derive new rejection
intervals for the fixed source-first normalized-input operation, separately for
each of the three independently measured source-normalization tables. The unknown
is one normalized-alpha reciprocal per alpha. Consume integer offsets and1/256
multipliers, search decreasing intervals for negative multipliers, and explicitly
handle constant zero-source/multiplier channels. Retain all1,302,912 controls.

## Findings

All255 alpha intervals are nonempty for each of the three source-normalization
sequences. Thus the current native controls **do not disprove existence** of a
coefficient for any of these sequences. This is not an admitted construction and
must not be turned into a lookup table of fitted interval values.

All seven independently measured reciprocal constructions still fail global
membership. Best memberships are208/255 for divide or rounded-source multiplication,
and176/255 for estimated-source multiplication. In particular, r53's estimated
integer inverse ×255 belongs to only107/255 intervals in the estimated-source path.

Alpha49 source-divide bounds are bits1084653516..1084653669; estimated-source bounds
are1084653683..1084653835. Their witnesses are retained: source26/multiplier4/offset−385
(native30) and source23/multiplier2046/256/offset−894(native11). These ranges are
rejection constraints only. Old r48 intervals remain unchanged and are not reused
as if they described this different operation sequence.

## Reproduce / checks

```
python3 -m tools.probes.analyze_cxform_normalized_bounds --output evidence/importer-loud-fail/r55/analysis.json.gz
python3 -m unittest tools.tests.test_cxform_normalized_bounds tools.tests.test_cxform_factor_grid tools.tests.test_cxform_scaled_inverse tools.tests.test_cxform_signed_bounds
```

Analysis exits1; targeted tests10/10 verify negative endpoints, constants and all
recorded lower/upper witnesses. Integrity/handoff/contracts rerun. No old probe,
runtime, reference or GPU gate modified. Latest full Python remains r51, full
cache/fingerprint/protected r49, exact rendering r48. Admission flags all false;
native-buffer43006/43200, GPU67774/72576, historical components9/54 and AS ownership
remain open. No additional rendering/full roster/Web build.

## Next independent rejection test

Enumerate actual hardware reciprocal-estimate outputs for every float32 input in
the independently chosen normalized-byte domain[1/256,1], retaining run boundaries
and mode/environment readbacks. Check whether each feasibility interval contains
any obtainable output. This can reject a single-estimate construction regardless
of its input normalization within that domain, without choosing an input or output
from the interval. It does not cover post-estimate scaling/combinations or prove
which instructions Flash uses.
