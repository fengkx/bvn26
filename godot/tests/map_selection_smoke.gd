extends SceneTree


func _initialize() -> void:
	create_timer(30).timeout.connect(func() -> void: quit(1))
	call_deferred("_run")


func _run() -> void:
	var menu := MapSelection.new()
	root.add_child(menu)
	await process_frame
	menu.reset()
	assert(menu.selected_stage() == "现世")
	# Same four navigation calls as the native Flash navigation.log probe.
	menu.move_selection("left")
	assert(menu.selected_stage() == "木叶村")
	menu.move_selection("up")
	assert(menu.selected_stage() == "宇智波村")
	menu.move_selection("right")
	assert(menu.selected_stage() == "尸魂界通道")
	menu.move_selection("down")
	assert(menu.selected_stage() == "现世")
	menu.reset()
	menu.tick({"down": true})
	assert(menu.selected_stage() == "流魂街")
	for tick in 4:
		menu.tick({"down": true})
		assert(menu.selected_stage() == "流魂街")
	menu.tick({"down": true})
	assert(menu.selected_stage() == "双极")
	menu.reset()
	menu.tick({"left": true, "right": true, "up": true, "down": true})
	assert(menu.selected_stage() == "现世")
	var confirms: Array[String] = []
	var cancellations: Array[bool] = []
	menu.confirmed.connect(func(stage: String) -> void: confirms.append(stage))
	menu.cancelled.connect(func() -> void: cancellations.append(true))
	menu.reset()
	for tick in 6:
		menu.tick({"down": true})
	for tick in 5:
		menu.tick({})
	menu.tick({"confirm": true})
	menu.tick({"down": true})
	assert(not menu.enabled and menu.selected_stage() == "双极")
	await create_timer(0.2).timeout
	assert(confirms.is_empty())
	await create_timer(0.35).timeout
	assert(confirms == ["双极"])
	menu.visible = true
	menu.reset()
	menu.tick({"confirm": true, "back": true})
	await create_timer(0.55).timeout
	assert(cancellations == [true] and confirms == ["双极"])
	menu.free()
	var scene = load("res://main.tscn").instantiate()
	root.add_child(scene)
	await process_frame
	scene.set_physics_process(false)
	scene._on_menu_confirmed("training")
	assert(scene.session.root_label == "地图")
	assert(scene.session.modo == 4)
	var catalog: Dictionary = JSON.parse_string(FileAccess.get_file_as_string("res://generated/stages/catalog/catalog.json"))
	for stage: Dictionary in catalog["stages"]:
		scene.stage_sound.random_tape.assign([0.99, 0.99])
		scene._on_map_confirmed(str(stage["id"]))
		assert(scene.stage_sound.selected_file == str(stage["music"]))
		assert(scene.session.root_label == "游戏场景")
		assert(scene.stage_background.visible)
		assert(scene.stage_background.get_child_count() > 0)
		assert(scene.stage_background.get_parent() == scene)
		assert(scene.selected_stage == str(stage["id"]))
		assert(scene.current_world.current_source_frame() == int(stage["frame"]))
		assert(scene.naruto.position == scene.current_world.named_instance_origin("p1"))
		assert(scene.ichigo.position == scene.current_world.named_instance_origin("p2"))
		assert(scene.naruto._ground_y == -25)
		scene._goto_menu()
		assert(not scene.stage_background.visible)
		scene._on_menu_confirmed("versus")
		assert(scene.session.root_label == "地图")
		assert(scene.map_selection.selected_stage() == "现世")
		await process_frame
	scene.queue_free()
	await process_frame
	print("MAP_SELECTION_SMOKE_OK: native navigation, repeat, timers, cancellation, all 10 stages")
	quit()
