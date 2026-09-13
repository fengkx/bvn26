extends SceneTree


func _initialize() -> void:
	_run.call_deferred()


func _run() -> void:
	var fighter_script = load("res://fighter_runtime.gd")
	var attacker: FighterRuntime = fighter_script.new()
	attacker.fighter_directory = "res://generated/fighters/rukia"
	root.add_child(attacker)
	var defender: FighterRuntime = fighter_script.new()
	defender.fighter_directory = "res://generated/fighters/yihu"
	root.add_child(defender)
	await process_frame
	attacker.opponent = defender
	defender.opponent = attacker
	attacker.source_x = 300.0
	defender.source_x = 350.0
	attacker.set_facing(1)
	attacker.start_action("砍技1")

	var combat_event: Dictionary = attacker._combat["body_warps"].filter(
		func(event: Dictionary) -> bool:
			return event.get("source_path", "") == "DefineSprite_533/frame_330/DoAction.as"
	)[0]
	var ai_event: Dictionary = attacker.ai_source_state.spec["frame_calls"]["330"].filter(
		func(event: Dictionary) -> bool:
			return event.get("op", "") == "body_warp"
	)[0]
	assert(ai_event["path"] == combat_event["source_path"])

	attacker._apply_body_warp_event(combat_event, 77)
	assert(is_equal_approx(attacker.source_x, 400.0) and attacker.facing == -1)
	attacker._apply_body_warp_event(ai_event, 77)
	assert(is_equal_approx(attacker.source_x, 400.0) and attacker.facing == -1)

	attacker._apply_body_warp_event(ai_event, 78)
	assert(is_equal_approx(attacker.source_x, 300.0) and attacker.facing == 1)
	attacker._apply_body_warps(330, 79)
	assert(is_equal_approx(attacker.source_x, 400.0) and attacker.facing == -1)
	print("BODY_WARP_EVENT_DEDUP_SMOKE_OK")
	quit()
