extends SceneTree


func _initialize() -> void:
	_run.call_deferred()


func _run() -> void:
	for spec in [["kakashi", 425, "zh1atm", 3], ["sakura", 442, "zh12atm", 5]]:
		var fighter := FighterRuntime.new()
		fighter.fighter_directory = "res://generated/fighters/" + spec[0]
		var opponent := FighterRuntime.new()
		opponent.fighter_directory = "res://generated/fighters/yihu"
		root.add_child(fighter)
		root.add_child(opponent)
		await process_frame
		fighter.ai_source_state.apply_load()
		fighter.opponent = opponent
		opponent.opponent = fighter
		var projectile: Dictionary = {}
		for candidate: Dictionary in fighter._combat["projectiles"]:
			if int(candidate["start_frame"]) == spec[1]:
				projectile = candidate
		assert(not projectile.is_empty())
		var name: String = spec[2]
		# The source load locals are fresh on every placement, including a
		# repeated cast after the preceding receiver hit has already settled.
		for facing in [1, -1, 1]:
			fighter.start_action("站立")
			fighter.start_action("招1")
			fighter.play_source_frame(spec[1])
			fighter.facing = facing
			fighter.position = Vector2(300, 0)
			opponent.position = Vector2(1500, 0)
			fighter.set_instance_local_offset(name, Vector2.ZERO)
			fighter._start_clip_playhead(name, projectile)
			fighter.mark_attack_hit(name)
			var speed: float = fighter.instance_source_variables(name)["movspeed"]
			assert(not fighter.run_projectile_callback(projectile))
			assert(fighter.instance_clip_frame(name) == 1)
			assert(fighter.instance_source_variables(name)["played"] == 0)
			assert(fighter.instance_local_offset(name).x == speed)
			# Only the child's actual hitTest branch sets played and movspeed.
			opponent.start_action("站立")
			opponent.position += fighter.instance_global_bounds(name).get_center() - opponent.instance_global_bounds("bdmn").get_center()
			assert(fighter.run_projectile_callback(projectile))
			assert(fighter.instance_clip_frame(name) == spec[3])
			assert(fighter.instance_source_variables(name)["played"] == 1)
			assert(fighter.instance_source_variables(name)["movspeed"] == 0)
			opponent.position = Vector2(1500, 0)
			assert(not fighter.run_projectile_callback(projectile))
			assert(fighter.instance_local_offset(name).x == speed)
		fighter.queue_free()
		opponent.queue_free()
		await process_frame
	print("PROJECTILE_CONTACT_HISTORY_SMOKE_OK casts=6")
	quit()
