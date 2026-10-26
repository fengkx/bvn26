# r11 exact color arithmetic diagnostic

No production renderer or shader changed in this track. The remaining differences
cannot be removed honestly by choosing a convenient floor/round operation.

The new packaged `tools/probes/flash_filters/color-arithmetic.as` isolates each
coefficient and each complete RGB row of the shipped XG_mfdjx ColorMatrix,
at opaque and 80% source fill alpha. Negative isolated coefficients use offset
128 to stay measurable; full rows use offset 9. It creates a fresh clip per case,
draws into transparent BitmapData, then onto opaque black to measure the actual
premultiplied RGB independently of getPixel32's unpremultiplication. There is no
timeline advancement or inherited placement state in this arithmetic fixture.
It is a diagnostic of the filter, not full shipped-component or gameplay parity.

Adobe Flash Player Debugger 32.0.0.465/Rosetta captured 24 cases plus the completion
event (25 events). `color-arithmetic/build.json` pins probe and JPEXS hashes;
`capture-environment.json` records the native application and launch. The native
executable and JPEXS match the previous reference environment. Godot 4.7.2
Compatibility captured the same 24 cases with
`godot/tests/flash_filter_arithmetic_render.gd`.

Strict result: **20/24 cases exact; 92/96 channels exact**. All four differences
are one red-channel level; `comparison.json` deliberately reports `passed:false`:

| Fill opacity | Matrix row | Component | Native RGBA | Godot RGBA |
|---|---|---|---|---|
| 100 | 0 | combined RGB | 111,127,170,255 | 112,127,170,255 |
| 80 | 0 | green only | 111,101,136,204 | 110,101,136,204 |
| 80 | 0 | combined RGB | 88,101,136,204 | 89,101,136,204 |
| 80 | 2 | red only | 16,101,136,204 | 17,101,136,204 |

The opposite signs in isolated and combined cases disprove a blanket one-level
subtraction. In the earlier order reference, opposite edges with alpha 40 also
have different transformed red channels, so quantizing solely from final alpha
cannot certify the native intermediate arithmetic. No conjectured rounding
patch, tolerance, replacement oracle, or additional allowlist was introduced.

The existing r03/r10 baseline remains unresolved: colors 3/5 exact (matrix100
64 differing channels, chain100 128), order 2/4 exact (one differing channel in
each Glow group), shipped components 9/54 exact with clocks 4242/4242 exact,
and r05 XG_rush 234/5103 differing channels, maximum error135. These are prior
measurements, not new r11 component captures. Lead acceptance reruns the canonical
GPU fixtures separately. This track adds information; it does not claim the
pixel blockers closed.

## Reproduction

Set absolute `FFDEC`, `FLASH_APP`, `GODOT`, and fresh `OUTPUT` paths:

```sh
python3 tools/probes/build_flash_filter_probe.py --case color-arithmetic \
  --ffdec "$FFDEC" --output "$OUTPUT/native"
python3 tools/probes/capture_native_player.py "$OUTPUT/native" \
  "$OUTPUT/native/native.log" --player-app "$FLASH_APP" \
  --allow-window-activation --timeout 40
"$GODOT" --path godot --rendering-method gl_compatibility \
  --log-file "$OUTPUT/godot-engine.log" \
  --script res://tests/flash_filter_arithmetic_render.gd -- "$OUTPUT/godot.json"
python3 tools/probes/compare_flash_color_arithmetic.py \
  --native-log "$OUTPUT/native/native.log" --godot-rows "$OUTPUT/godot.json" \
  --output "$OUTPUT/comparison.json"
python3 -m unittest tools.tests.test_color_arithmetic_comparison
```

The renderer's `MEASURED` marker only certifies capture. The comparator is the
parity gate and exits 1 for any differing channel. Its two regression tests
check one-level rejection, incomplete/reordered data, malformed channels, and
incomplete/duplicated native traces. Both tests passed.
