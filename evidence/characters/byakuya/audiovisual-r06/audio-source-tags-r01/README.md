# Byakuya source StartSoundTag capture r01

This artifact captures the four `StartSoundTag` markers in `DefineSprite_631` with a source-built AI reference runner and the same recovery fixture used by the existing Godot audio walk. The fixture is P1 Ichigo / P2 Byakuya, both helpers Kon; P1 special is held at fight ticks 10–13 and P2 dash at 62–66. The canonical probe output hash before tag insertion was `c0c6ec2799d69ed0c735dd379fe1b6d339e58c8bf0b397f7a8fa618730afcbb1`; the tagged SWF is `91b5353f886d43ed87972a530dd75fd1e1048c459867f12c36ff1b1cb663de0a`. Its build retained the `_root.aiKeyDown` fixture adapter.

`original-events.jsonl` is the complete run-filtered AIREF capture. It reaches frame 887 / sound 581, frame 934 / sound 44, and frame 944 / sound 52. P2 key read 66 is true at fight tick 63, tying the latter recovery path to the fixture's real N3 input window. It also sees the 963 / sound 619 tag in the pre-ready intro. The same resource IDs are present in the existing Godot recovery and intro `player_created` rows referenced by `source-tag-observations.json`.

This proves source tag arrival and resource linkage for these bounded runs. It does not prove audible output or full sound-stop/waveform parity. Tag markers execute immediately after source `StartSoundTag`; their event tick can precede the next sampled state row by one tick.

The `rejected-r02-input-adapter-removed/` subdirectory preserves a prior raw attempt. It is explicitly excluded: replacing the canonical Byakuya probe SWF removed the fixture key adapter, so the scheduled N3 was never read as held and the run did not reach the 934/944 recovery states. Its raw rows are retained to make that boundary auditable.
