extends SceneTree

var failed := false


func _initialize() -> void:
	_run.call_deferred()


func check(condition: bool, message: String) -> void:
	if not condition:
		failed = true
		push_error(message)


func _run() -> void:
	var game = load("res://main.tscn").instantiate()
	root.add_child(game)
	game.set_physics_process(false)
	game._on_menu_confirmed("vs_com")
	check(game.session.root_label == "选人画面" and game.session.modo == 2, "Vs Com menu did not enter character selection")
	game._on_characters_confirmed(["鸣人", "一护"], ["我爱罗", "魂"])
	game._on_map_confirmed("现世")
	check(not game.session.p1cpu and game.session.p2cpu, "Vs Com must control P2 only")
	check(game.naruto.fighter_name == "鸣人" and game.ichigo.fighter_name == "一护", "Fixed fighter selection changed")
	check(game.ichigo.ai_random_clock.difficulty == 5, "Easy difficulty must use source AI=5")
	check(game._input_for(game.ichigo).is_empty(), "CPU must not read P2 keyboard input")
	var child_count: int = game.game_world.get_child_count()
	for service: String in ["jumpxg", "luodixg"]:
		game._cpu_visual_service(service, [])
		check(not game.cpu_unresolved_services.has(service), "Missing source linkage is not an unimplemented visual service")
	check(game.game_world.get_child_count() == child_count, "Missing source linkage created a replacement clip")
	# Supply a known source random sample while retaining the main scene routing.
	var tape: Array = []
	var values := [0.0, 0.8, 0.2, 0.8, 0.8]
	var assignments: Array = game.ichigo.ai_source_state.spec.random_refresh.assignments
	for index in assignments.size():
		tape.append({"site": assignments[index].site, "value": values[index]})
	game.source_random.use_recorded_tape(tape)
	game.ichigo.ai_random_clock.cancel()
	game.ichigo.ai_random_clock.initialize(game.ichigo.ai_source_state, game.source_random, 5, true)
	game.ichigo.ai_random_clock.fire_recorded(500)
	for tick in 600:
		game._advance_fight()
		if not game.battle_intro.active:
			break
	check(not game.battle_intro.active, "Vs Com opening did not finish")
	var key := InputEventKey.new()
	key.keycode = game.session.flash_to_key(int(game.session.codes["d"]))
	key.physical_keycode = key.keycode
	key.pressed = true
	Input.parse_input_event(key)
	Input.flush_buffered_events()
	var player_x: float = game.naruto.position.x
	game._advance_fight()
	check(game._input_for(game.naruto).right, "P1 keyboard input was disabled by CPU mode")
	check(game.naruto.position.x > player_x, "P1 could not move in Vs Com")
	var release := key.duplicate() as InputEventKey
	release.pressed = false
	Input.parse_input_event(release)
	Input.flush_buffered_events()
	var hp: float = game.naruto.health
	var start_x: float = game.ichigo.position.x
	var trace: Array = []
	for tick in 240:
		game._advance_fight()
		trace.append({"tick": tick, "p1": game.naruto.snapshot(), "p2": game.ichigo.snapshot(),
			"p1_y": game.naruto.position.y, "p2_y": game.ichigo.position.y,
			"p1_helper_action": game.naruto_helper.source_action,
			"p2_helper_action": game.ichigo_helper.source_action,
			"pending_timeouts": game.opponent_driver.timeouts.pending_count(),
			"random_samples": game.ichigo.ai_random_clock.sample_count})
	var trace_path := OS.get_environment("BVN_AI_SMOKE_TRACE")
	if not trace_path.is_empty():
		var trace_file := FileAccess.open(trace_path, FileAccess.WRITE)
		check(trace_file != null, "Cannot write requested diagnostic trace")
		if trace_file != null:
			trace_file.store_string(JSON.stringify(trace, "", false, true) + "\n")
			trace_file.close()
	check(game.ichigo.position.x != start_x, "CPU did not move in the main scene")
	check(game.naruto.health < hp, "CPU did not damage the player in the main scene")
	print("VS_COM_RESULT ", JSON.stringify({"player_hp": game.naruto.health,
		"cpu": game.ichigo.snapshot(), "unimplemented_visual_services": game.cpu_unresolved_services.keys()}))
	game._goto_menu()
	check(game.opponent_driver == null and not game.ichigo.ai_timeline_controlled, "CPU driver survived return to menu")
	check(game.ichigo.ai_random_clock.registered_ms == -1, "CPU random interval survived return to menu")
	game._enter_current_fight(3)
	check(game.opponent_driver != null and not game.session.p2cpu, "Versus mode must use the shared source driver")
	check(not game.opponent_driver.controller.context.use_ai and not game.opponent_driver.body_context.use_ai,
		"Versus mode inherited CPU predicates")
	check(game.ichigo.ai_random_clock.registered_ms == -1, "Versus mode started an AI random interval")
	game._goto_menu()
	for node in game.find_children("*", "AudioStreamPlayer", true, false):
		node.stop()
	game.queue_free()
	await process_frame
	print("VS_COM_SMOKE_FAILED" if failed else "VS_COM_SMOKE_OK")
	quit(1 if failed else 0)
