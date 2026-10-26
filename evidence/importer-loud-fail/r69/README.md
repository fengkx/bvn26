# r69 — bounded integer-consumption extent clears old and fresh native controls

One common geometry construction uses `padding=floor(kernel/2)+1`, origin `left-padding`, and inclusive far extent `width+2*padding+1`. It depends only on geometry/kernel, with no per-kernel table or RGB-selected path. The unchanged scalar/long byte arithmetic is retained.

| Gate | Exact RGBA pixels |
|---|---:|
| All prior implicit controls, r62+r66+r68 | **85120/85120** |
| Fresh declared explicit model | **30720/30720** |
| Fresh implicit vs explicit filtered | **30720/30720** |
| Fresh implicit vs explicit final | **30720/30720** |

The192 fresh controls change source fill alpha from80% to53%, and cover kernels0,0.5,1,1.5,1.99609375,2,2.00390625,2.5,3.5,4,4.5,8; widths5,9,17,33; origins40/41; opacity100/50. Retained blurX, public rectangle, actual explicit bitmap extent and placement are read back. Paired transparent/black rows retain the real pre-transform bytes.

`bounded_native_controls_passed=true`, **`production_admitted=false`**. This is bounded behavioral parity for integer destination origins and a single Glow pass, not proof of executed allocator instructions, general clipping/affine behavior, or production eligibility. Fractional origins/widths and invalid inputs explicitly reject rather than being truncated by the diagnostic. Old rejected ceil and fixed-border fixtures remain unchanged and tested.

## Reproduce

```sh
python3 tools/probes/build_flash_filter_probe.py --case filter-integer-extent \
  --output /tmp/bvn-r69/native --ffdec /path/to/ffdec-cli.jar
python3 tools/probes/capture_native_player.py /tmp/bvn-r69/native /tmp/bvn-r69/native/native.log \
  --player-app '/path/to/Flash Player.app' --allow-window-activation --timeout 45
python3 -m tools.probes.analyze_integer_filter_extent \
  --native evidence/importer-loud-fail/r69/native --output /tmp/bvn-r69/analysis
python3 -m unittest tools.tests.test_integer_filter_extent
```

[Analysis](analysis.json), [provenance](provenance.json), [capture](native/native.log), [acceptance](acceptance.json). Exit0 means this bounded native/CPU gate only. No new GPU render or production code change. No tolerance, allowlist or reference rewrite.

Next port this exact construction into actual diagnostic FilterGroup allocation, preserving input bytes, filter order and all old GPU gates. Independently test destination clipping and fractional positions before widening eligibility; do not globally enable from the bounded pass. Components remain historical9/54; full AS/clip-action ownership and other visual gates remain open. Full roster/Web export and unchanged graphical suites were not rerun; pinned exact regressions remain in Python. Draft only; no merge/deploy/Worker.
