extends SceneTree

const Step := preload("res://manual_match_step.gd")
const Inputs := preload("res://rollback_test_session.gd")
const State := preload("res://simulation_state.gd")


func _initialize() -> void:
	_run.call_deferred()


func _players(frame: int) -> Dictionary:
	var players := {"p1": {}, "p2": {}}
	for slot in players:
		for button in Inputs.BUTTONS:
			players[slot][button] = false
	if frame >= 165 and frame < 190:
		players.p1.right = true
		players.p2.left = true
	if frame >= 195 and frame < 200:
		players.p1.attack = true
		players.p2.attack = true
	if frame >= 205 and frame < 207:
		players.p1.jump = true
	return players


func _sample(game: Node) -> Dictionary:
	var fighters := []
	for fighter in [game.naruto, game.ichigo]:
		fighters.append([fighter.current_source_frame(), fighter.action, fighter.source_x,
			fighter.source_y, fighter.health, fighter.energy, fighter.hits, fighter.root_zhanting])
	return {"tick": game.physics_tick, "fighters": fighters,
		"intro": [game.battle_intro.step, game.battle_intro.active],
		"random": game.source_random.save_state(), "clock": game.source_clock.save_state()}


func _run() -> void:
	var reference := []
	for iteration in 2:
		var saw_damage := false
		var game = load("res://main.tscn").instantiate()
		root.add_child(game)
		game.set_physics_process(false)
		game.set_process(false)
		game.ko_recorded_timers = true
		game.recorded_training_timers = true
		game.source_random.use_seed(727)
		game.source_clock.use_explicit_time(0)
		game._enter_current_fight(3)
		game.battle_intro.recorded_polling = true
		# The hidden title's navigation repeat timer is outside this battle fixture.
		for timer in game.title_menu.find_children("*", "Timer", true, false):
			timer.stop()
		var driver := Step.new()
		if iteration == 0:
			var configuration_error := driver.configure(game)
			assert(configuration_error.is_empty(), configuration_error)
			assert(not driver.advance(2, _players(1), false).is_empty())
			assert(game.physics_tick == 0)
			var invalid := _players(1)
			invalid.p1.erase("attack")
			assert(not driver.advance(1, invalid, false).is_empty())
			assert(game.physics_tick == 0)
		for frame in range(1, 331):
			assert(game.source_clock.set_explicit_time(frame * 33))
			var skip := frame >= 30 and frame < 90
			var cancels_poll: bool = skip and game.battle_intro.step > 1 and game.battle_intro.step < 4
			var callbacks := []
			# Synthetic external delivery schedule, NOT a Flash timing assertion.
			if game.battle_intro.polling and frame % 15 == 0 and not cancels_poll:
				callbacks.append({"kind": "intro_poll", "phase": "after_actor_advance",
					"sequence": frame, "time_ms": frame * 33})
			if iteration == 0:
				var problem := driver.advance(frame, _players(frame), skip, callbacks)
				assert(problem.is_empty(), problem)
				reference.append(_sample(game))
			else:
				var players := _players(frame)
				game.match_input.source = func(slot: String, _tick: int) -> Dictionary: return players[slot]
				game.match_input.intro_source = func(_tick: int) -> bool: return skip
				game.pause_menu.tick()
				game._advance_fight(callbacks)
				assert(State.first_difference(_sample(game), reference[frame - 1]).is_empty(), "Manual step differs at %d" % frame)
			saw_damage = saw_damage or game.naruto.health < game.session.maxhp or game.ichigo.health < game.session.maxhp
		assert(not game.battle_intro.active)
		assert(saw_damage, "The real battle fixture must exercise a received hit")
		driver.detach()
		game._goto_menu()
		game.free()
		await process_frame
	print("MANUAL_MATCH_STEP_SMOKE_OK frames=330 runs=2 comparison=selected_fields_not_complete_state")
	quit()
