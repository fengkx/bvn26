# Form runtime evidence (r13)

Read `source-first.md` for exact source sites and native observation boundaries.

- Sasuke: two native slot captures, 13 observations each. Real source frames1228–1232 execute slot selection/transfer, capture the slot-specific health function, start its root interval, set wrapper transformation state, and replace sprite603 with1019. The next initialized body observation is1017, HP671/energy234. Godot verifies both slots, retained root selection, undefined replacement gap, old path reference, direct-health interval behavior at root maxhp1500, and full before/after checkpoint restoration.
- Byakuya/Rifagu/Rukia: shared parameterized fixture invokes each real source wankai frame and installs its full target package. It checks native next-body frames1046/1204/1122, HP/energy transfer, retired state, restore-base and redo replacement, restore-target and invoke the captured live-root interval. Native captures are under `../form-helpers/`.
- Root journal: `form_root_interval_replay_smoke.gd` delivers an explicit `root_interval` envelope through RollbackBattle/Main, then restores the preceding complete snapshot and redelivers the immutable event; the complete resulting state is equal. Invalid ID0 is rejected, and the repeating registration survives delivery. This extends the existing externally scheduled `after_actor_advance` callback contract; the fixture does not infer deadlines from frame counts or claim a new native wall-clock scheduling measurement.
- Main/input activation: accepted source-bound manifests remove the development `万解` action block only after runtime preflight. The input fixture uses energy300 plus real attack+jump input after natural match opening. It must reach the original transformation action and replacement profile; unsupported graphs retain their block.

Three genuine candidate-consumer defects were caught before admission: the compiled Sasuke/Minren interval block lost its trailing `_parent.万解=true`, root state/interval references were incorrectly classified as external Main state for rollback, and natural Sasuke input exposed the initial body opponent-slot `pn` binding missing from Main activation. They are fixed by ordered compiler events, explicit checkpoint ownership, and the already source-validated `form_initialization.bind_opponent_slot` consumer. No undefined HP/energy fallback was introduced. Captured slot callback code now has a stable script resource identity for reconstruction.

Run Godot headlessly with `--path godot --script res://tests/<name>.gd --log-file <writable log>`:

- `form_slot_replacement_reference.gd`
- `form_wankai_graph_reference.gd`
- `form_root_interval_replay_smoke.gd`
- `form_input_activation_smoke.gd`
- `form_root_owner_smoke.gd`

Native probe reproduction: `tools/probes/build_form_slot_probe.py --slot 1|2 --ffdec <jar> --output <scratch>`, then `tools/probes/capture_native_player.py <scratch> <log> --player-app <Debugger32.app> --allow-window-activation --timeout 40`. Instrumentation changes only the observer/root DoAction; locked inputs and child action bytes remain unchanged.

Final production validation: six runtime scripts exit0 without SCRIPT ERROR or leaked-instance diagnostics: input activation5/5, wankai graph rollback3/3, Sasuke slots2/2, root interval envelope replay1/1, root ownership1/1, and retained Daitu full rollback1/1. Input validation also asserts initial pn, empty match-input error, defined HP/energy transfer, and exact target values. The full-roster/build acceptance is reported separately by the lead.
