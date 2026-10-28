# s131 — Konan attack: Clip-action handler coverage

Only `konan__attack__neutral__ground__near`, unchanged s126 generated tape.
Base `c567075b`; branch `feat/sampling-konan-attack-one-cell`.
`production_admitted=false`; `native_parity_proven=false`.

## Result

61/61 samples; 2753 clip entries / 12 handlers. Full gate exits 1: 610 unvisited, 415 uninstrumented.

See acceptance.json and the original receipt/build/raw trace. Missing receipt,
sample, box, node, image, entry or marker negatives are retained in this folder's
gate-proof.json or negative-proof.json as appropriate. Original inputs are restored
and revalidated. No incomplete source inventory was removed to obtain a pass.

90 focused + 25 import guard + 19 probe tests pass (134 distinct tests shared
across all seven dimensions); logs and integrity/handoff/contracts are in s126.
No gameplay/runtime changes. Source-bound Konan Sprite563/PlaceObject2_16_32
is the sole probe binding addition; source changes and ambiguous matches reject.

[Shared reproduction and limits](../s126/REPRODUCTION.md).
Capture completeness is not gameplay/pixel parity. Independent captures do not
prove clock/random/phase equivalence; exact AS ownership remains incomplete.

## Clip-action capture retry

The first s131 capture failed receipt validation for events beyond completion.
The unedited raw trace, command output and build remain in s131 as rejected
artifacts. A rebuilt probe with fresh run ID
`s131-konan-attack-20261028-retry1` was captured again and passed the unchanged
receipt gate. Source, input and observer code were unchanged. No tail trimming
or boundary relaxation was used. Use the retry ID to restore this evidence and
a fresh ID when recapturing.
