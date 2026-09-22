extends SceneTree

var comparisons: Array = []
var mismatch := false
var frame_comparisons: Array = []
var state_comparisons: Array = []
var original_states: Dictionary = {}
var original_geometry: Dictionary = {}
var geometry_comparisons: Array = []
var helper_snapshots: Array = []
var replay_held := {}
var input_transitions: Array = []

var boundary_mode := false
var boundary_expected: Array = []
var boundary_records: Array = []
var boundary_cursor := 0
var boundary_failure: Dictionary = {}
var boundary_frames: Dictionary = {}
var native_checkpoint: Dictionary = {}
var active_game: Node = null
var ready_recorded := false


func observe_body_boundary(frame: int, entering: bool, fighter: FighterRuntime) -> void:
	var slot := fighter.player_slot
	if not boundary_frames.get(slot, {}).has(frame) or not boundary_failure.is_empty():
		return
	var actual := {"slot": slot, "source_frame": frame, "entering": entering,
		"frame": fighter.current_source_frame(), "action": fighter.ai_source_state.read_field("动作"),
		"hp": fighter.health, "ql": fighter.energy, "sw": fighter.ai_source_state.read_field("sw"),
		"touch": fighter.ai_source_state.read_field("touch"), "touchFloor": fighter.ai_source_state.read_field("touchFloor"),
		"hits": fighter.hits, "paused": fighter.root_zhanting,
		"hstm": fighter.ai_source_state.read_field("hstm"), "hurtSkling": fighter.ai_source_state.read_field("hurtSkling")}
	if boundary_cursor >= boundary_expected.size():
		boundary_failure = {"reason": "native_boundary_after_reference_end", "actual": actual}
		mismatch = true
		return
	var expected: Dictionary = boundary_expected[boundary_cursor]
	var differences := {}
	for key: String in actual:
		if actual[key] != expected[key]:
			differences[key] = {"expected": expected[key], "actual": actual[key]}
	boundary_records.append({"source_sequence": expected.sequence, "differences": differences})
	boundary_cursor += 1
	if not differences.is_empty():
		boundary_failure = {"expected": expected, "actual": actual, "differences": differences}
		mismatch = true


func setup_body_boundaries(events: Array, checkpoint_sequence: int, fighters: Array[FighterRuntime]) -> void:
	for fighter in fighters:
		var model: Dictionary = JSON.parse_string(FileAccess.get_file_as_string(fighter.fighter_directory.path_join("fighter.json")))
		boundary_frames[fighter.player_slot] = {}
		for script: Dictionary in model["timeline_scripts"]:
			if str(script["path"]).ends_with("/DoAction.as"):
				boundary_frames[fighter.player_slot][int(script["frame"])] = true
	for event: Dictionary in events:
		if event.kind != "body_boundary" or int(event.sequence) <= checkpoint_sequence:
			continue
		var parts: PackedStringArray = str(event.value).split(",")
		assert(parts.size() == 14)
		var entry := {"slot": parts[0], "source_frame": int(parts[1]), "entering": parts[2] == "true",
			"frame": int(parts[3]), "sequence": event.sequence, "display_tick": event.display_tick}
		var fields := ["action", "hp", "ql", "sw", "touch", "touchFloor", "hits", "paused", "hstm", "hurtSkling"]
		for i in fields.size(): entry[fields[i]] = parse_value(parts[i + 4])
		boundary_expected.append(entry)
		assert(boundary_frames[parts[0]].has(int(parts[1])), "Missing source frame script in native inventory")
	assert(not boundary_expected.is_empty(), "Boundary mode requires instrumented source events")
	for fighter in fighters:
		fighter.source_frame_script_boundary.connect(observe_body_boundary.bind(fighter))


func apply_recorded_input(game, value: String, tick: int) -> void:
	var slots := {"right": "d", "attack": "j", "down": "s", "ranged": "u",
		"jump": "k", "special": "i", "summon": "o"}
	var held := {}
	for item in value.split(",", false):
		var pair := item.split("=")
		assert(pair.size() == 2 and slots.has(pair[0]))
		assert(pair[1] in ["true", "false", "undefined"])
		held[pair[0]] = pair[1] == "true"
	for field: String in slots:
		var pressed := bool(held.get(field, false))
		if pressed == bool(replay_held.get(field, false)):
			continue
		var key := InputEventKey.new()
		key.keycode = game.session.flash_to_key(int(game.session.codes[slots[field]]))
		key.physical_keycode = key.keycode
		key.pressed = pressed
		Input.parse_input_event(key)
		input_transitions.append({"display_tick": tick, "field": field, "pressed": pressed})
	Input.flush_buffered_events()
	replay_held = held


func compare_frames(fighters: Array[FighterRuntime], tick: int, original: Dictionary, present: bool = true) -> void:
	assert(original.has(tick), "Missing original root snapshot")
	var actual := [fighters[0].current_source_frame(), fighters[1].current_source_frame()] if present else [0, 0]
	var matches: bool = actual == original[tick]
	frame_comparisons.append({"display_tick": tick, "expected": original[tick],
		"actual": actual, "matches": matches})
	mismatch = mismatch or not matches
	if not present:
		return
	for i in 2:
		var fighter := fighters[i]
		var geometry := {"x": fighter.source_x, "y": fighter.source_y,
			"xscale": float(fighter.scale.x * 100)}
		var geometry_delta := {}
		for field: String in geometry:
			geometry_delta[field] = geometry[field] - original_geometry[tick][i][field]
		geometry_comparisons.append({"display_tick": tick, "slot": "p%d" % (i + 1),
			"expected": original_geometry[tick][i], "actual": geometry, "delta": geometry_delta})
		# Facing is discrete in this slice; do not hide a turn behind coordinate
		# diagnostics and report only a later collision/frame-order symptom.
		mismatch = mismatch or geometry["xscale"] != original_geometry[tick][i]["xscale"]
		var actual_state := {"hp": fighter.health, "ql": fighter.energy,
			"action": fighter.ai_source_state.read_field("动作"),
			"sw": fighter.ai_source_state.read_field("sw"),
			"touch": fighter.ai_source_state.read_field("touch"),
			"touchFloor": fighter.ai_source_state.read_field("touchFloor"),
			"hits": fighter.hits, "paused": fighter.root_zhanting,
			"hstm": fighter.ai_source_state.read_field("hstm"),
			"hurtSkling": fighter.ai_source_state.read_field("hurtSkling")}
		var expected: Dictionary = original_states[tick][i]
		var differences := {}
		for field: String in expected:
			if actual_state[field] != expected[field]:
				differences[field] = {"expected": expected[field], "actual": actual_state[field]}
		state_comparisons.append({"display_tick": tick, "slot": "p%d" % (i + 1),
			"expected": expected, "actual": actual_state, "differences": differences})
		mismatch = mismatch or not differences.is_empty()
	if present and ready_recorded:
		for helper in [active_game.naruto_helper, active_game.ichigo_helper]:
			if helper == null:
				continue
			helper_snapshots.append({"display_tick": tick, "tick": tick,
				"slot": helper.diagnostic_slot, "frame": helper.current_source_frame(),
				"x": helper.position.x, "y": helper.position.y,
				"facing": helper.facing, "action": helper.source_action,
				"attacking": helper.attacking, "hits": helper.hited})


func parse_value(value: String) -> Variant:
	return preload("res://tests/source_trace_number.gd").decode(value)


func geometry_summary() -> Dictionary:
	var result := {}
	for record: Dictionary in geometry_comparisons:
		var slot: String = record.slot
		if not result.has(slot):
			result[slot] = {"initial_actual": record.actual, "initial_expected": record.expected,
				"max_absolute_delta": {"x": 0.0, "y": 0.0, "xscale": 0.0},
				"max_displacement_delta": {"x": 0.0, "y": 0.0}, "snapshots": 0}
		var summary: Dictionary = result[slot]
		summary.snapshots += 1
		for field: String in record.delta:
			summary.max_absolute_delta[field] = maxf(summary.max_absolute_delta[field], absf(record.delta[field]))
		for field: String in ["x", "y"]:
			var difference: float = ((record.actual[field] - summary.initial_actual[field])
				- (record.expected[field] - summary.initial_expected[field]))
			summary.max_displacement_delta[field] = maxf(summary.max_displacement_delta[field], absf(difference))
	return result


func _initialize() -> void:
	_run.call_deferred()


func _run() -> void:
	var args := OS.get_cmdline_user_args()
	assert(args.size() in [2, 3], "Pass events, report and optional combat mode")
	boundary_mode = args.size() == 3 and args[2] == "combat-boundaries"
	var combat_mode := args.size() == 3 and args[2] in ["combat", "combat-boundaries"]
	var source_events: Array = []
	var polls: Array = []
	var original_ready: Array = []
	var original_frames := {}
	for line in FileAccess.get_file_as_string(args[0]).split("\n", false):
		var event: Dictionary = JSON.parse_string(line)
		source_events.append(event)
		if event.kind == "state" and (combat_mode or int(event.fight_tick) <= 0):
			var parts: PackedStringArray = str(event.value).split(",")
			var root_tick := int(event.display_tick)
			if not original_frames.has(root_tick):
				original_frames[root_tick] = []
				original_states[root_tick] = []
				original_geometry[root_tick] = []
			assert(parts[0] == "p%d" % (original_frames[root_tick].size() + 1))
			original_frames[root_tick].append(int(parts[1]))
			original_geometry[root_tick].append({"x": parse_value(parts[2]), "y": parse_value(parts[3]), "xscale": parse_value(parts[4])})
			var state := {}
			var columns := {"action": 5, "hp": 6, "ql": 7, "sw": 8, "touch": 9,
				"touchFloor": 10, "hits": 11, "paused": 12, "hstm": 13, "hurtSkling": 14}
			for field: String in columns:
				state[field] = parse_value(parts[columns[field]])
			original_states[root_tick].append(state)
		if event.kind == "state" and int(event.fight_tick) == 0:
			var state_values: PackedStringArray = str(event.value).split(",")
			original_ready.append({"slot": state_values[0], "frame": int(state_values[1]),
				"display_tick": int(event.display_tick)})
		if event.kind != "intro_poll_state":
			continue
		var values: PackedStringArray = str(event.value).split(",")
		if values[1] != "true":
			continue
		polls.append({"phase": "after_actor_advance", "sequence": int(event.sequence),
			"time_ms": int(event.time_ms), "display_tick": int(event.display_tick),
			"expected": {"step": int(values[0]), "states": [int(values[2]), int(values[3])],
				"frames": [int(values[4]), int(values[5])]}})
	assert(not polls.is_empty())
	var game = load("res://main.tscn").instantiate()
	active_game = game
	root.add_child(game)
	game.set_physics_process(false)
	# Acceptance-only setup: reproduce the clean source fixture identities before
	# entering the fight. This is not a production roster change.
	game._load_selected_stage("现世")
	game.character_selection.available.fighters["白哉"] = "byakuya"
	game.character_selection.available.helpers["魂"] = "kon"
	game._on_characters_confirmed(["一护", "白哉"], ["魂", "魂"])
	game._enter_current_fight(2)
	game.ichigo.ai_random_clock.cancel()
	var fighters: Array[FighterRuntime] = [game.naruto, game.ichigo]
	var intro: BattleIntro = game.battle_intro
	# This is an acceptance-only partial standing-checkpoint setup. The source
	# poll seed is retained and no source frame is shifted; production boot/intro
	# parity remains outside this run.
	intro.begin(fighters, true)
	# One explicit standing checkpoint; never overwrite later observed state.
	var seed: Dictionary = polls[0].expected
	assert(seed.step == 0 and seed.states == [0, 0])
	for i in 2:
		# Frame 2 has a valid predecessor: frame 1 was initialized by setup.
		# Frame 1 itself would require reconstructing the preceding loop/goto.
		# Frame 8 also has an ordinary predecessor; its loop script is deferred
		# until after the recorded poll, as in r15 sequences 1070–1073.
		assert(seed.frames[i] >= 2 and seed.frames[i] <= 8)
		fighters[i].play_source_frame(seed.frames[i] - 1)
		fighters[i]._ai_pending_frames.clear()
		fighters[i]._ai_state_frame_applied = seed.frames[i] - 1
	game.before_recorded_intro_poll.connect(func(event: Dictionary):
		var actual := {"step": intro.step, "states": [intro.states[0], intro.states[1]],
			"frames": [fighters[0].current_source_frame(), fighters[1].current_source_frame()]}
		var matches: bool = actual == event.expected
		comparisons.append({"sequence": event.sequence, "display_tick": event.display_tick,
			"expected": event.expected, "actual": actual, "matches": matches})
		if not boundary_mode: mismatch = mismatch or not matches)
	var scheduled := {}
	for poll: Dictionary in polls:
		if not scheduled.has(poll.display_tick): scheduled[poll.display_tick] = []
		scheduled[poll.display_tick].append(poll)
	var tape: Array = []
	var inputs := {}
	var seed_sample := ""
	if combat_mode:
		game.ko_recorded_timers = true
		for event: Dictionary in source_events:
			if int(event.sequence) < polls[0].sequence:
				if event.kind == "sample": seed_sample = event.value
				continue
			if event.kind == "match" and str(event.value).begins_with("nextfight_enter,"):
				var tick := int(event.display_tick)
				if not scheduled.has(tick): scheduled[tick] = []
				scheduled[tick].append({"kind": "nextfight", "phase": "before_root_observer",
					"sequence": int(event.sequence), "time_ms": int(event.time_ms)})
			if event.kind == "input_next_display":
				inputs[int(event.display_tick)] = str(event.value)
			if event.kind == "random":
				var values: PackedStringArray = str(event.value).split(",")
				tape.append({"site": values[1], "value": parse_value(values[2]),
					"original_index": int(values[0])})
			if event.kind == "sample":
				var tick := int(event.display_tick)
				if not scheduled.has(tick): scheduled[tick] = []
				scheduled[tick].append({"kind": "ai_random", "phase": "after_actor_advance",
					"sequence": int(event.sequence), "time_ms": int(event.time_ms)})
		var clock_tape: Array = []
		var clock_index := 0
		for event: Dictionary in source_events:
			if event.kind != "clock": continue
			var values: PackedStringArray = str(event.value).split(",")
			assert(values.size() == 3 and int(values[0]) == clock_index + 1)
			clock_index += 1
			if int(event.sequence) > int(polls[0].sequence):
				clock_tape.append({"site": values[1], "value": int(values[2]), "original_index": clock_index})
		var clock_valid: bool = game.source_clock.use_recorded_tape(clock_tape)
		assert(clock_valid)
		assert(seed_sample != "")
		var seed_values := seed_sample.split(",")
		var assignments: Array = game.ichigo.ai_source_state.spec.random_refresh.assignments
		for i in assignments.size():
			game.ichigo.ai_source_state.values[assignments[i].field] = parse_value(seed_values[i + 1])
		var tape_valid: bool = game.source_random.use_recorded_tape(tape)
		assert(tape_valid)
		game.ichigo.ai_random_clock.initialize(game.ichigo.ai_source_state, game.source_random, 5, true)
	for tick in scheduled:
		scheduled[tick].sort_custom(func(a: Dictionary, b: Dictionary): return a.sequence < b.sequence)
	if boundary_mode:
		setup_body_boundaries(source_events, int(polls[0].sequence), fighters)
	var native_ready: Array = []
	var last_tick: int = original_frames.keys().max()
	if combat_mode:
		var completion_events := source_events.filter(func(event: Dictionary) -> bool: return event.kind == "done")
		assert(completion_events.size() == 1 and int(completion_events[0].display_tick) == last_tick,
			"Combat replay cutoff must match the original root observer's done event")
	for current_tick in range(int(polls[0].display_tick), last_tick):
		if combat_mode and inputs.has(current_tick):
			apply_recorded_input(game, inputs[current_tick], current_tick)
		var observation_tick := current_tick + 1
		if game.session.root_label == "游戏场景":
			game._advance_fight(scheduled.get(current_tick, []), func() -> bool:
				var present: bool = game.session.root_label == "游戏场景"
				if not present:
					assert(game.opponent_driver == null and game.player_body_driver == null and not game.game_world.visible)
				compare_frames(fighters, observation_tick, original_frames, present)
				return observation_tick == last_tick)
		else:
			assert(scheduled.get(current_tick, []).is_empty(), "Source timer survived fight teardown")
			compare_frames(fighters, observation_tick, original_frames, false)
		if combat_mode and (game.source_random.failure != "" or game.source_clock.failure != ""):
			mismatch = true
			break
		if not intro.active and native_ready.is_empty():
			for i in 2:
				native_ready.append({"slot": "p%d" % (i + 1), "frame": fighters[i].current_source_frame(),
					"display_tick": current_tick + 1})
			native_checkpoint = {
				"display_tick": current_tick + 1,
				"fight_tick": 0,
				"actors": [],
				"random_absolute_index": game.source_random.absolute_index,
				"clock_absolute_index": game.source_clock.absolute_index,
				"battle_intro_active": game.battle_intro.active,
				"pending_frame_actions": [],
				"helpers": [],
			}
			for fighter in fighters:
				native_checkpoint["actors"].append({"slot": fighter.player_slot, "frame": fighter.current_source_frame(),
					"x": fighter.source_x, "y": fighter.source_y, "xscale": fighter.scale.x * 100,
					"action": fighter.ai_source_state.read_field("动作"), "hp": fighter.health,
					"ql": fighter.energy, "sw": fighter.sw, "touch": fighter.ai_source_state.read_field("touch"),
					"touchFloor": fighter.ai_source_state.read_field("touchFloor"),
					"hits": fighter.hits, "paused": fighter.root_zhanting,
					"hstm": fighter.ai_source_state.read_field("hstm"),
					"hurtSkling": fighter.ai_source_state.read_field("hurtSkling")})
				native_checkpoint["pending_frame_actions"].append(fighter._ai_pending_frames.size())
			for helper in [game.naruto_helper, game.ichigo_helper]:
				if helper == null:
					continue
				native_checkpoint["helpers"].append({"slot": helper.diagnostic_slot, "helper_id": helper.helper_id,
					"frame": helper.current_source_frame(), "source_action": helper.source_action,
					"attacking": helper.attacking, "timeline_playing": helper.timeline_playing,
					"visible": helper.visible, "deferred_frame": helper._deferred_frame})
				helper_snapshots.append({"display_tick": current_tick + 1, "tick": current_tick + 1,
					"slot": helper.diagnostic_slot, "frame": helper.current_source_frame(),
					"x": helper.position.x, "y": helper.position.y,
					"facing": helper.facing, "action": helper.source_action,
					"attacking": helper.attacking, "hits": helper.hited})
			ready_recorded = true
		if mismatch: break
	if boundary_mode and not mismatch and boundary_cursor != boundary_expected.size():
		boundary_failure = {"reason": "reference_boundaries_not_consumed", "remaining": boundary_expected.size() - boundary_cursor}
		mismatch = true
	if combat_mode and not mismatch:
		mismatch = not game.source_random.replay_complete() or not game.source_clock.replay_complete()
	var report := {"status": "first_difference" if mismatch else ("boundary_segment_observed_fields_match" if boundary_mode else "segment_observed_fields_match"),
		"observation_phase": "after_initial_frames_before_deferred_targets",
		"termination": "original_done_root_observer" if combat_mode else "intro_segment_cutoff",
		"reference_sha256": FileAccess.get_sha256(args[0]),
		"boundary_mode": boundary_mode, "boundary_failure": boundary_failure,
		"boundary_comparisons": boundary_records, "boundary_consumed": boundary_cursor,
		"boundary_expected": boundary_expected.size(),
		"clock_failure": game.source_clock.failure if combat_mode else "",
		"clock_consumed": game.source_clock.consumed if combat_mode else [],
		"clock_tape_complete": game.source_clock.replay_complete() if combat_mode else false,
		"random_failure": game.source_random.failure if combat_mode else "",
		"combat_mode": combat_mode, "random_consumed": game.source_random.consumed if combat_mode else [],
		"random_seed_sample": seed_sample if combat_mode else "",
		"random_original_indices": tape.map(func(record): return record.original_index),
		"input_transitions": input_transitions.duplicate(true),
		"random_tape_complete": game.source_random.replay_complete() if combat_mode else false,
		"original_parity_verified": false, "comparisons": comparisons,
		"frame_comparisons": frame_comparisons,
		"state_comparisons": state_comparisons,
		"geometry_comparisons": geometry_comparisons,
		"helper_snapshots": helper_snapshots,
		"geometry_summary": geometry_summary(),
		"original_ready": original_ready, "native_ready": native_ready,
		"native_checkpoint": native_checkpoint,
		"ready_matches": native_ready == original_ready,
		"limits": ["Starts from one partial standing checkpoint after load, not boot.",
			"Geometry records raw deltas separately; observed-fields status does not certify geometric parity.",
			"Native wall clock is cancelled; combat mode replays recorded random calls and an initial sample checkpoint.",
			"Legacy decimal captures may lose low bits; f: binary53 tokens preserve the recorded value. Loading/music prefix and timeout phases are not replayed.",
			"Assigns recorded polls to after_actor_advance; this phase remains provisional.",
			"Native snapshots use the root-observer phase before deferred target scripts; final fscommand(quit) cuts at that same phase.",
			"Stops at first differing frame, poll input or observed state; no per-poll state correction."]}
	var file := FileAccess.open(args[1], FileAccess.WRITE)
	assert(file != null)
	file.store_string(JSON.stringify(report, "  ", false, true) + "\n")
	file.close()
	apply_recorded_input(game, "", -1)
	game._goto_menu()
	game.queue_free()
	await process_frame
	print("INTRO_CONTINUOUS_REFERENCE_DONE ", report.status, " polls=", comparisons.size())
	quit()
