extends "res://tests/rollback_delayed_input_profile.gd"


func _run() -> void:
	var sparse := OS.get_cmdline_user_args().has("--sparse")
	var fixtures: Array[Dictionary] = []
	var sessions: Array = []
	for _index in range(2):
		# Match independent process roots: each Main is its parent's first child.
		var container := Node.new()
		root.add_child(container)
		var field_roster := OS.get_cmdline_user_args().has("--field-roster")
		var fixture := Fixture.create(self, ["白哉", "小李"], ["松本", "我爱罗"], "温泉", container) if field_roster else Fixture.create(self, [], [], "", container)
		fixture.battle.checkpoint.defer_replay_display = _index == 1
		fixture["container"] = container
		fixtures.append(fixture)
		var session := Session.new()
		session.sparse_saves = sparse and _index == 1
		session.checkpoint_stride = 2 if OS.get_cmdline_user_args().has("--stride-two") and _index == 1 else 1
		session.retain_hash_history = sparse
		var problem: String = session.configure(fixture.battle, "batch-battle", 8, 12)
		assert(problem.is_empty(), problem)
		sessions.append(session)
	var delivered := 0
	var wall_tick := 0
	var graphs_compared := 0
	while sessions[0].frontier < MEASURED_FRAMES or sessions[0].confirmed < MEASURED_FRAMES:
		wall_tick += 1
		assert(wall_tick < 400)
		if sessions[0].frontier < MEASURED_FRAMES:
			var next: int = sessions[0].frontier + 1
			for index in range(2):
				var fixture: Dictionary = fixtures[index]
				var envelope := _frame_events(fixture.game, next)
				assert(fixture.battle.set_frame_events(next, envelope[0], envelope[1], envelope[2]).is_empty())
				assert(sessions[index].receive("batch-battle", "p1", next, _players(next).p1).is_empty())
		if wall_tick % 3 == 0 and not (wall_tick >= 165 and wall_tick < 180):
			var through: int = MEASURED_FRAMES if sessions[0].frontier == MEASURED_FRAMES else maxi(0, sessions[0].frontier - 5)
			var corrections_before: int = sessions[1].rollback_count
			for frame in range(through, delivered, -1):
				for index in range(2):
					assert(sessions[index].receive("batch-battle", "p2", frame, _players(frame).p2, (sparse or index == 1)).is_empty())
			assert(sessions[0].reconcile().is_empty())
			assert(sessions[1].reconcile().is_empty())
			assert(sessions[1].rollback_count - corrections_before <= 1)
			delivered = maxi(delivered, through)
			if not sparse: assert(sessions[0]._states.keys() == sessions[1]._states.keys())
			for frame in sessions[1]._states:
				var difference := State.first_difference(sessions[0].state_at(frame), sessions[1].state_at(frame))
				if not difference.is_empty():
					var left: Array = bytes_to_var(sessions[0].state_at(frame).owners.battle.owners.graph)
					var right: Array = bytes_to_var(sessions[1].state_at(frame).owners.battle.owners.graph)
					push_error("Batch %d frame %d: %s" % [wall_tick, frame, State.first_difference(left, right)])
					quit(1)
					return
				graphs_compared += 1
		if sessions[0].frontier < MEASURED_FRAMES:
			var first: String = sessions[0].step()
			var second: String = sessions[1].step()
			assert(first == second and first in ["", "waiting_for_input"])
		assert(sessions[0].frontier == sessions[1].frontier)
		if wall_tick % 30 == 0:
			await process_frame
	print("ROLLBACK_BATCHED_BATTLE_SMOKE_OK frames=%d retained_graphs=%d immediate_corrections=%d batch_corrections=%d immediate_replayed=%d batch_replayed=%d" % [
		MEASURED_FRAMES, graphs_compared, sessions[0].rollback_count, sessions[1].rollback_count,
		sessions[0].replayed_frames, sessions[1].replayed_frames])
	for fixture in fixtures:
		Fixture.dispose(fixture.game, fixture.battle)
		fixture.container.free()
	await process_frame
	quit()
