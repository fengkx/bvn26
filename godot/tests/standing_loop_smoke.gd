extends SceneTree


func _initialize() -> void:
	_run.call_deferred()


func _run() -> void:
	for name in ["minren", "yihu"]:
		var fighter := FighterRuntime.new()
		fighter.fighter_directory = "res://generated/fighters/" + name
		root.add_child(fighter)
		# Both retained BODY scripts gotoAndStop("站立"); play() on frame 8.
		# Root pause does not suspend their timeline DoAction loop.
		fighter.root_zhanting = true
		for tick in 21:
			fighter.advance_timeline()
			fighter.run_frame_actions()
			assert(fighter.current_source_frame() == (tick + 1) % 7 + 1)
			assert(fighter.timeline_playing and fighter.action == "站立")
		fighter.queue_free()
	await process_frame
	print("STANDING_LOOP_SMOKE_OK")
	quit()
