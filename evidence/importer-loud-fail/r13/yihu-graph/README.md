# Yihu full body graph diagnostic (r13)

The source controller compound assignment `_parent._parent._xscale *= -1` now compiles through the same numeric conversion and mapped-field write path as existing += and -=. No character-specific rule. Unknown expressions/targets still fail. Three Python tests cover the original callback, generic local multiplication and rejection.

Native Flash Debugger 32.0.0.465 / Rosetta, original definitions and placements unchanged, root-only instrumentation:

- `yihu3-flip`: original sprite1672 frame390 child callback, sensor hit explicitly stubbed true, body enterFrame no-op. Wrapper xscale75 becomes -75; original goto招12 enters frame399. 2 observations /3 events.
- `yihu2-helper`: original initial body's wankai. After call new body HP/ql undefined; next parent2/body872, HP671/ql234, key values101..110. Root Y17 becomes12. 5 observations /6events.
- `yihu3-helper`: original parent2 body's wankai. After call parent3/body1 and bodyHP/ql undefined; next parent3/body1004, HP671/ql234, rootY17, key values101..110. 3 observations /4events.

`godot/tests/yihu_form_graph_reference.gd` executes both actual source frame wankai calls (638/1052 and1180/1036), asset/profile swaps, live state reset, captured interval, and complete Battle checkpoint restore across each edge. Both BODY graph edges pass. The native parity check exits1 on the exact root-Y mismatch. This is **not full native parity**: first replacement's native rootY is12, runtime17. The root-only capture makes movie root coincide with fighter wrapper; in the actual main movie this is stage-root displacement, not fighter position.

Exact unconsumed source: sprite1027 frame1 `_root._y -= 5`, frame3 `_root._y += 5`, used by the parent2 intro. Source text and hashes are in source-actions.json. No tolerance, override, or allowlist is introduced. Keep publication blocked until this nested root effect is consumed and parity asserted.

Third-form staging passed all11 compiler/materializer stages,262assets; full isolated candidate `/tmp/bvn-loud-fail/r13/yihu3-profile` and refreshed second form `/tmp/bvn-loud-fail/r13/yihu2-profile` were supplied to the lead. Candidate compilation does not certify pixels or full behavior.

Reproduce native:
```sh
python3 tools/probes/build_yihu_third_form_probe.py --case flip --ffdec /path/to/ffdec-cli.jar --output /tmp/yihu-flip
python3 tools/probes/build_yihu_third_form_probe.py --case helper --ffdec /path/to/ffdec-cli.jar --output /tmp/yihu-helper
python3 tools/probes/capture_native_player.py /tmp/yihu-flip /tmp/yihu-flip/native.log --player-app '/path/to/Flash Player.app' --allow-window-activation --timeout 40
```
First helper uses `build_form_helper_probe.py --fighter yihu --observe-frames`.

Reproduce body diagnostic:
```sh
godot --headless --path godot --script res://tests/yihu_form_graph_reference.gd -- --candidate-root=/tmp/bvn-loud-fail/r13/yihu-candidates
python3 -m unittest discover -s tools/tests -p test_controller_compound_assignment.py
```

The two asset profiles were removed from production `godot/generated/forms` and retained only under the explicit candidate root above. This diagnostic requires staged candidate assets; Yihu is not published.

Rebuild base program fixtures (rather than commit generated copies):
```sh
python3 tools/probes/build_form_program_fixture.py --fighter yihu --output /tmp/new-candidates/yihu-1
```
The candidate root needs complete source-built yihu-2 and yihu-3 profiles beside yihu-1. Use `stage_parent_forms.py` and `build_form_profile.py` with the source-locked parent2/3 requirements. The r13 native observations remain the acceptance reference; importing the packages does not publish the graph.

Final reproduction used all three program/profile candidates outside the Godot project, with the newly generated base sound segments removed from production. Both BODY edges and full rollback still pass; the sole emitted error is the strict root-Y mismatch (exit1). No Yihu production asset changes are retained.
