extends SceneTree

var game: Node
var intro_started := [false]

const CANDIDATES := [
	{"name": "樱", "directory": "sakura", "moves": [KEY_D, KEY_D]},
	{"name": "露其雅", "directory": "rukia", "moves": [KEY_A]},
	{"name": "石田", "directory": "yulong", "moves": [KEY_A, KEY_A, KEY_W]},
]


func _initialize() -> void:
	_run.call_deferred()


func _key(code: Key, pressed: bool) -> void:
	var event := InputEventKey.new()
	event.keycode = code
	event.physical_keycode = code
	event.pressed = pressed
	Input.parse_input_event(event)
	Input.flush_buffered_events()


func _step(frames: int = 1) -> void:
	for _frame in frames:
		game._physics_process(1.0 / 30.0)
		await process_frame


func _tap(code: Key) -> void:
	_key(code, true)
	await _step()
	_key(code, false)
	await _step(5)


func _confirm_after_source_delay() -> void:
	await create_timer(0.55).timeout
	await process_frame


func _assert_candidate_available(candidate: Dictionary) -> void:
	for slot: String in GameSession.DEFAULT_CODES:
		game.session.bind_slot(slot, int(GameSession.DEFAULT_CODES[slot]))
	assert(game.character_selection.available.fighters.get(str(candidate.name), "") == str(candidate.directory),
		"Production registry is missing %s" % candidate.name)
	assert(game.character_selection.available.helpers.get("松本", "") == "jinye",
		"Production registry is missing the source-mapped Ino helper")
	assert(game.battle_intro.spec["fighters"].has(str(candidate.directory)),
		"Production intro registry is missing %s" % candidate.directory)


func _choose_candidate_moves(moves: Array) -> void:
	for code: Key in moves:
		await _tap(code)


func _select_match(candidate: Dictionary) -> void:
	intro_started[0] = false
	game = load("res://main.tscn").instantiate()
	root.add_child(game)
	game.set_physics_process(false)
	await process_frame
	_assert_candidate_available(candidate)
	game.battle_intro.fight_started.connect(func() -> void: intro_started[0] = true)

	await _step(72)
	assert(game.title_menu.current_item().id == "vs_com")
	await _tap(KEY_S)
	assert(game.title_menu.current_item().id == "versus")
	_key(KEY_J, true)
	await _step(16)
	_key(KEY_J, false)
	await _step(30)
	assert(game.session.root_label == "选人画面")
	assert(game.session.modo == 3 and game.character_selection.phase == 0)

	# All confirmations use the production roster through normal keys.
	await _choose_candidate_moves(candidate.moves)
	assert(game.character_selection.fighters[0] == str(candidate.name))
	await _tap(KEY_J)
	await _confirm_after_source_delay()
	assert(game.character_selection.enabled[1])
	await _tap(KEY_LEFT)
	assert(game.character_selection.fighters[1] == "一护")
	await _tap(KEY_KP_1)
	await _confirm_after_source_delay()
	assert(game.character_selection.phase == 1)

	await _tap(KEY_D)
	await _tap(KEY_D)
	assert(game.character_selection.helpers[0] == "松本")
	await _tap(KEY_J)
	await _confirm_after_source_delay()
	await _tap(KEY_LEFT)
	assert(game.character_selection.helpers[1] == "魂")
	await _tap(KEY_KP_1)
	await _confirm_after_source_delay()
	assert(game.session.root_label == "地图")
	assert(game.naruto.fighter_directory == "res://generated/fighters/%s" % candidate.directory)
	assert(game.ichigo.fighter_directory == "res://generated/fighters/yihu")
	assert(game.naruto_helper.helper_directory == "res://generated/helpers/jinye")
	assert(game.ichigo_helper.helper_directory == "res://generated/helpers/kon")

	await _tap(KEY_J)
	await _confirm_after_source_delay()
	assert(game.session.root_label == "游戏场景")
	assert(game.battle_intro.active)
	assert(game.battle_intro.spec["fighters"].has(str(candidate.directory)))
	await _step(40)
	assert(game.naruto.action == "开场", "BattleIntro did not enter the candidate's opening action")


func _finish_natural_intro() -> void:
	for _frame in 900:
		if intro_started[0]:
			break
		await _step()
	assert(intro_started[0], "Natural intro did not reach source start-fight event")
	assert(not game.battle_intro.active)


func _check_candidate_action_and_ino_summon() -> void:
	_key(KEY_J, true)
	await _step(10)
	_key(KEY_J, false)
	await _step(2)
	var fighter_id := str(game.naruto.fighter_directory.get_file())
	assert(game.naruto.action in ["砍1", "砍2"], "%s attack input did not enter a source attack" % fighter_id)
	for _frame in 120:
		if game.naruto.action == "站立":
			break
		await _step()
	# The source zhaoHuan command requires 100 energy. Seed that authored
	# precondition in this isolated flow test so the real O input can be checked.
	game.naruto.energy = 100.0
	_key(KEY_O, true)
	await _step()
	_key(KEY_O, false)
	for _frame in 120:
		if game.naruto_helper.attacking:
			break
		await _step()
	assert(game.naruto_helper.helper_id == "松本", "%s did not load selected Ino" % fighter_id)
	assert(game.naruto_helper.attacking, "%s selected Ino did not activate from summon input" % fighter_id)
	assert(game.naruto_helper.current_source_frame() >= 2)


func _close_game() -> void:
	game._goto_menu()
	for node: Node in game.find_children("*", "AudioStreamPlayer", true, false):
		var player := node as AudioStreamPlayer
		player.stop()
		player.stream = null
	for node: Node in game.find_children("*", "AudioStreamPlayer2D", true, false):
		var player := node as AudioStreamPlayer2D
		player.stop()
		player.stream = null
	await process_frame
	await process_frame
	root.remove_child(game)
	game.free()
	await process_frame
	await process_frame


func _run() -> void:
	for candidate: Dictionary in CANDIDATES:
		await _select_match(candidate)
		assert(game.naruto.fighter_directory.get_file() == str(candidate.directory))
		assert(game.naruto_helper.helper_id == "松本")
		await _finish_natural_intro()
		await _check_candidate_action_and_ino_summon()
		await _close_game()
	print("ROSTER_CANDIDATE_FLOW_SMOKE_OK")
	quit()
