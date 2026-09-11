# Renji overlap source captures: upU

本目录保存 immutable Flash source capture、同输入 Godot native 输出与逐 tick comparator；未覆盖或改写既有红证据。

- Source run: `sasuke-you-renji-up-ranged-overlap-start20-original-r01`; frames after READY: `300`
- Explicit setup: p1=佐助 x=300 energy=300, p2=恋次 x=350 energy=300, p1 helper=鼬, p2 helper=魂; summon ticks 10..13
- Fixture SHA-256: `de7e08bd37b3e51b885703639206edada237fc59c7ec2e0f0ecfa6ae6d3cfc62`
- Source raw event SHA-256 (uncompressed): `1b709362666ca954a9ca1bb9cc33843f9f0fb9ab90b3dd4135a436e19540bc04`; retained gzip SHA-256: `ed7029f234bc0736407ceb5ca41285c23fe796d3fe4ac292714018c8e5edd3bf`
- Source original log retained gzip SHA-256: `7788986d7d55acf851ad825da2caeb2c716906db0a016c679d371ed1ba0595e9`
- Source build SHA-256: `a4be94bf9e701fd8f0a74e96a662a3cfdeaf0a470557d4b0639b63e32e02b5c2`; summary SHA-256: `61829d7b6a99f4a7ac7d1989e316948953b4fd7d33e6d156720da5e0e960b5f8`
- Native SHA-256: `3895d030aa3c2b3a8bd89f4c48db26a9974c59d9f484bb3790471955a81c8536`; native helper SHA-256: `a4c5e116ec98361e9a2f5babfead9de5ac43c23798beba540520c9bceee1db52`
- Comparator: fighter `matched` (602/602); helper `matched` (602/602); result: matched; fighter/helper 602/602, zero differences.

## Rebuild and compare

Source capture was already completed by the authorized Flash capture agent; these files are copied byte-for-byte from the immutable run. Native replay used:

```text
/tmp/godot-4.7.2/Godot.app/Contents/MacOS/Godot --headless --path godot --log-file <native>/engine.log -s res://tests/move_case_reference.gd --quit-after 1400 -- <fixture> <native>/native.json
python3 tools/probes/compare_mode_reference.py <source>/collected/events.jsonl <native>/native.json --output fighter-compare.json
python3 tools/probes/compare_helper_reference.py <source>/collected/events.jsonl <native>/native.json.helpers.json --output helper-compare.json
```

Source input/build hashes are preserved in `source-build.json`; raw event and original-player log hashes are preserved in `source-summary.json`.
