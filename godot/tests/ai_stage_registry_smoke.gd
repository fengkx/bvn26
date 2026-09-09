extends SceneTree


func _initialize() -> void:
	_run.call_deferred()


func _run() -> void:
	var caster := FighterRuntime.new()
	caster.fighter_directory = "res://generated/fighters/yihu"
	caster.player_slot = "p2"
	var defender := FighterRuntime.new()
	defender.fighter_directory = "res://generated/fighters/minren"
	defender.player_slot = "p1"
	root.add_child(caster)
	root.add_child(defender)
	await process_frame
	caster.opponent = defender
	defender.opponent = caster
	caster.position = Vector2(300, 0)
	var directory := "res://generated/effects/XG_baoqi"
	var spec: Dictionary = JSON.parse_string(FileAccess.get_file_as_string(directory.path_join("stage_hit.json")))
	var registry := StageHitRegistry.new()
	registry.configure(spec)
	var effects: Array[StageHitRuntime] = []
	for index in range(1, 12):
		var effect := StageHitRuntime.new()
		effect.configure(directory, caster, {"pw": 80, "zl": 5, "yup": 0, "hitx": 15, "hdtime": 0, "htype": "击飞"})
		root.add_child(effect)
		assert(registry.register(effect) == "stgk%d_P2" % index)
		effect.play_source_frame(16 if index <= 10 else 3)
		effects.append(effect)
	assert(registry.counter == 1)
	var active := effects[10]
	defender.position += active.instance_global_bounds("mian").get_center() - defender.instance_global_bounds("bdmn").get_center()
	assert(not active.attack_contact(defender).is_empty())
	assert(registry.first_contact(defender, spec.registry.lookup_prefixes).is_empty())
	var replacement := StageHitRuntime.new()
	replacement.configure(directory, caster, active.packet)
	root.add_child(replacement)
	assert(registry.register(replacement) == "stgk2_P2")
	replacement.play_source_frame(3)
	registry.forget(effects[1])
	assert(registry.first_contact(defender, spec.registry.lookup_prefixes).effect == replacement)
	# Source checkHit picks a fighter candidate before an overlapping burst.
	caster.start_action("砍1")
	caster.play_source_frame(177)
	caster.run_frame_actions()
	defender.position += caster.instance_global_bounds("k1atm").get_center() - defender.instance_global_bounds("bdmn").get_center()
	assert(not replacement.attack_contact(defender).is_empty())
	var attack := caster.attack_contact(defender)
	assert(not attack.is_empty())
	var health := defender.health
	assert(CombatResolver.resolve_incoming(defender, caster, null, registry, spec.registry.lookup_prefixes))
	assert(defender.health == health - float(attack.damage))
	caster.start_action("站立")
	caster.run_frame_actions()
	# Start a separate eligible lookup; the previous hit changed receiver clips.
	defender.start_action("站立")
	defender.run_frame_actions()
	defender.position += replacement.instance_global_bounds("mian").get_center() - defender.instance_global_bounds("bdmn").get_center()
	assert(not replacement.attack_contact(defender).is_empty())
	health = defender.health
	assert(CombatResolver.resolve_incoming(defender, caster, null, registry, spec.registry.lookup_prefixes))
	assert(defender.health == health - 80)
	registry.clear_effects()
	assert(registry.counter == 2)
	assert(registry.first_contact(defender, spec.registry.lookup_prefixes).is_empty())
	for effect in effects:
		effect.queue_free()
	replacement.queue_free()
	caster.queue_free()
	defender.queue_free()
	await process_frame
	print("AI_STAGE_REGISTRY_SMOKE_OK")
	quit()
