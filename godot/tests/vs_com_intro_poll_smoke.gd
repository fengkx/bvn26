extends SceneTree


func _initialize() -> void:
	_run.call_deferred()


func _run() -> void:
	var game = load("res://main.tscn").instantiate()
	root.add_child(game)
	game.set_physics_process(false)
	game._enter_current_fight(2)
	game.ichigo.ai_random_clock.cancel()
	var intro: BattleIntro = game.battle_intro
	var fighters: Array[FighterRuntime] = [game.naruto, game.ichigo]
	for entry_frame in [6, 8]:
		intro.begin(fighters, true)
		intro.step = 2
		intro.states = [2, 0]
		game.opponent_driver.controller.goto_label("站立", true)
		game.opponent_driver.run_target_frames()
		for tick in entry_frame - 2:
			game._advance_fight()
		assert(game.ichigo.current_source_frame() == entry_frame - 1)
		game._advance_fight([{"phase": "after_actor_advance", "sequence": 100, "time_ms": 500}])
		assert(intro.step == 3)
		if entry_frame == 8:
			assert(game.ichigo.current_source_frame() == 1)
			game._advance_fight([{"phase": "after_actor_advance", "sequence": 200, "time_ms": 1000}])
		assert(game.ichigo.current_source_frame() == 822)
		game._advance_fight()
		assert(game.ichigo.current_source_frame() == 823)
		assert(intro.states[1] == 1)
	game._goto_menu()
	game.queue_free()
	await process_frame
	print("VS_COM_INTRO_POLL_SMOKE_OK")
	quit()
