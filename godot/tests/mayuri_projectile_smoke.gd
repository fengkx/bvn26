extends SceneTree


func _initialize() -> void:
	_run.call_deferred()


func _run() -> void:
	var fighter := FighterRuntime.new()
	fighter.fighter_directory = "res://generated/fighters/mayuri"
	var opponent := FighterRuntime.new()
	opponent.fighter_directory = "res://generated/fighters/yihu"
	root.add_child(fighter)
	root.add_child(opponent)
	await process_frame
	fighter.opponent = opponent
	opponent.opponent = fighter
	opponent.position.x = 2000
	# Controlled source-state checks; this is not a native same-input fixture.
	for model: Dictionary in fighter._combat.projectiles:
		var authored := str(model.instance_name)
		var delta := 15.0 if authored == "abcd" else 10.0
		for placement in 2:
			fighter.start_action("站立")
			fighter.start_action(str(model.action))
			fighter.play_source_frame(int(model.start_frame))
			fighter.refresh_display()
			fighter._start_clip_playhead(authored, model)
			assert(fighter.instance_source_variables(authored).played == 0)
			var before := fighter.instance_local_offset(authored)
			assert(not fighter.run_projectile_callback(model))
			assert(fighter.instance_local_offset(authored).x == before.x + delta)
			var rename: Dictionary = model.rename_frames[0]
			fighter.set_instance_clip_frame(authored, int(rename.frame), true)
			fighter._apply_projectile_local_write(authored, {"writes": rename.local_writes})
			before = fighter.instance_local_offset(authored)
			assert(fighter.instance_source_variables(authored).played == 1)
			assert(not fighter.run_projectile_callback(model))
			assert(fighter.instance_local_offset(authored) == before)
	fighter.queue_free()
	opponent.queue_free()
	await process_frame
	print("MAYURI_PROJECTILE_SMOKE_OK source_locals=true placements=2 motion_guard=true")
	quit()
