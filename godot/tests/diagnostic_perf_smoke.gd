extends SceneTree

var _source_events: Array = []
var _inputs: Dictionary = {}
var _random_tape: Array[Dictionary] = []
var _clock_tape: Array[Dictionary] = []
var _events: Array[Dictionary] = []


func _initialize() -> void:
	_run.call_deferred()


func _run() -> void:
	var args := OS.get_cmdline_user_args()
	if args.size() != 2:
		push_error("Pass <source-match-json> <output-json>")
		quit(2)
		return
	var source: Dictionary = JSON.parse_string(FileAccess.get_file_as_string(args[0]))
	_source_events = source.get("runtime", {}).get("events", [])
	var match_started := _find_event("match_started")
	var match_id := str(match_started.get("payload", {}).get("match", {}).get("matchId", ""))
	var horizon := int(source.get("runtime", {}).get("snapshot", {}).get("match", {}).get("fightTick", -1))
	if match_id.is_empty() or horizon <= 0 or not _load_inputs(match_id, horizon):
		push_error("Source match is not a complete controlled-input recipe")
		quit(2)
		return
	_random_tape = _read_consumer("random_consumed", match_id)
	_clock_tape = _read_consumer("clock_consumed", match_id)
	var enabled := await _measure_run(true, match_started, horizon)
	var disabled := await _measure_run(false, match_started, horizon)
	if enabled.get("finalHP") != disabled.get("finalHP") or enabled.get("positions") != disabled.get("positions"):
		push_error("Diagnostic collection toggle changed gameplay state")
		quit(1)
		return
	var result := {"schemaVersion": 1, "source": args[0], "ticks": horizon,
		"enabled": enabled, "disabled": disabled,
		"note": "Measures runtime event emission/serialization fan-out; caller-built payload dictionaries remain present in both runs."}
	var file := FileAccess.open(args[1], FileAccess.WRITE)
	if file == null:
		push_error("Could not write performance result")
		quit(2)
		return
	file.store_string(JSON.stringify(result, "\t"))
	file.close()
	print("DIAGNOSTIC_PERF_OK ", JSON.stringify(result))
	quit()


func _measure_run(enabled: bool, match_started: Dictionary, horizon: int) -> Dictionary:
	_events.clear()
	var match_recipe: Dictionary = match_started.get("payload", {}).get("match", {})
	var initial: Dictionary = match_recipe.get("initialState", {})
	var game: Node = load("res://main.tscn").instantiate()
	root.add_child(game)
	game.set_physics_process(false)
	await process_frame
	game.diagnostics.enabled = enabled
	game.diagnostics.event_recorded.connect(_on_event)
	game._load_selected_stage(str(match_recipe.get("map", "")))
	var roster_error: String = game.configure_diagnostic_roster(initial)
	if roster_error != "":
		push_error(roster_error)
		game.queue_free()
		return {}
	game.source_random.use_recorded_tape(_random_tape)
	game.source_clock.use_recorded_tape(_clock_tape)
	game.diagnostic_input_provider = Callable(self, "_input_from_tape")
	game._enter_current_fight(int(match_recipe.get("mode", 3)))
	var start_usec := Time.get_ticks_usec()
	for _tick in horizon:
		game._advance_fight()
	var elapsed_usec := Time.get_ticks_usec() - start_usec
	var final: Dictionary = game._diagnostic_snapshot()
	var result := {"enabled": enabled, "elapsedUsec": elapsed_usec,
		"eventCount": _events.size(), "serializedEventBytes": JSON.stringify(_events).to_utf8_buffer().size(),
		"finalHP": [final.players.p1.hp, final.players.p2.hp],
		"positions": [[final.players.p1.x, final.players.p1.y], [final.players.p2.x, final.players.p2.y]]}
	game.queue_free()
	await process_frame
	return result


func _load_inputs(match_id: String, horizon: int) -> bool:
	for event in _source_events:
		if event.get("type") != "input_consumed" or str(event.get("matchId", "")) != match_id:
			continue
		var payload: Dictionary = event.get("payload", {})
		_inputs["%d:%s" % [int(event.get("fightTick", -1)), str(payload.get("slot", ""))]] = payload.get("keys", {})
	return _inputs.size() == horizon * 2


func _input_from_tape(slot: String, tick: int) -> Dictionary:
	return _inputs.get("%d:%s" % [tick, slot], {}).duplicate(true)


func _read_consumer(event_type: String, match_id: String) -> Array[Dictionary]:
	var records: Array[Dictionary] = []
	for event in _source_events:
		if event.get("type") == event_type and str(event.get("matchId", "")) == match_id:
			records.append(event.get("payload", {}).duplicate(true))
	return records


func _find_event(event_type: String) -> Dictionary:
	for event in _source_events:
		if event.get("type") == event_type:
			return event
	return {}


func _on_event(event: Dictionary) -> void:
	_events.append(event.duplicate(true))
