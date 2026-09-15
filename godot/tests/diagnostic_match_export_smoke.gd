extends SceneTree

var _events: Array[Dictionary] = []
var _game: Node
var _fight_started_tick: int = -1


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
	_game.diagnostic_input_provider = _input_tape
	_game._enter_current_fight(3)
	print("DIAGNOSTIC_INITIAL_POSITIONS ", JSON.stringify({
		"p1": _game._diagnostic_player(_game.naruto, _game.naruto_helper),
		"p2": _game._diagnostic_player(_game.ichigo, _game.ichigo_helper)}))
	var start_usec := Time.get_ticks_usec()
	for tick in 400:
		_game._advance_fight()
	var elapsed_usec := Time.get_ticks_usec() - start_usec
	var final_snapshot: Dictionary = _game._diagnostic_snapshot()
	var input_tape: Array[Dictionary] = []
	var settled_hits := 0
	for event in _events:
		if event.get("type") == "hit_settled":
			settled_hits += 1
		if event.get("type") == "input_consumed":
			input_tape.append(event)
	if _count_player_input("p1", "right") == 0 or _count_player_input("p1", "attack") == 0:
		push_error("Expected consumed right and attack inputs")
		quit(1)
		return
	if settled_hits == 0:
		push_error("Expected at least one settled hit in the controlled short match")
		quit(1)
		return
	_game.diagnostics.end_match("diagnostic_smoke_complete")
	var output := {
		"schemaVersion": 2,
		"runId": "native-diagnostic-smoke",
		"startedAt": Time.get_datetime_string_from_system(true),
		"buildID": _game.diagnostics.build_id,
		"runtime": {
			"events": _events,
			"inputTape": input_tape,
			"snapshot": {"match": final_snapshot},
			"droppedEvents": 0,
			"windowMs": 60000,
		},
		"test": {"fightTicks": 400, "elapsedUsec": elapsed_usec},
	}
	var file := FileAccess.open(args[0], FileAccess.WRITE)
	assert(file != null, "Could not write diagnostic smoke JSON")
	file.store_string(JSON.stringify(output, "\t"))
	file.close()
	print("DIAGNOSTIC_MATCH_EXPORT_OK events=", _events.size(), " hits=", settled_hits,
		" elapsedUsec=", elapsed_usec,
		" path=", args[0])
	_game.queue_free()
	await process_frame
	quit()


func _on_event(event: Dictionary) -> void:
	_events.append(event.duplicate(true))


func _input_tape(slot: String, tick: int) -> Dictionary:
	var keys := {"up": false, "down": false, "left": false, "right": false,
		"attack": false, "jump": false, "dash": false, "ranged": false,
		"special": false, "summon": false}
	if _fight_started_tick < 0 and not _game.battle_intro.active:
		_fight_started_tick = tick
	if slot == "p1" and _fight_started_tick >= 0 and tick >= _fight_started_tick and tick < _fight_started_tick + 24:
		keys["right"] = true
	if slot == "p1" and _fight_started_tick >= 0 and tick >= _fight_started_tick + 30 and tick < _fight_started_tick + 40:
		keys["attack"] = true
	return keys


func _count_player_input(slot: String, key: String) -> int:
	var count := 0
	for event in _events:
		if event.get("type") != "input_consumed":
			continue
		var payload: Dictionary = event.get("payload", {})
		if payload.get("slot") == slot and payload.get("keys", {}).get(key, false):
			count += 1
	return count
