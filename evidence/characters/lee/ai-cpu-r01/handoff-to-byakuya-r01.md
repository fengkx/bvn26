# Lee AI single-dispatch probe handoff

Use `godot/tests/lee_ai_single_dispatch_probe.gd` as the data-driven callback probe. It creates a production `FighterRuntime` for Lee and a Yihu opponent, configures `AiControllerHost`, calls `synchronize(0)`, dispatches `paths_by_descending_depth()`, then runs `run_frame_actions()`. The probe requires `use_ai=true`, records the source readset values and source context sequence, and fails closed unless the observed Godot action is `瞬步` at source frame 20.

The two source-derived cases are in the `CASES` constant. Formal output is `/tmp/lee-ai-single-dispatch-formal.json`; the retained accepted evidence is `godot-single-dispatch-formal-r01.json`. Each case records source context sequence, source observed goto sequence/frame, Godot action/frame, hook count, registered instances, predicate/goto results, and `use_ai`.

For reuse, replace only the case data and source fixture path while retaining the host setup and fail-closed `matched` predicate. Do not populate predicate values from synthetic branch forcing; values must come from the original callback readset.
