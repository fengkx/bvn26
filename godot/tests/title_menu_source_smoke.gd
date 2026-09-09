extends SceneTree

func _initialize() -> void:
	_run.call_deferred()

func _run() -> void:
	root.size = Vector2i(600, 400)
	var menu := TitleMenu.new()
	root.add_child(menu)
	var chosen: Array = []
	menu.confirmed.connect(func(item: String) -> void: chosen.append(item))
	for tick in 62:
		menu.apply_held({})
	assert(menu.source_frame == 63 and menu.select == 1)
	for tick in range(1, 27):
		var result := menu.apply_held({"down": tick == 1, "confirm": tick >= 12})
		assert(menu.select == 2)
		assert(menu.controller.positions[2] == maxf(1, 56 - tick * 5))
		assert(menu.controller.an == (1 if tick < 11 else 0))
		assert(menu.button_frame == maxi(1, tick - 11))
		assert(chosen.size() == (1 if tick == 26 else 0))
		if tick == 26:
			assert(result.id == "vs_com" and result.modo == 2 and result.goto == "选人画面")
	menu.reset()
	for tick in 62: menu.apply_held({})
	for tick in 12: menu.apply_held({"down": true})
	assert(menu.select == 3, "Held S must repeat after the wheel settles")
	menu.reset()
	for tick in 62: menu.apply_held({})
	menu.apply_held({"up": true, "down": true})
	assert(menu.select == 10, "Source W and S branches are independent")
	menu.reset()
	for tick in 72: menu.apply_held({})
	menu.apply_held({"down": true})
	for tick in 10: menu.apply_held({})
	if "capture" in OS.get_cmdline_user_args():
		await process_frame
		await RenderingServer.frame_post_draw
		root.get_texture().get_image().save_png("/tmp/bvn-title-menu/godot-vs-com.png")
	menu.queue_free()
	await process_frame
	print("TITLE_MENU_SOURCE_SMOKE_OK")
	quit()
