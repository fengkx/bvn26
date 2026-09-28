extends SceneTree

const Checkpoint = preload("res://battle_checkpoint.gd")
const Fixture = preload("res://tests/rollback_fixture.gd")
const State = preload("res://simulation_state.gd")

func _initialize() -> void:
	_run.call_deferred()

func _run() -> void:
	var checkpoint := Checkpoint.new()
	var shared_array: Array = [1, "same"]
	var equal_array_a: Array = [1, "same"]
	var equal_array_b: Array = [1, "same"]
	var shared_dictionary: Dictionary = {"same": 1}
	var equal_dictionary_a: Dictionary = {"same": 1}
	var equal_dictionary_b: Dictionary = {"same": 1}
	var typed_empty: Dictionary[String, int] = {}
	var typed_nonempty: Dictionary[String, int] = {"answer": 42}
	var roots := {
		"shared_array_a": shared_array,
		"shared_array_b": shared_array,
		"equal_array_a": equal_array_a,
		"equal_array_b": equal_array_b,
		"shared_dictionary_a": shared_dictionary,
		"shared_dictionary_b": shared_dictionary,
		"equal_dictionary_a": equal_dictionary_a,
		"equal_dictionary_b": equal_dictionary_b,
		"typed_empty": typed_empty,
		"typed_nonempty": typed_nonempty,
	}
	assert(checkpoint._encode(roots) == {"ref": 0})
	assert(checkpoint.error.is_empty(), checkpoint.error)
	var root_record: Dictionary = checkpoint._records[0]
	assert(root_record.kind == "dictionary")
	assert(root_record.entries.size() % 2 == 0)
	var references := {}
	for entry_index in range(0, root_record.entries.size(), 2):
		var key: String = root_record.entries[entry_index]
		var value: Variant = root_record.entries[entry_index + 1]
		assert(value is Dictionary and value.has("ref"), "Expected encoded container ref at " + key)
		references[key] = value.ref
	assert(references.shared_array_a == references.shared_array_b)
	assert(references.equal_array_a != references.equal_array_b)
	assert(references.shared_dictionary_a == references.shared_dictionary_b)
	assert(references.equal_dictionary_a != references.equal_dictionary_b)
	var empty_record: Dictionary = checkpoint._records[references.typed_empty]
	var nonempty_record: Dictionary = checkpoint._records[references.typed_nonempty]
	assert(empty_record.kind == "dictionary" and empty_record.entries.is_empty())
	assert(nonempty_record.kind == "dictionary" and nonempty_record.entries.size() == 2)
	var typed_prototype: Dictionary = checkpoint._constants[empty_record.prototype]
	assert(typed_prototype.is_typed_key() and typed_prototype.get_typed_key_builtin() == TYPE_STRING)
	assert(typed_prototype.is_typed_value() and typed_prototype.get_typed_value_builtin() == TYPE_INT)
	assert(empty_record.prototype == nonempty_record.prototype)
	assert(checkpoint._validate_graph_records([{"kind": "dictionary", "entries": ["key"]}]) == "Invalid dictionary graph entries")
	var cycle_records := [
		{"kind": "array", "entries": [{"ref": 0}]},
		{"kind": "dictionary", "entries": ["self", {"ref": 1}]},
	]
	assert(checkpoint._validate_graph_records(cycle_records).is_empty())
	checkpoint._restored = [[], {}]
	checkpoint._restored[0].append(checkpoint._decode({"ref": 0}))
	checkpoint._restored[1]["self"] = checkpoint._decode({"ref": 1})
	assert(is_same(checkpoint._restored[0][0], checkpoint._restored[0]))
	assert(is_same(checkpoint._restored[1]["self"], checkpoint._restored[1]))
	checkpoint._restored.clear()

	var fixture := Fixture.create(self)
	var game: Node = fixture.game
	var battle: RefCounted = fixture.battle
	var before: Dictionary = battle.save_state()
	assert(not before.has("error"), str(before))
	var retained_snapshot: Dictionary = before.owners.battle
	var original_key: String = battle.checkpoint._snapshot_key(retained_snapshot)
	var malformed := retained_snapshot.duplicate(true)
	var malformed_records: Array = bytes_to_var(malformed.owners.graph)
	var found_dictionary := false
	for record in malformed_records:
		if record.get("kind") == "dictionary":
			record.entries = ["odd"]
			found_dictionary = true
			break
	assert(found_dictionary, "Fixture graph had no dictionary record")
	malformed.owners.graph = var_to_bytes(malformed_records)
	var malformed_key: String = battle.checkpoint._snapshot_key(malformed)
	assert(malformed_key != original_key)
	battle.checkpoint._snapshot_graphs[malformed_key] = malformed.owners.graph
	battle.checkpoint._snapshot_frames[malformed_key] = malformed.frame
	battle.checkpoint._snapshots[malformed_key] = battle.checkpoint._snapshots[original_key]
	assert(battle.checkpoint.load_state(malformed) == "Invalid dictionary graph entries")
	assert(State.first_difference(before, battle.save_state()).is_empty(), "Odd entries changed the current battle state")
	Fixture.dispose(game, battle)
	await process_frame
	print("BATTLE_CHECKPOINT_FLAT_DICTIONARY_SMOKE_OK alias=true equal_identity=true typed_empty_nonempty=true cycle_refs=true odd_rejected_before_restore=true")
	quit()
