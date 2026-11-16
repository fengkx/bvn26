extends SceneTree


func _initialize() -> void:
	_run.call_deferred()


func _capture(path: String) -> void:
	await process_frame
	await RenderingServer.frame_post_draw
	assert(root.get_texture().get_image().save_png(path) == OK)


func _run() -> void:
	assert(DisplayServer.get_name() != "headless", "This test requires a real renderer")
	var output := OS.get_cmdline_user_args()[0]
	DirAccess.make_dir_recursive_absolute(output)
	root.size = Vector2i(600, 400)
	root.content_scale_size = Vector2i(600, 400)
	var game = load("res://main.tscn").instantiate()
	root.add_child(game)
	game.set_physics_process(false)
	await process_frame
	game._goto_character_selection(3)
	var menu = game.character_selection
	menu.fighters = ["一护", "鸣人"]
	menu._enter_phase(1)
	for card: Dictionary in menu.cards:
		if card.id == "织姬":
			assert(menu._select_grid(Vector2i(card.grid[0], card.grid[1]), 0))
	assert(menu.helpers[0] == "织姬")
	for tick in 60:
		menu.tick({}, {})
	for frame in 120:
		await process_frame
		if menu._text_counts[0] >= str(menu._footer_spec["织姬"].text).length():
			break
	assert(menu._text_counts[0] >= str(menu._footer_spec["织姬"].text).length())
	await _capture(output.path_join("selection.png"))
	game.ko_recorded_timers = true
	game.recorded_training_timers = true
	game._on_characters_confirmed(["一护", "鸣人"], ["织姬", "魂"])
	game._on_map_confirmed("现世")
	for tick in 700:
		game._advance_fight()
		if not game.battle_intro.active:
			break
	assert(not game.battle_intro.active)
	game.naruto.health = 950
	game.naruto.energy = 300
	game.naruto.enter_frame({"summon": true})
	var captured := false
	for tick in 180:
		game._advance_fight()
		if game.naruto_helper.attacking and game.naruto_helper.current_source_frame() == 50:
			assert(game.naruto_helper.visible and game.naruto_helper.visual_child_count() > 0)
			await _capture(output.path_join("healing.png"))
			captured = true
	assert(captured and game.naruto.health == 1090)
	game._stop_combat_drivers()
	game.queue_free()
	await process_frame
	game = null
	assert(await preload("res://tests/audio_shutdown.gd").drain(self))
	print("ZHIJI_VISUAL_CAPTURE_OK selection=true healing=true health=1090")
	quit()
