# Sasuke base form and You helper source audit

This audit covers the requested base form only. Sasuke's `WKframe=2` clone
(`佐助咒怨`) and `sasukexz.swf` (`佐助须佐`) are recorded as deferred forms;
they are not included in this build.

## Source identity

| Content | Display id | Source SWF | Source bundle | Compiled output |
|---|---|---|---|---|
| Base fighter | `佐助` | `game/fighter/Sasuke.swf` (`c413d7c4d840d99deedc22778ee9a6383263b8ecd2e77a6c0712ca2a166c73f6`) | `scripts/fighter/Sasuke.json` | `godot/generated/fighters/sasuke/` |
| Helper | `鼬` | `game/fighter/fz/you.swf` (`a00ed19723373b43b347f802a13c822eae21662d2a85b38336fdba9eb641f604`) | `scripts/fighter/fz/you.json` | `godot/generated/helpers/you/` |

`scripts/main.json` loads the helper through `fzurl:"you.swf"` and
`_root.fzDir`; the helper directory id is therefore `you`, while its Chinese
runtime `helper_id` is `鼬`. The main fighter `itachi.swf` is a separate
selectable fighter and is not the helper source.

## SOURCE_FIRST five questions

1. **Per-frame scripts and callbacks.** Sasuke's base timeline is
   `DefineSprite_603`, 1232 frames. The extraction retains every source frame
   record in `data/slices/Sasuke-base.json`, including empty frames, and all
   frame scripts/callbacks in the selected ranges. Root initialization and
   hit parameters are from
   `DefineSprite_603/frame_1/DoAction.as`; movement constants are from
   `frame_1/PlaceObject2_603_1/CLIPACTIONRECORD onClipEvent(load).as`.
   The You helper root timeline has 199 frames; its root frame scripts are
   retained in `data/slices/you-helper.timeline.json` and indexed in
   `data/actions/you-helper.json`.
2. **PlaceObject versus MOVE.** The timeline compiler preserves `move` on
   every display-list delta and records `placed_frame`. Sasuke's body is the
   root placement `frame_1/PlaceObject2_603_1`; controller and receiver clip
   lifetimes are kept in the compiled frame lists. You starts from the empty
   root frame 1 and is placed as a new helper instance at source frame 2.
3. **Exit mechanism.** Sasuke's explicit exits are compiled in
   `data/actions/sasuke-base.json` under `action_exits`; the two source
   fallthroughs (`跳招` → `跳招2` and `必杀` → `必杀2`) are retained under
   `timeline_fallthroughs`. You's frame 1 parks the helper and its root end
   reaches frame 199 before runtime deactivation; presentation and nested stop
   events are source-indexed, not inferred from duration.
4. **Assertions.** Regression assertions must use source labels, exact frame
   spans, attack values, source display-list bounds and helper events. This
   slice does not add guessed offsets or per-character hitbox enlargement.
5. **Original-player replay.** The fixed-input helper source capture is retained
   in `native-probe-you-r03`; `sasuke-you-helper-compare-r16.json` matches its
   native replay on the six common helper fields for 482 rows. The source-only
   `hits`/`atm1`/`atm2`/`atm3` fields, full helper lifecycle matrix, and visual or
   audio parity remain outside that comparison and are still pending.

## Source-derived helper attacks

`you.json` defines `atm1` (damage 5, impact 4), `atm2` (damage 40, impact 11)
and `atm3` (damage 100, impact 11, vertical impulse 0, horizontal impulse -3).
The source presentation events include `XG_fzcc` at frames 2 and 76,
`bsd("XG_fzbs", true)` at frame 24, `bsw` at frames 65 and 125, and shine
events at frames 42, 128, 144, 160 and 176.

## Deferred shared registration

The shared character/menu catalog must register only the base `佐助` output and
helper `鼬` output for this task. The deferred forms remain out of the menu and
must not be silently mapped to the base timeline.
