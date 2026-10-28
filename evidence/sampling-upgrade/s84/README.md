# s84 — Lee attack: Native receipt

One character PR, exactly `lee__attack__neutral__ground__near`, unchanged s84 tape.
Base `f378ca6493c252aabaf1619cfb3f7e179cdac298`; branch `feat/sampling-lee-attack-one-cell`.
`production_admitted=false`; `native_parity_proven=false`.

## Result

5,402 events, 122 actor states; receipt and Godot required-native selected execution pass (1/324, no errors). Full campaign exits 1 on other missing receipts.

Missing receipt, wrong-case receipt and missing native sample reject; original receipt revalidates. Unmarked entries need no receipt.

Review gate-proof.json and runtime-report.json; raw trace/build/runtime archives, plus acceptance.json and native receipt/build/capture artifacts.
Full residual lists remain intact; no allowlists, tolerances, reference rewriting
or runtime/gameplay changes. 84 focused + 25 importer guard + 19 probe tests
pass (128 distinct tests shared across these seven dimensions). Logs and final
integrity/handoff/contracts results live in [s84](../s84/README.md).

## Reproduction and limits

See [shared reproduction and evidence contract](../s84/REPRODUCTION.md) for exact
commands, paths, hashes and archive restoration. Each native run has its own
environment record; neither pixels nor observations are synthetic substitutes.
Capture completeness does not prove native parity. Source gaps, sampled lifetime
limits, clock/render-phase differences and full AS ownership remain explicit.
No geometry/image/ownership gap is waived by success in another dimension.


## Character review map

- [s85: Global geometry](../s85/README.md)
- [s86: Child display list and camera](../s86/README.md)
- [s87: BitmapData and RGBA](../s87/README.md)
- [s88: DoAction entry coverage](../s88/README.md)
- [s89: Clip-action handler entries](../s89/README.md)
- [s90: Call-site and branch observations](../s90/README.md)
