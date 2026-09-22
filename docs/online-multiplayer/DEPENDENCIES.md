# Rollback dependency evaluation

Status: Candidates only, inspected 2026-09-22. No dependency installed or tested.

This page concerns the browser's rollback coordinator. For the separate backend
runtime question (SolidObjects + SQLite versus local Wrangler), see
[LOCAL_DEVELOPMENT.md](LOCAL_DEVELOPMENT.md). It does not supply game-state rollback.

Prefer a maintained rollback coordinator if it can preserve the source-derived
simulation order and export to the exact project Web runtime. The project still
owns complete state, deterministic stepping and presentation reconciliation.

| Candidate | Maintainer evidence | Fit and unresolved work |
|---|---|---|
| Snopek Godot Rollback Netcode | GDScript, custom NetworkAdaptor, save/load/network-process hooks; MIT | Closest candidate for symmetric input-based rollback; prove 4.7.2 single-thread Web/WebRTC compatibility |
| netfox | Godot 4.x/Web and MultiplayerAPI support statements; MIT | Default authoritative correction model differs from the selected peer-equal battle; do not adopt it by silently making the owner authoritative |
| GGPO original SDK | Deterministic stepping/save-load contract; MIT | Algorithm and SyncTest reference; no verified direct Godot WebRTC/Web integration |

Snopek's asset listing and development branch differ: the asset listing says
`1.0.0-alpha` / Godot 4.2, while inspected main metadata says `1.0.0` and its
example project declares 4.6. Pin a specific reviewed revision; neither statement
proves compatibility with this project's 4.7.2 build. Avoid relying on old API
names in prose when the selected revision's source behaves differently.
Sources: [README](https://gitlab.com/snopek-games/godot-rollback-netcode/-/raw/main/README.md),
[plugin metadata](https://gitlab.com/snopek-games/godot-rollback-netcode/-/raw/main/addons/godot-rollback-netcode/plugin.cfg),
[example project](https://gitlab.com/snopek-games/godot-rollback-netcode/-/raw/main/project.godot),
[asset listing](https://godotengine.org/asset-library/asset/2450),
[license](https://gitlab.com/snopek-games/godot-rollback-netcode/-/raw/main/LICENSE.txt).

netfox's platform support does not resolve the authority mismatch; its own FAQ
describes server-authoritative prediction/correction and the requirement to
register all simulation state.
Sources: [FAQ](https://foxssake.github.io/netfox/latest/faq/),
[repository and license](https://github.com/foxssake/netfox).

GGPO's own build instructions do not establish a browser target. Compiling or
wrapping its native SDK would be a separate integration project, not a free
consequence of choosing its algorithm.
Sources: [GGPO](https://github.com/pond3r/ggpo),
[developer guide](https://github.com/pond3r/ggpo/blob/master/doc/DeveloperGuide.md).

## Selection gate

1. Pin revision/license and load using the actual Godot 4.7.2 toolchain.
2. Export single-thread Web; connect two browsers over the chosen WebRTC API,
   testing direct and forced TURN without native extensions.
3. Adapt one restorable battle fixture. Demonstrate identical confirmed state
   against a non-network reference under repeated corrections.
4. Prove source callback/lifecycle order, mutable-state isolation, control barriers
   and side-effect reconciliation. No online helper may rewrite source semantics.
5. Profile browser memory and maximum-window re-simulation; then expand coverage
   to the entire [launch scope](CONTENT_SCOPE.md).

If a candidate fails, capture the concrete incompatibility. Decide between a
small adapter and a minimal project-owned coordinator based on that evidence.
Do not rewrite an entire networking stack speculatively, or call an untested
editor-only diagnostics tool browser-compatible.
