# s80 — Renji attack: BitmapData and RGBA

One character PR, exactly `renji__attack__neutral__ground__near`, unchanged s77 tape.
Base `9ce1db68421d91f3ef0433d41d59b324f92344f7`; branch `feat/sampling-renji-attack-one-cell`.
`production_admitted=false`; `native_parity_proven=false`.

## Result

29,628 native events; native/Godot 61/61 images each, 600×400 opaque RGBA, 58,560,000 bytes per capture. Strict gate exits 1: 0/61 exact, 17,860,537 differing channels, 6,895,977 differing pixels, max delta 255.

Missing native frame/row and Godot image reject; restored images/receipt revalidate. One-channel mutation detected without tolerance.

Review comparison.json, negative-proof.json, actual native/Godot image archives and tick-13 previews, plus acceptance.json and native receipt/build/capture artifacts.
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

