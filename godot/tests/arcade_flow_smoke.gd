extends SceneTree


func _initialize() -> void:
	call_deferred("_run")


func _key(code: Key) -> InputEventKey:
	var event := InputEventKey.new()
	event.keycode = code
	event.physical_keycode = code
	event.pressed = true
	return event


func _finish_loading(game) -> void:
	assert(game._pack_screen != null and game._pack_screen.loaded)
	game._pack_screen._process(float(game._pack_screen.timeline.frames.size()))
	await process_frame


func _run() -> void:
	var game = load("res://main.tscn").instantiate()
	root.add_child(game)
	game.set_physics_process(false)
	var screen = game.arcade
	assert(not screen._quote.has_theme_font_override("font"))
	for i in 72:
		game.title_menu.apply_held({})
	assert(game.title_menu.current_item().id == "single")
	for i in 15:
		game.title_menu.apply_held({"confirm": true})
	assert(screen.visible and game.session.root_label == "HOWTOPLAY")
	for i in 14:
		screen.tick()
	game._input(_key(KEY_J))
	assert(screen.frame == 1249)
	for i in 11:
		screen.tick()
	assert(game.character_selection.visible and game.character_selection.enabled == [true, false])
	var selector = game.character_selection
	selector._finish_confirmation(0)
	assert(selector.phase == 1 and selector.enabled == [true, false])
	selector._finish_confirmation(0)
	await _finish_loading(game)
	assert(game.session.root_label == "游戏场景" and game.session.p2cpu)
	assert(not game.map_selection.visible)
	var player: String = screen.player
	var helper: String = screen.helper
	for stage in 8:
		assert(screen.stage == stage and screen.player == player and screen.helper == helper)
		assert(game.selected_stage == screen.encounter().map)
		assert(game.ichigo_helper.helper_directory.get_file() == selector.available.helpers[screen.encounter().helper])
		assert(game.opponent_driver.controller.context.use_ai)
		if stage == 2:
			game.ko_state["_root.p2ws"] = 3
			game.timeout_timeline.controller.event_11()
			game._physics_process(1.0 / 30.0)
			assert(screen.screen == "continue")
			game._input(_key(KEY_Y))
			assert(screen.stage == stage and selector.visible)
			game._on_characters_confirmed([player, ""], [helper, ""])
		game.ko_state["_root.p1ws"] = 3
		game.ko_timeline.controller.event_13()
		game._physics_process(1.0 / 30.0)
		assert(screen.screen == "win")
		for i in 23:
			screen.tick()
			assert(screen._page_cache.size() <= 1)
		if stage < 7:
			assert(screen._page_cache.is_empty())
		if stage == 0:
			assert(not screen._quote.text.is_empty())
			var font: Font = screen._quote.get_theme_font("font")
			assert(font.resource_path == OnlineUserTextFont.CJK_FALLBACK_PATH)
			for lines: Array in screen.data.quotes.values():
				for line: String in lines:
					for character in line:
						assert(character == "\n" or font.has_char(character.unicode_at(0)), line)
		if stage < 7:
			game._input(_key(KEY_J))
			await _finish_loading(game)
			assert(game.session.root_label == "游戏场景")
		await process_frame
	assert(screen.screen == "ending" and screen.stage == 8)
	while screen.frame < 318:
		screen.tick()
		assert(screen._page_cache.size() <= 1)
		for image: Image in screen._page_cache.values():
			assert(image.get_data_size() <= 600 * 800 * 3)
	assert(screen._page_cache.is_empty())
	game._input(_key(KEY_ENTER))
	assert(game.session.root_label == "MENU" and screen.stage == 0)

	# Four rivals start in a transformed BODY which cannot be picked on the menu.
	for entry in [["小乌", 5], ["蓝染", 6], ["我爱罗", 6], ["带土", 6]]:
		screen.stage = entry[1]
		game._on_characters_confirmed([entry[0], ""], ["魂", ""])
		var form: Dictionary = screen.data.forms[screen.encounter().fighter]
		assert(game.ichigo.fighter_directory.get_file() == form.id)
		assert(game.opponent_driver.controller.context.use_ai)
		game.ko_state["_root.p2ws"] = 3
		game.ko_timeline.controller.event_13()
		game._physics_process(1.0 / 30.0)
		assert(screen.screen == "continue")
		game._input(_key(KEY_N))
		for i in 149:
			screen.tick()
		assert(game.session.root_label == "MENU" and screen.stage == 0)
		await process_frame
	game.queue_free()
	await process_frame
	print("ARCADE_FLOW_OK stages=8 rivals=4 continue_retry=true timeout=true gameover=true ending=true")
	quit()
