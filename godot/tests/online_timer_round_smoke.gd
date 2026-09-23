extends SceneTree

const State = preload("res://simulation_state.gd")
const Battle = preload("res://rollback_battle.gd")
const TimerAuthority = preload("res://online_timer_authority.gd")


class OnlineRoundAdapter extends RefCounted:
	var game: Node
	var battle: RefCounted
	var timers: RefCounted
	var ko_triggered := false
	var error := ""

	func configure(tree: SceneTree) -> String:
		game = load("res://main.tscn").instantiate()
		tree.root.add_child(game)
		game.set_physics_process(false)
		game.set_process(false)
		game.ko_recorded_timers = true
		game.recorded_training_timers = true
		game.source_random.use_seed(727)
		if not game.source_clock.use_explicit_time(0): return "Could not set initial explicit clock"
		var roster_error: String = game.configure_diagnostic_roster({
			"p1": {"resourcePath": "res://generated/fighters/minren", "helper": {"resourcePath": "res://generated/helpers/woailuo"}},
			"p2": {"resourcePath": "res://generated/fighters/yihu", "helper": {"resourcePath": "res://generated/helpers/kon"}},
		})
		if not roster_error.is_empty(): return roster_error
		game._load_selected_stage("现世")
		game._enter_current_fight(3)
		game.battle_intro.recorded_polling = true
		for driver in [game.player_body_driver._driver, game.opponent_driver]:
			driver.timeouts.recorded = true
		timers = TimerAuthority.new()
		var problem: String = timers.configure(game, 0)
		if not problem.is_empty(): return problem
		battle = Battle.new()
		problem = battle.configure(game)
		if not problem.is_empty(): return problem
		return battle.set_event_supplier(Callable(timers, "events_for_phase"))

	func advance(frame: int, players: Dictionary) -> String:
		var elapsed_ms := (frame - 1) * 33
		var problem: String = timers.set_time(elapsed_ms)
		if not problem.is_empty(): return problem
		problem = battle.set_frame_clock(frame, elapsed_ms)
		if not problem.is_empty(): return problem
		if frame == 170 and not ko_triggered:
			# Follow the rollback round fixture's real source KO trigger.
			game.naruto.health = 0
			game.naruto._check_dead(false)
			ko_triggered = true
		problem = battle.advance(frame, players)
		timers.finish_frame()
		if not timers.error.is_empty(): return timers.error
		return problem

	func save_state() -> Dictionary:
		var battle_state: Dictionary = battle.save_state()
		if battle_state.has("error"): return battle_state
		return State.pack_state("online-round-timer-v1", battle_state.frame, {
			"battle": battle_state,
			"timers": timers.save_state(battle_state.frame),
		})

	func validate_state(snapshot: Dictionary) -> String:
		var problem := State.validate_snapshot(snapshot, "online-round-timer-v1", ["battle", "timers"])
		if not problem.is_empty(): return problem
		problem = battle.validate_state(snapshot.owners.battle)
		if not problem.is_empty(): return problem
		if snapshot.frame != snapshot.owners.battle.frame: return "Round/timer checkpoint frame mismatch"
		return timers.validate_state(snapshot.owners.timers, snapshot.frame)

	func load_state(snapshot: Dictionary) -> String:
		var problem := validate_state(snapshot)
		if not problem.is_empty(): return problem
		problem = battle.load_state(snapshot.owners.battle)
		if not problem.is_empty(): return problem
		return timers.load_state(snapshot.owners.timers)

	func dispose() -> void:
		if battle != null: battle.close()
		if game != null:
			game._goto_menu()
			game.free()
		game = null


func _initialize() -> void:
	_run.call_deferred()


func _run() -> void:
	var adapter := OnlineRoundAdapter.new()
	var problem: String = adapter.configure(self)
	assert(problem.is_empty(), problem)
	var initial_rounds := int(adapter.game.ko_state.get("_root.rounds", 0))
	var source_countdown: Node = adapter.game.countdown
	var neutral := {}
	for button in preload("res://keyboard_input_source.gd").BUTTONS:
		neutral[button] = false
	var players := {"p1": neutral.duplicate(), "p2": neutral.duplicate()}
	var before_round: Dictionary = {}
	var after_round: Dictionary = {}
	var round_change_frame := -1
	var first_nextfight_sequence := -1
	for frame in range(1, 520):
		problem = adapter.advance(frame, players)
		assert(problem.is_empty(), "frame %d: %s" % [frame, problem])
		if before_round.is_empty() and adapter.game.ko_nextfight_timer != null and adapter.timers.nextfight_due_ms >= 0:
			before_round = adapter.save_state()
			first_nextfight_sequence = adapter.timers.nextfight_sequence
			assert(adapter.game.countdown != null and adapter.game.countdown.recorded_active)
		if round_change_frame < 0 and int(adapter.game.ko_state.get("_root.rounds", initial_rounds)) > initial_rounds:
			round_change_frame = frame
		if round_change_frame >= 0 and frame >= round_change_frame + 6:
			after_round = adapter.save_state()
			break
		if frame % 60 == 0: await process_frame
	assert(not before_round.is_empty(), "Source KO did not register the actual nextfight interval")
	assert(not after_round.is_empty(), "Recorded nextfight did not advance the source round")
	assert(round_change_frame > before_round.frame, "Round transition did not cross the retained interval deadline")
	assert(adapter.game.ko_interval_sequence == first_nextfight_sequence)
	assert(adapter.game.countdown.recorded_active and adapter.game.countdown == source_countdown,
		"Source nextfight should keep the match countdown registration active")
	assert(adapter.timers.nextfight_sequence == first_nextfight_sequence)
	var restored_problem: String = adapter.load_state(before_round)
	assert(restored_problem.is_empty(), restored_problem)
	for frame in range(int(before_round.frame) + 1, int(after_round.frame) + 1):
		problem = adapter.advance(frame, players)
		assert(problem.is_empty(), "replay frame %d: %s" % [frame, problem])
	var replayed: Dictionary = adapter.save_state()
	var difference := State.first_difference(after_round, replayed)
	assert(difference.is_empty(), "Source round timer replay diverged at %s" % difference)
	assert(adapter.game.countdown == source_countdown and adapter.game.countdown.recorded_active,
		"Restoring the cross-round checkpoint replaced the persistent countdown registration")
	print("ONLINE_TIMER_ROUND_SMOKE_OK ko_to_nextfight=true persistent_countdown=true round=%d replayed=%d_frames" % [int(adapter.game.ko_state["_root.rounds"]), int(after_round.frame - before_round.frame)])
	adapter.dispose()
	await process_frame
	quit()
