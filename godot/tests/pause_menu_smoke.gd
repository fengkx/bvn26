extends SceneTree

func _initialize() -> void:
	_run.call_deferred()

func key(scene: Node, code: Key, pressed: bool = false) -> void:
	var event := InputEventKey.new()
	event.keycode = code
	event.pressed = pressed
	scene._input(event)

func finish_opening(scene: Node) -> void:
	for tick in 600:
		scene._advance_fight()
		if not scene.battle_intro.active:
			break
	assert(not scene.battle_intro.active)

func _run() -> void:
	var scene = load("res://main.tscn").instantiate()
	root.add_child(scene)
	current_scene = scene
	scene.set_physics_process(false)
	key(scene, KEY_ENTER)
	assert(not scene.pause_menu.visible)
	scene._enter_current_fight(3)
	# The imported opening now locks pause input until startFight.
	finish_opening(scene)
	key(scene, KEY_ENTER, true)
	assert(not scene.pause_menu.visible)
	key(scene, KEY_ENTER)
	assert(scene.pause_menu.visible and scene.pause_menu.selection == 2)
	assert(scene.super_runtime.game_paused)
	var frame: int = scene.naruto.current_source_frame()
	var pos: Vector2 = scene.naruto.position
	for i in range(5):
		scene._advance_fight()
	assert(scene.naruto.current_source_frame() == frame)
	assert(scene.naruto.position == pos)
	key(scene, KEY_DOWN)
	assert(scene.pause_menu.selection == 0)
	key(scene, KEY_UP)
	assert(scene.pause_menu.selection == 2)
	key(scene, KEY_ENTER)
	assert(not scene.pause_menu.visible and not scene.super_runtime.game_paused)
	assert(scene.naruto.timeline_playing)
	# stopMc must leave hited clips running, as in frame_8.
	scene.naruto.hited = 1
	key(scene, KEY_ENTER)
	assert(scene.naruto.timeline_playing)
	scene.naruto.hited = 0
	key(scene, KEY_UP)
	assert(scene.pause_menu.selection == 1)
	await process_frame
	await process_frame
	if DisplayServer.get_name() != "headless":
		await RenderingServer.frame_post_draw
		root.get_texture().get_image().save_png("/tmp/bvn-pause-menu.png")
	key(scene, KEY_UP)
	key(scene, KEY_ENTER)
	assert(scene.session.root_label == "MENU")
	assert(scene.title_menu.visible and not scene.game_world.visible)
	assert(not scene.pause_menu.visible and not scene.super_runtime.game_paused)
	await scene_changed
	scene = current_scene
	scene.set_physics_process(false)
	scene._enter_current_fight(3)
	assert(scene.naruto.health == scene.session.maxhp)
	assert(scene.battle_intro.active and scene.naruto.root_zhanting)
	finish_opening(scene)
	assert(not scene.naruto.root_zhanting)
	scene.naruto.sw = true
	key(scene, KEY_ENTER)
	assert(not scene.pause_menu.visible)
	print("PAUSE_MENU_SMOKE_OK")
	scene.queue_free()
	await process_frame
	quit()
