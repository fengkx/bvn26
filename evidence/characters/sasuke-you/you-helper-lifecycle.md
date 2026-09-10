# You helper lifecycle fixture

The helper is sourced from `game/fighter/fz/you.swf` and `scripts/fighter/fz/you.json`, materialized as runtime id `you` with display id `鼬`. Source root playback is frame 2 through frame 199; frame 1 parks the helper at the off-stage position.

The focused Godot trace in `godot/tests/you_helper_lifecycle.gd` activates the helper at `(300,-25)` and records every source frame. It checks the source action writes at frames 18, 61, and 181; named attack clip lifetimes `atm1` 48..59, `atm2` 128..129, 144..145, 160..161, and `atm3` 176..177; timeline sounds 54 at frame 92 and 63 at frames 127, 143, 159, and 175; and source effect events `XG_fzcc` at frames 2 and 76. The lifecycle ends by deactivating at frame 199 and returning to frame 1.

Command:

```sh
/tmp/godot-4.7.2/Godot.app/Contents/MacOS/Godot --headless --path godot -s res://tests/you_helper_lifecycle.gd -- /tmp/you-helper-lifecycle.json
```

Result: `YOU_HELPER_LIFECYCLE_OK rows=198 effects=2`. Retained trace: `you-helper-lifecycle.json`.

The original-player summon fixture is prepared at `you-helper-probe-fixture.json`; its capture remains pending the parent-controlled Flash sampling window. Build command and fixture are recorded in the handoff message.
