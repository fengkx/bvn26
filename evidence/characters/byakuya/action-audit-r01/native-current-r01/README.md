# Byakuya base-form hitbox contact probe (native-only interim)

This archive records current-tree Godot test-only `hit_contact` observations for natural-input down+U (`zh2atm`) and down+I (`cbsatm`), guard and opposite-facing inputs, placements, and state at the resolver callback. It does not claim source geometry parity: source-side callback-time AABB observation is pending.

`*.game_bounds` are source game-space values from generated placement bounds and the existing `SourceMatrixBounds` implementation. `*.global_bounds` are Godot scene/viewport coordinates and remain separate. Full actor Node2D source matrix chains are retained in each contact record. The source raw/build/fixture paths and hashes are recorded in `manifest.json`.

The `zh2-mirror` fixture has no P2 down input, so it proves reversed-facing hit geometry/contact only; it is not a second guard-break case. In the guarded native cases, P2 is in guard at contact and afterward transitions to action `-1`; HP changes 1000→900 (`zh2`) and 1000→550 (`cbs`). This establishes the native path only, pending exact source callback AABB pairing.

## Source/native Byak 690 guard pairing

The paired source capture is `evidence/characters/byakuya/validation/hit-receive-r02-source/` (run `hit-receive-byak-690-guard-r01`), with exact same fixture inputs and setup as `cbs-guard.fixture.json`. At display tick 496 / fight tick 45, source records `source_hit_test=true` and then `source_guard_packet` (`pw=450`, `zl=15`, `htype=击飞`, branch `break`) on `cbsatm` parent frame 736 against P2 `bdmn`. The current native probe records a real `hit_contact` for `cbsatm` on frame 736 and the P2 transition from guard to 击飞, HP 1000→550.

The source and native AABBs are close but not exact: attack x-min/max differ by 0.05 px and receiver x-min differs by 0.05 px; y bounds match. The exact deltas are in `cbs-guard-comparison-r01.json`; this is a bounded contact/break match with unresolved geometry difference, not pixel-exact bounds parity.
