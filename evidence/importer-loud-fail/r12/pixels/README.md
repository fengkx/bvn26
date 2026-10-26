# r12 ColorMatrix arithmetic ramps

This track adds native arithmetic evidence, not a production rendering fix.
No renderer/shader, tolerance, oracle baseline or allowlist was changed.

`tools/probes/flash_filters/color-arithmetic-ramp.as` varies one source color
channel through all 256 byte values in four matrix configurations, with opaque
and 80% fill alpha: **2,048 native cases**, emitted as eight transparent/black
row pairs plus completion (**17 events**). Fresh clips and BitmapData instances
isolate every sample. The mixed row and coefficients come from the same shipped
XG_mfdjx matrix as r11; this fixture has no playback or gameplay transitions.

Native Flash Player Debugger 32.0.0.465/Rosetta completed the capture. The build
and capture metadata are in `color-arithmetic-ramp/`; raw native traces are
preserved. No Godot parity is claimed for these new ramp samples.

`tools/probes/analyze_flash_color_ramp.py` checks completeness, identity, alpha
and opaque-black RGB coverage, then compares the opaque red outputs to an ideal
float affine calculation with nearest rounding. **86/1,024 opaque red outputs
differ**: mixed RGB row 82, isolated negative coefficient 2, isolated green
coefficient 0, isolated small positive coefficient 2. This is a diagnostic model
comparison, not a substitute for the Godot/native pixel gate.

Assuming a nearest-rounded affine model for each isolated coefficient, the
negative ramp bounds its effective coefficient to approximately
[-0.59473684,-0.59469697], excluding source -0.5946631. The small positive ramp's
interval begins at 0.1015625, excluding source 0.10156211. These conditional
intervals do **not** prove a fixed-point format or a rounding algorithm. The
mixed row additionally has accumulated differences that a blanket floor or
one-level subtraction cannot justify. No speculative coefficient quantization
was installed in production.

Two analysis/coverage regression tests pass. Existing r11 scalar 20/24, canonical
colors 3/5, order 2/4 and shipped components 9/54 remain open; they were not newly
captured here. Lead acceptance reruns the existing GPU gates separately.

## Reproduction

Use fresh absolute output paths and the same FFDEC/Flash environment:

```sh
python3 tools/probes/build_flash_filter_probe.py --case color-arithmetic-ramp \
  --ffdec "$FFDEC" --output "$OUTPUT/native"
python3 tools/probes/capture_native_player.py "$OUTPUT/native" \
  "$OUTPUT/native/native.log" --player-app "$FLASH_APP" \
  --allow-window-activation --timeout 40
python3 tools/probes/analyze_flash_color_ramp.py \
  --native-log "$OUTPUT/native/native.log" --output "$OUTPUT/analysis.json"
python3 -m unittest tools.tests.test_color_ramp_analysis
```
