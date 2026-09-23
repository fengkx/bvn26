extends SceneTree
const Battle = preload("res://rollback_battle.gd")
const Inputs = preload("res://rollback_test_session.gd")
const State = preload("res://simulation_state.gd")

func _initialize() -> void:
	_run.call_deferred()

func _run() -> void:
	var players := {"p1": {}, "p2": {}}
	for slot in players:
		for button in Inputs.BUTTONS: players[slot][button] = false
	for terminal in [false, true]:
		var fixture := preload("res://tests/rollback_fixture.gd").create(self)
		var game: Node = fixture.game
		var battle: RefCounted = fixture.battle
		var states := {}
		var nextfight_due := -1
		var timer_sequence := 0
		var delivered := false
		var last := 0
		for frame in range(1, 601):
			if frame == 170:
				# Fixture enters the source KO path; it does not redefine damage.
				if terminal: game.ko_state["_root.p2ws"] = 2
				game.naruto.health = 0
				assert(game.naruto._check_dead(false))
			var skip := frame >= 30 and frame < 90
			var events := []
			if game.battle_intro.polling and frame % 15 == 0 and not (skip and game.battle_intro.step > 1 and game.battle_intro.step < 4):
				events.append({"kind": "intro_poll", "phase": "after_actor_advance", "sequence": frame, "time_ms": frame * 33})
			if game.ko_nextfight_timer != null and timer_sequence != game.ko_interval_sequence:
				timer_sequence = game.ko_interval_sequence
				nextfight_due = frame + int(ceil(game.ko_nextfight_timer.wait_time * 30))
			if frame == nextfight_due:
				events.append({"kind": "nextfight", "phase": "before_root_observer"})
				delivered = true
			assert(battle.set_frame_events(frame, frame * 33, skip, events).is_empty())
			var problem: String = battle.advance(frame, players)
			assert(problem.is_empty(), problem)
			last = frame
			if frame >= 170 and (frame % 20 == 10 or game.ko_terminal_pending or frame == 600):
				states[frame] = battle.save_state()
				assert(not states[frame].has("error"), str(states[frame]))
			if game.ko_terminal_pending: break
			if frame % 60 == 0: await process_frame
		assert(delivered or terminal)
		assert(game.ko_terminal_pending == terminal)
		if terminal:
			assert(battle.advance(last + 1, players) == "waiting_for_confirmation")
			battle.confirm_through(last)
			assert(battle.advance(last + 1, players) == "match_finished")
			assert(game.session.root_label == "游戏场景")
		var boundaries := states.keys()
		for index in range(boundaries.size() - 1):
			var first: int = boundaries[index]
			var end: int = boundaries[index + 1]
			var problem: String = battle.load_state(states[first])
			assert(problem.is_empty(), problem)
			for frame in range(first + 1, end + 1):
				problem = battle.advance(frame, players)
				assert(problem.is_empty(), problem)
			var restored: Dictionary = battle.save_state()
			var difference := State.first_difference(states[end], restored)
			if not difference.is_empty():
				FileAccess.open("/tmp/round-expected.json", FileAccess.WRITE).store_string(JSON.stringify(bytes_to_var(states[end].owners.battle.owners.graph.hex_decode()), "  "))
				FileAccess.open("/tmp/round-actual.json", FileAccess.WRITE).store_string(JSON.stringify(bytes_to_var(restored.owners.battle.owners.graph.hex_decode()), "  "))
			assert(difference.is_empty(), "%d..%d %s" % [first, end, difference])
		print("ROLLBACK_ROUND_CASE_OK terminal=%s checkpoints=%d frames=%d" % [terminal, states.size(), last])
		preload("res://tests/rollback_fixture.gd").dispose(game, battle)
		await process_frame
	await create_timer(0.1).timeout
	print("ROLLBACK_ROUND_SMOKE_OK")
	quit()
