extends SceneTree


func _initialize() -> void:
	_run.call_deferred()


func _run() -> void:
	var game = load("res://main.tscn").instantiate()
	root.add_child(game)
	game.set_physics_process(false)
	game._on_menu_confirmed("vs_com")
	game._on_characters_confirmed(["日番谷", "恋次"], ["鼬", "我爱罗"])
	game._on_map_confirmed("现世")
	for tick in 700:
		game._advance_fight()
		if not game.battle_intro.active:
			break
	assert(not game.battle_intro.active and game.session.p2cpu)
	var helper = game.ichigo_helper
	for attempt in 3:
		# Controlled overlap trigger; retain the CPU driver and all actor instances.
		# Positions/energy are setup, not expected source outputs.
		game.naruto.goto_ai_label("站立", true)
		game.ichigo.goto_ai_label("站立", true)
		game.naruto.position.x = 300 if attempt % 2 == 0 else 650
		game.ichigo.position.x = 650 if attempt % 2 == 0 else 300
		game.naruto.energy = 300
		game.ichigo.energy = 300
		var entered_super := false
		var helper_released := false
		var recovered := false
		for tick in 300:
			if tick == 15:
				game.ichigo.goto_ai_label("招换", true)
			for key in [KEY_W, KEY_I]:
				var event := InputEventKey.new()
				event.keycode = key
				event.physical_keycode = key
				event.pressed = tick >= 20 and tick < 23
				Input.parse_input_event(event)
			Input.flush_buffered_events()
			game._advance_fight()
			entered_super = entered_super or game.naruto.current_source_frame() == 570
			helper_released = helper_released or helper.current_source_frame() == 38
			recovered = recovered or (entered_super and helper_released and not game.naruto.root_zhanting)
		assert(entered_super and helper_released and recovered, "CPU/helper overlap did not recover")
		assert(game.ichigo_helper == helper and game.session.p2cpu)
	game._goto_menu()
	game.queue_free()
	await process_frame
	print("VS_COM_HELPER_OVERLAP_OK")
	quit()
