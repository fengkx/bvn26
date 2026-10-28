# s87 — Lee attack: BitmapData and RGBA

One character PR, exactly `lee__attack__neutral__ground__near`, unchanged s84 tape.
Base `f378ca6493c252aabaf1619cfb3f7e179cdac298`; branch `feat/sampling-lee-attack-one-cell`.
`production_admitted=false`; `native_parity_proven=false`.

## Result

30,135 native events; native/Godot 61/61 images each, 600×400 opaque RGBA, 58,560,000 bytes per capture. Strict gate exits 1: 0/61 exact, 17,650,119 differing channels, 6,865,361 differing pixels, max delta 255.

Missing native frame/row and Godot image reject; restored images/receipt revalidate. One-channel mutation detected without tolerance.

Review comparison.json, negative-proof.json, actual native/Godot image archives and tick-13 previews, plus acceptance.json and native receipt/build/capture artifacts.
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

