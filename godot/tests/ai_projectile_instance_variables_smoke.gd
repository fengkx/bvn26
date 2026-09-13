extends SceneTree


func _initialize() -> void:
	_run.call_deferred()


func _run() -> void:
	var fighter := FighterRuntime.new()
	fighter.fighter_directory = "res://generated/fighters/yulong"
	var opponent := FighterRuntime.new()
	opponent.fighter_directory = "res://generated/fighters/yulong"
	root.add_child(fighter)
	root.add_child(opponent)
	await process_frame
	fighter.opponent = opponent
	opponent.opponent = fighter
	fighter.position = Vector2(250, 0)
	opponent.position = Vector2(1000, 0)
	fighter.start_action("砍1")
	fighter.play_source_frame(188)
	fighter.refresh_display()
	var projectile: Dictionary = {}
	for item: Dictionary in fighter._combat["projectiles"]:
		if item["instance_name"] == "k1atm":
			projectile = item
			break
	assert(not projectile.is_empty())
	fighter._start_clip_playhead("k1atm", projectile)
	var variables := fighter.instance_source_variables("k1atm")
	assert(int(variables["played"]) == 0 and float(variables["movspeed"]) == 20.0)
	assert(not fighter.run_projectile_callback(projectile))
	assert(fighter.instance_local_offset("k1atm").x == 20)
	var hit_event: Dictionary = projectile["on_hit_events"][0]
	fighter._apply_projectile_local_write("k1atm", hit_event)
	variables = fighter.instance_source_variables("k1atm")
	assert(int(variables["played"]) == 1 and float(variables["movspeed"]) == 0.0)
	assert(not fighter.run_projectile_callback(projectile))
	assert(fighter.instance_local_offset("k1atm").x == 20)
	# Once spent, a later non-contact tick keeps the same instance stopped.
	fighter.set_instance_clip_frame("k1atm", 6, true)
	variables = fighter.instance_source_variables("k1atm")
	assert(int(variables["played"]) == 1 and float(variables["movspeed"]) == 0.0)
	# Removing the source placement and placing it again creates fresh load state.
	fighter.start_action("站立")
	fighter.start_action("砍1")
	fighter.play_source_frame(188)
	fighter.refresh_display()
	fighter._update_projectiles()
	variables = fighter.instance_source_variables("k1atm")
	assert(int(variables["played"]) == 0 and float(variables["movspeed"]) == 20.0)
	fighter.queue_free()
	opponent.queue_free()
	await process_frame
	print("AI_PROJECTILE_INSTANCE_VARIABLES_SMOKE_OK")
	quit()
