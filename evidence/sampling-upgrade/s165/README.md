# s165 — Jiraiya attack: DoAction entry coverage

Only `jiraiya__attack__neutral__ground__near`, unchanged s161 generated tape.
Base `5e1b186c`; branch `feat/sampling-jiraiya-attack-one-cell`.
`production_admitted=false`; `native_parity_proven=false`.

## Result

61/61 samples; 437 entries / 29 blocks. Full gate exits 1: 440 unvisited, 607 uninstrumented.

See acceptance.json and the original receipt/build/raw trace. Missing receipt,
sample, box, node, image, entry or marker negatives are retained in this folder's
gate-proof.json or negative-proof.json as appropriate. Original inputs are restored
and revalidated. No incomplete source inventory was removed to obtain a pass.

94 focused + 25 import guard + 19 probe tests pass (138 distinct tests shared
across all seven dimensions); logs and integrity/handoff/contracts are in s161.
No gameplay/runtime changes. Source-bound Jiraiya Sprite342/PlaceObject2_11_33
is the sole probe binding addition; source changes and ambiguous matches reject.

[Shared reproduction and limits](../s161/REPRODUCTION.md).
Capture completeness is not gameplay/pixel parity. Independent captures do not
prove clock/random/phase equivalence; exact AS ownership remains incomplete.
