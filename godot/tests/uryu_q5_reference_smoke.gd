extends SceneTree


func _initialize() -> void:
	_run.call_deferred()


func _run() -> void:
	var fixture_path := "res://../evidence/characters/yulong/q5/r04/fixture.json"
	var fixture: Dictionary = JSON.parse_string(FileAccess.get_file_as_string(fixture_path))
	var player := FighterRuntime.new()
	player.fighter_directory = "res://generated/fighters/yulong"
	var opponent := FighterRuntime.new()
	opponent.fighter_directory = "res://generated/fighters/yihu"
	opponent.player_slot = "p2"
	root.add_child(player)
	root.add_child(opponent)
	await process_frame
	player.opponent = opponent
	opponent.opponent = player
	for fighter: FighterRuntime in [player, opponent]:
		fighter.ai_source_state.apply_load()
		fighter.ai_source_state.apply_frame(1)
	player.position = Vector2(float(fixture.setup.p1.x), -25)
	opponent.position = Vector2(float(fixture.setup.p2.x), -25)
	player.energy = float(fixture.setup.p1.energy)
	opponent.energy = float(fixture.setup.p2.energy)
	var registry := SourceCallbackRegistry.new()
	var child_frame_queue: Array[Callable] = []
	player.source_child_frame_requested.connect(
		func(operation: Callable) -> void: child_frame_queue.append(operation)
	)
	var driver: Node = preload("res://player_body_driver.gd").new()
	root.add_child(driver)
	driver.configure(player, "res://generated/fighters/yulong/player_controller", {}, -25, 1000,
		func(_name: String, _args: Array) -> Variant: return null, registry)
	var transitions: Array[Dictionary] = []
	var trace: Array[Dictionary] = []
	var prior_counter := int(player.ai_source_state.read_field("k1n"))
	for tick in range(1, int(fixture.frames) + 1):
		var attack := false
		for input: Dictionary in fixture.inputs:
			if input.slot == "p1" and tick >= int(input.start) and tick < int(input.end):
				attack = "attack" in input.keys
		driver.begin_tick(tick, {"attack": attack})
		driver.advance_timeline()
		driver.prepare_callbacks()
		registry.dispatch(tick)
		player.run_frame_actions()
		while not child_frame_queue.is_empty():
			var operation: Callable = child_frame_queue.pop_front()
			if operation.is_valid():
				operation.call()
		var counter := int(player.ai_source_state.read_field("k1n"))
		if counter != prior_counter:
			transitions.append({"tick": tick, "counter": counter,
				"action": player.action, "frame": player.current_source_frame()})
			prior_counter = counter
		trace.append({"tick": tick, "action": player.action,
			"frame": player.current_source_frame(), "k1n": counter,
			"projectile_variables": player.instance_source_variables("k1atm"),
			"projectile_offset": [player.instance_local_offset("k1atm").x,
				player.instance_local_offset("k1atm").y]})
	var evidence := {
		"fixture": fixture_path,
		"engine": Engine.get_version_info(),
		"counter_transitions": transitions,
		"trace": trace,
	}
	FileAccess.open("res://../evidence/characters/yulong/q5/godot-r04-runtime.json", FileAccess.WRITE).store_string(
		JSON.stringify(evidence, "\t", true, true) + "\n")
	assert(transitions.any(func(event: Dictionary) -> bool: return event.counter == 1),
		"Source frame 184 did not increment k1n in the player callback path")
	assert(transitions.any(func(event: Dictionary) -> bool: return event.counter == 2),
		"The repeated source action did not increment k1n a second time")
	assert(transitions.any(func(event: Dictionary) -> bool: return event.counter == 3),
		"The third source action did not increment k1n a third time")
	driver.stop()
	driver.queue_free()
	player.queue_free()
	opponent.queue_free()
	await process_frame
	print("URYU_Q5_REFERENCE_SMOKE_OK ", JSON.stringify(transitions))
	quit()
