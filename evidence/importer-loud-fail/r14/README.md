# r14 — Minren full form graph and wrapper filter lifecycle

The specific `minren.swf:DefineSprite_764/frame_1379/DoAction.as:5` wrapper-transfer error is resolved by admitting the complete source-checked three-node graph. Cache acceptance is **25/26** (was24/26). The Web manifest now reaches the intentional **Yihu638/frame1052 wankai** error; the PR remains Draft. No new allowlist or pixel tolerance, no Worker/production/master change.

## What executes

- Base764 → parent2/body1293 → parent3/body1821, with complete visual/combat/controller/BODY/audio dependencies. Existing generic frame consumers execute both player-slot HP/energy transfers, captured health functions, independent root interval IDs, wrapper state and source initialization. The actual1379/1380 assignments are retained as compiled operations; no catch or exception hides them.
- Source parent3 places an outer red Glow (7×10, passes3, strength1.1367188). The original body's first frame calls `resColor`, which assigns `_this.filters=[]`. Native observations show filter length0 after initialization. Extraction now retains wrapper filters, rendering has the existing filter-group consumer, and the compiled source-checked initial clear executes before first display. Runtime resColor also clears authored filters; that state participates in full rollback.
- Conditional or modified filter-reset initialization is rejected. The initialization proof now requires the original sequence to be at top level, not merely a substring inside a condition. Cached source wrapper filters must match exactly; deleting the wrapper or changing/dropping its filters remains an error with source frame/depth.

See [source-first five questions](source-first.md). Two fresh native Flash slot probes each produce9 state observations plus completion: HP/energy671/234, replacement gap undefined, parent2/body892 and parent3/body981, initialized filters0. Godot both-slot/two-edge transfer, callback floor/pause/live references and complete rollback pass. This is bounded lifecycle/state evidence, not a claim of complete transformed combat or component image parity.

The wrapper rendering fixture compares two existing native Glow cases exactly: **1,280 channel samples**, no tolerance. Canonical ColorMatrix/order pixel differences remain outside this turn's scope. No new stability deviation; prior online simulation-clock policy remains unchanged.

## Acceptance and next blockers

Final counts: [acceptance-summary.json](acceptance-summary.json). Form test: `form.log`; real input six admitted graphs: `godot/form_input_activation_smoke.log`. GPU/standard/additional checks: `godot/results.json`. Python: `python-final.log`. Protected function: `protected.log`. All locked game/ and scripts/ bytes remain unchanged; reviewed covered-file hash updates are recorded separately.

The compiler/build snapshot test fixture also needed `__init__.py` after the previous staging fix; its copy list was corrected. No production staging guard was changed this turn.

Remaining: Yihu nested stage Y12/native versus17/runtime and its unadmitted form graph; Yulong cached wrapper filter omission; the prior34 source placement errors; unresolved exact pixels/full AS ownership. Shipped placement closures are95/96, including the two new Minren targets. This turn checks current closures against the pinned inventory rather than rescanning all62 source SWFs. It does not start those other workstreams.

## Reproduce

```sh
python3 tools/probes/build_minren_form_probe.py --slot 1 --ffdec "$FFDEC" --output "$OUT/native-slot1"
python3 tools/probes/capture_native_player.py "$OUT/native-slot1" "$OUT/native-slot1/native.log" --player-app "$FLASH_APP" --allow-window-activation --timeout 40
# Repeat with --slot 2 and a fresh output directory.
python3 tools/importer/prepare_form_graph.py --base godot/generated/fighters/minren --target 2=godot/generated/forms/minren-2 --target 3=godot/generated/forms/minren-3 --report "$OUT/graph.json"
"$GODOT" --headless --path godot --script res://tests/minren_form_replacement_reference.gd --log-file "$OUT/form-engine.log"
"$GODOT" --path godot --rendering-method gl_compatibility --script res://tests/flash_filter_colors_render.gd --log-file "$OUT/wrapper-engine.log" -- "$OUT/wrapper.json" "$PWD/tools/probes/flash_filters/color-matrix.json" wrapper
python3 tools/importer/audit_frame_calls.py --output "$OUT/frame-calls.json"
python3 tools/build_online_manifest.py --check
python3 -m unittest discover -s tools/tests
python3 tools/test_importer_roster.py --godot "$GODOT" --output "$OUT/roster"
```

Target3 staging uses `requirements.json` with stage_parent_forms.py;11/11 stages compiled,293assets. Build with build_form_profile.py, then prepare the whole graph. Parent2 was rebuilt from the source-bound r12 candidate with current compilers. Package hashes and source requirements are committed in the production manifest; no scratch path is required to execute production.
