# Ichigo zero-stage attack: seven-dimension observation slice

Base `70951935`; branch `feat/sampling-ichigo-attack-one-cell`.

Only `ichigo__attack__neutral__ground__near`. The explicit lowercase source is `ichigo.swf` / `ichigo.json`: native catalog **一护2 / 零段**, Sprite 274. The ordinary 一护 catalog entry loads **yihu.swf** instead. See [source binding](source-binding.json).

The Godot available catalog has no ichigo and no generated ichigo fighter exists. The existing campaign generator rejects it; this slice uses the existing pure fixture function for a native-only case. No catalog or gameplay implementation was added and no yihu output was substituted.

- s224 Native receipt: PASS (exit 0); 5031 native events, 122 actor observations. Campaign exit 1; Godot execution unavailable.
- s225 Global geometry: PASS (exit 0); 61 samples, {'hurt': 238, 'attack': 2}, 9 observed lifetimes. Godot geometry parity untested.
- s226 Display list / camera: INCOMPLETE (exit 1); receipt rejected: native evidence: events beyond completion boundary
- s227 BitmapData / RGBA: INCOMPLETE (exit 1); 61 native images, 0 Godot images. Pixel comparison not evaluated (missing ichigo implementation).
- s228 DoAction: INCOMPLETE (exit 1); receipt rejected: native evidence: events beyond completion boundary
- s229 Clip-action: INCOMPLETE (exit 1); 61 samples, 3333 entries, 42 visited / 772 unvisited / 417 uninstrumented items. Entry kinds: {'doaction_entry': 438, 'clipaction_entry': 2895}.
- s230 Call / branch: INCOMPLETE (exit 1); 61 samples, 3264 entries, 42 visited / 772 unvisited / 417 uninstrumented items. 453 complete invocations (47 true / 406 false), 1 incomplete.

148 focused/import/probe tests pass. Per-dimension negative proofs accompany admitted captures. Receipt completeness is not gameplay parity.

Full native parity, Godot implementation/comparisons, source binding, dynamic masks, intra-frame lifetime and complete AS/callee ownership remain unproven.

[Reproduction](REPRODUCTION.md) · [structured acceptance](character-acceptance.json) · [measured timing](session-timing.json).

`production_admitted=false`; `native_parity_proven=false`. No merge or deployment.
