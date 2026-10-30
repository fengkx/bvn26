# Sampling fix priority after s248

Baseline: master `69319713`. Ranked before implementation of s249. This is a
fix queue, not a new character campaign. Both admission/parity flags stay false.
Impact means prerequisites recovered, not that full dimension gates turn green.

| Rank | Theme / evidence | Why this position | First thin cut | Excluded |
| --- | --- | --- | --- | --- |
| 1 | Display capture completion-window re-entry: [s219](s219/README.md), [s226](s226/README.md), [s233](s233/README.md), [s240](s240/README.md), [s248](s248/README.md) | At least four fighters have rejected display receipts. s248 identifies continued root observation during pending quit and proves a terminal-period closure. Shared, isolated, already experimentally supported. | Enable the proven closure for ordinary display-only sampling; exercise unchanged Yijiao s233 tape without the Yulong opt-in. Preserve terminal callbacks, strict validator and all display obligations. | Other sampling modes, source binding, gameplay, retroactive receipts or trimmed traces. |
| 2 | Display source/frame ownership: [s86](s86/README.md), [s93](s93/README.md), [s100](s100/README.md), [s248](s248/README.md) | Repeated main-source obligations span characters (s248 alone has 122 missing frames plus 44 symbols). Wider full-gate impact, but provenance resolution needs more evidence than the proven boundary fix. | Bind one repeated AImain source-frame family to authored timeline placement and native identity, then fix only that mapping if proved. | Blanket aliases, suppressing unresolved nodes, masks/camera ownership or declaring the entire display gate complete. |
| 3 | Geometry stamp lifecycle: [s64](s64/README.md), [s246](s246/README.md) | Concrete DoAction-only stamping mechanism: newly placed helper atm1 remains unstamped at frames 1–3, first authored action is frame 33. Smaller observed reach than display, but actionable. | Prove and instrument placement/load stamping for this one helper lifetime without changing authored actions. | BitmapData s66, all helpers, receiver ownership, gameplay. |
| 4 | AS call exit / receiver ownership: [s76](s76/README.md), [s245](s245/README.md), [s247](s247/README.md) | Repeated call-return gaps have broad potential impact, but removal of the receiver does not prove VM return; nested geometry receiver context is a separate ownership symptom. | Observe one Chad call boundary across receiver removal before choosing an exit model. | Synthesizing call_after, treating disappearance as return, ancestor-pn guessing, full AS completion. |
| 5 | Strict RGBA / clock alignment: [s217](s217/README.md), [s231](s231/README.md), [s238](s238/README.md) | Broad failure surface, but pixel mismatch alone does not identify phase versus rendering causes. Least isolated until a common phase is proved. | Diagnose one paired native/Godot sampling phase using unchanged inputs before any renderer change. | Threshold relaxation, baseline replacement, broad renderer/gameplay rewrites. |

s247's nested receiver diagnosis is retained, not a mandate to change eligibility.
The Yulong residual queue is closed as evidence work; s241–s244 are recorded
failures, not unfinished residuals. s249 executes rank 1 only. Non-display
completion rejects remain a separately scoped follow-up even where the symptom
looks similar.
