extends SceneTree
func _initialize() -> void:
	call_deferred("_run")
func _run() -> void:
	var menu := CharacterSelection.new()
	root.add_child(menu)
	menu.reset(3)
	menu.tick({"left": true}, {})
	assert(menu.fighters[0] == "日番谷")
	for tick in 15:
		menu.tick({}, {})
		await process_frame
	await create_timer(0.6).timeout
	await RenderingServer.frame_post_draw
	var image := root.get_texture().get_image()
	# The source bitmap's upper centre is dark; a released texture renders white.
	var background := image.get_pixel(image.get_width() / 2, image.get_height() / 20)
	assert(background.r < 0.5 and background.g < 0.5 and background.b < 0.5)
	image.save_png("/tmp/bvn-character-selection.png")
	print("CHARACTER_SELECTION_VISUAL_OK")
	quit()
