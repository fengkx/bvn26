# Frozen launch-scope proposal

Inspected: 2026-09-22. Q12 requires all currently enabled content in the first
playable online release. This is a static inventory, not rollback acceptance.

## Enabled content

The menu intersects [available.json](../../godot/generated/main/character_selection/available.json)
with its actual cards, as implemented in
[character_selection.gd](../../godot/character_selection.gd). Current intersection:

- 11 fighters: 日番谷, 恋次, 露其雅, 一护, 鸣人, 樱, 佐助, 卡卡西, 白哉, 小李, 石田.
- 4 helpers: 鼬 (`you`), 魂 (`kon`), 我爱罗 (`woailuo`), 松本 (`jinye`).
- 10 stage IDs: 现世, 流魂街, 双极, 静涎亭, 尸魂界通道, 温泉, 火影瀑布, 楼顶,
  宇智波村, 木叶村.

Stage cards come from
[map presentation](../../godot/generated/main/map_selection/presentation.json)
and resolve in the [stage catalog](../../godot/generated/stages/catalog/catalog.json).
Protocol IDs must retain the stable identifiers; display aliases such as
`火影瀑布` / `终结之谷` and `宇智波村` / `宇智波一族` are not interchangeable IDs.

All 11 current fighter configurations have `form_frame: 1`. Main initialization
and reselection set `disabled_actions = ["万解"]` in
[main.gd](../../godot/main.gd); action/source/AI entry points enforce that gate in
[fighter_runtime.gd](../../godot/fighter_runtime.gd). Existing closed transformations
stay closed. Generated data for another form is not permission to expose it.

The latest [roster evidence](../../evidence/characters/roster-2026-09-22/README.md)
keeps original parity partial. Networking acceptance cannot upgrade that status.

## Build-time manifest proposal

Freeze the menu-derived IDs, resource mappings, enabled form frames and action
gates, together with exact runtime/content hashes, Godot version, simulation rate,
network protocol and complete-state schema versions. Hash simulation-affecting
generated data and runtime scripts, not merely the visible roster list.

The build must verify that online content equals this agreed local enabled set.
Any existing entry that fails rollback tests blocks release rather than being
silently removed. Audit newly enabled content through an explicit manifest diff;
the phrase "currently enabled" must not become a moving, unreviewable target.

Preserve separate fields for enabled content and validation evidence. Validate
the same manifest that is bundled with the Web build; reject mismatched peers
before ready/start. Fingerprints detect incompatibility, not malicious clients.

Coverage should exercise every character's enabled actions, each helper's
lifecycle, all stages and known interactions: simultaneous hits, pauses/supers,
spawns/removals, round end and timer behavior. Measure what pairings are covered;
do not equate testing each fighter once with testing all cross-interactions.
