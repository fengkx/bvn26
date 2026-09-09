extends SceneTree


func _initialize() -> void:
	_run.call_deferred()


func _run() -> void:
	var game = load("res://main.tscn").instantiate()
	root.add_child(game)
	game.set_physics_process(false)
	for cycle in 3:
		game._enter_current_fight(2)
		game.ichigo.ai_random_clock.cancel()
		var driver_ref: WeakRef = weakref(game.player_body_driver)
		var body_ref: WeakRef = weakref(game.player_body_driver.body)
		var context_ref: WeakRef = weakref(game.player_body_driver.context)
		assert(game.naruto.source_body != null)
		assert(game.naruto.source_frame_changed.get_connections().size() == 1)
		game._advance_fight()
		game._goto_menu()
		assert(game.player_body_driver == null and game.player_body_services == null)
		assert(game.naruto.source_body == null)
		assert(game.naruto.source_frame_changed.get_connections().is_empty())
		await process_frame
		assert(driver_ref.get_ref() == null)
		assert(body_ref.get_ref() == null and context_ref.get_ref() == null)
	game.queue_free()
	await process_frame
	print("PLAYER_BODY_LIFECYCLE_SMOKE_OK")
	quit()
