extends SceneTree

const Fixture = preload("res://tests/rollback_fixture.gd")
const BattleInputs = preload("res://rollback_session.gd")
const State = preload("res://simulation_state.gd")

func _initialize() -> void:
	_run.call_deferred()

func _players(frame: int) -> Dictionary:
	var result := {"p1": {}, "p2": {}}
	for slot in result:
		for button in BattleInputs.BUTTONS: result[slot][button] = false
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

func _run() -> void:
	assert(State.BINARY_GRAPH_BUILD == "battle-local-pba-dict-flat-v2", "Run this comparator only against the flat graph build")
	var args := OS.get_cmdline_user_args()
	if args.size() != 1:
		push_error("Expected the frozen 331-frame PBA graph tape path")
		quit(1)
		return
	var baseline_file := FileAccess.open(args[0], FileAccess.READ)
	if baseline_file == null:
		push_error("Could not open frozen graph tape: " + args[0])
		quit(1)
		return
	var fixture := Fixture.create(self)
	var game: Node = fixture.game
	var battle: RefCounted = fixture.battle
	var compared_dictionary_entries := 0
	var baseline_graph_bytes := 0
	var candidate_graph_bytes := 0
	var baseline_pair_arrays := 0
	var frames := 0
	var max_records := 0
	for frame in range(331):
		if frame > 0:
			var skip := frame >= 30 and frame < 90
			var callbacks := []
			if game.battle_intro.polling and frame % 15 == 0 and not (skip and game.battle_intro.step > 1 and game.battle_intro.step < 4):
				callbacks.append({"kind": "intro_poll", "phase": "after_actor_advance", "sequence": frame, "time_ms": frame * 33})
			var problem: String = battle.set_frame_events(frame, frame * 33, skip, callbacks)
			if not problem.is_empty():
				push_error(problem)
				Fixture.dispose(game, battle)
				quit(1)
				return
			problem = battle.advance(frame, _players(frame))
			if not problem.is_empty():
				push_error(problem)
				Fixture.dispose(game, battle)
				quit(1)
				return
		var baseline_line := baseline_file.get_line()
		var baseline_parts := baseline_line.split(":", false, 2)
		if baseline_parts.size() != 3 or int(baseline_parts[0]) != frame:
			push_error("Frozen graph tape frame mismatch at %d" % frame)
			Fixture.dispose(game, battle)
			quit(1)
			return
		var baseline_bytes: PackedByteArray = baseline_parts[2].hex_decode()
		if baseline_bytes.size() != int(baseline_parts[1]):
			push_error("Frozen graph tape byte length mismatch at %d" % frame)
			Fixture.dispose(game, battle)
			quit(1)
			return
		var baseline_records_value: Variant = bytes_to_var(baseline_bytes)
		var snapshot: Dictionary = battle.save_state()
		if snapshot.has("error"):
			push_error(str(snapshot.error))
			Fixture.dispose(game, battle)
			quit(1)
			return
		var candidate_bytes: PackedByteArray = snapshot.owners.battle.owners.graph
		var candidate_records_value: Variant = bytes_to_var(candidate_bytes)
		if not baseline_records_value is Array or not candidate_records_value is Array:
			push_error("Graph tape did not decode to record arrays")
			Fixture.dispose(game, battle)
			quit(1)
			return
		var baseline_records: Array = baseline_records_value
		var candidate_records: Array = candidate_records_value
		if baseline_records.size() != candidate_records.size():
			push_error("Graph record count differs at frame %d" % frame)
			Fixture.dispose(game, battle)
			quit(1)
			return
		var baseline_flat_records: Array = baseline_records.duplicate(true)
		for record_index in baseline_records.size():
			var baseline_record: Dictionary = baseline_records[record_index]
			var baseline_flat_record: Dictionary = baseline_flat_records[record_index]
			var candidate_record: Dictionary = candidate_records[record_index]
			if baseline_record.get("kind") != candidate_record.get("kind"):
				push_error("Graph record kind differs at %d/%d" % [frame, record_index])
				Fixture.dispose(game, battle)
				quit(1)
				return
			if baseline_record.kind != "dictionary": continue
			var old_entries: Array = baseline_record.entries
			var flat_entries: Array = candidate_record.entries
			var derived_flat_entries := []
			if flat_entries.size() % 2 != 0:
				push_error("Flat dictionary has odd entries at %d/%d" % [frame, record_index])
				Fixture.dispose(game, battle)
				quit(1)
				return
			var paired_entries := []
			for old_pair in old_entries:
				if not old_pair is Array or old_pair.size() != 2:
					push_error("Frozen dictionary pair layout invalid at %d/%d" % [frame, record_index])
					Fixture.dispose(game, battle)
					quit(1)
					return
				baseline_pair_arrays += 1
				derived_flat_entries.append(old_pair[0])
				derived_flat_entries.append(old_pair[1])
			baseline_flat_record.entries = derived_flat_entries
			for entry_index in range(0, flat_entries.size(), 2):
				paired_entries.append([flat_entries[entry_index], flat_entries[entry_index + 1]])
			if old_entries.size() != paired_entries.size():
				push_error("Dictionary entry count differs at %d/%d" % [frame, record_index])
				Fixture.dispose(game, battle)
				quit(1)
				return
			compared_dictionary_entries += paired_entries.size()
			candidate_record.entries = paired_entries
		var derived_baseline_bytes: PackedByteArray = var_to_bytes(baseline_flat_records)
		if derived_baseline_bytes != candidate_bytes:
			push_error("Raw graph bytes differ after dictionary-layout-only conversion at frame %d" % frame)
			Fixture.dispose(game, battle)
			quit(1)
			return
		var difference := State.first_difference(baseline_records, candidate_records)
		if not difference.is_empty():
			push_error("Full graph first difference at frame %d: %s" % [frame, difference])
			Fixture.dispose(game, battle)
			quit(1)
			return
		baseline_graph_bytes += baseline_bytes.size()
		candidate_graph_bytes += candidate_bytes.size()
		max_records = maxi(max_records, candidate_records.size())
		frames += 1
	if not baseline_file.get_line().is_empty():
		push_error("Frozen graph tape has trailing frames")
		Fixture.dispose(game, battle)
		quit(1)
		return
	baseline_file.close()
	Fixture.dispose(game, battle)
	await process_frame
	print("CHECKPOINT_FLAT_GRAPH_EQUIVALENCE_OK frames=%d raw_byte_identical_after_r2_dictionary_flatten=true normalization=dictionary_entries_only baseline_pairs=%d dictionary_entries=%d pair_arrays_removed_by_r3_layout=%d baseline_bytes=%d candidate_bytes=%d bytes_saved_by_r3_layout=%d max_records=%d" % [frames, baseline_pair_arrays, compared_dictionary_entries, baseline_pair_arrays, baseline_graph_bytes, candidate_graph_bytes, baseline_graph_bytes - candidate_graph_bytes, max_records])
	quit()
