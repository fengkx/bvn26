extends "res://tests/rollback_batched_correction_smoke.gd"


class ForcedAdapter extends Adapter:
	func must_save_frame(value: int) -> bool:
		return value == 17 or value == 59


func _run() -> void:
	var sessions := []
	for sparse in [false, true]:
		var adapter := ForcedAdapter.new()
		var session := Session.new()
		session.sparse_saves = sparse
		adapter.session = session
		assert(session.configure(adapter, "batch", 8, 32).is_empty())
		sessions.append(session)
	# Receive ahead of simulation, as a clock-limited guest does.
	for block in range(0, 120, 8):
		for frame in range(block + 1, block + 9):
			for session in sessions:
				for slot in ["p1", "p2"]:
					assert(session.receive("batch", slot, frame, _buttons(frame % 3 == 0)).is_empty())
		for frame in range(block + 1, block + 9):
			for session in sessions: assert(session.step().is_empty())
			assert(State.first_difference(sessions[0]._adapter.save_state(), sessions[1]._adapter.save_state()).is_empty())
			if frame in [17, 30, 59, 60, 90, 120]: assert(not sessions[1].state_at(frame).is_empty())
			if frame == 59:
				assert(sessions[1].latest_hash_frame() == 30)
				assert(sessions[1].hash_floor() <= 30)
			if frame == 60:
				assert(sessions[1].latest_hash_frame() == 60)
				assert(not sessions[1].state_at(30).is_empty())
			assert(sessions[0].input_floor == sessions[1].input_floor)
			assert(not sessions[1].can_receive_frame(sessions[1].input_floor))
	assert(sessions[1].profile.save_count < sessions[0].profile.save_count / 3)
	# A burst correcting predicted history must erase skipped, stale snapshots.
	for frame in range(121, 127):
		for session in sessions:
			assert(session.receive("batch", "p1", frame, _buttons()).is_empty())
			assert(session.step().is_empty())
	for frame in range(126, 120, -1):
		for session in sessions: assert(session.receive("batch", "p2", frame, _buttons(frame % 2 == 0), true).is_empty())
	for session in sessions: assert(session.reconcile().is_empty())
	assert(State.first_difference(sessions[0].state_at(126), sessions[1].state_at(126)).is_empty())
	for frame in range(122, 126): assert(sessions[1].state_at(frame).is_empty())
	assert(sessions[1].profile.saves_skipped_count > 0)
	print("ROLLBACK_SPARSE_SMOKE_OK frames=126 exact_state=true baseline_saves=%d sparse_saves=%d stale_snapshots_removed=true" % [sessions[0].profile.save_count, sessions[1].profile.save_count])
	for session in sessions: _dispose(session)
	quit()
