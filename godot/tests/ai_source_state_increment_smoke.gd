extends SceneTree


func _initialize() -> void:
	_run.call_deferred()


func _run() -> void:
	var fighter := FighterRuntime.new()
	fighter.fighter_directory = "res://generated/fighters/yulong"
	root.add_child(fighter)
	await process_frame
	assert(fighter.ai_source_state.read_field("k1n") == 0)
	fighter.start_action("砍1")
	fighter.run_frame_actions()
	fighter.play_source_frame(184)
	fighter.run_frame_actions()
	assert(fighter.ai_source_state.read_field("k1n") == 1)
	# Re-entering the action runs the same sourced increment again on this instance.
	fighter.start_action("砍1")
	fighter.run_frame_actions()
	fighter.play_source_frame(184)
	fighter.run_frame_actions()
	assert(fighter.ai_source_state.read_field("k1n") == 2)
	# Re-entering source frame 1 runs its sourced initialization again.
	fighter.start_action("站立")
	fighter.run_frame_actions()
	assert(fighter.ai_source_state.read_field("k1n") == 0)
	fighter.queue_free()
	await process_frame
	print("AI_SOURCE_STATE_INCREMENT_SMOKE_OK")
	quit()
