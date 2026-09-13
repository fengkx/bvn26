extends SceneTree


func _initialize() -> void:
	_run.call_deferred()


func _run() -> void:
	var player := FighterRuntime.new()
	player.fighter_directory = "res://generated/fighters/rukia"
	var opponent := FighterRuntime.new()
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
	opponent.set_facing(-1)
	var registry := SourceCallbackRegistry.new()
	var no_service := func(_name: String, _args: Array) -> Variant: return null
	var receiver_calls := {"beida": 0}
	var opponent_service := func(name: String, _args: Array) -> Variant:
		if name == "receive:beida":
			receiver_calls["beida"] += 1
		return null
	var player_driver: Node = preload("res://player_body_driver.gd").new()
	var opponent_driver := AiCpuDriver.new()
	root.add_child(player_driver)
	root.add_child(opponent_driver)
	player_driver.configure(player, player.fighter_directory + "/player_controller", {}, -25, 1000,
		no_service, registry)
	opponent_driver.configure(opponent, opponent.fighter_directory + "/player_controller", {}, -25,
		1000, {"touchFloor": null}, opponent_service, false, registry)
	for tick in range(1, 16):
		var input_tick := tick - 1
		var attack := input_tick >= 10 and input_tick < 13
		player_driver.begin_tick(tick, {"attack": attack})
		opponent_driver.begin_display_tick(tick)
		player_driver.advance_timeline()
		opponent_driver.advance_timeline()
		player_driver.prepare_callbacks()
		player_driver.prepare_frame_actions(player._ai_pending_frames.size())
		opponent_driver.initial_frame_count = opponent._ai_pending_frames.size()
		registry.dispatch(tick)
		player.run_frame_actions()
		opponent.run_frame_actions()
		if tick in [13, 14, 15]:
			print("RUKIA_GEOMETRY ", JSON.stringify({
				"tick": tick,
				"p1_frame": player.current_source_frame(),
				"p1_x": player.position.x,
				"p1_facing": player.facing,
				"p1_root_transform": player.global_transform,
				"p1_names": player.current_named_instances(),
				"k1atm": player.instance_global_bounds("k1atm"),
				"attack": player.active_attack(),
				"p2_frame": opponent.current_source_frame(),
				"p2_x": opponent.position.x,
				"p2_facing": opponent.facing,
				"p2_root_transform": opponent.global_transform,
				"p2_names": opponent.current_named_instances(),
				"bdmn": opponent.instance_global_bounds("bdmn"),
				"receiver": opponent.has_active_hit_receiver(),
				"receiver_calls": receiver_calls.duplicate(),
				"source_contact": player.attack_contact(opponent, true),
			}))
	player_driver.stop()
	opponent_driver.stop()
	player.queue_free()
	opponent.queue_free()
	await process_frame
	quit()
