extends SceneTree

var rows: Array = []
var output_path := ""
var failed := false


func _initialize() -> void:
	var args := OS.get_cmdline_user_args()
	if not args.is_empty():
		output_path = args[0]
	_run.call_deferred()


func _key(code: Key, pressed: bool) -> void:
	var event := InputEventKey.new()
	event.keycode = code
	event.physical_keycode = code
	event.pressed = pressed
	Input.parse_input_event(event)
	Input.flush_buffered_events()


func _snapshot(game: Control, relative_tick: int, input_state: Dictionary) -> Dictionary:
	var p1: FighterRuntime = game.naruto
	var p2: FighterRuntime = game.ichigo
	var helper: HelperRuntime = game.naruto_helper
	var p2_state := p2.ai_source_state
	return {
		"tick": relative_tick,
		"absolute_tick": game.physics_tick,
		"input": input_state.duplicate(true),
		"p1": p1.snapshot(),
		"p2": p2.snapshot(),
		"p2_source": {
			"frame": p2.current_source_frame(),
			"action": p2_state.read_field("动作"),
			"x": p2.source_x,
			"facing": p2.facing,
			"hp": p2.health,
			"ql": p2.energy,
			"sw": p2.sw,
			"touch": p2_state.read_field("touch"),
			"touchFloor": p2_state.read_field("touchFloor"),
			"hitBan": p2_state.read_field("hitBan"),
			"hited": p2.hited,
			"hstm": p2_state.read_field("hstm"),
			"dashing": p2_state.read_field("dashing"),
			"dashF": p2_state.read_field("dashF"),
			"rootZhanting": p2.root_zhanting,
		},
		"helper": {
			"id": helper.helper_id,
			"frame": helper.current_source_frame(),
			"action": helper.source_action,
			"attacking": helper.attacking,
			"atm1": helper.instance_clip_frame("atm1"),
			"atm2": helper.instance_clip_frame("atm2"),
			"atm3": helper.instance_clip_frame("atm3"),
			"x": helper.position.x,
		},
		"pause": game.naruto.root_zhanting,
		"random": game.source_random.diagnostic_state(),
	}


func _prime_fixture(game: Control) -> void:
	var p1: FighterRuntime = game.naruto
	var p2: FighterRuntime = game.ichigo
	for actor: FighterRuntime in [p1, p2]:
		actor.root_zhanting = false
		actor.sw = false
		actor.bs = 0
		actor.hited = 0
		actor.timeline_playing = true
		actor.goto_ai_label("站立", true)
		actor.run_frame_actions()
		actor.ai_source_state.values.merge({
			"动作": 0, "hited": 0, "beida": 0, "bs": 0,
			"sw": false, "touch": true, "touchFloor": true,
			"hitBan": false, "hstm": 0, "time": 0,
		}, true)
	p1.source_x = 300.0
	p2.source_x = 350.0
	p1.source_y = p1._ground_y
	p2.source_y = p2._ground_y
	p1.set_facing(1)
	p2.set_facing(-1)
	p1.energy = 300.0
	p2.energy = 300.0
	p1.sync_body_collision_position()
	p2.sync_body_collision_position()
	p2.ai_source_state.values.merge({
		"goran": 400.0,
		"attran": 400.0,
		"defran": 400.0,
		"jumpran": 400.0,
		"bisharan": NAN,
		"ql": 300.0,
		"_lastX": 350.0,
	}, true)
	# Keep the real VS COM driver/controller, but make the source random state
	# deterministic until the explicit post-capture transition below.
	p2.ai_random_clock.cancel()
	game.naruto_helper.deactivate()
	game.ichigo_helper.deactivate()


func _run() -> void:
	var game = load("res://main.tscn").instantiate()
	root.add_child(game)
	game.set_physics_process(false)
	game._on_menu_confirmed("vs_com")
	game._on_characters_confirmed(["日番谷", "恋次"], ["鼬", "魂"])
	game._on_map_confirmed("现世")
	for _tick in 700:
		game._advance_fight()
		if not game.battle_intro.active:
			break
	assert(not game.battle_intro.active and game.session.p2cpu)
	assert(game.naruto.fighter_name == "日番谷" and game.ichigo.fighter_name == "恋次")
	assert(game.naruto_helper.helper_id == "鼬")
	_prime_fixture(game)
	var o_key: Key = game.session.flash_to_key(int(game.session.codes["o"]))
	var previous_pressed := false
	for relative_tick in 180:
		# One-tick taps, repeated throughout the opening. The first summon is
		# accepted by the real P1 player BODY; later taps are intentionally kept
		# to mirror a user repeatedly pressing the assist key.
		var pressed := relative_tick >= 10 and relative_tick < 90 and relative_tick % 2 == 0
		if pressed != previous_pressed:
			_key(o_key, pressed)
		previous_pressed = pressed
		if relative_tick == 79:
			# Controlled source-random transition: retain all COM paths and only
			# lower the same goran field after helper capture/pause begins.
			game.ichigo.ai_source_state.values["goran"] = 0.0
		var input_state: Dictionary = game.session.fighter_input("p1")
		game._advance_fight()
		rows.append(_snapshot(game, relative_tick, input_state))
	if previous_pressed:
		_key(o_key, false)
	if not output_path.is_empty():
		var file := FileAccess.open(output_path, FileAccess.WRITE)
		assert(file != null, "Cannot write probe output")
		file.store_string(JSON.stringify(rows, "\t") + "\n")
		file.close()
	var capture_rows := rows.filter(func(row: Dictionary) -> bool:
		return bool(row["helper"]["attacking"]) and int(row["helper"]["frame"]) >= 45 and int(row["helper"]["frame"]) <= 132)
	assert(not capture_rows.is_empty(), "You helper was not captured in VS COM probe")
	print("VS_COM_YOU_RENJI_CAPTURE_PROBE_OK rows=", rows.size(), " output=", output_path)
	game._goto_menu()
	game.queue_free()
	await process_frame
	quit(1 if failed else 0)
