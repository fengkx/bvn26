extends SceneTree


func _initialize() -> void:
	_run.call_deferred()


func _run() -> void:
	var args := OS.get_cmdline_user_args()
	var output := args[0] if not args.is_empty() else "/tmp/sasuke-native-trace.json"
	var fighter := FighterRuntime.new()
	fighter.fighter_directory = "res://generated/fighters/sasuke"
	root.add_child(fighter)
	await process_frame
	fighter.source_x = 300.0
	fighter.source_y = -25.0
	fighter._ground_y = -25.0
	fighter.energy = 300.0
	fighter.ai_source_state.values["touch"] = true
	fighter.start_action("站立")
	var rows: Array = []
	for tick in 361:
		if tick > 0:
			var input_tick := tick - 1
			var input := {"attack": input_tick >= 10 and input_tick < 13}
			fighter.ai_source_state.values["touchFloor"] = true
			fighter.enter_frame(input)
			fighter.advance_timeline()
			fighter.run_frame_actions()
		rows.append({"tick": tick, "slot": "p1", "frame": fighter.current_source_frame(),
			"x": fighter.source_x, "y": fighter.source_y, "xscale": fighter.scale.x * 100,
			"action": fighter.ai_source_state.read_field("动作"), "hp": fighter.health,
			"ql": fighter.energy, "sw": fighter.sw,
			"touch": fighter.ai_source_state.read_field("touch"),
			"touchFloor": fighter.ai_source_state.read_field("touchFloor"), "hits": fighter.hits,
			"paused": fighter.root_zhanting, "hstm": fighter.ai_source_state.read_field("hstm"),
			"hurtSkling": fighter.ai_source_state.read_field("hurtSkling")})
	FileAccess.open(output, FileAccess.WRITE).store_string(JSON.stringify(rows, "", true, true))
	fighter.queue_free()
	await process_frame
	print("SASUKE_NATIVE_TRACE_OK ", rows.size())
	quit()
