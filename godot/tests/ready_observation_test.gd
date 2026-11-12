extends SceneTree

const Observation = preload("res://tests/ready_observation.gd")


func _initialize() -> void:
	_run.call_deferred()


func _row(slot: String, hp: int) -> Dictionary:
	return {"slot": slot, "display_tick": 484, "observation_phase": Observation.PHASE,
		"actor_identity": {"godot_instance_id": 1 if slot == "p1" else 2, "source_model": slot},
		"actual": {"hp": hp, "ql": 0, "action": 0, "sw": false, "touch": true,
			"touchFloor": null, "hits": 0, "paused": false, "hstm": 0, "hurtSkling": false},
		"frame": 2, "x": 1, "y": -25, "xscale": 100, "pending_frame_actions": 0}


func _run() -> void:
	var p1 := _row("p1", 900)
	var p2 := _row("p2", 700)
	var ids := {"p1": p1.actor_identity, "p2": p2.actor_identity}
	var ordered := Observation.bind_actors([p1, p2], ids, 484)
	var reordered := Observation.bind_actors([p2, p1], ids, 484)
	assert(ordered == reordered)
	assert(ordered.actors[0].hp == 900 and ordered.actors[1].hp == 700)
	assert(ordered.actors[0].touchFloor == null)
	assert(not Observation.bind_actors([p1], ids, 484).error.is_empty())
	assert(not Observation.bind_actors([p1, p1], ids, 484).error.is_empty())
	assert(not Observation.bind_actors([p1, p2, p2], ids, 484).error.is_empty())
	for field in ["display_tick", "observation_phase", "actor_identity", "slot"]:
		var stale := p2.duplicate(true)
		stale[field] = {"display_tick": 483, "observation_phase": "after_deferred",
			"actor_identity": p1.actor_identity, "slot": "p3"}[field]
		assert(not Observation.bind_actors([p1, stale], ids, 484).error.is_empty())
	var missing := p2.duplicate(true)
	missing.actual.erase("hp")
	assert(not Observation.bind_actors([p1, missing], ids, 484).error.is_empty())
	missing = p2.duplicate(true)
	missing.erase("frame")
	assert(not Observation.bind_actors([p1, missing], ids, 484).error.is_empty())
	var refused := Observation.identity_refusal({"error": "test_identity_mismatch"})
	for flag in Observation.non_admission():
		assert(refused.has(flag) and refused[flag] == false)
	assert(refused.native_checkpoint == {})
	print("READY_OBSERVATION_OK reordered_bound missing_duplicate_stale_foreign_refused null_retained explicit_false_flags")
	var args := OS.get_cmdline_user_args()
	if not args.is_empty():
		# Execute the reviewed record_ready body extracted verbatim into a test
		# adapter, using real FighterRuntime instances. No Flash is involved.
		var legacy = load(args[0]).new()
		var first := FighterRuntime.new()
		var second := FighterRuntime.new()
		first.player_slot = "p1"
		second.player_slot = "p2"
		var fighters: Array[FighterRuntime] = [first, second]
		legacy.state_comparisons = [p2, p1]
		var game := {"source_random": {"absolute_index": 95}, "source_clock": {"absolute_index": 0},
			"battle_intro": {"active": false}, "naruto_helper": null, "ichigo_helper": null}
		legacy.record_ready(game, fighters, 484)
		assert(legacy.native_checkpoint.actors[0].slot == "p1" and legacy.native_checkpoint.actors[0].hp == 700)
		print("LEGACY_MISBIND_REPRODUCED p2_hp_assigned_to_p1")
		first.free()
		second.free()
	quit()
