extends SceneTree

func _initialize() -> void:
	_run.call_deferred()

func _run() -> void:
	var view := SubViewport.new()
	view.size = Vector2i(256, 256)
	view.transparent_bg = true
	view.render_target_update_mode = SubViewport.UPDATE_ALWAYS
	root.add_child(view)
	var renderer := TimelinePreview.new()
	for foreground in [false, true]:
		var image := Image.create(256, 256, false, Image.FORMAT_RGBA8)
		for y in 256:
			for x in 256:
				var gray := float(y if foreground else x) / 255.0
				image.set_pixel(x, y, Color(gray, gray, gray, 1.0))
		var item := TextureRect.new()
		item.texture = ImageTexture.create_from_image(image)
		item.texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
		if foreground:
			renderer._apply_blend(item, 13, view)
		view.add_child(item)
	renderer.free()
	for tick in 3:
		await process_frame
		await RenderingServer.frame_post_draw
	var image := view.get_texture().get_image()
	var rows: Array = []
	for y in 256:
		var row: Array = []
		for x in 256:
			var color := image.get_pixel(x, y)
			row.append([roundi(color.r * 255), roundi(color.g * 255), roundi(color.b * 255), roundi(color.a * 255)])
		rows.append(row)
	FileAccess.open(OS.get_cmdline_user_args()[0], FileAccess.WRITE).store_string(JSON.stringify(rows))
	quit()
