extends SceneTree


func _initialize() -> void:
	_run.call_deferred()


func _run() -> void:
	var attacker := FighterRuntime.new()
	attacker.fighter_directory = "res://generated/fighters/minren"
	var defender := FighterRuntime.new()
	defender.fighter_directory = "res://generated/fighters/yihu"
	root.add_child(attacker)
	root.add_child(defender)
	await process_frame
	attacker.opponent = defender
	defender.opponent = attacker
	attacker.position = Vector2(200, 0)
	defender.position = Vector2(200, 0)
	attacker.start_action("砍1")
	attacker.play_source_frame(174)
	attacker.run_frame_actions()
	assert(not attacker.attack_contact(defender).is_empty())
	var health := defender.health
	for disabled: Variant in [null, false, 0]:
		defender.ai_source_state.values["canhit"] = disabled
		CombatResolver.resolve_pair(attacker, defender)
		assert(defender.health == health)
	# A rejected lookup must not mark the attack instance as already consumed.
	defender.ai_source_state.values["canhit"] = true
	defender.root_zhanting = true
	assert(attacker.attack_contact(defender).is_empty())
	defender.root_zhanting = false
	CombatResolver.resolve_pair(attacker, defender)
	assert(defender.health < health)
	var helper := HelperRuntime.new()
	helper.helper_directory = "res://generated/helpers/woailuo"
	root.add_child(helper)
	helper.activate({"x": 200, "y": 0, "facing": 1, "start_frame": 2}, attacker)
	helper.play_source_frame(44)
	defender.start_action("站立")
	defender.run_frame_actions()
	defender.position += helper.instance_global_bounds("atm1").get_center() - defender.instance_global_bounds("bdmn").get_center()
	assert(not helper.attack_contact(defender).is_empty())
	defender.ai_source_state.values["canhit"] = false
	health = defender.health
	CombatResolver.resolve_helpers([helper], [attacker, defender])
	assert(defender.health == health)
	defender.ai_source_state.values["canhit"] = true
	CombatResolver.resolve_helpers([helper], [attacker, defender])
	assert(defender.health < health)
	helper.queue_free()
	attacker.queue_free()
	defender.queue_free()
	await process_frame
	print("AI_HIT_GATE_SMOKE_OK")
	quit()
