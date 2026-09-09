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
	attacker.opponent = defender
	defender.opponent = attacker
	attacker.position = Vector2(200, 0)
	defender.position = Vector2(200, 0)
	attacker.start_action("砍1")
	attacker.play_source_frame(174)
	attacker.run_frame_actions()
	var first := attacker.attack_contact(defender, true)
	assert(not first.is_empty())
	attacker.mark_attack_hit(first["instance_name"])
	# No placement change: a new receiver query must still see the retained hitbox.
	assert(attacker.attack_contact(defender, true) == first)
	for disabled: Variant in [false, null, 0]:
		defender.ai_source_state.values["canhit"] = disabled
		assert(attacker.attack_contact(defender, true).is_empty())
	defender.ai_source_state.values["canhit"] = true
	assert(attacker.attack_contact(defender, true) == first)
	defender.root_zhanting = true
	assert(attacker.attack_contact(defender, true).is_empty())
	defender.root_zhanting = false
	assert(attacker.attack_contact(defender, true) == first)
	attacker.queue_free()
	defender.queue_free()
	await process_frame
	print("SOURCE_REPEAT_CONTACT_SMOKE_OK")
	quit()
