extends SceneTree

func _initialize() -> void:
	_run.call_deferred()

func _run() -> void:
	var game = load("res://main.tscn").instantiate()
	root.add_child(game)
	game.set_physics_process(false)
	for mode in [2, 3, 4, 3, 2, 4]:
		game.recorded_training_timers = true
		game._enter_current_fight(mode)
		assert(game.opponent_driver != null and game.player_body_driver != null)
		assert(game.naruto.source_body != null and game.ichigo.source_body != null)
		assert(game.opponent_driver.controller.context.use_ai == (mode == 2))
		assert(game.opponent_driver.body_context.use_ai == (mode == 2))
		assert((game.training_timer != null) == (mode == 4))
		if mode != 2:
			assert(game.ichigo.ai_random_clock.registered_ms == -1)
		for tick in 700:
			game._advance_fight()
			if not game.battle_intro.active: break
		assert(not game.battle_intro.active)
		if mode != 2:
			var key := InputEventKey.new()
			key.keycode = KEY_LEFT
			key.physical_keycode = KEY_LEFT
			key.pressed = true
			Input.parse_input_event(key)
			Input.flush_buffered_events()
			var before: float = game.ichigo.position.x
			game._advance_fight()
			assert(game.ichigo.position.x < before)
			key = key.duplicate()
			key.pressed = false
			Input.parse_input_event(key)
			Input.flush_buffered_events()
		if mode == 4:
			game.naruto.health = 0
			assert(not game.naruto._check_dead(false) and not game.naruto.sw and not game.ko_active)
			game.naruto.energy = 17
			game.naruto.beida = 1
			game._recover_training()
			assert(game.naruto.health == 0 and game.naruto.energy == 17)
			game.naruto.beida = 0
			game.naruto.root_zhanting = true
			game._recover_training()
			assert(game.naruto.health == game.session.maxhp and game.naruto.energy == 300)
		game._goto_menu()
		assert(game.opponent_driver == null and game.player_body_driver == null)
		assert(game.training_timer == null and game.source_callbacks == null)
		assert(game.ichigo.ai_random_clock.registered_ms == -1)
	game.recorded_training_timers = false
	game._enter_current_fight(4)
	assert(not game.training_timer.is_stopped() and game.training_timer.wait_time == 1.0)
	game.naruto.beida = 0
	game.naruto.health = 500
	game.naruto.energy = 0
	game.naruto.root_zhanting = true
	await create_timer(1.1).timeout
	assert(game.naruto.health == game.session.maxhp and game.naruto.energy == 300)
	var recovery: WeakRef = weakref(game.training_timer)
	game._goto_menu()
	await process_frame
	assert(recovery.get_ref() == null)
	game.queue_free()
	await process_frame
	print("SHARED_MODE_LIFECYCLE_SMOKE_OK")
	quit()
