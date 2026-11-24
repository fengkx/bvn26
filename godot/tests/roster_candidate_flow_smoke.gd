extends SceneTree

var game: Node
var intro_started := [false]

const CANDIDATES := [
	{"name": "樱", "directory": "sakura", "moves": [KEY_D, KEY_D]},
	{"name": "露其雅", "directory": "rukia", "moves": [KEY_A]},
	{"name": "石田", "directory": "yulong", "moves": [KEY_A, KEY_A, KEY_W]},
]

const BASE_FORM_CANDIDATES := [
	{"name": "白哉", "directory": "byakuya", "moves": [KEY_A, KEY_A, KEY_A, KEY_A, KEY_A]},
	{"name": "小李", "directory": "lee", "moves": [KEY_D, KEY_D, KEY_D, KEY_D, KEY_D, KEY_D, KEY_D, KEY_D, KEY_D, KEY_D]},
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


func _assert_base_roster_shared_by_vs_modes() -> void:
	for mode in [2, 3]:
		game.character_selection.reset(mode)
		var visible_ids: Array[String] = []
		for card: Dictionary in game.character_selection.cards:
			visible_ids.append(str(card.id))
		assert(visible_ids.has("白哉") and visible_ids.has("小李"),
			"Base roster differs or is incomplete in VS mode %d" % mode)
		game.character_selection.leave()


func _choose_candidate_moves(moves: Array) -> void:
	for code: Key in moves:
		await _tap(code)


func _selection_neighbor(index: int, direction: String) -> int:
	var point := Vector2i(int(game.character_selection.cards[index].grid[0]), int(game.character_selection.cards[index].grid[1]))
	var horizontal := direction == "left" or direction == "right"
	var step := -1 if direction == "left" or direction == "up" else 1
	var low := 9999
	var high := 0
	for card: Dictionary in game.character_selection.cards:
		var value := int(card.grid[0 if horizontal else 1])
		low = mini(low, value)
		high = maxi(high, value)
	var start := point.x if horizontal else point.y
	if step < 0 and start <= low:
		start = high + 1
	elif step > 0 and start >= high:
		start = low - 1
	for offset in [0, -2, 2]:
		var coordinate := start + step
		while coordinate >= low and coordinate <= high:
			var candidate := Vector2i(coordinate, point.y + offset) if horizontal else Vector2i(point.x + offset, coordinate)
			for next_index in game.character_selection.cards.size():
				var next_grid: Array = game.character_selection.cards[next_index].grid
				if candidate == Vector2i(int(next_grid[0]), int(next_grid[1])):
					return next_index
			coordinate += step
	return index


func _source_keyboard_path(candidate: Dictionary, player := 0, use_arrows := false) -> Array:
	var target := -1
	for index in game.character_selection.cards.size():
		if str(game.character_selection.cards[index].id) == str(candidate.name):
			target = index
			break
	assert(target >= 0, "Source grid has no candidate card")
	var start := int(game.character_selection.selected[player])
	var queue: Array = [start]
	var previous: Dictionary = {start: {"index": -1, "direction": ""}}
	# P1's source keyboard bindings are WASD; arrows belong to P2.
	var directions := {"left": KEY_A, "right": KEY_D, "up": KEY_W, "down": KEY_S}
	if use_arrows:
		directions = {"left": KEY_LEFT, "right": KEY_RIGHT, "up": KEY_UP, "down": KEY_DOWN}
	while not queue.is_empty() and not previous.has(target):
		var current: int = queue.pop_front()
		for direction: String in directions:
			var next := _selection_neighbor(current, direction)
			if next == current or previous.has(next):
				continue
			previous[next] = {"index": current, "direction": direction}
			queue.append(next)
	assert(previous.has(target), "Source grid candidate is unreachable")
	var path: Array = []
	var cursor := target
	while int(previous[cursor]["index"]) >= 0:
		path.push_front(directions[previous[cursor]["direction"]])
		cursor = int(previous[cursor]["index"])
	return path


func _select_match(candidate: Dictionary, use_source_path: bool = false) -> void:
	intro_started[0] = false
	game = load("res://main.tscn").instantiate()
	root.add_child(game)
	game.set_physics_process(false)
	await process_frame
	if use_source_path:
		_assert_base_roster_shared_by_vs_modes()
	_assert_candidate_available(candidate)
	game.battle_intro.fight_started.connect(func() -> void: intro_started[0] = true)

	await _step(72)
	assert(game.title_menu.current_item().id == "single")
	await _tap(KEY_S)
	assert(game.title_menu.current_item().id == "vs_com")
	await _tap(KEY_S)
	assert(game.title_menu.current_item().id == "versus")
	_key(KEY_J, true)
	await _step(16)
	_key(KEY_J, false)
	await _step(30)
	assert(game.session.root_label == "选人画面")
	assert(game.session.modo == 3 and game.character_selection.phase == 0)

	if use_source_path:
		for code: Key in _source_keyboard_path(candidate):
			await _tap(code)
	else:
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

	for code: Key in _source_keyboard_path({"name": "松本"}):
		await _tap(code)
	assert(game.character_selection.helpers[0] == "松本")
	await _tap(KEY_J)
	await _confirm_after_source_delay()
	for code: Key in _source_keyboard_path({"name": "魂"}, 1, true):
		await _tap(code)
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
	var candidates: Array = CANDIDATES
	var use_source_path := false
	for argument in OS.get_cmdline_user_args():
		if str(argument) == "--base-forms":
			candidates = BASE_FORM_CANDIDATES
			use_source_path = true
	for candidate: Dictionary in candidates:
		await _select_match(candidate, use_source_path)
		assert(game.naruto.fighter_directory.get_file() == str(candidate.directory))
		assert(game.naruto_helper.helper_id == "松本")
		await _finish_natural_intro()
		await _check_candidate_action_and_ino_summon()
		await _close_game()
	print("ROSTER_CANDIDATE_FLOW_SMOKE_OK")
	quit()
