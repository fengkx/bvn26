extends SceneTree


func _initialize() -> void:
	_run.call_deferred()


func _run() -> void:
	var fighter := FighterRuntime.new()
	fighter.fighter_directory = "res://generated/fighters/yihu"
	root.add_child(fighter)
	fighter.ai_timeline_controlled = true
	var colors := fighter.ai_color_state
	assert(colors.colors == null and colors.index == 0 and colors.gap == 0)
	fighter.receive_attack({"damage": 1, "horizontal_impulse": 0, "hitstun_ms": 100, "impact_strength": 7}, 1)
	assert(colors.transform.is_empty())
	fighter.apply_ai_colors()
	assert(colors.transform == {"rb": 255.0, "gb": 25.0, "bb": -255.0})
	assert(colors.index == 1)
	assert(fighter._source_color_add == Color(1, 25.0 / 255, -1, 0))
	# Wrapper setColor and BODY resColor both preserve the cycle index.
	colors.receive(fighter.ai_color_operations["8"])
	fighter.apply_ai_colors()
	assert(colors.transform == {"rb": 0.0, "gb": 198.0, "bb": 255.0})
	assert(colors.index == 0)
	fighter.apply_ai_colors()
	assert(colors.index == 1)
	colors.receive(fighter.ai_color_operations["10"])
	fighter.set_source_color(colors.transform, colors.matrix)
	assert(fighter._source_color_matrix.size() == 20)
	var shader_found := false
	for child in fighter.get_children():
		if child is CanvasItem and not child.is_queued_for_deletion() and child.material is ShaderMaterial:
			assert(child.material.get_shader_parameter("row_r") == Vector4(0.3086, 0.6094, 0.082, 0))
			shader_found = true
	assert(shader_found)
	fighter.reset_ai_colors()
	assert(colors.index == 1 and colors.gap == 1 and colors.colors == null)
	assert(colors.matrix.is_empty() and fighter._source_color_matrix.is_empty())
	assert(fighter._source_color_add == Color(0, 0, 0, 0))
	assert(not colors.apply_colors())
	var opponent := FighterRuntime.new()
	opponent.fighter_directory = "res://generated/fighters/minren"
	root.add_child(opponent)
	fighter.opponent = opponent
	opponent.opponent = fighter
	var driver := AiCpuDriver.new()
	root.add_child(driver)
	driver.configure(fighter, "res://generated/fighters/yihu/ai_controller", {}, 0, 1000,
		{"touchFloor": null}, func(name: String, _args: Array) -> Variant:
			assert(false, "Unexpected frame service: " + name)
			return null, true)
	# BODY frame 1 executes resColor before the later _cgap=0 and _csn=0.
	# Revisit it twice: this is not limited to initial actor construction.
	for iteration in range(2):
		colors.receive(fighter.ai_color_operations["7"])
		fighter.apply_ai_colors()
		colors.receive(fighter.ai_color_operations["10"])
		colors.index = 1
		colors.gap = 9
		fighter.set_source_color(colors.transform, colors.matrix)
		driver.controller.goto_label("站立", true)
		driver.run_target_frames()
		assert(colors.colors == null and colors.index == 0 and colors.gap == 0)
		assert(colors.matrix.is_empty() and fighter._source_color_matrix.is_empty())
		assert(fighter._source_color_add == Color(0, 0, 0, 0))
	driver.stop()
	driver.queue_free()
	opponent.queue_free()
	fighter.queue_free()
	await process_frame
	print("AI_COLORS_SMOKE_OK")
	quit()
