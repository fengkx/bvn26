extends SceneTree

func _initialize() -> void:
	_run.call_deferred()

func key(code: Key, pressed: bool) -> void:
	var event := InputEventKey.new()
	event.keycode = code
	event.physical_keycode = code
	event.pressed = pressed
	Input.parse_input_event(event)
	Input.flush_buffered_events()

func _run() -> void:
	var game = load("res://main.tscn").instantiate()
	root.add_child(game)
	game.set_physics_process(false)
	game.session.bind_slot("s", 81)
	game.session.bind_slot("j", 69)
	for tick in 72: game._physics_process(1.0/30.0)
	assert(game.title_menu.current_item().id == "vs_com")
	key(KEY_E, true)
	for tick in 14:
		game._physics_process(1.0/30.0)
		assert(game.session.root_label == "MENU")
	game._physics_process(1.0/30.0)
	assert(game.session.root_label == "地图" and game.session.modo == 2)
	key(KEY_E, false)
	game._on_map_confirmed("现世")
	assert(game.session.p2cpu and not game.session.p1cpu)
	assert(game.ichigo.ai_random_clock.difficulty == 5)
	assert(game.naruto.fighter_name == "鸣人" and game.ichigo.fighter_name == "一护")
	game._goto_menu()
	game.queue_free()
	await process_frame
	print("VS_COM_MENU_ENTRY_SMOKE_OK")
	quit()
