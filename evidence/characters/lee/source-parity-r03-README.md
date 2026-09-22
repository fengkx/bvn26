# Lee source parity r03

This batch is evidence-only and uses the frozen runtime/generated outputs. Each case uses the Lee fixture manifest, source build, normalized Flash trace, Godot native trace, and exact 14-field comparator output. Helpers are explicit: P1 `我爱罗`, P2 `魂`; source character IDs are `小李` and `一护`.

Reproduce the native batch:

```sh
/private/tmp/godot-4.7.2/Godot.app/Contents/MacOS/Godot --headless --path godot -s res://tests/move_case_reference.gd -- --batch /private/tmp/lee-acceptance-r03-case-paths.json evidence/characters/lee/godot/acceptance-r03
```

Reproduce one comparator:

```sh
python3 tools/probes/compare_mode_reference.py \
  evidence/characters/lee/original/lee-157-nornalhit-mirror-acceptance-r03/events.jsonl/events.jsonl \
  evidence/characters/lee/godot/acceptance-r03/lee-157-nornalhit-mirror.json \
  --source-build evidence/characters/lee/original/lee-157-nornalhit-mirror-acceptance-r03/build.json \
  --output /tmp/lee-r03-compare.json
```

The exact fixture, build, raw normalized events, compare, and SHA-256 links are recorded in `source-parity-manifest-r03.json`. Current matrix classification is separate from historical r02 failures in `matrix-source-classification-r04.json`; the 60 r02 failures are history only.
