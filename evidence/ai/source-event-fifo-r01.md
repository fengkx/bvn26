# Source frame event FIFO regression r01

This record covers the shared source-event change used by the six generated
base-form fighters. A root `DoAction` body warp and `_root.shine()` are emitted
as ordered `frame_calls`; the runtime consumes them from the pending source
frame rather than looking up the action's current playhead after a same-frame
controller `goto`. Controller gotos remain immediate. The source order used
for Kakashi frame 961 is warp line 1, then shine line 12, followed by the child
callback's goto to frame 983.

## Inputs and implementation hashes

- Source timeline: `scripts/fighter/Kakashi.json`, `DefineSprite_710`, frame
  961; source SWF SHA256 is retained in `evidence/combat/kakashi-source-audit.json`.
- Runtime `godot/fighter_runtime.gd`:
  `5f7a9172d05ad2015842177665caebd133838721b83c76fd8a977bf593dc4066`.
- Compiler `tools/importer/compile_ai_context.py`:
  `d3cb0bd74fafb9bb2236946d8141c6476f30f69192da981d2094040a8ff2dc17`.
- All six `godot/generated/fighters/*/ai.json` files were rebuilt after the
  compiler change; the generated hashes are retained by the worktree manifest
  update owner.

## Replays

All commands used `/tmp/godot-4.7.2/Godot.app/Contents/MacOS/Godot --headless`
and wrote reports under `/tmp/kakashi-regressions`.

| Input | Result |
| --- | --- |
| Kakashi super fixture, `kakashi-863-super-down-special.json`, 1100 frames | `/tmp/kakashi-regressions/kakashi-super-dedup.json` vs original: 2202/2202, `matched`, zero differences |
| Renji `renji-245-skill1-held`, original 360-frame capture | 722/722, `matched`, zero differences; includes frame 946 placement boundary |
| `evidence/ai/input-binary-r13/events.jsonl` | 897 frame comparisons, 12 polls, random and clock tapes complete, `segment_observed_fields_match` |
| `evidence/ai/input-binary-r14/events.jsonl` | 867 frame comparisons, 10 polls, random and clock tapes complete, `segment_observed_fields_match` |
| `evidence/ai/match-flow-r15/events.jsonl` | 6281 frame comparisons, 11 polls, random and clock tapes complete, `segment_observed_fields_match`; 6000 fight ticks and teardown covered |

The r13/r14/r15 runs used `godot/tests/intro_continuous_reference.gd` in
`combat` mode and did not alter the retained original events or tapes.

## Shared regressions

`tools/test_shared_modes.py` matched both PVP and training at 602 actor states.
The repeated Hitsugaya ice placement smoke passed all three same-instance casts
and both facings. The projectile-source, player-controller, Kon helper, Sasuke
trace, and Kakashi projectile semantic smokes all exited successfully with no
SCRIPT ERROR. `source_flash_dedup_smoke.gd` observed one runtime flash per
execution of Kakashi frame 961, equal to the one authored root `shine()` in
`frame_calls`. The same `FighterRuntime` repeated that source frame twice and
observed exactly two flashes; the companion Minren frame 881 case retained
both same-frame source lines (two flashes) rather than collapsing them by path
or color.
