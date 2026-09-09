extends SceneTree


func _initialize() -> void:
	_run.call_deferred()


func _run() -> void:
	var fighter := FighterRuntime.new()
	fighter.fighter_directory = "res://generated/fighters/yihu"
	var target := FighterRuntime.new()
	target.fighter_directory = "res://generated/fighters/minren"
	root.add_child(fighter)
	root.add_child(target)
	await process_frame
	fighter.opponent = target
	target.opponent = fighter
	for fixture in [["跳招", 150, 18.0], ["招1", 327, 0.0], ["招3", 421, -18.0]]:
		target.position = Vector2(10000, 10000)
		fighter.start_action(fixture[0])
		fighter.play_source_frame(fixture[1])
		fighter.run_frame_actions()
		var before := fighter.instance_local_offset("zh1atm")
		fighter._update_projectiles()
		assert(fighter.instance_local_offset("zh1atm") == before + Vector2(18, fixture[2]))
		assert(fighter.instance_clip_frame("zh1atm") == 1)
		fighter._update_projectiles()
		assert(fighter.instance_clip_frame("zh1atm") == 1)
		target.position += fighter.instance_global_bounds("zh1atm").get_center() - target.instance_global_bounds("bdmn").get_center()
		before = fighter.instance_local_offset("zh1atm")
		fighter._update_projectiles()
		assert(fighter.instance_clip_frame("zh1atm") == 5)
		assert(fighter.instance_local_offset("zh1atm") == before)
		target.position = Vector2(10000, 10000)
		for tick in 8:
			fighter._update_projectiles()
			assert(fighter.instance_local_offset("zh1atm") == before)
		assert(fighter.instance_clip_frame("zh1atm") == 10)
	# Place only the opponent projectile in range, keeping its body far away.
	fighter.start_action("招1")
	fighter.play_source_frame(327)
	fighter.run_frame_actions()
	fighter.set_instance_clip_frame("zh1atm", 1, false)
	target.start_action("招1")
	target.play_source_frame(382)
	target.run_frame_actions()
	target.set_instance_clip_frame("zh1atm", 1, false)
	target.set_instance_local_offset("zh1atm", Vector2(1000, 0))
	target.position += fighter.instance_global_bounds("zh1atm").get_center() - target.instance_global_bounds("zh1atm").get_center()
	var projectile: Dictionary = fighter._combat.projectiles[1]
	assert(projectile.collision_queries == [
		{"receiver": "self", "target": "bdmn"},
		{"receiver": "self", "target": "zh1atm"},
		{"receiver": "self", "target": "zh2atm"},
		{"receiver": "hitmc", "target": "zh3atm"},
		{"receiver": "self", "target": "abcd"}])
	assert(not fighter.instance_global_bounds("zh1atm").intersects(target.instance_global_bounds("bdmn")))
	assert(fighter._projectile_blocked("zh1atm", projectile))
	target.set_instance_clip_frame("zh1atm", 5, true)
	assert(not target.source_projectile_target_bounds("zh1atm").has_area())
	assert(target.source_projectile_target_bounds("abcd").has_area())
	target.position += fighter.instance_global_bounds("zh1atm").get_center() - target.source_projectile_target_bounds("abcd").get_center()
	assert(fighter._projectile_blocked("zh1atm", projectile))
	assert(not fighter.child_instance_global_bounds("zh1atm", "hitmc").has_area())
	fighter.queue_free()
	target.queue_free()
	await process_frame
	print("AI_PROJECTILE_SOURCE_SMOKE_OK")
	quit()
