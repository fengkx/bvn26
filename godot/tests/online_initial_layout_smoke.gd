extends SceneTree
const Fixture = preload("res://tests/rollback_fixture.gd")
const State = preload("res://simulation_state.gd")
func _initialize() -> void:
	_run.call_deferred()
func _run() -> void:
	var left_parent := Node.new()
	var right_parent := Node.new()
	root.add_child(left_parent)
	root.add_child(right_parent)
	right_parent.add_child(Node.new())
	var left := Fixture.create(self, [], [], "", left_parent)
	var right := Fixture.create(self, [], [], "", right_parent)
	var a: Dictionary = left.battle.save_state()
	var b: Dictionary = right.battle.save_state()
	var graph: PackedByteArray = a.owners.battle.owners.graph
	print("CHECKPOINT_BYTES graph=%d envelope=%d raw_30hz_Bps=%d" % [graph.size(), var_to_bytes(a).size(), var_to_bytes(a).size() * 30])
	var diff := State.first_difference(bytes_to_var(graph), bytes_to_var(b.owners.battle.owners.graph))
	print("INITIAL_LAYOUT_DIFFERENCE ", diff)
	var sequence: int = left.game.diagnostics.sequence
	left.battle.begin_replay()
	left.game.diagnostics.push_event("input_consumed", {"keys": {}})
	assert(left.game.diagnostics.sequence == sequence)
	left.battle.end_replay()
	left.game.diagnostics.push_event("input_consumed", {"keys": {}})
	assert(left.game.diagnostics.sequence == sequence + 1)
	Fixture.dispose(left.game, left.battle)
	Fixture.dispose(right.game, right.battle)
	left_parent.free()
	right_parent.free()
	if not diff.is_empty():
		quit(1)
		return
	print("ONLINE_INITIAL_LAYOUT_SMOKE_OK")
	quit()
