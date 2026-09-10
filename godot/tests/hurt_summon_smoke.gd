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
	world.add_child(cpu)
	world.add_child(player)
	await process_frame
	cpu.opponent = player
	player.opponent = cpu
	var services := AiCombatServices.new()
	services.fighter = cpu
	services.effect_parent = world
	services.super_runtime = SuperRuntime.new()
	services.stage_registry = StageHitRegistry.new()
	var spec: Dictionary = JSON.parse_string(FileAccess.get_file_as_string(
		"res://generated/effects/XG_baoqi/stage_hit.json"))
	services.stage_registry.configure(spec)
	services.stage_lookup_order = spec.registry.lookup_prefixes
	services.remaining_services = func(name: String, _args: Array) -> Variant:
		assert(name == "applyColors")
		return null
	var driver := AiCpuDriver.new()
	world.add_child(driver)
	driver.configure(cpu, "res://generated/fighters/yihu/ai_controller", {}, 0, 1000,
		{"touchFloor": null}, services.invoke, true)
	# Keep both actors across normal summons and repeated airborne escapes.
	for cycle in 2:
		cpu.goto_ai_label("站立", true)
		cpu.run_frame_actions()
		cpu.energy = 300
		cpu.helper_spawn.clear()
		cpu.goto_ai_label("招换", true)
		for tick in 50:
			cpu.run_frame_actions()
			if not cpu.helper_spawn.is_empty():
				break
			cpu.advance_ai_timeline()
		assert(not cpu.helper_spawn.is_empty() and cpu.energy == 200 and cpu.bs == 1)
		cpu.helper_spawn.clear()
		cpu.goto_ai_label("站立", true)
		cpu.run_frame_actions()
		cpu.energy = 300
		cpu.position = Vector2(700, -125)
		player.position = Vector2(100, -25)
		cpu.ai_source_state.values.merge({"goran": 0, "hstm": 0, "time": 0,
			"htx": 0, "yup": 0, "tdtime": 50, "touch": false}, true)
		# Source beidax(true) must not call the non-flying escape branch.
		driver.body.beidax(true)
		assert(driver.timeouts.pending_count() == 0 and cpu.energy == 300)
		# A paused non-flying callback must also leave the escape untouched.
		cpu.root_zhanting = true
		driver.body.beidax(false)
		assert(driver.timeouts.pending_count() == 0 and cpu.energy == 300)
		cpu.root_zhanting = false
		driver.body.beidax(false)
		assert(cpu.energy == 200 and driver.timeouts.pending_count() == 1)
		assert(cpu.ai_source_state.read_field("hurtSkling") == true)
		assert(driver.timeouts.fire_recorded(cycle + 1))
		assert(cpu.action == "招换" and services.stage_effects.size() == 1)
		for tick in 50:
			cpu.run_frame_actions()
			if not cpu.helper_spawn.is_empty() or cpu.energy != 200 or cpu.bs != 0:
				print("HURT_SUMMON_DIFFERENCE cycle=", cycle, " frame=", cpu.current_source_frame(),
					" energy=", cpu.energy, " bs=", cpu.bs, " helper=", cpu.helper_spawn)
				push_error("Source doZhaoHuan returns during hurtSkling: no helper, energy cost, or bs write")
				quit(1)
				return
			if cpu.action == "站立":
				break
			cpu.advance_ai_timeline()
		assert(cpu.action == "站立")
		assert(cpu.ai_source_state.read_field("hurtSkling") == false)
		print("HURT_SUMMON_CYCLE_OK ", cycle)
		for effect in services.stage_effects:
			services.stage_registry.forget(effect)
			effect.queue_free()
		services.stage_effects.clear()
	driver.stop()
	services.clear()
	world.queue_free()
	await process_frame
	print("HURT_SUMMON_SMOKE_OK")
	quit()
