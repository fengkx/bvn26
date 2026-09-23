extends SceneTree

const State = preload("res://simulation_state.gd")
const TimerAuthority = preload("res://online_timer_authority.gd")


class TimeoutTarget extends RefCounted:
	func on_timeout() -> void:
		pass


func _initialize() -> void:
	_run.call_deferred()


func _run() -> void:
	var game: Node = load("res://main.tscn").instantiate()
	root.add_child(game)
	game.set_physics_process(false)
	game.ko_recorded_timers = true
	game.recorded_training_timers = true
	game.source_random.use_seed(727)
	assert(game.source_clock.use_explicit_time(0))
	var roster_error: String = game.configure_diagnostic_roster({
		"p1": {"resourcePath": "res://generated/fighters/minren", "helper": {"resourcePath": "res://generated/helpers/woailuo"}},
		"p2": {"resourcePath": "res://generated/fighters/yihu", "helper": {"resourcePath": "res://generated/helpers/kon"}},
	})
	assert(roster_error.is_empty(), roster_error)
	game._load_selected_stage("现世")
	game._enter_current_fight(3)
	game.battle_intro.recorded_polling = true
	for driver in [game.player_body_driver._driver, game.opponent_driver]:
		driver.timeouts.recorded = true

	var timers := TimerAuthority.new()
	assert(timers.configure(game, 0).is_empty())
	assert(timers.countdown_due_ms == 1000)
	assert(timers.intro_due_ms == 500)

	# Irregular monotonic samples define delivery; no frame-rate conversion is used.
	assert(_events(timers, 499).is_empty())
	var first_intro := _events(timers, 503).filter(func(item: Dictionary) -> bool: return item.kind == "intro_poll")
	assert(first_intro.size() == 1 and first_intro[0].sequence == 1 and first_intro[0].due_ms == 500)
	game.battle_intro.polling = false
	assert(_events(timers, 700).is_empty())
	assert(timers.intro_due_ms == -1)

	# A later round starts a new intro registration after source cancellation.
	game.battle_intro.active = true
	game.battle_intro.polling = true
	assert(_events(timers, 701).is_empty())
	assert(timers.intro_due_ms == 1201)
	var before_second_intro := _events(timers, 1200)
	assert(before_second_intro.filter(func(item: Dictionary) -> bool: return item.kind == "intro_poll").is_empty())
	var events_at_round_two := _events(timers, 1204)
	var second_intro := events_at_round_two.filter(func(item: Dictionary) -> bool: return item.kind == "intro_poll")
	assert(second_intro.size() == 1 and second_intro[0].sequence == 2 and second_intro[0].due_ms == 1201)

	var first_countdown := before_second_intro.filter(func(item: Dictionary) -> bool: return item.kind == "countdown")
	assert(first_countdown.size() == 1 and first_countdown[0].due_ms == 1000)
	assert(events_at_round_two.filter(func(item: Dictionary) -> bool: return item.kind == "countdown").is_empty())
	assert(timers.countdown_due_ms == 2200)
	game.countdown.stop()
	assert(_events(timers, 1500).filter(func(item: Dictionary) -> bool: return item.kind == "countdown").is_empty())
	assert(timers.countdown_due_ms == -1)
	# MatchCountdown.configure sets this flag for the next round registration.
	game.countdown.recorded_active = true
	assert(_events(timers, 1501).is_empty())
	assert(timers.countdown_due_ms == 2501)
	assert(_events(timers, 2500).filter(func(item: Dictionary) -> bool: return item.kind == "countdown").is_empty())
	var second_countdown := _events(timers, 2504).filter(func(item: Dictionary) -> bool: return item.kind == "countdown")
	assert(second_countdown.size() == 1 and second_countdown[0].due_ms == 2501)

	# A large tab-suspension jump emits one repeat and re-anchors at that sample.
	var resumed := _events(timers, 7000).filter(func(item: Dictionary) -> bool: return item.kind == "countdown")
	assert(resumed.size() == 1 and resumed[0].due_ms == 3504)
	assert(timers.countdown_due_ms == 8000)

	# New nextfight interval generations receive fresh deadlines without native ids.
	var first_round_timer := Timer.new()
	first_round_timer.wait_time = 1.0
	game.add_child(first_round_timer)
	game.ko_nextfight_timer = first_round_timer
	game.ko_interval_sequence += 1
	timers.finish_frame()
	assert(timers.nextfight_due_ms == 8000)
	assert(_events_phase(timers, 7999, "before_root_observer").is_empty())
	var first_nextfight := _events_phase(timers, 8000, "before_root_observer")
	assert(first_nextfight.size() == 1 and first_nextfight[0].kind == "nextfight")
	assert(timers.nextfight_due_ms == 9000)
	first_round_timer.stop()
	game.ko_nextfight_timer = null
	timers.finish_frame()
	assert(timers.nextfight_due_ms == -1)
	var second_round_timer := Timer.new()
	second_round_timer.wait_time = 1.0
	game.add_child(second_round_timer)
	game.ko_nextfight_timer = second_round_timer
	game.ko_interval_sequence += 1
	timers.finish_frame()
	assert(timers.nextfight_due_ms == 9000)
	assert(_events_phase(timers, 8999, "before_root_observer").is_empty())
	assert(_events_phase(timers, 9000, "before_root_observer").size() == 1)

	var p1_timeouts: AiSourceTimeouts = game.player_body_driver._driver.timeouts
	var p2_timeouts: AiSourceTimeouts = game.opponent_driver.timeouts
	var target := TimeoutTarget.new()
	var p1_id := p1_timeouts.schedule(Callable(target, "on_timeout"), 150)
	var p2_id := p2_timeouts.schedule(Callable(target, "on_timeout"), 150)
	assert(_events(timers, 9000).filter(func(item: Dictionary) -> bool: return item.kind == "body_timeout").is_empty())
	var body_events := _events(timers, 9150).filter(func(item: Dictionary) -> bool: return item.kind == "body_timeout")
	assert(body_events.size() == 2)
	assert(body_events[0].slot == "p1" and body_events[0].id == p1_id)
	assert(body_events[1].slot == "p2" and body_events[1].id == p2_id)
	assert(p1_timeouts.cancel(p1_id))
	var after_cancel := _events(timers, 9151).filter(func(item: Dictionary) -> bool: return item.kind == "body_timeout")
	assert(after_cancel.size() == 1 and after_cancel[0].slot == "p2" and after_cancel[0].id == p2_id)
	assert(p2_timeouts.cancel(p2_id))

	var checkpoint: Dictionary = timers.save_state(900)
	var expected := _events_phase(timers, 10_000, "before_root_observer", 901)
	assert(timers.load_state(checkpoint).is_empty())
	var set_time_error: String = timers.set_time(10_000)
	assert(set_time_error.is_empty(), set_time_error)
	var replayed := timers.events_for_phase("before_root_observer", 901)
	assert(State.canonical(replayed) == State.canonical(expected), "Timer event replay differs after restoring the later-round checkpoint: expected=%s actual=%s" % [JSON.stringify(expected), JSON.stringify(replayed)])

	timers = null
	game._goto_menu()
	game.free()
	await process_frame
	print("ONLINE_TIMER_AUTHORITY_SMOKE_OK irregular_samples=true second_round_rearmed=true late_resume_bounded=true restored=true")
	quit()


func _events(timers: RefCounted, time_ms: int) -> Array:
	var problem: String = timers.set_time(time_ms)
	assert(problem.is_empty(), problem)
	return timers.events_for_phase("after_actor_advance", 1)


func _events_phase(timers: RefCounted, time_ms: int, phase: String, frame: int = 1) -> Array:
	var problem: String = timers.set_time(time_ms)
	assert(problem.is_empty(), problem)
	return timers.events_for_phase(phase, frame)
