extends SceneTree

var rows: Array = []
var logical := {"p1": {}, "p2": {}}
var random_tape: Array = []
var clock_tape: Array = []

func _initialize() -> void:
	_run.call_deferred()


func _control(game: Node, code: Key, pressed: bool = false) -> void:
	var event := InputEventKey.new()
	event.keycode = code
	event.pressed = pressed
	game._input(event)


func _mouse(game: Node, pressed: bool, inside: bool = true) -> void:
	var event := InputEventMouseButton.new()
	event.button_index = MOUSE_BUTTON_LEFT
	event.position = Vector2(461, 91) if inside else Vector2.ZERO
	event.pressed = pressed
	game._input(event)


func _inputs(tick: int) -> void:
	logical = {"p1": {}, "p2": {}}
	if tick >= 165 and tick < 190:
		logical.p1 = {"right": true}
		logical.p2 = {"left": true}
	if tick >= 195 and tick < 200:
		logical.p1 = {"attack": true}
		logical.p2 = {"attack": true}
	if tick >= 205 and tick < 207:
		logical.p1 = {"jump": true}
	if tick >= 280 and tick < 295:
		logical.p1 = {"left": true}
		logical.p2 = {"right": true}


func _snapshot(game: Node) -> Array:
	var row := [game.physics_tick, game.battle_intro.active, game.battle_intro.step,
		game.pause_menu.visible, game.pause_menu.source_frame, game.pause_menu.selection,
		game.super_runtime.game_paused]
	for fighter in [game.naruto, game.ichigo]:
		row.append([fighter.current_source_frame(), fighter.action, fighter.source_x,
			fighter.source_y, fighter.facing, fighter.health, fighter.energy,
			fighter.hits, fighter.root_zhanting])
	return row


func _run() -> void:
	var game = load("res://main.tscn").instantiate()
	root.add_child(game)
	current_scene = game
	game.set_physics_process(false)
	game.session.maxhp = 1200.0
	game.session.maxtime = 90
	game.source_random.value_consumed.connect(func(event: Dictionary) -> void: random_tape.append(event))
	game.source_clock.value_consumed.connect(func(event: Dictionary) -> void: clock_tape.append(event))
	assert(game.arm_input_recording("/tmp/bvn-match-input-smoke.json").is_empty())
	game.match_input.source = func(slot: String, _tick: int) -> Dictionary: return logical[slot]
	game.match_input.intro_source = func(tick: int) -> bool: return tick >= 30 and tick < 90
	game.session.modo = 3
	game._on_characters_confirmed(["鸣人", "一护"], ["我爱罗", "魂"])
	game._on_map_confirmed("现世")
	for tick in range(331):
		_inputs(tick + 1)
		match tick:
			230:
				assert(not game.battle_intro.active)
				_control(game, KEY_ENTER)
				assert(game.super_runtime.game_paused)
			231, 246:
				_control(game, KEY_UP)
				_control(game, KEY_ENTER)
			241:
				assert(game.pause_menu.source_frame == 10)
				_mouse(game, false)
				assert(game.pause_menu.source_frame == 10)
			242, 244: _mouse(game, true)
			243:
				_mouse(game, false, false)
				assert(game.pause_menu.source_frame == 10)
			245:
				_mouse(game, false)
				assert(game.pause_menu.source_frame == 1)
			256:
				assert(game.pause_menu.source_frame == 10)
				_control(game, KEY_ENTER, true)
				assert(game.pause_menu.source_frame == 1 and game.super_runtime.game_paused)
				_control(game, KEY_ENTER)
				assert(not game.super_runtime.game_paused)
			270, 271: _control(game, KEY_ENTER)
			330:
				_control(game, KEY_ENTER)
				_control(game, KEY_DOWN)
				_control(game, KEY_ENTER)
				break
		game._physics_process(1.0 / 30.0)
		rows.append(_snapshot(game))
	var boundary = game.match_input
	assert(boundary.finished)
	var data: Variant = JSON.parse_string(FileAccess.get_file_as_string("/tmp/bvn-match-input-smoke.json"))
	assert(boundary.validate(data).is_empty())
	assert(data.setup.maxhp == 1200.0 and data.setup.maxtime == 90)
	await scene_changed
	game = current_scene
	game.set_physics_process(false)
	assert(game.arm_input_recording("/tmp/bvn-match-input-conflict.json").is_empty())
	var original_fighter = game.naruto
	var original_settings: Dictionary = game._input_setup()
	var conflict: String = game.start_input_playback(data)
	if conflict.is_empty():
		push_error("Armed recording must reject playback before changing match state")
		quit(1)
		return
	assert(game.session.root_label == "MENU" and game.physics_tick == 0)
	assert(game.naruto == original_fighter and game._input_setup() == original_settings)
	assert(not game.match_input.playback and not game.match_input.recording)
	assert(game.input_recording_path == "/tmp/bvn-match-input-conflict.json")
	# A rejected playback must leave the pending recording usable.
	game._enter_current_fight(3)
	assert(game.match_input.recording and not game.match_input.playback)
	game.free()
	game = load("res://main.tscn").instantiate()
	root.add_child(game)
	current_scene = game
	game.set_physics_process(false)
	assert(game.source_random.use_recorded_tape(random_tape))
	assert(game.source_clock.use_recorded_tape(clock_tape))
	var problem: String = game.start_input_playback(data)
	assert(problem.is_empty(), problem)
	assert(not game.arm_input_recording("/tmp/bvn-match-input-conflict.json").is_empty())
	assert(game.match_input.playback and not game.match_input.recording)
	assert(game.input_recording_path.is_empty())
	# Replay must ignore both the keyboard and the old diagnostic override.
	game.diagnostic_input_provider = func(_slot: String, _tick: int) -> Dictionary:
		assert(false, "Playback used diagnostic input")
		return {}
	for code in [KEY_J, KEY_A, KEY_KP_6]:
		var event := InputEventKey.new()
		event.keycode = code
		event.pressed = true
		Input.parse_input_event(event)
	Input.flush_buffered_events()
	for index in rows.size():
		_control(game, KEY_ENTER)
		game._physics_process(1.0 / 30.0)
		assert(game.match_input.error.is_empty(), game.match_input.error)
		assert(_snapshot(game) == rows[index], "Controlled match differs at display tick %d" % (index + 1))
	assert(game.source_random.replay_complete())
	assert(game.source_clock.replay_complete())
	boundary = game.match_input
	game._physics_process(1.0 / 30.0)
	assert(boundary.finished and boundary.error.is_empty())
	assert(game.session.root_label == "MENU")
	await scene_changed
	game = current_scene
	game.set_physics_process(false)
	assert(game.physics_tick == 0 and game.session.root_label == "MENU")
	for code in [KEY_J, KEY_A, KEY_KP_6]:
		var event := InputEventKey.new()
		event.keycode = code
		event.pressed = false
		Input.parse_input_event(event)
	Input.flush_buffered_events()
	game.queue_free()
	await process_frame
	print("MATCH_INPUT_SCENE_SMOKE_OK ticks=330 slots=2 intro=poll pause=ordered random=controlled clock=controlled")
	quit()
