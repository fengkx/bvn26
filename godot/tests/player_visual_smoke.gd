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
	# Let the queued Ready-to-stand source transition finish before holding input.
	for tick in 5:
		game._advance_fight()
	# Isolate locomotion from the opponent's attack/hurt direction rules.
	game.naruto.position.x = 200
	game.ichigo.position.x = game.game_world.wall_max() - 50
	for fighter in [game.naruto, game.ichigo]:
		fighter.ai_source_state.values["_lastX"] = fighter.position.x
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
	for tick in range(2, 7):
		game._advance_fight()
		check(game.naruto.unnamed_sprite_local_frame(31) == tick, "Main-scene held input froze run animation: tick=%s frame=%s child=%s action=%s" % [tick, game.naruto.current_source_frame(), game.naruto.unnamed_sprite_local_frame(31), game.naruto.action])
		check(game.naruto.global_transform.x.x > 0, "Main-scene right input rendered left-facing")
	var release := key.duplicate() as InputEventKey
	release.pressed = false
	Input.parse_input_event(release)
	Input.flush_buffered_events()
	# Reverse through the same production keyboard route with a fresh event.
	key = key.duplicate() as InputEventKey
	key.keycode = game.session.flash_to_key(int(game.session.codes["a"]))
	key.physical_keycode = key.keycode
	Input.parse_input_event(key)
	Input.flush_buffered_events()
	for tick in 16:
		game._advance_fight()
		check(game.naruto.facing == -1 and game.naruto.global_transform.x.x < 0,
			"Main-scene left input lost rendered facing: %s" % game.naruto.snapshot())
		check(game.naruto.global_transform.y.y > 0, "Facing inverted the vertical axis")
	release = key.duplicate() as InputEventKey
	release.pressed = false
	Input.parse_input_event(release)
	Input.flush_buffered_events()
	for tick in 4:
		game._advance_fight()
	check(game.naruto.action == "站立", "Released movement did not leave run")
	# Release intro and fighter playbacks before this accelerated fixture exits.
	for player in game.find_children("*", "AudioStreamPlayer", true, false):
		player.stop()
		player.stream = null
	await process_frame
	game._goto_menu()
	game.queue_free()
	await process_frame
	await process_frame
	print("PLAYER_VISUAL_SMOKE_FAILED" if failed else "PLAYER_VISUAL_SMOKE_OK")
	quit(1 if failed else 0)
