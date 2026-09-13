extends SceneTree


func _initialize() -> void:
	_run.call_deferred()


func _run() -> void:
	var player: FighterRuntime = FighterRuntime.new()
	player.fighter_directory = "res://generated/fighters/sakura"
	var opponent: FighterRuntime = FighterRuntime.new()
	opponent.fighter_directory = "res://generated/fighters/yihu"
	opponent.player_slot = "p2"
	root.add_child(player)
	root.add_child(opponent)
	player.opponent = opponent
	opponent.opponent = player
	for fighter: FighterRuntime in [player, opponent]:
		fighter.ai_source_state.apply_load()
		fighter.ai_source_state.apply_frame(1)
	player.position = Vector2(300, -25)
	opponent.position = Vector2(350, -25)

	var registry := SourceCallbackRegistry.new()
	var driver: Node = preload("res://player_body_driver.gd").new()
	root.add_child(driver)
	driver.configure(player, "res://generated/fighters/sakura/player_controller", {}, -25, 1000,
		func(_name: String, _args: Array) -> Variant: return null, registry)
	driver.begin_tick(1, {"attack": true})
	driver.advance_timeline()
	driver.prepare_callbacks()
	registry.dispatch(1)
	player.run_frame_actions()
	assert(player.fighter_name == "樱")
	assert(player._combat["source"]["timeline_symbol_id"] == 630)
	assert(player.action == "砍1", "A close-range P1 attack should dispatch to source label 砍1")
	assert(player.current_source_frame() == 205, "砍1 should start at source frame 205")
	assert(player.ai_senses.sensors.size() == 11)

	var cpu: FighterRuntime = FighterRuntime.new()
	cpu.fighter_directory = "res://generated/fighters/sakura"
	root.add_child(cpu)
	var cpu_driver := AiCpuDriver.new()
	root.add_child(cpu_driver)
	cpu_driver.configure(cpu, "res://generated/fighters/sakura/ai_controller", {}, -25, 1000,
		{}, func(_name: String, _args: Array) -> Variant: return null)
	assert(cpu.ai_timeline_controlled)
	assert(cpu.source_body != null)
	assert(cpu_driver.controller._hooks.size() > 0)

	cpu_driver.stop()
	driver.stop()
	player.queue_free()
	opponent.queue_free()
	cpu.queue_free()
	await process_frame
	print("SAKURA_IMPORT_SMOKE_OK")
	quit()
