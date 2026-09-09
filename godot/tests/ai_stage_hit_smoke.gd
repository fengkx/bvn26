extends SceneTree


func _initialize() -> void:
	_run.call_deferred()


func _run() -> void:
	var caster := FighterRuntime.new()
	caster.fighter_directory = "res://generated/fighters/yihu"
	var defender := FighterRuntime.new()
	defender.fighter_directory = "res://generated/fighters/minren"
	root.add_child(caster)
	root.add_child(defender)
	await process_frame
	caster.opponent = defender
	defender.opponent = caster
	caster.position = Vector2(300, 0)
	caster.set_facing(-1)
	var effect := StageHitRuntime.new()
	effect.configure("res://generated/effects/XG_baoqi", caster,
		{"pw": 80, "zl": 5, "yup": 0, "hitx": 15, "hdtime": 0, "htype": "击飞"})
	root.add_child(effect)
	assert(effect.attack_contact(defender).is_empty())
	caster.position.x = 500
	assert(effect.position.x == 300 and effect.scale.x == -1)
	effect.advance_timeline()
	assert(effect.attack_contact(defender).is_empty())
	effect.advance_timeline()
	var bounds := effect.instance_global_bounds("mian")
	assert(bounds.has_area())
	defender.position += bounds.get_center() - defender.instance_global_bounds("bdmn").get_center()
	var packet := effect.attack_contact(defender)
	assert(packet["damage"] == 80 and packet["reaction_label"] == "击飞")
	assert(not effect.attack_contact(defender).is_empty())
	assert(effect.attack_contact(caster).is_empty())
	defender.ai_source_state.values["canhit"] = false
	assert(effect.attack_contact(defender).is_empty())
	defender.ai_source_state.values["canhit"] = true
	var health := defender.health
	effect.apply_attack_contact(packet, defender)
	assert(defender.health == health - 80)
	while effect.current_source_frame() < 16:
		effect.advance_timeline()
	assert(not effect.instance_global_bounds("mian").has_area())
	assert(effect.attack_contact(defender).is_empty())
	while effect.current_source_frame() < 20:
		effect.advance_timeline()
	effect.run_frame_actions()
	assert(effect.expired and effect.is_queued_for_deletion())
	caster.queue_free()
	defender.queue_free()
	await process_frame
	print("AI_STAGE_HIT_SMOKE_OK")
	quit()
