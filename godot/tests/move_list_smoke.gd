extends SceneTree

func _initialize() -> void:
	_run.call_deferred()

func key(scene: Node, code: Key, pressed: bool = false) -> void:
	var event := InputEventKey.new()
	event.keycode = code
	event.pressed = pressed
	scene._input(event)

func click_back(scene: Node, pressed: bool) -> void:
	var event := InputEventMouseButton.new()
	event.button_index = MOUSE_BUTTON_LEFT
	event.position = Vector2(461, 91)
	event.pressed = pressed
	scene._input(event)

func _run() -> void:
	var scene = load("res://main.tscn").instantiate()
	root.add_child(scene)
	current_scene = scene
	scene.set_physics_process(false)
	scene._enter_current_fight(3)
	key(scene, KEY_ENTER)
	key(scene, KEY_UP)
	key(scene, KEY_ENTER)
	assert(scene.pause_menu.source_frame == 1)
	assert(scene.pause_menu.selection == 2)
	for frame in range(2, 11):
		scene.pause_menu.tick()
		assert(scene.pause_menu.source_frame == frame)
		assert(scene.super_runtime.game_paused)
	scene.pause_menu.tick()
	assert(scene.pause_menu.source_frame == 10)
	await process_frame
	await process_frame
	if DisplayServer.get_name() != "headless":
		await RenderingServer.frame_post_draw
		root.get_texture().get_image().save_png("/tmp/bvn-move-list.png")
	click_back(scene, false)
	assert(scene.pause_menu.source_frame == 10)
	click_back(scene, true)
	click_back(scene, false)
	assert(scene.pause_menu.source_frame == 1)
	assert(scene.pause_menu.visible and scene.super_runtime.game_paused)
	key(scene, KEY_UP)
	key(scene, KEY_ENTER)
	for i in range(9):
		scene.pause_menu.tick()
	assert(scene.pause_menu.source_frame == 10)
	# Source Button2009 keyPress returns to frame 1; controller keyUp resumes.
	key(scene, KEY_ENTER, true)
	assert(scene.pause_menu.source_frame == 1)
	assert(scene.super_runtime.game_paused)
	key(scene, KEY_ENTER)
	assert(not scene.pause_menu.visible and not scene.super_runtime.game_paused)
	key(scene, KEY_ENTER)
	assert(scene.pause_menu.source_frame == 1 and scene.pause_menu.selection == 2)
	print("MOVE_LIST_SMOKE_OK")
	scene.queue_free()
	await process_frame
	quit()
