extends SceneTree


func _initialize() -> void:
	_run.call_deferred()


func _run() -> void:
	var game = load("res://main.tscn").instantiate()
	root.add_child(game)
	game.set_physics_process(false)
	game._enter_current_fight(2)
	game.ichigo.ai_random_clock.cancel()
	for tick in 600:
		game._advance_fight()
		if not game.battle_intro.active:
			break
	assert(not game.battle_intro.active)
	var cpu: FighterRuntime = game.ichigo
	cpu.play_source_frame(740)
	cpu.timeline_playing = false
	game.opponent_driver.begin_display_tick(game.physics_tick)
	cpu.ai_color_state.receive(cpu.ai_color_operations["7"])
	cpu.ai_source_state.values["htx"] = 10
	cpu.ai_source_state.values["time"] = 2
	cpu.hited = 1
	game.naruto.hited = 0
	game.naruto.bs = 0
	game.naruto.sw = false
	game.naruto.timeline_playing = true
	var position_before := cpu.position
	game._on_hit_fx_pause()
	assert(cpu.root_zhanting and game.naruto.root_zhanting)
	assert(not game.naruto.timeline_playing)
	game._advance_fight()
	assert(cpu.current_source_frame() == 740)
	assert(cpu.ai_color_state.index == 1)
	assert(cpu.position == position_before)
	assert(cpu.ai_source_state.read_field("time") == 2)
	game._advance_fight()
	assert(cpu.ai_color_state.index == 0)
	# pauseGame does not register nested pauses; one resume clears it.
	game._on_hit_fx_pause()
	game._on_hit_fx_resume()
	assert(not cpu.root_zhanting and game.naruto.timeline_playing)
	assert(not cpu.timeline_playing)
	game._goto_menu()
	game.queue_free()
	await process_frame
	print("AI_HIT_PAUSE_SMOKE_OK")
	quit()
