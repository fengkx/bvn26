extends SceneTree


func _initialize() -> void:
	_run.call_deferred()


func _capture(path: String) -> void:
	await process_frame
	await RenderingServer.frame_post_draw
	assert(root.get_texture().get_image().save_png(path) == OK)


func _run() -> void:
	var args := OS.get_cmdline_user_args()
	assert(args.size() == 1, "Expected evidence output directory")
	var output: String = args[0]
	DirAccess.make_dir_recursive_absolute(output)
	var game = load("res://main.tscn").instantiate()
	root.add_child(game)
	game.set_physics_process(false)
	await process_frame
	game._goto_character_selection(3)
	var menu = game.character_selection
	for card: Dictionary in menu.cards:
		if card.id == "仙鸣":
			assert(menu._select_grid(Vector2i(card.grid[0], card.grid[1]), 0))
	assert(menu.fighters[0] == "仙鸣")
	for tick in 60:
		menu.tick({}, {})
	# The source footer types one character per timer callback. Wait for the
	# visible text, since a locked desktop can deliver render callbacks slowly.
	var footer_ready := false
	for frame in 120:
		await process_frame
		footer_ready = true
		for player in 2:
			var entry: Dictionary = menu._footer_spec[menu.fighters[player]]
			footer_ready = footer_ready and int(menu._text_counts[player]) >= str(entry.text).length()
		if footer_ready:
			break
	assert(footer_ready, "Source footer typing did not finish")
	await _capture(output.path_join("selection.png"))
	game.ko_recorded_timers = true
	game.recorded_training_timers = true
	game._on_characters_confirmed(["仙鸣", "一护"], ["我爱罗", "魂"])
	game._on_map_confirmed("现世")
	game.battle_intro.recorded_polling = true
	game.source_random.use_seed(727)
	game.source_clock.use_explicit_time(0)
	var battle := preload("res://rollback_battle.gd").new()
	assert(battle.configure(game).is_empty())
	var players := {"p1": {}, "p2": {}}
	for slot in players:
		for button in preload("res://rollback_test_session.gd").BUTTONS:
			players[slot][button] = false
	var captured := false
	var attack_start := -1
	for tick in range(1, 501):
		if not game.battle_intro.active and attack_start < 0:
			attack_start = tick
			game.naruto.energy = 300
		players.p1.attack = attack_start > 0 and tick <= attack_start + 3
		players.p1.jump = players.p1.attack
		var callbacks := []
		if game.battle_intro.polling and tick % 15 == 0:
			callbacks.append({"kind": "intro_poll", "phase": "after_actor_advance", "sequence": tick, "time_ms": tick * 33})
		assert(battle.set_frame_events(tick, tick * 33, false, callbacks).is_empty())
		assert(battle.advance(tick, players).is_empty())
		if game.naruto.source_parent_frame == 2 and game.naruto.source_body_available and game.naruto.action == "站立":
			captured = true
			break
		if tick % 30 == 0:
			await process_frame
	assert(captured, "Natural opening and input did not complete required replacement")
	await _capture(output.path_join("in-fight.png"))
	FileAccess.open(output.path_join("metadata.json"), FileAccess.WRITE).store_string(JSON.stringify({
		"method": "Native Godot Compatibility renderer; production selection, natural opening and transformation input",
		"fighter": "仙鸣", "opponent": "一护", "stage": "现世",
		"fighter_directory": game.naruto.fighter_directory,
		"paused": game.naruto.root_zhanting,
		"fight_source_frame": game.naruto.current_source_frame(),
		"engine": Engine.get_version_info().string,
		"viewport": [root.size.x, root.size.y],
		"limitations": "Visual inspection only; no Flash pixel comparison."
	}, "  ") + "\n")
	print("MINRENX_FORM_VISUAL_CAPTURE_OK")
	quit()
