# s77 — Renji attack: Native receipt

One character PR, exactly `renji__attack__neutral__ground__near`, unchanged s77 tape.
Base `9ce1db68421d91f3ef0433d41d59b324f92344f7`; branch `feat/sampling-renji-attack-one-cell`.
`production_admitted=false`; `native_parity_proven=false`.

## Result

5,107 events, 122 actor states; receipt and Godot required-native selected execution pass (1/324, no errors). Full campaign exits 1 on other missing receipts.

Missing receipt, wrong-case receipt and missing native sample reject; original receipt revalidates. Unmarked entries need no receipt.

Review gate-proof.json and runtime-report.json; raw trace/build/runtime archives, plus acceptance.json and native receipt/build/capture artifacts.
Full residual lists remain intact; no allowlists, tolerances, reference rewriting
or runtime/gameplay changes. 83 focused + 25 importer guard + 19 probe tests
pass (127 distinct tests shared across these seven dimensions). Logs and final
integrity/handoff/contracts results live in [s77](../s77/README.md).

## Reproduction and limits

See [shared reproduction and evidence contract](../s77/REPRODUCTION.md) for exact
commands, paths, hashes and archive restoration. Each native run has its own
environment record; neither pixels nor observations are synthetic substitutes.
Capture completeness does not prove native parity. Source gaps, sampled lifetime
limits, clock/render-phase differences and full AS ownership remain explicit.
No geometry/image/ownership gap is waived by success in another dimension.


## Character review map

- [s78: Global geometry](../s78/README.md)
- [s79: Child display list and camera](../s79/README.md)
- [s80: BitmapData and RGBA](../s80/README.md)
- [s81: DoAction entry coverage](../s81/README.md)
- [s82: Clip-action handler entries](../s82/README.md)
- [s83: Call-site and branch observations](../s83/README.md)
