# Native Flash filter fixtures

These isolated AVM1 programs are development oracles, never production runtime
inputs. Build with Python 3 and JPEXS 26.2.1; capture with Adobe Flash Player
Debugger 32.0.0.465. No paths to a particular developer's scratch directory are
embedded. `--output` holds all generated SWFs, imports and JPEXS configuration.

From the repository root, set `FFDEC`, `GODOT`, `FLASH_APP`, and `PROBE_OUTPUT`
to your local tool/output paths, then run (replace the case as needed):

```sh
python3 tools/probes/build_flash_filter_probe.py --case blur-small \
  --ffdec "$FFDEC" --output "$PROBE_OUTPUT/blur-small"
python3 tools/probes/capture_native_player.py "$PROBE_OUTPUT/blur-small" \
  "$PROBE_OUTPUT/blur-small/native.log" --player-app "$FLASH_APP" \
  --allow-window-activation --timeout 40
"$GODOT" --path godot --rendering-method gl_compatibility \
  --script res://tests/flash_filters_render.gd -- "$PROBE_OUTPUT/small.json" small
python3 tools/probes/compare_flash_filters.py --kind blur \
  --native-log "$PROBE_OUTPUT/blur-small/native.log" \
  --godot-rows "$PROBE_OUTPUT/small.json" --output "$PROBE_OUTPUT/small-comparison.json"
```

| Builder case | Godot test | Mode argument | Comparator kind | Cases |
|---|---|---|---|---|
| blur-large | flash_filters_render.gd | large | blur | 16 |
| blur-small | flash_filters_render.gd | small | blur | 16 |
| blur-bounds | flash_filters_render.gd | bounds | bounds | 210 |
| colors | flash_filter_colors_render.gd | omit | color | 5 |

The color test reads `color-matrix.json` from this directory by default. The
matrix is copied from the locked main SWF's XG_mfdjx filter (see source inventory
in evidence/importer-loud-fail/shipped-filters.json). A custom matrix argument
must be an absolute file path. Color rendering alone only emits measurements;
the comparator is mandatory and currently exits 1 for real differences.

The comparator rejects incomplete, mixed, reordered or duplicate native cases,
and mismatched sample counts. It exits 1 for **any** differing channel. Flash
getPixel32 returns straight ARGB while the Godot viewport returns premultiplied
RGBA: comparison converts the reference to the nearest 8-bit premultiplied
channel. This representation conversion does not forgive a one-level error.
Blur tests compare alpha directly, without color conversion or tolerance.

References are retained under evidence/importer-loud-fail, including raw traces,
build hashes and capture metadata. Do not replace them with Godot output.
