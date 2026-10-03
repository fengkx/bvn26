extends SceneTree

const Session := preload("res://rollback_session.gd")
const State := preload("res://simulation_state.gd")


class Adapter extends RefCounted:
	var frame := 0
	var score := 0
	var confirmed := 0
	var loads := 0
	var replaying := false
	var session: RefCounted

	func save_state() -> Dictionary:
		return State.pack_state("batch-fixture", frame, {"score": score})

	func validate_state(snapshot: Dictionary) -> String:
		return State.validate_snapshot(snapshot, "batch-fixture", ["score"])

	func load_state(snapshot: Dictionary) -> String:
		frame = snapshot.frame
		score = snapshot.owners.score
		loads += 1
		return ""

	func advance(next: int, players: Dictionary) -> String:
		assert(next == frame + 1)
		frame = next
		# A rolling value detects missing, reordered and repeated input consumption.
		score = (score * 17 + frame * (3 if players.p1.attack or players.p2.attack else 1)) % 1_000_003
		return ""

	func confirm_through(value: int) -> void:
		assert(session._dirty_from < 0, "Cannot confirm a stale prediction")
		confirmed = value

	func begin_replay() -> void:
		replaying = true

	func end_replay() -> void:
		replaying = false


func _initialize() -> void:
	_run.call_deferred()


func _buttons(attack: bool = false) -> Dictionary:
	var held := Session._neutral()
	held.attack = attack
	return held


func _make() -> RefCounted:
	var adapter := Adapter.new()
	var session := Session.new()
	adapter.session = session
	assert(session.configure(adapter, "batch", 8, 16).is_empty())
	return session


func _run() -> void:
	for delivery in [[1, 2, 3, 4, 5, 6], [6, 5, 4, 3, 2, 1], [3, 1, 6, 2, 5, 4]]:
		var immediate := _make()
		var batched := _make()
		for frame in range(1, 7):
			for session in [immediate, batched]:
				assert(session.receive("batch", "p1", frame, _buttons()).is_empty())
				assert(session.step().is_empty())
		for frame in delivery:
			var held := _buttons(frame % 2 == 0)
			assert(immediate.receive("batch", "p2", frame, held).is_empty())
			assert(batched.receive("batch", "p2", frame, held, true).is_empty())
			assert(batched.receive("batch", "p2", frame, held, true).is_empty())
		assert(batched.rollback_count == 0 and batched._adapter.loads == 0)
		assert(batched._adapter.confirmed < 2)
		assert(batched.pending_correction().dirty_from == 2)
		# Exact reads are a safety barrier even without a transport drain signal.
		assert(State.first_difference(immediate.state_at(6), batched.state_at(6)).is_empty())
		assert(batched.rollback_count == 1 and batched._adapter.loads == 1)
		assert(batched.replayed_frames == 5 and batched.settled() == 6)
		for frame in range(7):
			assert(State.first_difference(immediate.state_at(frame), batched.state_at(frame)).is_empty())
		assert(batched.reconcile().is_empty() and batched.rollback_count == 1)
		print("BATCH_CORRECTION_CASE ", JSON.stringify({"order": delivery,
			"immediate_corrections": immediate.rollback_count, "batched_corrections": batched.rollback_count,
			"immediate_replayed": immediate.replayed_frames, "batched_replayed": batched.replayed_frames}))
		_dispose(immediate)
		_dispose(batched)
	_test_step_and_pruning()
	print("ROLLBACK_BATCHED_CORRECTION_SMOKE_OK all_frames_equal=true orders=3 duplicate_idempotent=true final_reads_settled=true")
	quit()


func _test_step_and_pruning() -> void:
	var session := _make()
	assert(session.receive("batch", "p1", 1, _buttons()).is_empty())
	assert(session.step().is_empty())
	assert(session.receive("batch", "p2", 1, _buttons(true), true).is_empty())
	var pending: Dictionary = session.pending_correction()
	assert(session.receive("batch", "p2", 1, _buttons(), true) == "Conflicting immutable input")
	assert(session.pending_correction() == pending)
	assert(session.step().is_empty())
	assert(session.rollback_count == 1 and session._dirty_from < 0)
	for frame in range(2, 40):
		for slot in ["p1", "p2"]:
			assert(session.receive("batch", slot, frame, _buttons(), true).is_empty())
		assert(session.reconcile().is_empty())
		if frame > session.frontier:
			assert(session.step().is_empty())
	assert(session.input_floor == session.oldest_frame())
	assert(not session.can_receive_frame(session.input_floor))
	assert(session.can_receive_frame(session.input_floor + 1))
	_dispose(session)


func _dispose(session: RefCounted) -> void:
	session._adapter.session = null
