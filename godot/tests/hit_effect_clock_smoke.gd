extends SceneTree


func _initialize() -> void:
	_run.call_deferred()


func _run() -> void:
	var game = load("res://main.tscn").instantiate()
	root.add_child(game)
	game.set_physics_process(false)
	game._enter_current_fight(2)
	game.ichigo.ai_random_clock.cancel()
	game._spawn_hit_effect("XG_qdjx", Vector2.ZERO, 1)
	var effect: HitEffectRuntime
	for child in game.game_world.get_children():
		if child is HitEffectRuntime:
			effect = child
	assert(effect != null and effect.effect_frame == 1)
	effect._physics_process(1.0 / 30.0)
	assert(effect.effect_frame == 1)
	game._advance_fight()
	assert(effect.effect_frame == 2 and effect.game_paused)
	assert(game.hit_fx_pause_count == 1)
	for tick in 13:
		game._advance_fight()
	assert(effect.effect_frame == 15 and not effect.game_paused)
	assert(game.hit_fx_pause_count == 0)
	game._goto_menu()
	game.queue_free()
	await process_frame
	print("HIT_EFFECT_CLOCK_SMOKE_OK")
	quit()
