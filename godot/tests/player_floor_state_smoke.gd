extends SceneTree


func _initialize() -> void:
	_run.call_deferred()


func _run() -> void:
	var fighters: Array[FighterRuntime] = []
	for name in ["minren", "yihu"]:
		var fighter := FighterRuntime.new()
		fighter.fighter_directory = "res://generated/fighters/" + name
		root.add_child(fighter)
		fighters.append(fighter)
	fighters[0].position.x = 100
	fighters[1].position.x = 700
	for i in 2:
		var fighter := fighters[i]
		var other := fighters[1 - i]
		for flags in [[true, 0], [false, 1], [false, 0]]:
			fighter.position.y = fighter._ground_y
			fighter.root_zhanting = flags[0]
			fighter._dash_ticks = flags[1]
			fighter.ai_source_state.values["touch"] = false
			fighter.ai_source_state.values["touchFloor"] = null
			fighter.resolve_body_collision(other)
			if flags[0] or flags[1] > 0:
				assert(fighter.ai_source_state.read_field("touchFloor") == null)
				assert(fighter.ai_source_state.read_field("touch") == false)
			else:
				assert(fighter.ai_source_state.read_field("touchFloor") == true)
				assert(fighter.ai_source_state.read_field("touch") == true)
	for fighter in fighters:
		fighter.queue_free()
	await process_frame
	print("PLAYER_FLOOR_STATE_SMOKE_OK")
	quit()
