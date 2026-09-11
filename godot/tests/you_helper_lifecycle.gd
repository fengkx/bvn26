extends SceneTree


func _initialize() -> void:
	_run.call_deferred()


func _run() -> void:
	var helper := HelperRuntime.new()
	helper.helper_directory = "res://generated/helpers/you"
	helper.fighter_directory = helper.helper_directory
	helper.autoplay = false
	root.add_child(helper)
	var owner := FighterRuntime.new()
	owner.fighter_directory = "res://generated/fighters/sasuke"
	root.add_child(owner)
	await process_frame

	assert(helper.helper_id == "鼬")
	assert(helper._combat.start_frame == 2 and helper._combat.end_frame == 199)
	var callback_registry := SourceCallbackRegistry.new()
	helper.bind_source_frames(callback_registry, 0)
	assert(callback_registry.size() == 1, "helper root callback registration missing")
	var effects: Array = []
	helper.effect_requested.connect(func(clip: String, _position: Vector2, _facing: int, _offset: float) -> void:
		effects.append({"frame": helper.current_source_frame(), "clip": clip})
	)
	helper.activate({"x": 300.0, "y": -25.0, "facing": 1, "start_frame": 2}, owner)
	assert(helper.attacking and helper.visible and helper.current_source_frame() == 2)
	helper.play_source_frame(48)
	helper._sync_nested_callbacks()
	assert(callback_registry.size() == 2, "nested callback was not registered for frame 48")
	helper.activate({"x": 300.0, "y": -25.0, "facing": 1, "start_frame": 2}, owner)
	assert(callback_registry.size() == 1, "repeated activate leaked the old nested callback")
	helper.unbind_source_frames()
	assert(callback_registry.size() == 0, "unbind leaked helper callbacks")
	effects.clear()
	helper.activate({"x": 300.0, "y": -25.0, "facing": 1, "start_frame": 2}, owner)
	var rows: Array = []
	for _tick in range(2, 100):
		var frame := helper.current_source_frame()
		helper.enter_frame()
		rows.append({
			"frame": frame,
			"action": helper.source_action,
			"attacking": helper.attacking,
			"atm1": helper.instance_global_bounds("atm1").has_area(),
			"atm2": helper.instance_global_bounds("atm2").has_area(),
			"atm3": helper.instance_global_bounds("atm3").has_area(),
			"instances": helper.current_named_instances(),
			"sounds": helper.last_sound_ids.duplicate(),
		})
		if frame < 199:
			helper.advance_timeline()
		if not helper.attacking:
			break
	# Source You frame 76 calls gotoAndStop(1) after the miss path's effect.
	assert(not helper.attacking and not helper.visible and helper.current_source_frame() == 1)
	helper.advance_timeline()
	assert(helper.current_source_frame() == 1, "parked miss helper advanced after root stop")
	helper.activate({"x": 300.0, "y": -25.0, "facing": 1, "start_frame": 2}, owner)
	assert(helper.attacking and helper.current_source_frame() == 2, "reactivation did not restart at source frame 2")

	var by_frame := {}
	for row: Dictionary in rows:
		by_frame[int(row.frame)] = row
	assert(by_frame[18].action == 1)
	assert(by_frame[61].action == 0)
	assert("atm1" in by_frame[48].instances and "atm1" in by_frame[59].instances and "atm1" not in by_frame[60].instances)
	assert(not by_frame[76].attacking and by_frame[76].frame == 76)
	assert(effects == [{"frame": 2, "clip": "XG_fzcc"}, {"frame": 76, "clip": "XG_fzcc"}, {"frame": 2, "clip": "XG_fzcc"}])
	var output := OS.get_cmdline_user_args()[0] if not OS.get_cmdline_user_args().is_empty() else ""
	if output != "":
		FileAccess.open(output, FileAccess.WRITE).store_string(JSON.stringify({"rows": rows, "effects": effects}, "", true, true))
	print("YOU_HELPER_LIFECYCLE_OK rows=", rows.size(), " effects=", effects.size())
	helper.queue_free()
	owner.queue_free()
	await process_frame
	quit()
