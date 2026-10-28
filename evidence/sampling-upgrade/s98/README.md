# s98 — Sakura attack: Native receipt

Only `sakura__attack__neutral__ground__near`, unchanged s98 generated tape.
Base `39c2c41a`; branch `feat/sampling-sakura-attack-one-cell`.
`production_admitted=false`; `native_parity_proven=false`.

## Result

5275 native events; receipt revalidation and Godot required-native selected execution pass (1/324). Full campaign rejects other missing receipts.

See acceptance.json and the original receipt/build/raw trace. Missing receipt,
sample, box, node, image, entry or marker negatives are retained in this folder's
gate-proof.json or negative-proof.json as appropriate. Original inputs are restored
and revalidated. No incomplete source inventory was removed to obtain a pass.

86 focused + 25 import guard + 19 probe tests pass (130 distinct tests shared
across all seven dimensions); logs and integrity/handoff/contracts are in s98.
No gameplay/runtime changes. Source-bound Sakura Sprite630/PlaceObject2_11_31
is the sole probe binding addition; source changes and ambiguous matches reject.

[Shared reproduction and limits](../s98/REPRODUCTION.md).
Capture completeness is not gameplay/pixel parity. Independent captures do not
prove clock/random/phase equivalence; exact AS ownership remains incomplete.

## Character review map

- [s99: Global geometry](../s99/README.md)
- [s100: Child display list and camera](../s100/README.md)
- [s101: BitmapData and RGBA](../s101/README.md)
- [s102: DoAction entry coverage](../s102/README.md)
- [s103: Clip-action handler coverage](../s103/README.md)
- [s104: Call-site and branch observations](../s104/README.md)

## PR review correction: path case

The Sakura binding test now opens the tracked `scripts/fighter/Sakura.json`,
matching case-sensitive filesystems. The old lowercase spelling is rejected by
an exact directory-entry check, and the corrected test passes under that check
(see path-case-review.txt). This was run on macOS, not Linux. All 130 tests were
rerun; updated logs are retained. The PR's 126 changed files, including compressed
evidence archives, contain no other lowercase bundle-path references. Native
captures, receipt hashes and gameplay code are unchanged.
