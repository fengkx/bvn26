# Stage import progress

Status (synchronized 2026-09-08): all ten source stages imported; map selection and stage replacement are wired in main.gd. Full original-player comparison remains pending.

The current request prioritizes the remaining maps, skips character selection, and
allows a map-selection step. The initial import preserved the fighters; subsequent runtime integration now selects catalog stages and configures their platforms.

## Rebuild

```sh
python3 tools/importer/build_stage_catalog.py --workspace /tmp/main-pinned
python3 -m unittest tools.tests.test_stage_catalog
```

The workspace must be a pinned JPEXS export of `game/main.swf`. Its export report
source hash is checked before conversion. Output: `godot/generated/stages/catalog/`.

DefineSprite 1738 source labels resolve to frames 2, 4, 5, 6, 7, 15, 16, 17, 18,
and 19. All ten maps retain their source display lists, nested definitions,
placement matrices, depth order, spawn markers and referenced bitmap assets.
The manifest supplies names and music filenames. No coordinates were invented.

Source gate and native selection evidence are recorded in `map-selection/README.md`.
The selector is integrated; full stage behavior parity remains pending.

Validation: all ten source labels and p1/p2 markers checked; every materialized
asset hash checked; `tools/verify.py` and `tools/check_handoff.py` passed.
Actual effort: approximately 0.01 person-days for this import and static validation.

Selector integration and native input evidence: [map-selection/README.md](map-selection/README.md).
