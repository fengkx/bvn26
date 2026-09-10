# You helper callback order r11

This evidence covers the source nested `enterFrame` callback for the You helper
(`you.swf` / display name `鼬`). It is limited to Sasuke base plus the helper;
Sasuke alternate forms are outside this run.

## Source anchors

- `game/fighter/fz/you.swf`, SHA-256 `a00ed19723373b43b347f802a13c822eae21662d2a85b38336fdba9eb641f604`
- `scripts/fighter/fz/you.json`, SHA-256 `6f2b9c27fa900866d91fb1dced55c7d8efb73c7b250e60413032ecf98d92f9ca`
- `scripts/fighter/fz/you.json` frame 24 calls `_root.bsd(pn,"XG_fzbs",true)`; frames 65 and 125 call `_root.bsw(pn)`.
- `frame_48/PlaceObject2_24_3/CLIPACTIONRECORD onClipEvent(enterFrame).as` tests `hitTest` against `bdmn` and calls `_parent.gotoAndPlay("攻击2")`.
- `data/slices/you-helper.timeline.json` records the placement and source SWF hash; frame 92 contains the explicit opponent-X position event.

## Same-input observations

Original capture: `/tmp/bvn-sasuke-you-probe-r03/collected.json/events.jsonl`,
fixture `evidence/characters/sasuke-you/you-helper-production-fixture-r03.json`.
The original trace places the nested clip at tick 62/frame 48, dispatches its
callback on the next tick (tick 63/frame 92), then reaches frame 124 at tick 95
and frame 125 at tick 96 while the helper pause is active. The production helper
rows in `sasuke-you-production-r03.helpers.json` contain the same observations.

Production replay and comparison:

```text
/tmp/godot-4.7.2/Godot.app/Contents/MacOS/Godot --headless --path godot -s res://tests/move_case_reference.gd -- /tmp/sasuke-cases-r01/sasuke-775-zhaoHuan-neutral-you-240.json /tmp/sasuke-prod-you-r11.json
python3 tools/probes/compare_mode_reference.py /tmp/bvn-sasuke-you-probe-r03/collected.json/events.jsonl /tmp/sasuke-prod-you-r11.json --output /tmp/sasuke-you-compare-r11.json
```

Result: `matched`, source/native 482 fighter state rows each. The comparator
keeps the real source `touchFloor` values and does not normalize them.

The `r03` capture is the immutable original-player capture reused by r11;
r11 is a new production replay against that capture. Around the callback and
pause boundary, the source and production rows are identical:

| fight tick | slot | source frame | source paused | production frame | production paused |
| ---: | :--- | ---: | :--- | ---: | :--- |
| 94 | p1 | 5 | true | 5 | true |
| 95 | p1 | 6 | true | 6 | true |
| 96 | p1 | 7 | false | 7 | false |
| 97 | p1 | 1 | false | 1 | false |
| 98 | p1 | 2 | false | 2 | false |
| 99 | p1 | 3 | false | 3 | false |
| 100 | p1 | 4 | false | 4 | false |

The earlier r08/r09 native pause-to-100 observation was a pre-fix production
diagnostic, not the immutable r03 source observation; it is superseded by r11
after registry phase correction. No expected output or pause threshold was
changed.

## Runtime rule

`godot/source_callback_registry.gd` exposes the shared dispatch phase. Helper
placements registered before dispatch use the next display tick; a callback
registered during dispatch uses the current tick and is excluded from the
current pending snapshot. `godot/helper_runtime.gd` registers callbacks by
placement generation and keeps the registration while the same MOVE generation
is retained; replacement or removal, deactivate, repeated activate, and unbind
unregister it. The focused lifecycle test asserts registry sizes through those
transitions, including registry clear followed by a new tick-0 placement.

Focused checks:

```text
YOU_HELPER_LIFECYCLE_OK rows=198 effects=2
HELPER_REPEAT_CONTACT_SMOKE_OK
KON_HELPER_SMOKE_OK
YOU_HELPER_CALLBACK_ORDER_OK frame48_wait=1 frame92_dispatch=2
SASUKE_YOU_NATIVE_OK
```
