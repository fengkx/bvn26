extends "res://tests/rollback_batched_correction_smoke.gd"


func _run() -> void:
	for delivery in [[1, 2, 3, 4, 5, 6, 7], [7, 6, 5, 4, 3, 2, 1], [3, 1, 7, 2, 6, 4, 5]]:
		var reference := _make()
		var sparse := _make()
		sparse.sparse_saves = true
		sparse.checkpoint_stride = 2
		for frame in range(1, 8):
			for session in [reference, sparse]:
				assert(session.receive("batch", "p1", frame, _buttons()).is_empty())
				assert(session.step().is_empty())
		assert(sparse.state_at(7).is_empty())
		for frame in delivery:
			for session in [reference, sparse]:
				assert(session.receive("batch", "p2", frame, _buttons(frame % 2 == 0)).is_empty())
			# Live synthetic values have no encoder cache side effects.
			assert(reference._adapter.score == sparse._adapter.score)
			assert(reference.frontier == sparse.frontier)
		for frame in sparse._states:
			assert(State.first_difference(reference.state_at(frame), sparse.state_at(frame)).is_empty())
		assert(sparse.replayed_frames >= reference.replayed_frames)
		_dispose(reference)
		_dispose(sparse)
	var invalid := Session.new()
	invalid.checkpoint_stride = 3
	assert(not invalid.configure(Adapter.new(), "invalid", 8, 16).is_empty())
	print("ROLLBACK_CHECKPOINT_STRIDE_SMOKE_OK orders=3 odd_frontier=true full_state_equal=true")
	quit()
