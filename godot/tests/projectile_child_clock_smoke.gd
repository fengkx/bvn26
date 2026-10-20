extends SceneTree


func _initialize() -> void:
	_run.call_deferred()


func _run() -> void:
	var fighter := FighterRuntime.new()
	fighter.fighter_directory = "res://generated/fighters/didala"
	root.add_child(fighter)
	fighter.start_action("招1")
	fighter.play_source_frame(356)
	var model: Dictionary = fighter._combat.projectiles[1]
	for flight_age in [4, 10, 20]:
		fighter._instance_local_frames.clear()
		fighter._start_clip_playhead("abcd", model)
		for tick in flight_age:
			fighter._advance_clip_playhead("abcd", model)
		# Sprite 210 replaces its flight child with Sprite 82 at frame 5.
		fighter.set_instance_clip_frame("abcd", 5, true)
		assert(_explosion_frame(fighter, 5, flight_age) == 1)
		fighter._advance_clip_playhead("abcd", model)
		assert(_explosion_frame(fighter, 6, flight_age + 1) == 2)
		var checkpoint := fighter._instance_local_frames.duplicate(true)
		for tick in 20:
			fighter._advance_clip_playhead("abcd", model)
		# Sprite 82/frame_12/DoAction.as stops on the empty final display list.
		assert(_explosion_frame(fighter, 12, flight_age + 21) == 12)
		fighter._instance_local_frames = checkpoint
		assert(_explosion_frame(fighter, 6, flight_age + 1) == 2)
	fighter.free()
	print("PROJECTILE_CHILD_CLOCK_SMOKE_OK placements=3 checkpoint=true source_stop=true")
	quit()


func _explosion_frame(fighter: FighterRuntime, parent_frame: int, age: int) -> int:
	var placement: Dictionary = fighter._definitions[210].display_list_frames[parent_frame - 1][0]
	return fighter._nested_frame(placement, parent_frame, 13, age)
