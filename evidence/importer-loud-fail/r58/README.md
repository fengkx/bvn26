# r58 — byte-domain arithmetic clears the complete CPU gate

**1,302,912/1,302,912 old/signed RGB controls and43,200/43,200 pinned native filter
boundary pixels are exact.** No tolerance, allowlist, fitted coefficient or source
reference change. GPU diagnostics may now advance; production admission stays false.

## Independent construction and its limits

Read-only inspection of the installed Flash Player Debugger32 binary found a static
candidate at virtual address0x1001fc300 with a16-pixel branch and byte-domain color
arithmetic. `static-binary.json` pins the executable hash, constant words and small
instruction byte spans. This is **static evidence only**, not proof that the probe
executed that branch. LLDB did not reach a verified execution stop.

The fixed sequence uses exact binary constant words:

- normalizer `0x3b808081`, multiplier scale `0x3b800000`, maximum255;
- denominator input `f32(f32(alpha*normalizer) + bits(0x37808081))`;
- measured reciprocal estimate of that input;
- raw premultiplied source byte ×reciprocal, then consumed multiplier/256 and integer
  offset, clamped in byte range[0,255];
- multiply by `f32(output_alpha*normalizer)`, then truncate to integer.

The denominator constant is read from the binary, not chosen from a feasibility
interval or adjusted to a native output. It is not a comparison tolerance. The
byte-domain operation order differs from the old normalized-source hypotheses;
old sequence-specific intervals are retained, not reinterpreted as universal bounds.
All raw native controls underlying those bounds are checked and pass exactly.

Reciprocal values are obtained from the already independently enumerated r56
hardware image. Alpha255's input is just above that domain; r57's integer-domain
image supplies a post-scaled output whose inverse is proven unique by checking the
adjacent float32 outputs. No native RGB value or feasibility interval participates
in this construction. Every alpha's input/run/output witness is retained.

## Exact checks

| Gate | Exact /total |
|---|---:|
| old RGB controls | 1284192/1284192 |
| signed RGB controls | 18720/18720 |
| r39 long-row controls | 25920/25920 |
| scalar controls | 3072/3072 |
| held-out constant /alternating spans | 8652/8652 each |
| pinned native filter boundaries | 43200/43200 |
| all-alpha pixels | 24576/24576 |
| non-binary opacity pixels | 32768/32768 |
| source-boundary intersections, alpha135 /197 | 192000/192000 each |

The old exact-reciprocal negative control still rejects25621/25920. Clip-only routing
without source intersection still rejects191860/192000 and191606/192000; the already
supported intersection geometry passes. Scalar/tail handling is unchanged. The old
harness is injected only within a scoped diagnostic context, never edited on disk.

## Reproduction and environment caveat

```
python3 -m tools.probes.extract_cxform_binary_constants --binary '/Users/fengkx/me/code/flash-player/Flash Player.app/Contents/MacOS/Flash Player Debugger' --output evidence/importer-loud-fail/r58/static-binary.json
python3 -m tools.probes.analyze_cxform_native_candidate --output evidence/importer-loud-fail/r58/analysis.json.gz
python3 -m unittest tools.tests.test_native_cxform_candidate
python3 -m unittest discover -s tools/tests
```

No new Flash capture was used. The attempted LLDB launch stalled during Rosetta
startup; its processes were cleaned up. An independent new C helper subsequently
stalled before producing output; TERM/KILL were requested, but its PID24123 remained
in uninterruptible state at the recorded check. Its output is **not used**. Existing
r56/r57 hashed hardware measurements make the successful Python reproduction fully
independent of that failed helper. Debugger logs/status are retained. The optional
`write_cxform_trace.py` writes a reproducible script but does not launch it or assert
execution evidence. Do not retry a still-live blocked process without checking it.

## Admission and next work

The bounded behavioral CPU arithmetic gate passes, so `gpu_advance_allowed=true`.
`execution_routing_verified=false` and `production_admitted=false`; matching outputs
do not establish native instruction routing. No GPU/runtime was changed this round.
The nested GPU gate remains historical67774/72576 until rerun. Components remain
historical9/54. Full AS/clip-action ownership is still incomplete.

Next port this fixed byte-domain sequence into the existing actual-FilterGroup GPU
diagnostic, preserving geometry, pinned buffers and all prior exact regressions.
Require72576/72576 exact before any wider eligibility. No global production enablement.
