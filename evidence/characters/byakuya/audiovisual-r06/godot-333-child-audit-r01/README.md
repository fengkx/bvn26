# Byakuya source-frame 333 child and visual audit

This is a bounded, same-fixture observation for base-form Byakuya: P1 白哉, P2 一护, helpers 魂/魂, stage 现世, source target frame 333. It does not claim full visual parity.

The Godot probe recursively walks the live `FighterRuntime` `TimelinePreview` display list and records each child local frame. It does not copy the root frame into child fields. The source side uses the recursive-freeze `capture-state.txt` leaf rows at display tick 448. `bdmn`, `jiao`, and `mian` are frame 1 on both sides. Source `AImain` reports frame 0 because the human branch calls `AImain.gotoAndStop(1)` then `AImain.unloadMovie()`; Godot retains an empty frame-1 symbol. Neither side has visible AImain descendants in this fixture, so this is recorded as an empty-controller representation difference.

The screenshot crop is a direct 1200x800 Flash stage crop resized to 600x400, with only window chrome removed. The scene and fighters are broadly aligned and the ranged sword presentation is visible in both. The Flash timer is 60 versus Godot 59, and the energy bar styling differs; these remain visual acceptance gaps.

Reproduce:

```sh
/private/tmp/godot-4.7.2/Godot.app/Contents/MacOS/Godot --headless --path godot -s res://tests/byakuya_visual_child_probe.gd -- 333 /private/tmp/byakuya-child333-r01
```
