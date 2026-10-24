# r48 — signed reciprocal constraints

Diagnostic only. No new native capture, runtime change, reference rewrite, tolerance,
allowlist, GPU advancement, or production admission. Reuse the pinned r47 source
readbacks and signed native controls; all arithmetic consumes integer offsets and
multipliers truncated toward zero onto the 1/256 grid.

## Direction-correct bounds

`cxform_signed_bounds.py` searches nonnegative finite float32 coefficients. For a
negative multiplier, the output decreases: the inclusive interval is the first
coefficient producing at most the native byte through the predecessor of the first
coefficient producing at most native-minus-one. Positive searches are unchanged.
Zero source/multiplier channels are coefficient-independent and explicitly handled.
Tests check both endpoints and neighboring coefficients, constant/invalid inputs,
positive compatibility, and retention of every old bound.

The 18,720 signed RGB constraints comprise 14,720 positive, 1,760 zero and 2,240
negative multiplier channels. Intersecting them with all 1,284,192 old constraints
produces **1,302,912 constraints**. No interval becomes empty. Only alpha255 tightens
in the combined models; its new upper witness is a **positive** multiplier control:
source128, alpha255, multiplier128/256, offset128, opacity100, native191.

| Coefficient space | Old upper bits | New upper bits |
|---|---|---|
| unit | 0x3b808080 | 0x3b80807f |
| normalized | 0x3f7fffff | 0x3f7ffffd |
| byte | 0x3f7ffffe | 0x3f7ffffd |

## Concrete rejection, not a fitted reciprocal

Alpha49/source-green25/multiplier−129/256/offset128/opacity100 yields native12.
The three independently measured normalization sequences yield11 (32 repeated
signed failures; each sequence scores 18,688/18,720). The `estimate_inverse`
construction locally yields12, but its unit coefficient bits1017587712 exceed the
old combined upper bound1017587596. Thus selecting that local match would violate
older native controls. This signed site does not further narrow the old interval.

Global direct sequence scores on old controls are 1,257,950, 1,257,577 and
1,250,064 of 1,284,192, respectively. All three operation orders retain these
counts. No tested common construction covers all255 alpha intervals (best209/255).
All admission flags remain false; the analysis command deliberately exits1.

## Reproduction and verification

```
python3 -m tools.probes.analyze_cxform_signed_bounds --output evidence/importer-loud-fail/r48/analysis.json.gz
python3 -m unittest tools.tests.test_cxform_signed_bounds
python3 -m unittest discover -s tools/tests
```

The compressed report retains native endpoint witnesses, all intersections and
sequence counterexamples. `provenance.json` pins tools, source evidence and outputs.
`acceptance.json` and `checks/` record rerun gates. Pinned GPU controls remain4032/4032,
nested composition124416/124416, complete Yulong4/4, leaf6/6, Glow4/4 and sampler
71824/71824; CPU sampler regressions remain exact. No full roster replay or Web
export was rerun for this diagnostic-only change.

## Still blocked

No reciprocal/input-normalization construction is admitted. Native filter boundary
status remains43006/43200; the unadvanced nested-filter GPU gate remains67774/72576.
Components remain historical9/54, not remeasured. Full AS/clip-action ownership is
also unresolved; the PR stays draft and not merge-ready.

A next experiment should discriminate an independently defined reciprocal/operation
construction against both the signed alpha49 case and its older upper-bound witness
before additional rendering. The feasible interval is a rejection constraint, not
a source from which to choose coefficients. No new construction is asserted here.
