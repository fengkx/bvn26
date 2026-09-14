extends SceneTree

var _events: Array[Dictionary] = []
var _game: Node


func _initialize() -> void:
	_run.call_deferred()


func _run() -> void:
	var args := OS.get_cmdline_user_args()
	assert(args.size() == 1, "Pass the absolute v2 JSON output path")
	_game = load("res://main.tscn").instantiate()
	root.add_child(_game)
	_game.set_physics_process(false)
	await process_frame
	_game.diagnostics.event_recorded.connect(_on_event)
	_game._load_selected_stage("现世")
	_game._enter_current_fight(3)
	print("DIAGNOSTIC_INITIAL_POSITIONS ", JSON.stringify({
		"p1": _game._diagnostic_player(_game.naruto, _game.naruto_helper),
		"p2": _game._diagnostic_player(_game.ichigo, _game.ichigo_helper)}))
	var start_usec := Time.get_ticks_usec()
	for tick in 150:
		if tick == 38:
			_set_key(KEY_D, true)
		elif tick == 64:
			_set_key(KEY_D, false)
		elif tick == 70:
			_set_key(KEY_J, true)
		elif tick == 74:
			_set_key(KEY_J, false)
		_game._advance_fight()
	var elapsed_usec := Time.get_ticks_usec() - start_usec
	_game.diagnostics.end_match("diagnostic_smoke_complete")
	var output := {
		"schemaVersion": 2,
		"runId": "native-diagnostic-smoke",
		"startedAt": Time.get_datetime_string_from_system(true),
		"runtime": {
			"events": _events,
			"snapshot": {"match": _game._diagnostic_snapshot()},
			"droppedEvents": 0,
			"windowMs": 60000,
		},
		"test": {"fightTicks": 150, "elapsedUsec": elapsed_usec},
	}
	var file := FileAccess.open(args[0], FileAccess.WRITE)
	assert(file != null, "Could not write diagnostic smoke JSON")
	file.store_string(JSON.stringify(output, "\t"))
	file.close()
	print("DIAGNOSTIC_MATCH_EXPORT_OK events=", _events.size(), " elapsedUsec=", elapsed_usec,
		" path=", args[0])
	quit()


func _on_event(event: Dictionary) -> void:
	_events.append(event.duplicate(true))


func _set_key(code: Key, pressed: bool) -> void:
	var event := InputEventKey.new()
	event.keycode = code
	event.physical_keycode = code
	event.pressed = pressed
	Input.parse_input_event(event)
	Input.flush_buffered_events()
