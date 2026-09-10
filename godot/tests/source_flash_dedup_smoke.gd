extends SceneTree


func _initialize() -> void:
	_run.call_deferred()


func _run() -> void:
	var game = load("res://main.tscn").instantiate()
	root.add_child(game)
	game.set_physics_process(false)
	game._replace_selected_actors(["卡卡西", "一护"], ["我爱罗", "魂"])
	game._load_selected_stage("现世")
	game._enter_current_fight(3)
	for _tick in 700:
		game._advance_fight()
		if not game.battle_intro.active:
			break

	var flashes: Array = []
	game.naruto.screen_flash_requested.connect(func(color: int) -> void:
		flashes.append({"frame": game.naruto.current_source_frame(), "color": color}))
	for _cast in 2:
		# Re-enter the authored standing label between casts on the same actor;
		# this is the source action restart path on one FighterRuntime.
		game.naruto.start_action("超必杀2")
		game.naruto.play_source_frame(961)
		game.naruto._ai_pending_frames.clear()
		game.naruto._ai_state_frame_applied = -1
		game.naruto._queue_source_frame(961)
		game.naruto.run_frame_actions()
	var frame_calls: Array = game.naruto.ai_source_state.spec["frame_calls"].get("961", [])
	var expected := frame_calls.filter(func(event: Dictionary) -> bool:
		return event.get("op") == "screen_flash").size()
	var actual := flashes.filter(func(event: Dictionary) -> bool:
		return int(event["frame"]) == 961).size()
	assert(expected == 1, "Source frame 961 must contain one authored root shine")
	assert(actual == expected * 2,
		"Each repeated cast must emit the root shine once: %s vs %s" % [actual, expected * 2])
	game._goto_menu()
	game.queue_free()
	await process_frame

	# Frame 881 has two authored same-source-path shines on different source
	# lines. The line-aware dedupe must remove only the root duplicate and keep
	# the second child/presentation event.
	game = load("res://main.tscn").instantiate()
	root.add_child(game)
	game.set_physics_process(false)
	game._replace_selected_actors(["鸣人", "一护"], ["我爱罗", "魂"])
	game._load_selected_stage("现世")
	game._enter_current_fight(3)
	for _tick in 700:
		game._advance_fight()
		if not game.battle_intro.active:
			break
	var child_flashes: Array = []
	game.naruto.screen_flash_requested.connect(func(color: int) -> void:
		child_flashes.append({"frame": game.naruto.current_source_frame(), "color": color}))
	game.naruto.start_action("超必杀")
	game.naruto.play_source_frame(881)
	game.naruto._ai_pending_frames.clear()
	game.naruto._ai_state_frame_applied = -1
	game.naruto._queue_source_frame(881)
	game.naruto.run_frame_actions()
	var frame_881 := child_flashes.filter(func(event: Dictionary) -> bool:
		return int(event["frame"]) == 881)
	assert(frame_881.size() == 2,
		"Same-frame different source lines must both survive: %s" % str(frame_881))
	assert(frame_881[0]["color"] == 0xFFFFFF and frame_881[1]["color"] == 303095,
		"Unexpected frame 881 shine order/colors: %s" % str(frame_881))
	game._goto_menu()
	game.queue_free()
	await process_frame
	print("SOURCE_FLASH_DEDUP_SMOKE_OK frame=961 repeated=", actual, " frame=881 child=", frame_881.size())
	quit()
