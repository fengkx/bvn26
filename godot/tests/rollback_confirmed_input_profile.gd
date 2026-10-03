extends "res://tests/rollback_delayed_input_profile.gd"


func _run() -> void:
	var sparse := OS.get_cmdline_user_args().has("--sparse")
	var fixture := Fixture.create(self)
	var battle: RefCounted = fixture.battle
	var initial: Dictionary = battle.save_state()
	for frame in range(1, MEASURED_FRAMES + 1):
		var events := _frame_events(fixture.game, frame)
		assert(battle.set_frame_events(frame, events[0], events[1], events[2]).is_empty())
		assert(battle.advance(frame, _players(frame)).is_empty())
	var reference: Dictionary = battle.save_state()
	assert(battle.load_state(initial).is_empty())
	var session := Session.new()
	session.sparse_saves = sparse
	assert(session.configure(battle, "confirmed", 8, 32).is_empty())
	var samples: Array[int] = []
	for block in range(0, MEASURED_FRAMES, 8):
		var end := mini(block + 8, MEASURED_FRAMES)
		for frame in range(block + 1, end + 1):
			for slot in ["p1", "p2"]:
				assert(session.receive("confirmed", slot, frame, _players(frame)[slot]).is_empty())
		for frame in range(block + 1, end + 1):
			var events := _frame_events(fixture.game, frame)
			assert(battle.set_frame_events(frame, events[0], events[1], events[2]).is_empty())
			var started := Time.get_ticks_usec()
			assert(session.step().is_empty())
			samples.append(Time.get_ticks_usec() - started)
		if block % 40 == 0: await process_frame
	# Do not inspect the live graph on skipped frames: that would populate the
	# serializer caches and hide a dependency on an omitted checkpoint save.
	var final: Dictionary = session.state_at(MEASURED_FRAMES)
	assert(State.first_difference(reference, final).is_empty())
	print("ROLLBACK_CONFIRMED_INPUT_PROFILE_OK ", JSON.stringify({"frames": MEASURED_FRAMES,
		"sparse": sparse, "step_us": _stats(samples), "profile": session.profile_counters(),
		"full_state_equal": true, "semantic_sha256": _semantic_hash(_semantic_snapshot(final))}))
	Fixture.dispose(fixture.game, battle)
	await process_frame
	quit()
