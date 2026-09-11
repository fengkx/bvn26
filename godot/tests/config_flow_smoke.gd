extends SceneTree

func _initialize() -> void:
	_run.call_deferred()

func press(code: Key, pressed: bool) -> void:
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
	game.session.store_path = "/tmp/bvn-config-flow-test.cfg"
	for tick in 85: game.title_menu.apply_held({})
	assert(game.title_menu.current_item().id == "vs_com")
	for direction in ["down", "up"]:
		for tick in 700:
			game.title_menu.apply_held({direction: true})
			assert(game.title_menu.current_item().id in ["vs_com", "versus", "training", "key_settings"])
	for index in [1, 6, 7, 8, 9, 10, 11]:
		assert(not game.title_menu._buttons[index].visible)
	game._on_menu_confirmed("key_settings")
	assert(game.session.root_label == "游戏设置" and game.config_menu.visible)
	press(KEY_S, true)
	press(KEY_S, false)
	assert(game.config_menu.selected == 2)
	press(KEY_D, true)
	press(KEY_D, false)
	game.config_menu.tick()
	assert(game.session.ai_level == 4)
	game.config_menu.selected = 1
	game.config_menu.key_down({"confirm": true})
	assert(game.session.root_label == "键位设置")
	game.key_settings._request_back()
	assert(game.session.root_label == "游戏设置" and game.config_menu.visible)
	assert(not game.key_settings.visible and not game.key_settings.capturing)
	game.config_menu.selected = 4
	game.config_menu.key_down({"left": true})
	game.config_menu.tick()
	assert(game.session.maxtime == 30)
	game.config_menu.selected = 5
	game.config_menu.key_down({"right": true})
	game.config_menu.tick()
	assert(game.session.maxhp == 2000)
	game.config_menu.key_down({"back": true})
	assert(game.session.root_label == "MENU")
	var restored := GameSession.new()
	restored.store_path = game.session.store_path
	restored.load_store()
	assert(restored.ai_level == 4 and restored.maxtime == 30 and restored.maxhp == 2000)
	game.ko_recorded_timers = true
	game._enter_current_fight(2)
	assert(game.naruto.health == 2000 and game.ichigo.health == 2000)
	assert(game.ichigo.ai_random_clock.difficulty == 4)
	assert(game.countdown.digit_frames == {"十": 1, "个": 1})
	assert(game.health_hud.countdown == game.countdown)
	game.naruto.root_zhanting = false
	game.ichigo.root_zhanting = false
	game.countdown.fire()
	assert(game.ko_state["_root.gametime"] == 29)
	assert(game.countdown.digit_frames == {"十": 3, "个": 10})
	game.naruto.root_zhanting = true
	game.countdown.fire()
	assert(game.ko_state["_root.gametime"] == 29)
	assert(game.countdown.digit_frames == {"十": 3, "个": 10})
	game.naruto.root_zhanting = false
	for remaining in range(28, -1, -1):
		game.countdown.fire()
		assert(game.countdown.digit_frames == {"十": remaining / 10 + 1, "个": remaining % 10 + 1})
	assert(game.ko_state["_root.to"])
	game._goto_menu()
	game.session.maxtime = 100
	game._enter_current_fight(2)
	assert(game.countdown.unlimited and game.countdown.timer == null)
	assert(not game.countdown is CanvasItem)
	game.countdown.fire()
	assert(game.ko_state["_root.gametime"] == 100)
	game._goto_menu()
	game.session.maxtime = 30
	game._enter_current_fight(4)
	assert(game.countdown.unlimited and game.countdown.timer == null)
	assert(not game.countdown is CanvasItem)
	game._goto_menu()
	game.queue_free()
	await process_frame
	DirAccess.remove_absolute(restored.store_path)
	print("CONFIG_FLOW_SMOKE_OK")
	quit()
