extends SceneTree


func _initialize() -> void:
	_run.call_deferred()


func _run() -> void:
	var game = load("res://main.tscn").instantiate()
	root.add_child(game)
	game.set_physics_process(false)
	game._enter_current_fight(2)
	game.ichigo.position = Vector2(300, -10)
	game.ichigo.set_facing(-1)
	# Ichigo doHurtSkill calls bsd(pn,"XG_bsq",false).
	game.cpu_services.invoke("bsd", ["XG_bsq", false])
	var effect: HitEffectRuntime = null
	for child in game.game_world.get_children():
		if child is HitEffectRuntime and child._directory.ends_with("/XG_bsq"):
			effect = child
	assert(effect != null)
	effect.auto_advance = false
	assert(effect.position == Vector2(300, -35))
	assert(effect.scale.x == -1)
	assert(effect.effect_frame == 1)
	assert(effect._preview._frames.size() == 17)
	assert(effect._preview.get_child_count() > 0)
	for frame in range(2, 17):
		effect.advance_effect()
		assert(effect.effect_frame == frame and not effect.is_queued_for_deletion())
	effect.advance_effect()
	assert(effect.effect_frame == 17)
	assert(effect.last_ops == ["unload"])
	assert(effect.is_queued_for_deletion())
	game._goto_menu()
	game.queue_free()
	await process_frame
	print("AI_ESCAPE_EFFECT_SMOKE_OK")
	quit()
