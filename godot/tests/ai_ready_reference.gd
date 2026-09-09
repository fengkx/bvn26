extends SceneTree


func _initialize() -> void:
	_run.call_deferred()


func state(game) -> Array:
	var result: Array = []
	for f in [game.naruto, game.ichigo]:
		result.append({"slot": f.player_slot, "frame": f.current_source_frame(), "x": f.position.x, "y": f.position.y, "hp": f.health, "ql": f.energy, "source_action": f.ai_source_state.read_field("动作"), "paused": f.root_zhanting})
	return result


func _run() -> void:
	var game = load("res://main.tscn").instantiate()
	root.add_child(game)
	game.set_physics_process(false)
	game._on_menu_confirmed("vs_com")
	game._on_map_confirmed("现世")
	# This probes the Ready boundary, not full random/timer replay. The retained
	# original has no predicate calls before Ready. Do not synthesize a tape.
	game.ichigo.ai_random_clock.cancel()
	var capture := {}
	game.battle_intro.fight_started.connect(func(): capture["signal"] = state(game))
	for tick in 600:
		var before := state(game)
		game._advance_fight()
		if not game.battle_intro.active:
			capture["before_tick"] = before
			capture["after_tick"] = state(game)
			capture["native_tick"] = tick
			break
	assert(capture.has("after_tick"), "Ready boundary was not reached")
	print("AI_READY_CAPTURE ", JSON.stringify(capture))
	game._goto_menu()
	game.queue_free()
	await process_frame
	quit()
