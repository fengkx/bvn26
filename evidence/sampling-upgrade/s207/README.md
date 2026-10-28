# s207 — Rifagu attack: DoAction entry coverage

Only `rifagu__attack__neutral__ground__near`, unchanged s203 generated tape.
Base `02919820`; branch `feat/sampling-rifagu-attack-one-cell`.
`production_admitted=false`; `native_parity_proven=false`.

## Result

61/61 samples; 421 entries / 29 blocks. Full gate exits 1: 560 unvisited, 653 uninstrumented.

See acceptance.json and the original receipt/build/raw trace. Missing receipt,
sample, box, node, image, entry or marker negatives are retained in this folder's
gate-proof.json or negative-proof.json as appropriate. Original inputs are restored
and revalidated. No incomplete source inventory was removed to obtain a pass.

100 focused + 25 import guard + 19 probe tests pass (144 distinct tests shared
across all seven dimensions); logs and integrity/handoff/contracts are in s203.
No gameplay/runtime changes. Source-bound Rifagu Sprite638/PlaceObject2_14_31
is the sole probe binding addition; source changes and ambiguous matches reject.

[Shared reproduction and limits](../s203/REPRODUCTION.md).
Capture completeness is not gameplay/pixel parity. Independent captures do not
prove clock/random/phase equivalence; exact AS ownership remains incomplete.
