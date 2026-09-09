extends SceneTree


func _initialize() -> void:
	_run.call_deferred()


func _run() -> void:
	var game = load("res://main.tscn").instantiate()
	root.add_child(game)
	game.set_physics_process(false)
	var count := 0
	for mode in [2, 3, 4]:
		game._enter_current_fight(mode)
		var branch: Dictionary = game.naruto.ai_source_state.spec.frame_calls["538"][0]
		for hp in [-1, 0, 1]:
			for action in [-1, 0]:
				game.naruto.goto_ai_label("必杀", true)
				game.naruto.play_source_frame(538)
				game.ichigo.health = hp
				game.ichigo.ai_source_state.values["动作"] = action
				game.player_body_driver._driver._frame_service(branch)
				var expected := 543 if hp > 0 and action == -1 else 538
				assert(game.naruto.current_source_frame() == expected)
				count += 1
	game._goto_menu()
	game.queue_free()
	await process_frame
	print("CONDITIONAL_FRAME_BOUNDARY_SMOKE_OK ", count)
	quit()
