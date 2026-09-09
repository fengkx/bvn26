extends SceneTree


func _initialize() -> void:
	_run.call_deferred()


func _run() -> void:
	var fighter := FighterRuntime.new()
	fighter.fighter_directory = "res://generated/fighters/yihu"
	root.add_child(fighter)
	await process_frame
	assert(fighter.ai_source_state.read_field("动作") == 0)
	assert(fighter.ai_source_state.read_field("sw") == null)
	assert(fighter.ai_source_state.read_field("canhit") == true)
	# Sprite 638 sets 动作=1 at 233, then 0 at 258 without leaving 砍技1.
	fighter.start_action("砍技1")
	fighter.play_source_frame(233)
	fighter.run_frame_actions()
	assert(fighter.ai_source_state.read_field("动作") == 1)
	fighter.play_source_frame(258)
	fighter.run_frame_actions()
	assert(fighter.action == "砍技1")
	assert(fighter.ai_source_state.read_field("动作") == 0)
	# A declaration without initializer preserves the existing value on goto 1.
	fighter.ai_source_state.values["sw"] = true
	fighter.ai_source_state.values["hurtSkling"] = true
	fighter.start_action("站立")
	fighter.run_frame_actions()
	assert(fighter.ai_source_state.read_field("sw") == true)
	assert(fighter.ai_source_state.read_field("hurtSkling") == false)
	# onBeHit0 is an immediate function writer; target scripts are deferred.
	fighter.receive_attack({"damage": 5.0, "horizontal_impulse": 1.0, "hitstun_ms": 100}, 1)
	assert(fighter.ai_source_state.read_field("动作") == -1)
	assert(fighter.ai_source_state.read_field("jumped") == 0)
	assert(fighter.ai_source_state.read_field("htx") == 1)
	assert(fighter.ai_source_state.read_field("jhp") == 5)
	assert(fighter.ai_source_state.read_field("tdtime") == 3)
	fighter.start_action("站立")
	assert(fighter.ai_source_state.read_field("动作") == -1)
	fighter.run_frame_actions()
	assert(fighter.ai_source_state.read_field("动作") == 0)
	# Preserve each requested target write, including the intermediate guard.
	fighter.start_action("防御2")
	fighter.start_action("砍1")
	fighter.run_frame_actions()
	assert(fighter.ai_source_state.read_field("动作") == 2)
	fighter.play_source_frame(174)
	fighter.run_frame_actions()
	assert(fighter.ai_source_state.read_field("动作") == 1)
	var local := {}
	for name: String in fighter.ai_senses.sensors:
		var bounds := fighter.ai_senses.local_bounds(name)
		assert(bounds.has_area())
		local[name] = [bounds.position.x, bounds.position.y, bounds.end.x, bounds.end.y]
		fighter.position = Vector2(200, 50)
		fighter.set_facing(-1)
		var mirrored := fighter.ai_senses.global_bounds(name)
		assert(is_equal_approx(mirrored.position.x, 200.0 - bounds.end.x))
		assert(is_equal_approx(mirrored.end.x, 200.0 - bounds.position.x))
	assert(fighter.ai_senses.hit("absmian", fighter) == null)
	var context := fighter.ai_predicate_context
	# Load and DoAction remain separate events, rather than synthesized defaults.
	fighter.ai_source_state.apply_load()
	assert(context.read_field("jumpPower") == 15)
	assert(context.read_field("fall") == false)
	assert(context.read_field("speed") == 0)
	fighter.ai_source_state.apply_frame(1)
	assert(context.read_field("speed") == 6)
	assert(context.read_field("sw") == false)
	assert(context.power_field("kj1zl") == 13)
	assert(context.power_field("missingzl") == null)
	context.write_field("x", 321.5)
	assert(fighter.position.x == 321.5)
	fighter.energy = 123.0
	assert(context.read_field("ql") == 123.0)
	context.write_field("scale_X", -1)
	context.write_field("xscale", -100)
	assert(context.read_field("scale_X") == -1)
	assert(context.read_field("xscale") == -100)
	assert(context.read_field("opponent_action") == null)
	fighter.guarding = true
	fighter.ai_source_state.values["time"] = 7
	fighter.receive_attack({"damage": 10, "horizontal_impulse": 4, "vertical_impulse": 6, "hitstun_ms": 50, "impact_strength": 5}, 1)
	assert(fighter.ai_source_state.read_field("time") == 7)
	assert(fighter.ai_source_state.read_field("tdtime") == 1.5)
	assert(fighter.ai_source_state.read_field("yup") == 0)
	fighter.guarding = true
	fighter.receive_attack({"damage": 10, "horizontal_impulse": 4, "vertical_impulse": 6, "hitstun_ms": 50, "impact_strength": 15}, 1)
	assert(fighter.ai_source_state.read_field("time") == 0)
	assert(fighter.ai_source_state.read_field("bdzl") == 5)
	assert(fighter.ai_source_state.read_field("yup") == 6)
	print("AI_SENSOR_BOUNDS ", JSON.stringify(local, "", false, true))
	print("AI_CONTEXT_SMOKE_OK")
	fighter.queue_free()
	quit()
