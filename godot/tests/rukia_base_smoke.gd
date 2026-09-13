extends SceneTree


func _initialize() -> void:
	_run.call_deferred()


func _run() -> void:
	var player: FighterRuntime = FighterRuntime.new()
	player.fighter_directory = "res://generated/fighters/rukia"
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
	driver.configure(player, "res://generated/fighters/rukia/player_controller", {}, -25, 1000,
		func(_name: String, _args: Array) -> Variant: return null, registry)
	for tick in range(1, 14):
		var input_tick := tick - 1
		var attack_held := input_tick >= 10 and input_tick < 13
		driver.begin_tick(tick, {"attack": attack_held})
		driver.advance_timeline()
		driver.prepare_callbacks()
		registry.dispatch(tick)
		player.run_frame_actions()
		if tick == 11:
			assert(player.action == "砍1")
			assert(player.current_source_frame() == 218)
		elif tick == 12:
			assert(player.current_source_frame() == 219)
	assert(player.action == "砍1", "A close-range P1 attack should dispatch to source label 砍1")
	assert(player.current_source_frame() == 220, "The recorded [10,13) attack tape reaches SWF frame 220")
	assert(player.fighter_directory == "res://generated/fighters/rukia")
	assert(player._combat["source"]["timeline_symbol_id"] == 533)
	driver.stop()
	player.queue_free()
	opponent.queue_free()
	await process_frame
	print("RUKIA_BASE_SMOKE_OK")
	quit()
