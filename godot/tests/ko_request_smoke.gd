extends SceneTree


func _initialize() -> void:
	_run.call_deferred()


func _run() -> void:
	for name: String in ["minren", "yihu"]:
		var fighter := FighterRuntime.new()
		fighter.fighter_directory = "res://generated/fighters/" + name
		root.add_child(fighter)
		fighter.player_slot = "p1" if name == "minren" else "p2"
		fighter.ai_timeline_controlled = name == "yihu"
		fighter.ai_source_state.apply_load()
		fighter.ai_source_state.apply_frame(1)
		var requests: Array = []
		fighter.ko_requested.connect(func(number: int) -> void:
			requests.append({"number": number, "action": fighter.action,
				"sw": fighter.ai_source_state.read_field("sw"), "bdzl": fighter.ai_source_state.read_field("bdzl")}))
		fighter.modo = 4
		fighter.health = 0
		fighter.ai_source_state.values["bdzl"] = 15
		assert(not fighter._check_dead(false))
		assert(requests.is_empty() and not fighter.sw)
		fighter.modo = 2
		assert(fighter._check_dead(false))
		assert(fighter.ai_source_state.read_field("sw") == true)
		assert(fighter.ai_source_state.read_field("bdzl") == 0)
		var observer := FighterRuntime.new()
		observer.opponent = fighter
		var context := AiPredicateContext.new(observer)
		assert(context.read_field("opponent_sw") == true)
		observer.free()
		assert(requests.size() == 1)
		assert(requests[0].number == (2 if name == "minren" else 1))
		assert(requests[0].action == "站立")
		assert(requests[0].sw == true and requests[0].bdzl == 0)
		assert(fighter.action == "击飞" and fighter.timeline_playing)
		assert(not fighter._check_dead(false) and requests.size() == 1)
		fighter.queue_free()
	await process_frame
	print("KO_REQUEST_SMOKE_OK")
	quit()
