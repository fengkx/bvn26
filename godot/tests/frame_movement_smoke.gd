extends SceneTree


func _initialize() -> void:
	var fighter := FighterRuntime.new()
	var driver := AiCpuDriver.new()
	driver.fighter = fighter
	var spec: Dictionary = JSON.parse_string(FileAccess.get_file_as_string("res://generated/fighters/didala/ai.json"))
	# The authored speed operand must be read at execution, including on reuse.
	for sample in [[10, 1, 480], [7, 1, 426], [10, -1, 120]]:
		fighter.source_x = 300
		fighter.facing = sample[1]
		fighter.ai_source_state.values["speed"] = sample[0]
		driver._frame_service(spec.frame_calls["34"][0])
		assert(fighter.source_x == sample[2])
		fighter.source_x = 300
		driver._frame_service(spec.frame_calls["970"][0])
		assert(fighter.source_x == 300 - sample[0] * 6 * sample[1])
	# Wrapper moveY adds its argument without facing or the child moveY inversion.
	fighter.source_y = -25
	driver._frame_service({"op": "wrapper_move", "axis": "moveY",
		"pixels_expression": {"op": "negate", "operand": {"op": "read", "field_name": "speed"}}})
	assert(fighter.source_y == -35)
	driver._frame_service({"op": "wrapper_move", "axis": "moveY", "pixels": 5})
	assert(fighter.source_y == -30)
	driver.free()
	fighter.free()
	print("FRAME_MOVEMENT_SMOKE_OK current_speed facing recovery vertical literal")
	quit()
