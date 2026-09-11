# Renji overlap source captures: upI

本目录保存 immutable Flash source capture、同输入 Godot native 输出与逐 tick comparator；未覆盖或改写既有红证据。

- Source run: `sasuke-you-renji-up-special-overlap-start20-original-r01`; frames after READY: `300`
- Explicit setup: p1=佐助 x=300 energy=300, p2=恋次 x=350 energy=300, p1 helper=鼬, p2 helper=魂; summon ticks 10..13
- Fixture SHA-256: `5c404cc179562565c91499458671706af6302645ad10b5b6da1ebeebff5e3512`
- Source raw event SHA-256 (uncompressed): `e2ffadb38593f0dc4a8e4d775a2031b4bb4170a71fb83be7cc1f3d323d7fb8bf`; retained gzip SHA-256: `166374f0653e47ff6daed9f416264b631d87546ab498eda481ca486a59e3eba6`
- Source original log retained gzip SHA-256: `cf89aefb589fa3ee53cce8f6c79f9b58a95822da28158a28c95e85e4c87fc38d`
- Source build SHA-256: `45d14830edee4212b9058ec5ad8f6b66df7378d25a94822f472950ed7b4e3e2f`; summary SHA-256: `1a3117ef5f460cb11923298462da760a7d791cbb398be545a12662cd695cfcb4`
- Native SHA-256: `2fba5f560fb2195609edfaaac68c68ccf18c0c0908210501dd32ce239eb28434`; native helper SHA-256: `ec934235a6e27d1b2b4adab8193e98cff055ea10ac630964ee65ebfb6a4e430f`
- Comparator: fighter `different` (602/602); helper `different` (602/602); result: different; fighter first diff tick63 p2 source frame969/native627; helper first diff tick29 p1 source frame15/native14.

## Rebuild and compare

Source capture was already completed by the authorized Flash capture agent; these files are copied byte-for-byte from the immutable run. Native replay used:

```text
/tmp/godot-4.7.2/Godot.app/Contents/MacOS/Godot --headless --path godot --log-file <native>/engine.log -s res://tests/move_case_reference.gd --quit-after 1400 -- <fixture> <native>/native.json
python3 tools/probes/compare_mode_reference.py <source>/collected/events.jsonl <native>/native.json --output fighter-compare.json
python3 tools/probes/compare_helper_reference.py <source>/collected/events.jsonl <native>/native.json.helpers.json --output helper-compare.json
```

Source input/build hashes are preserved in `source-build.json`; raw event and original-player log hashes are preserved in `source-summary.json`.
