extends "res://tests/roster_candidate_flow_smoke.gd"


func _run() -> void:
	var candidate := {"name": "鼬", "directory": "itachi"}
	game = load("res://main.tscn").instantiate()
	root.add_child(game)
	game.set_physics_process(false)
	await process_frame
	_assert_candidate_available(candidate)
	game.battle_intro.fight_started.connect(func() -> void: intro_started[0] = true)
	await _step(72)
	assert(game.title_menu.current_item().id == "single")
	await _tap(KEY_S)
	assert(game.title_menu.current_item().id == "vs_com")
	_key(KEY_J, true)
	while game.session.root_label != "选人画面":
		await _step()
	_key(KEY_J, false)
	await _step(12)
	assert(game.session.modo == 2 and game.character_selection.phase == 0)
	for code: Key in _source_keyboard_path(candidate):
		await _tap(code)
		await _step(12)
	assert(game.character_selection.fighters[0] == "鼬", str(game.character_selection.fighters))
	await _tap(KEY_J)
	await _confirm_after_source_delay()
	assert(game.character_selection.enabled[1])
	await _tap(KEY_A)
	assert(game.character_selection.fighters[1] == "一护")
	await _tap(KEY_J)
	await _confirm_after_source_delay()
	assert(game.character_selection.phase == 1)
	for code: Key in _source_keyboard_path({"name": "松本"}):
		await _tap(code)
	assert(game.character_selection.helpers[0] == "松本")
	await _tap(KEY_J)
	await _confirm_after_source_delay()
	for code: Key in _source_keyboard_path({"name": "魂"}, 1, false):
		await _tap(code)
	assert(game.character_selection.helpers[1] == "魂")
	await _tap(KEY_J)
	await _confirm_after_source_delay()
	assert(game.session.root_label == "地图")
	await _tap(KEY_J)
	await _confirm_after_source_delay()
	assert(game.naruto.fighter_directory.get_file() == "itachi")
	await _finish_natural_intro()
	await _check_candidate_action_and_ino_summon()
	await _close_game()
	print("ITACHI_SELECTION_SMOKE_OK mode=vs_com input=keyboard intro=natural attack=true summon=true")
	quit()
