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
must be an absolute file path. Color rendering asserts the exact Glow subset and emits all measurements;
the full comparator remains mandatory and currently exits 1 for real differences.

The comparator rejects incomplete, mixed, reordered or duplicate native cases,
and mismatched sample counts. It exits 1 for **any** differing channel. Flash
getPixel32 returns straight ARGB while the Godot viewport returns premultiplied
RGBA: r03 additionally draws the native result onto opaque black to read RGB
directly, retaining alpha from the transparent capture. Reconstructing RGB from
straight ARGB loses bits and is rejected. No one-level error is forgiven.
Blur tests compare alpha directly, without color conversion or tolerance.

References are retained under evidence/importer-loud-fail, including raw traces,
build hashes and capture metadata. Do not replace them with Godot output.

## Color/order and cached-raster diagnostics

Build and capture `colors`, `color-order`, or `color-raster` using the same
builder/capture commands above. Other `color-*` programs preserve coefficient,
offset and opacity experiments; they are diagnostic measurements, not parity
assertions. The canonical ColorMatrix is taken from the locked source.

```sh
"$GODOT" --path godot --rendering-method gl_compatibility \
  --script res://tests/flash_filter_colors_render.gd -- "$PROBE_OUTPUT/colors.json"
python3 tools/probes/compare_flash_filters.py --kind color \
  --native-log "$PROBE_OUTPUT/colors/native.log" \
  --godot-rows "$PROBE_OUTPUT/colors.json" --output "$PROBE_OUTPUT/colors-comparison.json"
"$GODOT" --path godot --rendering-method gl_compatibility \
  --script res://tests/flash_filter_colors_render.gd -- "$PROBE_OUTPUT/order.json" \
  "$PWD/tools/probes/flash_filters/color-matrix.json" order
python3 tools/probes/compare_flash_filters.py --kind color-order \
  --native-log "$PROBE_OUTPUT/color-order/native.log" \
  --godot-rows "$PROBE_OUTPUT/order.json" --output "$PROBE_OUTPUT/order-comparison.json"
"$GODOT" --path godot --rendering-method gl_compatibility \
  --script res://tests/flash_filter_raster_render.gd
```

Both full color comparators currently exit 1. GPU assertions cover only the two
canonical Glow groups, two Matrix-with-CXFORM groups, and 36 cached-raster cases.
The remaining differences are recorded in evidence/importer-loud-fail/r03.

## Real shipped filter/cache placements

Use a fresh absolute output directory. Python requires Pillow for image checks.
The raw-tag harness is reused from the prior placement review; no locked source
file is changed. Native capture activates Flash windows.

```sh
export BVN_REVIEW_DIR="$PROBE_OUTPUT/components-review"
export BVN_FLASH_APP="$FLASH_APP" BVN_GODOT="$GODOT"
python3 tools/probes/build_filter_components.py --ffdec "$FFDEC" --output "$BVN_REVIEW_DIR"
python3 evidence/characters/pain/visual-parity/review/probes/capture_components.py
python3 evidence/characters/pain/visual-parity/review/probes/render_components.py
python3 tools/probes/compare_filter_components.py --output "$BVN_REVIEW_DIR"
```

The strict component comparator validates image coverage and exits 1 for any
pixel or clock difference. r03 captures 21 placements, 54 images and 4,242 clock
samples. Only 9 images are exact; successful capture is not parity acceptance.

Reproduce the unchanged native gameplay trace comparisons separately:

```sh
python3 tools/test_importer_roster.py --godot "$GODOT" --output "$PROBE_OUTPUT/roster"
```

## Scalar ColorMatrix arithmetic

`color-arithmetic` isolates each RGB coefficient and complete row of the shipped
matrix at opaque and 80% fill alpha. Pair it with
`godot/tests/flash_filter_arithmetic_render.gd` (one absolute output JSON argument)
and `tools/probes/compare_flash_color_arithmetic.py --native-log LOG
--godot-rows JSON --output REPORT`. The strict comparator currently fails:
20/24 cases and 92/96 channels are exact. The render script only measures; its
successful exit does not assert parity. Reproduction commands and the four
remaining scalar differences are in `evidence/importer-loud-fail/r11/pixels/README.md`.
