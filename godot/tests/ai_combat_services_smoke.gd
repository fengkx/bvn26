extends SceneTree


func _initialize() -> void:
	_run.call_deferred()


func _run() -> void:
	var world := Node2D.new()
	root.add_child(world)
	var cpu := FighterRuntime.new()
	cpu.fighter_directory = "res://generated/fighters/yihu"
	cpu.player_slot = "p2"
	var player := FighterRuntime.new()
	player.fighter_directory = "res://generated/fighters/minren"
	player.player_slot = "p1"
	world.add_child(cpu)
	world.add_child(player)
	await process_frame
	cpu.opponent = player
	player.opponent = cpu
	cpu.position.x = 300
	cpu.energy = 200
	cpu.ai_source_state.values["goran"] = 0
	var services := AiCombatServices.new()
	services.fighter = cpu
	services.effect_parent = world
	services.super_runtime = SuperRuntime.new()
	services.stage_registry = StageHitRegistry.new()
	var spec: Dictionary = JSON.parse_string(FileAccess.get_file_as_string(
		"res://generated/effects/XG_baoqi/stage_hit.json"))
	services.stage_registry.configure(spec)
	services.stage_lookup_order = spec.registry.lookup_prefixes
	var driver := AiCpuDriver.new()
	world.add_child(driver)
	driver.configure(cpu, "res://generated/fighters/yihu/ai_controller", {}, 0, 1000,
		{"touchFloor": null}, services.invoke, true)
	driver.body.doHurtSkill()
	assert(cpu.energy == 100 and cpu.bs == 1)
	assert(cpu.root_zhanting and player.root_zhanting)
	assert(not player.timeline_playing)
	assert(services.super_runtime.last_xg == "XG_bsq")
	assert(services.stage_effects.is_empty())
	assert(driver.timeouts.fire_recorded(1))
	assert(cpu.bs == 0 and not cpu.root_zhanting and not player.root_zhanting)
	assert(player.timeline_playing and cpu.action == "招换")
	assert(services.stage_effects.size() == 1)
	var burst := services.stage_effects[0]
	assert(burst.source_name == "stgk1_P2" and burst.current_source_frame() == 1)
	for tick in 2:
		services.advance_stage_timelines()
		services.run_stage_frames()
	player.position += burst.instance_global_bounds("mian").get_center() - player.instance_global_bounds("bdmn").get_center()
	var contact := services.stage_registry.first_contact(player, spec.registry.lookup_prefixes)
	assert(not contact.is_empty())
	var hp := player.health
	burst.apply_attack_contact(contact.packet, player)
	assert(player.health == hp - 80)
	while not services.stage_effects.is_empty():
		services.advance_stage_timelines()
		services.run_stage_frames()
	assert(burst.expired)
	# A receiver is callable only after its authored placement tick.
	cpu.start_action("站立")
	cpu.run_frame_actions()
	cpu.ai_source_state.apply_load()
	cpu.ai_source_state.values.merge({"_lastX": 0, "wdFrameX": 0, "goran": 400, "attran": 400,
		"jumpran": 400, "defran": 400, "bisharan": 400}, true)
	player.start_action("砍1")
	player.play_source_frame(174)
	player.run_frame_actions()
	cpu.position += player.instance_global_bounds("k1atm").get_center() - cpu.instance_global_bounds("bdmn").get_center()
	driver.body_context.floor_y = cpu.position.y
	var hit := player.attack_contact(cpu)
	assert(not hit.is_empty())
	var profile: Dictionary = JSON.parse_string(FileAccess.get_file_as_string("res://../spec/execution-profile.json"))
	hp = cpu.health
	driver.begin_display_tick(100)
	driver.run_enter_frame(profile)
	assert(cpu.health == hp)
	driver.begin_display_tick(101)
	driver.run_enter_frame(profile)
	assert(cpu.health == hp - float(hit.damage))
	driver.stop()
	services.clear()
	world.queue_free()
	await process_frame
	print("AI_COMBAT_SERVICES_SMOKE_OK")
	quit()
