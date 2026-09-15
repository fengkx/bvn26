extends SceneTree

var _events: Array[Dictionary] = []
var _game: Node
var _inputs: Dictionary = {}


func _initialize() -> void:
	_run.call_deferred()


func _run() -> void:
	var args := OS.get_cmdline_user_args()
	if args.size() == 1 and args[0] == "--test-normalization":
		_run_normalization_test()
		return
	if args.size() != 2:
		push_error("Pass <diagnostic-json> <replay-result-json>")
		quit(2)
		return
	var parsed: Variant = JSON.parse_string(FileAccess.get_file_as_string(args[0]))
	if not parsed is Dictionary or int(parsed.get("schemaVersion", 0)) != 2:
		push_error("Expected diagnostics schema v2")
		quit(2)
		return
	var source: Dictionary = parsed
	var runtime: Dictionary = source.get("runtime", {})
	var source_events: Array = runtime.get("events", [])
	var source_snapshot: Dictionary = runtime.get("snapshot", {}).get("match", {})
	var start_event := _find_event(source_events, "match_started")
	if start_event.is_empty():
		push_error("Log lacks a complete fresh-match recipe")
		quit(2)
		return
	var match_recipe: Dictionary = start_event.get("payload", {}).get("match", {})
	if not match_recipe.get("replayability", {}).get("canonicalInitialization", false):
		push_error("Log lacks a complete fresh-match recipe")
		quit(2)
		return
	var initial_state: Dictionary = match_recipe.get("initialState", {})
	if initial_state.size() != 2 or not initial_state.has("p1") or not initial_state.has("p2"):
		push_error("Log lacks both initial player states")
		quit(2)
		return
	var match_id := str(match_recipe.get("matchId", ""))
	var fight_ticks := int(source_snapshot.get("fightTick", -1))
	if match_id.is_empty() or fight_ticks <= 0:
		push_error("Missing match identity or replay horizon")
		quit(2)
		return
	if int(match_recipe.get("mode", -1)) != 3 or bool(match_recipe.get("p1cpu", false)) or bool(match_recipe.get("p2cpu", false)):
		push_error("Unsupported replay mode: only non-CPU versus mode 3 is currently supported")
		quit(2)
		return
	for slot in ["p1", "p2"]:
		var actor: Dictionary = initial_state[slot]
		if actor.get("form") != null:
			push_error("Unsupported transformed fighter state for " + slot)
			quit(2)
			return
	var pause_events: Array = []
	for event in source_events:
		if event.get("type") == "pause_state" and event.get("payload", {}).get("pause", {}).get("userPaused", false):
			pause_events.append(event)
	if not pause_events.is_empty():
		push_error("User-paused matches are not replayable yet")
		quit(2)
		return
	var local_metadata: Dictionary = _read_build_metadata()
	var source_build_id := str(match_recipe.get("buildID", ""))
	var source_resource_version := str(match_recipe.get("resourceVersion", ""))
	var local_build_id := str(local_metadata.get("buildID", ""))
	var local_resource_version := str(local_metadata.get("resourceVersion", ""))
	if not source_build_id.is_empty() and not local_build_id.is_empty() and source_build_id != local_build_id:
		push_error("Build ID mismatch; refusing replay")
		quit(2)
		return
	if not source_resource_version.is_empty() and not local_resource_version.is_empty() and source_resource_version != local_resource_version:
		push_error("Resource version mismatch; refusing replay")
		quit(2)
		return
	var version_verified := not source_build_id.is_empty() and source_build_id == local_build_id \
		and not source_resource_version.is_empty() and source_resource_version == local_resource_version
	var random_start_index := int(match_recipe.get("replayability", {}).get("randomStartIndex", -1))
	var clock_start_index := int(match_recipe.get("replayability", {}).get("clockStartIndex", -1))
	if random_start_index != 0 or clock_start_index != 0:
		push_error("Nonzero pre-match random/clock offsets are unsupported by this fresh-scene executor")
		quit(2)
		return
	var tape_error := _load_input_tape(source_events, match_id, fight_ticks)
	if tape_error != "":
		push_error(tape_error)
		quit(2)
		return
	var sequence_error := _validate_match_sequence(source_events, match_id)
	if sequence_error != "":
		push_error(sequence_error)
		quit(2)
		return
	var random_tape := _consumer_tape(source_events, "random_consumed", match_id)
	var clock_tape := _consumer_tape(source_events, "clock_consumed", match_id)
	var random_error := _validate_consumer_tape(random_tape, "random")
	var clock_error := _validate_consumer_tape(clock_tape, "clock")
	if random_error != "" or clock_error != "":
		push_error(random_error if random_error != "" else clock_error)
		quit(2)
		return

	_game = load("res://main.tscn").instantiate()
	root.add_child(_game)
	_game.set_physics_process(false)
	await process_frame
	_game.diagnostics.event_recorded.connect(_on_event)
	_game._load_selected_stage(str(match_recipe.get("map", "")))
	var roster_error: String = _game.configure_diagnostic_roster(initial_state)
	if roster_error != "":
		push_error("Unsupported roster: " + roster_error)
		quit(2)
		return
	if not _game.source_random.use_recorded_tape(random_tape, random_start_index):
		push_error("Could not load recorded random tape: " + _game.source_random.failure)
		quit(2)
		return
	if not _game.source_clock.use_recorded_tape(clock_tape, clock_start_index):
		push_error("Could not load recorded clock tape: " + _game.source_clock.failure)
		quit(2)
		return
	_game.diagnostic_input_provider = _input_from_tape
	_game._enter_current_fight(int(match_recipe.get("mode", 3)))
	for _tick in fight_ticks:
		_game._advance_fight()
	var final_snapshot: Dictionary = _game._diagnostic_snapshot()
	var replay_match_id := str(_game.diagnostics.match_id)
	var match_end := _find_event(source_events, "match_ended")
	if not match_end.is_empty():
		_game.diagnostics.end_match(str(match_end.get("payload", {}).get("reason", "match_ended")))
	var expected := _semantic_events(source_events, match_id)
	var actual := _semantic_events(_events, replay_match_id)
	var first_difference := _first_difference(expected, actual)
	var snapshot_difference := _compare_match_state(source_snapshot, final_snapshot)
	var complete_random: bool = _game.source_random.replay_complete()
	var complete_clock: bool = _game.source_clock.replay_complete()
	var behavior_matches: bool = first_difference.is_empty() and snapshot_difference.is_empty() \
		and complete_random and complete_clock
	var passed: bool = behavior_matches and version_verified
	var result := {
		"schemaVersion": 1,
		"source": args[0],
		"sourceMatchId": match_id,
		"replay": {
			"status": "exact_match" if passed else ("semantic_match_version_unverified" if behavior_matches else "diverged"),
			"freshMainRecipe": true,
			"versionVerified": version_verified,
			"sourceBuildID": source_build_id,
			"localBuildID": local_build_id,
			"sourceResourceVersion": source_resource_version,
			"localResourceVersion": local_resource_version,
			"fightTicks": fight_ticks,
			"expectedEvents": expected.size(),
			"observedEvents": actual.size(),
			"inputRecords": _inputs.size(),
			"randomRecords": random_tape.size(),
			"clockRecords": clock_tape.size(),
			"randomComplete": complete_random,
			"clockComplete": complete_clock,
			"firstDifference": first_difference,
			"snapshotDifference": snapshot_difference,
		},
	}
	var file := FileAccess.open(args[1], FileAccess.WRITE)
	if file == null:
		push_error("Could not write replay result")
		quit(2)
		return
	file.store_string(JSON.stringify(result, "\t"))
	file.close()
	print("DIAGNOSTIC_REPLAY_", result.replay.status.to_upper(), " ", JSON.stringify(result.replay))
	_game.queue_free()
	await process_frame
	quit(0 if behavior_matches else 1)


func _read_build_metadata() -> Dictionary:
	const metadata_path := "res://generated/build_metadata.json"
	if not FileAccess.file_exists(metadata_path):
		return {}
	var value: Variant = JSON.parse_string(FileAccess.get_file_as_string(metadata_path))
	return value if value is Dictionary else {}


func _load_input_tape(events: Array, match_id: String, horizon: int) -> String:
	var found: Dictionary = {}
	for event in events:
		if event.get("type") != "input_consumed" or str(event.get("matchId", "")) != match_id:
			continue
		var tick := int(event.get("fightTick", -1))
		var payload: Dictionary = event.get("payload", {})
		var slot := str(payload.get("slot", ""))
		if tick < 1 or tick > horizon or slot not in ["p1", "p2"]:
			return "Input event outside the recorded Main horizon or invalid slot"
		if str(payload.get("source", "")) not in ["player", "diagnostic_tape"]:
			return "Input event source is not a replayable player/tape input"
		var key := "%d:%s" % [tick, slot]
		if found.has(key):
			return "Duplicate consumed input for " + key
		found[key] = payload.get("keys", {})
	if found.size() != horizon * 2:
		return "Input tape is incomplete; expected %d slot/tick records, got %d" % [horizon * 2, found.size()]
	_inputs = found
	return ""


func _validate_match_sequence(events: Array, match_id: String) -> String:
	var previous := -1
	for event in events:
		if str(event.get("matchId", "")) != match_id or not event.has("seq"):
			continue
		var current := int(event["seq"])
		if previous >= 0 and current != previous + 1:
			return "Runtime event sequence has a gap; exported event coverage is incomplete"
		previous = current
	return ""


func _input_from_tape(slot: String, tick: int) -> Dictionary:
	return _inputs.get("%d:%s" % [tick, slot], {}).duplicate(true)


func _consumer_tape(events: Array, event_type: String, match_id: String) -> Array[Dictionary]:
	var records: Array[Dictionary] = []
	for event in events:
		if event.get("type") == event_type and str(event.get("matchId", "")) == match_id:
			records.append(event.get("payload", {}).duplicate(true))
	return records


func _validate_consumer_tape(records: Array[Dictionary], name: String) -> String:
	for index in records.size():
		if int(records[index].get("index", -1)) != index + 1:
			return "%s tape is not complete from index 1" % name
	return ""


func _find_event(events: Array, event_type: String) -> Dictionary:
	for event in events:
		if event.get("type") == event_type:
			return event
	return {}


func _semantic_events(events: Array, match_id: String) -> Array:
	var result: Array = []
	for event in events:
		if str(event.get("matchId", "")) != match_id:
			continue
		result.append(_normalize(event))
	return result


func _normalize(value: Variant, parent_key: String = "") -> Variant:
	if value is Dictionary:
		var result := {}
		for key in value:
			if parent_key.is_empty() and str(key) in [
				"origin", "runId", "receivedAt", "receivedMonoMs"]:
				continue
			if str(key) in ["monoMs", "matchId", "buildID"]:
				continue
			if parent_key in ["random", "clock"] and str(key) in [
				"mode", "replaying", "rngSeed", "rngState", "retainedPolicy", "retainedDropped"]:
				continue
			result[key] = _normalize(value[key], str(key))
		return result
	if value is Array:
		var result: Array = []
		for item in value:
			result.append(_normalize(item, parent_key))
		return result
	return value


func _run_normalization_test() -> void:
	var runtime_event := {
		"seq": 42,
		"type": "hit_settled",
		"fightTick": 18,
		"monoMs": 1000,
		"matchId": "runtime-match",
		"buildID": "runtime-build",
		"payload": {"damage": 15, "defended": false},
	}
	var shell_event: Dictionary = runtime_event.duplicate(true)
	shell_event.merge({"origin": "runtime", "runId": "shell-run",
		"receivedAt": "2026-09-15T00:00:00Z", "receivedMonoMs": 995}, true)
	assert(_first_difference([_normalize(runtime_event)], [_normalize(shell_event)]).is_empty(),
		"Shell transport envelope must not change semantic equality")
	for field in ["seq", "type", "fightTick", "payload"]:
		var changed: Dictionary = runtime_event.duplicate(true)
		if field == "payload":
			changed.payload.damage = 16
		elif field == "type":
			changed[field] = "hit_received"
		else:
			changed[field] = int(changed[field]) + 1
		assert(not _first_difference([_normalize(runtime_event)], [_normalize(changed)]).is_empty(),
			"Gameplay event field must remain part of semantic comparison: " + field)
	print("DIAGNOSTIC_REPLAY_NORMALIZE_OK envelope=ignored gameplay_fields=preserved")
	quit()


func _first_difference(expected: Array, actual: Array) -> Dictionary:
	var shared := mini(expected.size(), actual.size())
	for index in shared:
		if not _deep_equal(expected[index], actual[index]):
			return {"index": index, "expected": expected[index], "actual": actual[index]}
	if expected.size() != actual.size():
		return {"index": shared, "expectedCount": expected.size(), "actualCount": actual.size()}
	return {}


func _deep_equal(left: Variant, right: Variant) -> bool:
	return JSON.stringify(_canonical(left)) == JSON.stringify(_canonical(right))


func _canonical(value: Variant) -> Variant:
	if value is Dictionary:
		var keys: Array = value.keys()
		keys.sort_custom(func(a: Variant, b: Variant) -> bool: return str(a) < str(b))
		var result: Array = []
		for key in keys:
			result.append([str(key), _canonical(value[key])])
		return result
	if value is Array:
		var result: Array = []
		for item in value:
			result.append(_canonical(item))
		return result
	if value is int or value is float:
		return "number:" + str(float(value))
	return value


func _compare_match_state(expected: Dictionary, actual: Dictionary) -> Dictionary:
	var expected_players: Dictionary = expected.get("players", {})
	var actual_players: Dictionary = actual.get("players", {})
	for slot in ["p1", "p2"]:
		var a: Dictionary = expected_players.get(slot, {})
		var b: Dictionary = actual_players.get(slot, {})
		for field in ["fighter", "resourcePath", "action", "sourceFrame", "x", "y", "facing", "hp", "energy", "bs", "hited", "zhanting", "sw"]:
			if a.get(field) != b.get(field):
				return {"slot": slot, "field": field, "expected": a.get(field), "actual": b.get(field)}
	return {}


func _on_event(event: Dictionary) -> void:
	_events.append(event.duplicate(true))
