extends SceneTree


func _initialize() -> void:
	_run.call_deferred()


func _run() -> void:
	var fighter := FighterRuntime.new()
	fighter.fighter_directory = "res://generated/fighters/yin"
	root.add_child(fighter)
	fighter.start_action("招换")
	fighter.run_frame_actions()
	while fighter.current_source_frame() < 905:
		fighter.advance_ai_timeline()
		fighter.run_frame_actions()
	fighter.energy = 200.0
	fighter.advance_ai_timeline()
	assert(fighter.current_source_frame() == 906)
	# Source frame 906 is already queued when a newer hit callback jumps away.
	fighter.goto_ai_label("击飞", true)
	assert(fighter.current_source_frame() == 1000)
	fighter.flush_queued_frame_scripts(1)
	assert(fighter.energy == 100.0 and not fighter.helper_spawn.is_empty())
	fighter.flush_queued_frame_scripts()
	assert(fighter.energy == 100.0)
	# doZhaoHuan still honors the source guard at execution time.
	fighter.ai_source_state.apply_write({"field": "hurtSkling", "value": true})
	fighter._queue_source_frame(906)
	fighter.flush_queued_frame_scripts()
	assert(fighter.energy == 100.0)
	fighter.queue_free()
	await process_frame
	print("SOURCE_QUEUED_SUMMON_SMOKE_OK")
	quit()
