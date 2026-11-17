extends "res://tests/move_case_reference.gd"


func _observe(tick: int) -> void:
	super._observe(tick)
	if tick >= 39 and tick <= 46:
		var actor = game.naruto
		print("VISUAL_STATE ", JSON.stringify({
			"tick": tick,
			"frame": actor.current_source_frame(),
			"render_frame": actor._current_frame,
			"clips": actor._retained_visual_clips,
			"instance_frames": actor._instance_local_frames,
			"pending": actor._ai_pending_frames,
			"hidden_stage": Array(game.current_world.hidden_instance_names),
		}))
