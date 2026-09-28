extends SceneTree

const Fixture = preload("res://tests/rollback_fixture.gd")
const Session = preload("res://rollback_test_session.gd")
const State = preload("res://simulation_state.gd")
const MEASURED_FRAMES := 330

func _initialize() -> void:
	_run.call_deferred()

func _players(frame: int) -> Dictionary:
	var result := {"p1": {}, "p2": {}}
	for slot in result:
		for button in Session.BUTTONS:
			result[slot][button] = false
	if frame >= 165 and frame < 190:
		result.p1.right = true
		result.p2.left = true
	if frame >= 195 and frame < 200:
		result.p1.attack = true
		result.p2.attack = true
	if frame >= 205 and frame < 207: result.p1.jump = true
	if frame >= 235 and frame < 237: result.p1.ranged = true
	if frame >= 270 and frame < 272: result.p2.summon = true
	return result

func _frame_events(game: Node, frame: int) -> Array:
	var skip := frame >= 30 and frame < 90
	var callbacks := []
	if game.battle_intro.polling and frame % 15 == 0 and not (skip and game.battle_intro.step > 1 and game.battle_intro.step < 4):
		callbacks.append({"kind": "intro_poll", "phase": "after_actor_advance", "sequence": frame, "time_ms": frame * 33})
	return [frame * 33, skip, callbacks]

func _run() -> void:
	var fixture := Fixture.create(self)
	var game: Node = fixture.game
	var battle: RefCounted = fixture.battle
	# The fixture already owns a configured rollback battle; keep it and run the
	# same no-late reference and delayed-input schedule as rollback_battle_smoke.
	var initial: Dictionary = battle.save_state()
	var reference := {}
	for frame in range(1, MEASURED_FRAMES + 1):
		var envelope := _frame_events(game, frame)
		var journal_problem: String = battle.set_frame_events(frame, envelope[0], envelope[1], envelope[2])
		if not _check(journal_problem):
			Fixture.dispose(game, battle)
			quit(1)
			return
		var players := _players(frame)
		if not _check(battle.advance(frame, players)):
			Fixture.dispose(game, battle)
			quit(1)
			return
		if frame == MEASURED_FRAMES: reference = battle.save_state()
	var problem: String = battle.load_state(initial)
	if not _check(problem):
		Fixture.dispose(game, battle)
		quit(1)
		return
	battle.checkpoint.profile = {"saves": 0, "encode_us": 0, "pack_us": 0, "retains_us": 0}
	var session := Session.new()
	problem = session.configure(battle, "real-battle", 8, 12)
	if not _check(problem):
		Fixture.dispose(game, battle)
		quit(1)
		return
	var receive_samples: Array[int] = []
	var correction_receive_samples: Array[int] = []
	var step_samples: Array[int] = []
	var combined_samples: Array[int] = []
	var wall_tick := 0
	var delivered := 0
	var waits := 0
	var measured_started := Time.get_ticks_usec()
	while session.frontier < MEASURED_FRAMES or session.confirmed < MEASURED_FRAMES:
		wall_tick += 1
		if wall_tick >= 400:
			_check("Delayed-input profile exceeded 399 wall ticks")
			Fixture.dispose(game, battle)
			quit(1)
			return
		var combined_started := Time.get_ticks_usec()
		if session.frontier < MEASURED_FRAMES:
			var next := session.frontier + 1
			var receive_started := Time.get_ticks_usec()
			problem = session.receive("real-battle", "p1", next, _players(next).p1)
			receive_samples.append(Time.get_ticks_usec() - receive_started)
			if not _check(problem):
				Fixture.dispose(game, battle)
				quit(1)
				return
		if wall_tick % 3 == 0 and not (wall_tick >= 165 and wall_tick < 180):
			var through := MEASURED_FRAMES if session.frontier == MEASURED_FRAMES else maxi(0, session.frontier - 5)
			for remote_frame in range(through, delivered, -1):
				var rollback_before := session.rollback_count
				var receive_started := Time.get_ticks_usec()
				problem = session.receive("real-battle", "p2", remote_frame, _players(remote_frame).p2)
				var receive_us := Time.get_ticks_usec() - receive_started
				receive_samples.append(receive_us)
				if session.rollback_count > rollback_before:
					correction_receive_samples.append(receive_us)
				if not _check(problem):
					Fixture.dispose(game, battle)
					quit(1)
					return
				problem = session.receive("real-battle", "p2", remote_frame, _players(remote_frame).p2)
				if not _check(problem):
					Fixture.dispose(game, battle)
					quit(1)
					return
			delivered = maxi(delivered, through)
		if session.frontier < MEASURED_FRAMES:
			var previous := session.frontier
			var step_started := Time.get_ticks_usec()
			problem = session.step()
			step_samples.append(Time.get_ticks_usec() - step_started)
			if problem == "waiting_for_input":
				waits += 1
				if session.frontier != previous:
					_check("Waiting step changed the simulation frontier")
					Fixture.dispose(game, battle)
					quit(1)
					return
			elif not _check(problem):
				Fixture.dispose(game, battle)
				quit(1)
				return
		combined_samples.append(Time.get_ticks_usec() - combined_started)
		if wall_tick % 30 == 0:
			await process_frame
	var actual: Dictionary = session.state_at(MEASURED_FRAMES)
	var reference_semantic := _semantic_snapshot(reference)
	var actual_semantic := _semantic_snapshot(actual)
	var difference := State.first_difference(reference_semantic, actual_semantic)
	if not difference.is_empty():
		push_error("Full logical checkpoint diverged after delayed input: " + difference)
		Fixture.dispose(game, battle)
		quit(1)
		return
	var operation_wall_us := Time.get_ticks_usec() - measured_started
	var semantic_cross_source_difference := "not_compared"
	var args := OS.get_cmdline_user_args()
	if args.size() == 2 and args[0] == "write-state":
		var state_file := FileAccess.open(args[1], FileAccess.WRITE)
		if state_file == null:
			_check("Could not write canonical state: " + args[1])
			Fixture.dispose(game, battle)
			quit(1)
			return
		state_file.store_buffer(var_to_bytes(reference_semantic))
		state_file.close()
		semantic_cross_source_difference = "written"
	elif args.size() == 2 and args[0] == "compare-state":
		var state_file := FileAccess.open(args[1], FileAccess.READ)
		if state_file == null:
			_check("Could not read baseline canonical state: " + args[1])
			Fixture.dispose(game, battle)
			quit(1)
			return
		var baseline_semantic: Variant = bytes_to_var(state_file.get_buffer(state_file.get_length()))
		state_file.close()
		semantic_cross_source_difference = State.first_difference(baseline_semantic, actual_semantic)
		if not semantic_cross_source_difference.is_empty():
			push_error("Cross-source full logical checkpoint differs: " + semantic_cross_source_difference)
			Fixture.dispose(game, battle)
			quit(1)
			return
	elif not args.is_empty():
		_check("Expected no arguments, write-state <path>, or compare-state <path>")
		Fixture.dispose(game, battle)
		quit(1)
		return
	var profile: Dictionary = battle.checkpoint.profile.duplicate(true)
	var result := {
		"fixture": "rollback_battle_smoke_default_330_ticks",
		"delayed_input_schedule": "same reverse-order, 5-frame-old P2 batches, duplicate delivery, and temporary outage as rollback_battle_smoke.gd",
		"frames": MEASURED_FRAMES,
		"frontier": session.frontier,
		"confirmed": session.confirmed,
		"rollbacks": session.rollback_count,
		"replayed_frames": session.replayed_frames,
		"waits": waits,
		"semantic_full_state_sha256": _semantic_hash(actual_semantic),
		"semantic_reference_sha256": _semantic_hash(reference_semantic),
		"semantic_cross_source_difference": semantic_cross_source_difference,
		"logical_record_count": actual_semantic.owners.battle.owners.graph.size(),
		"checkpoint_profile": profile,
		"receive_us": _stats(receive_samples),
		"correction_receive_us": _stats(correction_receive_samples),
		"step_us": _stats(step_samples),
		"wall_tick_us": _stats(combined_samples),
		"operation_wall_us": operation_wall_us,
	}
	print("ROLLBACK_DELAYED_INPUT_PROFILE ", JSON.stringify(result))
	Fixture.dispose(game, battle)
	await process_frame
	quit()

func _semantic_snapshot(snapshot: Dictionary) -> Dictionary:
	var result: Dictionary = snapshot.duplicate(true)
	var source_build: String = result.owners.battle.build
	if source_build not in ["battle-local-v1", "battle-local-pba-v1", "battle-local-pba-dict-flat-v2"]:
		push_error("Unknown graph build marker in semantic comparison: " + source_build)
		return {}
	var graph: Variant = result.owners.battle.owners.graph
	var graph_bytes: PackedByteArray = graph.hex_decode() if graph is String else graph
	var records_value: Variant = bytes_to_var(graph_bytes)
	if source_build == "battle-local-pba-dict-flat-v2":
		for record in records_value:
			if record.get("kind") != "dictionary": continue
			var flat_entries: Array = record.entries
			assert(flat_entries.size() % 2 == 0, "Flat dictionary graph has an odd entry count")
			var pairs := []
			for entry_index in range(0, flat_entries.size(), 2):
				pairs.append([flat_entries[entry_index], flat_entries[entry_index + 1]])
			record.entries = pairs
	result.owners.battle.owners.graph = records_value
	# The build marker selects a known dictionary entry layout. All payload fields
	# remain exact; only the flat representation is paired for comparison.
	result.owners.battle.build = "battle-local-v1"
	return State.canonical(result)

func _semantic_hash(snapshot: Dictionary) -> String:
	var hashing := HashingContext.new()
	if hashing.start(HashingContext.HASH_SHA256) != OK:
		return ""
	if hashing.update(var_to_bytes(snapshot)) != OK:
		return ""
	return hashing.finish().hex_encode()

func _stats(samples: Array[int]) -> Dictionary:
	if samples.is_empty(): return {"count": 0}
	samples.sort()
	var total := 0
	for value in samples: total += value
	return {
		"count": samples.size(),
		"mean": float(total) / samples.size(),
		"p50": _percentile(samples, 0.50),
		"p95": _percentile(samples, 0.95),
		"p99": _percentile(samples, 0.99),
		"max": samples.back(),
	}

func _percentile(sorted_samples: Array[int], fraction: float) -> int:
	return sorted_samples[mini(sorted_samples.size() - 1, maxi(0, int(ceil(sorted_samples.size() * fraction)) - 1))]

func _check(problem: String) -> bool:
	if problem.is_empty(): return true
	push_error(problem)
	return false
