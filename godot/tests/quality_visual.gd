extends Node

func press(code: Key, down: bool) -> void:
	var event := InputEventKey.new()
	event.keycode = code
	event.physical_keycode = code
	event.pressed = down
	Input.parse_input_event(event)
	Input.flush_buffered_events()


func _ready() -> void:
	_run.call_deferred()


func _run() -> void:
	var surface := preload("res://render_surface.tscn").instantiate()
	add_child(surface)
	var game = surface.game
	game.set_physics_process(false)
	game.session.render_quality = "HIGH"
	game._goto_config()
	press(KEY_S, true)
	press(KEY_S, false)
	assert(game.config_menu.selected == 2, "The rendering viewport must receive keys once")
	press(KEY_S, true)
	press(KEY_S, false)
	assert(game.config_menu.selected == 3)
	press(KEY_D, true)
	press(KEY_D, false)
	game.config_menu.tick()
	assert(game.session.render_quality == "MEDIUM" and surface.sample_grid == 2)
	press(KEY_D, true)
	press(KEY_D, false)
	game.config_menu.tick()
	assert(game.session.source_quality == "LOW" and surface.sample_grid == 2)
	var button := Button.new()
	button.position = Vector2(300, 200)
	button.size = Vector2(80, 30)
	surface.source_viewport.add_child(button)
	var clicks := [0]
	button.pressed.connect(func() -> void: clicks[0] += 1)
	for quality in ["HIGH", "MEDIUM"]:
		game.session.render_quality = quality
		for down in [true, false]:
			var click := InputEventMouseButton.new()
			click.position = Vector2(320, 210)
			click.global_position = click.position
			click.button_index = MOUSE_BUTTON_LEFT
			click.pressed = down
			get_viewport().push_input(click, true)
	assert(clicks[0] == 2, "Mouse coordinates must survive quality changes")
	button.queue_free()
	game.hide()
	var background := ColorRect.new()
	background.color = Color.BLACK
	background.size = Vector2(600, 400)
	surface.source_viewport.add_child(background)
	var shape := Polygon2D.new()
	shape.polygon = PackedVector2Array([Vector2(50.15, 45.35), Vector2(280.25, 126.65), Vector2(65.3, 170.2)])
	shape.color = Color.WHITE
	surface.source_viewport.add_child(shape)
	var report := {}
	var images := {}
	for quality in ["LOW", "MEDIUM", "HIGH"]:
		game.session.render_quality = quality
		await get_tree().process_frame
		await RenderingServer.frame_post_draw
		await get_tree().process_frame
		await RenderingServer.frame_post_draw
		var pixels := get_viewport().get_texture().get_image()
		print("QUALITY_DIMENSIONS ", quality, " root_texture=", get_viewport().get_texture().get_size(), " canvas=", surface.size, " window=", get_window().size, " raster=", surface.source_viewport.size, " final_transform=", get_viewport().get_final_transform())
		images[quality] = pixels
		var levels := {}
		for y in pixels.get_height():
			for x in pixels.get_width():
				var value := pixels.get_pixel(x, y).r8
				if value > 0 and value < 255: levels[value] = true
		report[quality] = {"intermediate_levels": levels.keys(), "raster_size": str(surface.source_viewport.size)}
		if not OS.has_feature("web"):
			pixels.save_png("/tmp/bvn-quality-%s.png" % quality.to_lower())
	assert(report.LOW.intermediate_levels.size() == 0)
	assert(report.MEDIUM.intermediate_levels.size() > 0)
	assert(report.HIGH.intermediate_levels.size() > report.MEDIUM.intermediate_levels.size())
	assert(images.HIGH.get_data() != images.MEDIUM.get_data())
	background.queue_free()
	shape.queue_free()
	game.show()
	game.session.render_quality = "HIGH"
	await get_tree().process_frame
	await RenderingServer.frame_post_draw
	print("QUALITY_VISUAL_OK ", JSON.stringify(report))
	if OS.has_feature("web"):
		JavaScriptBridge.eval("window.qualityVisualResult = " + JSON.stringify(report) + ";")
	else:
		get_viewport().get_texture().get_image().save_png("/tmp/bvn-quality-config.png")
		FileAccess.open("/tmp/bvn-quality-visual.json", FileAccess.WRITE).store_string(JSON.stringify(report, "\t"))
		game._goto_menu()
		surface.queue_free()
		await get_tree().process_frame
		get_tree().quit()
