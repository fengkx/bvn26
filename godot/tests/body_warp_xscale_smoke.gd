extends SceneTree


func _initialize() -> void:
	_run.call_deferred()


func _run() -> void:
	var fighter_script = load("res://fighter_runtime.gd")
	var opponent: FighterRuntime = fighter_script.new()
	opponent.fighter_directory = "res://generated/fighters/yihu"
	root.add_child(opponent)
	var fighter: FighterRuntime = fighter_script.new()
	fighter.fighter_directory = "res://generated/fighters/yulong"
	root.add_child(fighter)
	await process_frame
	fighter.opponent = opponent
	opponent.opponent = fighter
	var source_event: Dictionary = fighter._combat["body_warps"].filter(
		func(event: Dictionary) -> bool:
			return event.get("source_path", "") == "DefineSprite_345/frame_250/DoAction.as"
	)[0]
	assert(source_event["op"] == "offset_parent_x_by_xscale")
	assert(source_event["xscale_factor"] == -1.0)

	fighter.source_x = 300.0
	fighter.set_facing(1)
	_run_skill1_until_warp(fighter)
	assert(is_equal_approx(fighter.source_x, 200.0))
	fighter.enter_frame({})
	assert(is_equal_approx(fighter.source_x, 200.0))
	fighter._queue_source_frame(250)
	fighter.enter_frame({})
	assert(is_equal_approx(fighter.source_x, 100.0))
	fighter.start_action("站立")
	_run_skill1_until_warp(fighter)
	assert(is_equal_approx(fighter.source_x, 0.0))

	fighter.start_action("站立")
	fighter.source_x = 300.0
	fighter.set_facing(-1)
	_run_skill1_until_warp(fighter)
	assert(is_equal_approx(fighter.source_x, 400.0))
	fighter.start_action("站立")
	_run_skill1_until_warp(fighter)
	assert(is_equal_approx(fighter.source_x, 500.0))
	print("BODY_WARP_XSCALE_SMOKE_OK")
	quit()


func _run_skill1_until_warp(fighter: FighterRuntime) -> void:
	fighter.start_action("砍技1")
	while fighter.current_source_frame() < 250:
		fighter.advance_timeline()
		fighter._ai_pending_frames.clear()
	fighter.enter_frame({})
