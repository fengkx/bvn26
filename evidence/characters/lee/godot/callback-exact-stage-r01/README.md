# Lee frame 738 rooftop callback

This is a bounded same-input callback comparison for Lee's naturally reached
frame 738 on the original `楼顶` stage. The source run is
`lee-callback-738-rooftop-walkoff-r04`; its build configuration selects `楼顶`,
and `stage-build-overlay.diff` records the temporary source-build stage overlay.
The source fixture itself is unchanged. `lee-callback-738-rooftop-walkoff-r04.godot-fixture.json`
adds that stage to the native replay. The stage preflight records the selected
catalog directory and tick-zero fighter positions.

Run the exact callback probe with the paired fixture:

```sh
"$GODOT" --headless --path godot \
  --script tests/lee_callback_exact_probe.gd -- \
  "$PWD/evidence/characters/lee/godot/callback-exact-stage-r01/lee-callback-738-rooftop-walkoff-r04.native-fixture-r02.json" \
  "$PWD/evidence/characters/lee/godot/callback-exact-stage-r01/out/lee-callback-738-rooftop-walkoff-r04-r02.json" \
  > evidence/characters/lee/godot/callback-exact-stage-r01/engine-r02.log 2>&1
python3 evidence/characters/lee/godot/callback-exact-stage-r01/compare_738.py
```

`comparison-r01.json` binds the source raw/build/fixture/instrumentation hashes,
the native fixture/output/log hashes, and the runtime/probe hashes. The two
source body markers at frame 738 match the two native callbacks in
`source_frame`, `entering`, decoded `action`, and decoded `ql`; native exit also
reports `current_frame=723`, matching the source exit marker. The source clock
is fight tick 109 and the native probe reports fixture tick 110; no clock mapping
was established here, so timing is not compared. The evidence does not establish
full-state, stage-visual, or complete Lee parity.

The first attempt (`engine.log`, `out/…-r04.json`) used the source manifest's
`callback_targets` property, while the exact probe consumes
`source_callback_targets`; it therefore observed no target callbacks. That
attempt is preserved and excluded. The corrected fixture and successful run are
the `r02` artifacts.
