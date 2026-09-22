# Byakuya source/Godot frame 576 child audit

This is a bounded display-list audit for the same explicit fixture: P1 白哉, P2 一护, helpers 魂/魂, stage 现世, target source frame 576 (上必杀). The Godot probe is `godot/tests/byakuya_visual_child_probe.gd` and was invoked with:

```sh
/private/tmp/godot-4.7.2/Godot.app/Contents/MacOS/Godot --headless --path godot -s res://tests/byakuya_visual_child_probe.gd -- 576 /private/tmp/byakuya-child576-r01
```

`child-map.json` records 30 live Godot display-list paths at capture tick 286. The native source capture contains 215 full-scene state paths; 67 are under `root.game.p1`, including repeated `_this` aliases from the AS2 wrapper chain. `audit.json` records the 21 direct `p1.mc` source entries and hashes.

This evidence confirms target/root/action/input alignment and records both child-clock observations. It does not claim child parity: source aliases must be mapped to compiled display-list instances before a path-by-path equivalence can be accepted. The existing Godot GUI artifacts remain in `../godot-576/`.
