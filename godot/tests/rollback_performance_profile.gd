extends SceneTree

const Fixture = preload("res://tests/rollback_fixture.gd")
const Session = preload("res://rollback_session.gd")
const State = preload("res://simulation_state.gd")
const USER_TAPE_PATH := "res://tests/rollback_performance_user_log_r01.json"
const WARMUP_FRAMES := 90
const MEASURED_FRAMES := 330
const USER_LOG_SCENARIO := "user-log-r01"
const USER_FIGHTERS := ["日番谷", "佐助"]
const USER_HELPERS := ["鼬", "我爱罗"]
const USER_STAGE := "现世"
const CURRENT_LOG_ROSTER_SCENARIO := "current-log-roster-r01"
const CURRENT_LOG_FIGHTERS := ["一护", "佐助"]
const CURRENT_LOG_HELPERS := ["我爱罗", "松本"]
const CURRENT_LOG_STAGE := "流魂街"
const RETENTION_FIELDS := [
	"_states",
	"_snapshots",
	"_snapshot_graphs",
	"_constants",
	"_constant_values",
	"_constant_keys",
	"_retired",
	"_empty_array_prototypes",
	"_empty_dictionary_prototypes",
]
var _scenario := "default"
var _recorded_inputs := {}
var _tape_metadata := {}
var _reference_state := {}


func _initialize() -> void:
	_run.call_deferred()


func _run() -> void:
	if not _read_scenario_args() or not _load_scenario_inputs():
		quit(1)
		return
	for mode in ["battle_only", "rollback_no_late_input"]:
		var warm_fixture := _create_fixture()
		if warm_fixture.is_empty():
			quit(1)
			return
		if not _run_frames(warm_fixture, mode, WARMUP_FRAMES):
			Fixture.dispose(warm_fixture.game, warm_fixture.battle)
			quit(1)
			return
		Fixture.dispose(warm_fixture.game, warm_fixture.battle)
		await process_frame

		var fixture := _create_fixture()
		if fixture.is_empty():
			quit(1)
			return
		if not _validate_fixture_roster(fixture.game):
			Fixture.dispose(fixture.game, fixture.battle)
			quit(1)
			return
		var session: RefCounted = _configure_session(fixture.battle, mode)
		if mode != "battle_only" and session == null:
			Fixture.dispose(fixture.game, fixture.battle)
			quit(1)
			return
		var advance_samples: Array[int] = []
		var receive_samples: Array[int] = []
		var step_samples: Array[int] = []
		var receive_plus_step_samples: Array[int] = []
		var retention_samples: Array[Dictionary] = []
		var started_wall := Time.get_ticks_usec()
		for frame in range(1, MEASURED_FRAMES + 1):
			if not _set_frame(fixture.game, fixture.battle, frame):
				Fixture.dispose(fixture.game, fixture.battle)
				quit(1)
				return
			var players := _players(frame)
			if mode == "battle_only":
				var started := Time.get_ticks_usec()
				if not _check(fixture.battle.advance(frame, players)):
					Fixture.dispose(fixture.game, fixture.battle)
					quit(1)
					return
				advance_samples.append(Time.get_ticks_usec() - started)
			else:
				var started_total := Time.get_ticks_usec()
				var started_receive := Time.get_ticks_usec()
				for slot in players:
					if not _check(session.receive("performance", slot, frame, players[slot])):
						Fixture.dispose(fixture.game, fixture.battle)
						quit(1)
						return
				receive_samples.append(Time.get_ticks_usec() - started_receive)
				var started_step := Time.get_ticks_usec()
				if not _check(session.step()):
					Fixture.dispose(fixture.game, fixture.battle)
					quit(1)
					return
				step_samples.append(Time.get_ticks_usec() - started_step)
				receive_plus_step_samples.append(Time.get_ticks_usec() - started_total)
			if frame % 30 == 0 or frame == MEASURED_FRAMES:
				retention_samples.append({
					"frame": frame,
					"session": _container_sizes(session, ["_states"]) if session != null else {},
					"checkpoint": _container_sizes(fixture.battle.checkpoint, RETENTION_FIELDS),
				})
		var measured_checkpoint_profile: Dictionary = fixture.battle.checkpoint.profile.duplicate(true)
		var final_state: Dictionary = fixture.battle.save_state()
		if mode == "battle_only":
			_reference_state = final_state
		else:
			var difference := State.first_difference(_reference_state, final_state)
			if not _check(difference):
				Fixture.dispose(fixture.game, fixture.battle)
				quit(1)
				return
		var elapsed_wall := Time.get_ticks_usec() - started_wall
		var report := {
			"mode": mode,
			"warmup_frames": WARMUP_FRAMES,
			"frames": MEASURED_FRAMES,
			"input_fixture": _scenario_id(),
			"input_fixture_metadata": _tape_metadata,
			"random_seed": 727,
			"intro_schedule": "poll every 15 ticks; skip intro ticks 30-89",
			"advance_us": _stats(advance_samples),
			"receive_inputs_us": _stats(receive_samples),
			"session_step_us": _stats(step_samples),
			"receive_plus_step_us": _stats(receive_plus_step_samples),
			"operation_wall_us": _sum(advance_samples) + _sum(receive_plus_step_samples),
			"harness_wall_us": elapsed_wall,
			"rollbacks": session.rollback_count if session != null else 0,
			"replayed_frames": session.replayed_frames if session != null else 0,
			"checkpoint_profile": measured_checkpoint_profile,
			"live_container_sizes": retention_samples,
		}
		print("ROLLBACK_PERFORMANCE ", JSON.stringify(report))
		Fixture.dispose(fixture.game, fixture.battle)
		await process_frame
	quit()


func _configure_session(battle: RefCounted, mode: String) -> RefCounted:
	if mode == "battle_only":
		return null
	var session := Session.new()
	if not _check(session.configure(battle, "performance", 8, 32, 0)):
		return null
	return session


func _run_frames(fixture: Dictionary, mode: String, count: int) -> bool:
	var session: RefCounted = _configure_session(fixture.battle, mode)
	if mode != "battle_only" and session == null:
		return false
	for frame in range(1, count + 1):
		if not _set_frame(fixture.game, fixture.battle, frame):
			return false
		var players := _players(frame)
		if mode == "battle_only":
			if not _check(fixture.battle.advance(frame, players)):
				return false
		else:
			for slot in players:
				if not _check(session.receive("performance", slot, frame, players[slot])):
					return false
			if not _check(session.step()):
				return false
	return true


func _set_frame(game: Node, battle: RefCounted, frame: int) -> bool:
	var skip := frame >= 30 and frame < 90
	var callbacks := []
	if game.battle_intro.polling and frame % 15 == 0 and not (skip and game.battle_intro.step > 1 and game.battle_intro.step < 4):
		callbacks.append({"kind": "intro_poll", "phase": "after_actor_advance", "sequence": frame, "time_ms": frame * 33})
	return _check(battle.set_frame_events(frame, frame * 33, skip, callbacks))


func _players(frame: int) -> Dictionary:
	if _scenario == USER_LOG_SCENARIO:
		if _recorded_inputs.has(frame):
			return _recorded_inputs[frame].duplicate(true)
		return _neutral_players()
	var players := {"p1": {}, "p2": {}}
	for slot in players:
		for button in Session.BUTTONS:
			players[slot][button] = false
	if frame >= 165 and frame < 190:
		players.p1.right = true
		players.p2.left = true
	if frame >= 195 and frame < 200:
		players.p1.attack = true
		players.p2.attack = true
	if frame >= 205 and frame < 207:
		players.p1.jump = true
	if frame >= 235 and frame < 237:
		players.p1.ranged = true
	if frame >= 270 and frame < 272:
		players.p2.summon = true
	return players


func _neutral_players() -> Dictionary:
	var players := {"p1": {}, "p2": {}}
	for slot in players:
		for button in Session.BUTTONS:
			players[slot][button] = false
	return players


func _read_scenario_args() -> bool:
	for argument in OS.get_cmdline_user_args():
		if argument.begins_with("--scenario="):
			_scenario = argument.trim_prefix("--scenario=")
		elif argument == "--scenario":
			return _check("Pass scenario as --scenario=<name>")
		else:
			return _check("Unknown performance profile argument: " + argument)
	if _scenario not in ["default", USER_LOG_SCENARIO, CURRENT_LOG_ROSTER_SCENARIO]:
		return _check("Unknown performance scenario: " + _scenario)
	return true


func _load_scenario_inputs() -> bool:
	if _scenario == "default":
		_tape_metadata = {
			"id": "default-naruto-ichigo-r01",
			"kind": "deterministic synthetic screening input",
		}
		return true
	if _scenario == CURRENT_LOG_ROSTER_SCENARIO:
		_tape_metadata = {
			"id": CURRENT_LOG_ROSTER_SCENARIO,
			"kind": "complete deterministic synthetic input from a fresh fixture",
			"recorded_range": {"first_tick": 1, "last_tick": MEASURED_FRAMES, "ticks": MEASURED_FRAMES},
			"input_schedule": "the profiler's deterministic movement, attack, jump, ranged, and summon pattern",
			"derived_from_user_log": false,
		}
		var tape: Array = []
		for frame in range(1, MEASURED_FRAMES + 1):
			tape.append({"fightTick": frame, "players": _players(frame)})
		var hashing := HashingContext.new()
		if hashing.start(HashingContext.HASH_SHA256) != OK or hashing.update(JSON.stringify(tape).to_utf8_buffer()) != OK:
			return _check("Could not hash the deterministic current-roster input tape")
		_tape_metadata.input_tape_sha256 = hashing.finish().hex_encode()
		return true
	var source := FileAccess.get_file_as_string(USER_TAPE_PATH)
	if source.is_empty():
		return _check("Cannot read user-log performance tape: " + USER_TAPE_PATH)
	var parsed: Variant = JSON.parse_string(source)
	if not parsed is Dictionary or parsed.get("format") != "bvn-recorded-input-tape-v1":
		return _check("Invalid user-log performance tape format")
	var scenario: Dictionary = parsed.get("scenario", {})
	if scenario.get("p1", {}).get("fighter") != USER_FIGHTERS[0] \
			or scenario.get("p1", {}).get("helper") != USER_HELPERS[0] \
			or scenario.get("p1", {}).get("helper_asset") != "you" \
			or scenario.get("p2", {}).get("fighter") != USER_FIGHTERS[1] \
			or scenario.get("p2", {}).get("helper") != USER_HELPERS[1] \
			or scenario.get("stage") != USER_STAGE:
		return _check("User-log tape roster differs from the declared fixture")
	var capture: Dictionary = parsed.get("capture", {})
	var first_tick := int(capture.get("first_recorded_tick", -1))
	var last_tick := int(capture.get("last_recorded_tick", -1))
	var records: Array = parsed.get("records", [])
	if first_tick != 28 or last_tick != 249 or records.size() != last_tick - first_tick + 1 \
			or int(capture.get("complete_ticks", -1)) != records.size():
		return _check("User-log tape has an unexpected or incomplete tick range")
	for index in records.size():
		var record: Variant = records[index]
		var expected_tick := first_tick + index
		if not record is Dictionary or int(record.get("fightTick", -1)) != expected_tick:
			return _check("User-log tape has a missing or reordered tick at %d" % expected_tick)
		var tick_players := {}
		for slot in ["p1", "p2"]:
			var held: Variant = record.get(slot)
			if not held is Dictionary or held.size() != Session.BUTTONS.size():
				return _check("User-log tape has an incomplete input slot at tick %d" % expected_tick)
			for button in Session.BUTTONS:
				if not held.has(button) or not held[button] is bool:
					return _check("Invalid %s.%s in user-log tape at tick %d" % [slot, button, expected_tick])
			tick_players[slot] = held.duplicate(true)
		_recorded_inputs[expected_tick] = tick_players
	var hashing := HashingContext.new()
	if hashing.start(HashingContext.HASH_SHA256) != OK or hashing.update(source.to_utf8_buffer()) != OK:
		return _check("Could not hash the user-log input tape")
	var tape_sha := hashing.finish().hex_encode()
	_tape_metadata = {
		"id": USER_LOG_SCENARIO,
		"source_kind": parsed.get("source", {}).get("kind", ""),
		"source_log_sha256": parsed.get("source", {}).get("sha256", ""),
		"input_tape_sha256": tape_sha,
		"recorded_range": {"first_tick": first_tick, "last_tick": last_tick, "ticks": records.size()},
		"padded_neutral_ranges": [{"first_tick": 1, "last_tick": first_tick - 1}, {"first_tick": last_tick + 1, "last_tick": MEASURED_FRAMES}],
		"padding_is_synthetic_neutral_only": true,
		"attacks_assists_supers_added_by_harness": false,
		"fight_started_tick": int(capture.get("fight_started_tick", -1)),
	}
	return true


func _scenario_id() -> String:
	match _scenario:
		"default": return "default-naruto-ichigo-r01"
		USER_LOG_SCENARIO: return USER_LOG_SCENARIO
		_: return CURRENT_LOG_ROSTER_SCENARIO


func _create_fixture() -> Dictionary:
	if _scenario == USER_LOG_SCENARIO:
		return Fixture.create(self, USER_FIGHTERS, USER_HELPERS, USER_STAGE)
	if _scenario == CURRENT_LOG_ROSTER_SCENARIO:
		return Fixture.create(self, CURRENT_LOG_FIGHTERS, CURRENT_LOG_HELPERS, CURRENT_LOG_STAGE)
	return Fixture.create(self)


func _validate_fixture_roster(game: Node) -> bool:
	if _scenario == CURRENT_LOG_ROSTER_SCENARIO:
		if game.naruto.fighter_name != CURRENT_LOG_FIGHTERS[0] or game.ichigo.fighter_name != CURRENT_LOG_FIGHTERS[1]:
			return _check("Selected current-log roster fighters do not match the complete synthetic fixture")
		if game.naruto_helper.helper_id != CURRENT_LOG_HELPERS[0] or game.ichigo_helper.helper_id != CURRENT_LOG_HELPERS[1]:
			return _check("Selected current-log roster helpers do not match the complete synthetic fixture")
		if game.naruto_helper.helper_directory.get_file() != "woailuo" or game.selected_stage != CURRENT_LOG_STAGE:
			return _check("Selected current-log roster helper asset or stage does not match the complete synthetic fixture")
		return true
	if _scenario != USER_LOG_SCENARIO:
		return true
	if game.naruto.fighter_name != USER_FIGHTERS[0] or game.ichigo.fighter_name != USER_FIGHTERS[1]:
		return _check("Selected performance fighters do not match the user log")
	if game.naruto_helper.helper_id != USER_HELPERS[0] or game.ichigo_helper.helper_id != USER_HELPERS[1]:
		return _check("Selected performance helpers do not match the user log")
	if game.naruto_helper.helper_directory.get_file() != "you" or game.selected_stage != USER_STAGE:
		return _check("Selected performance helper asset or stage does not match the user log")
	return true


func _stats(samples: Array[int]) -> Dictionary:
	if samples.is_empty():
		return {}
	samples.sort()
	return {
		"mean": float(_sum(samples)) / samples.size(),
		"p50": _percentile(samples, 0.50),
		"p95": _percentile(samples, 0.95),
		"p99": _percentile(samples, 0.99),
		"max": samples.back(),
	}


func _percentile(sorted_samples: Array[int], fraction: float) -> int:
	return sorted_samples[mini(sorted_samples.size() - 1, maxi(0, int(ceil(sorted_samples.size() * fraction)) - 1))]


func _sum(samples: Array[int]) -> int:
	var total := 0
	for value in samples:
		total += value
	return total


func _container_sizes(target: Object, fields: Array) -> Dictionary:
	var available := {}
	for property in target.get_property_list():
		available[property.name] = true
	var sizes := {}
	for field in fields:
		if not available.has(field):
			continue
		var value: Variant = target.get(field)
		if value is Array or value is Dictionary:
			sizes[field] = value.size()
	return sizes


func _check(problem: String) -> bool:
	if not problem.is_empty():
		push_error(problem)
		return false
	return true
