# s160 — Itachi attack: Call-site and branch observations

Only `itachi__attack__neutral__ground__near`, unchanged s154 generated tape.
Base `5e1b186c`; branch `feat/sampling-itachi-attack-one-cell`.
`production_admitted=false`; `native_parity_proven=false`.

## Result

61/61 samples; 429 complete invocations (389 false / 40 true); 1 incomplete. Full ownership gate exits 1; callee bodies, other branches and Godot ownership remain unproven. Exact incomplete boundaries retained in callsite-summary.json.

See acceptance.json and the original receipt/build/raw trace. Missing receipt,
sample, box, node, image, entry or marker negatives are retained in this folder's
gate-proof.json or negative-proof.json as appropriate. Original inputs are restored
and revalidated. No incomplete source inventory was removed to obtain a pass.

94 focused + 25 import guard + 19 probe tests pass (138 distinct tests shared
across all seven dimensions); logs and integrity/handoff/contracts are in s154.
No gameplay/runtime changes. Source-bound Itachi Sprite294/PlaceObject2_11_33
is the sole probe binding addition; source changes and ambiguous matches reject.

[Shared reproduction and limits](../s154/REPRODUCTION.md).
Capture completeness is not gameplay/pixel parity. Independent captures do not
prove clock/random/phase equivalence; exact AS ownership remains incomplete.

## Rejected first call-site capture

The first s160 capture was rejected by receipt validation: `native evidence:
events beyond completion boundary`. Its unchanged trace, build and environment
are retained as `rejected-*` artifacts. No events were trimmed. The same source,
case and observer were rebuilt under fresh run ID
`s160-itachi-attack-20261028-retry1` and recaptured; that receipt passes. Its
incomplete invocation remains in the ownership report and the full gate exits 1.
