extends SceneTree


func _initialize() -> void:
	_run.call_deferred()


func _run() -> void:
	assert(DisplayServer.get_name() != "headless")
	root.size = Vector2i(600, 400)
	root.content_scale_size = Vector2i(600, 400)
	var background := ColorRect.new()
	background.size = Vector2(600, 400)
	background.color = Color.BLUE
	root.add_child(background)
	var stale_copy := BackBufferCopy.new()
	stale_copy.copy_mode = BackBufferCopy.COPY_MODE_VIEWPORT
	root.add_child(stale_copy)
	for index in 2:
		var foreground := ColorRect.new()
		foreground.position.x = index * 300
		foreground.size = Vector2(300, 400)
		foreground.color = Color.RED if index == 0 else Color.GREEN
		root.add_child(foreground)
	var owner = load("res://main.gd").new()
	owner.diagnostics.free()
	owner.diagnostics = null
	owner._setup_screen_flash()
	var flash: ColorRect = owner.screen_flash
	if "--without-refresh" in OS.get_cmdline_user_args():
		for child in flash.get_children():
			child.free()
	owner.remove_child(flash)
	root.add_child(flash)
	flash.visible = true
	for tint in [Vector3.ZERO, Vector3.ONE]:
		flash.material.set_shader_parameter("tint", tint)
		flash.material.set_shader_parameter("opacity", 114.0 / 256.0)
		for frame in 3:
			await process_frame
			await RenderingServer.frame_post_draw
		var image := root.get_texture().get_image()
		if image.get_pixel(150, 200) != Color.RED or image.get_pixel(450, 200) != Color.GREEN:
			push_error("Shine reused a lower object's backdrop: %s / %s" % [image.get_pixel(150, 200), image.get_pixel(450, 200)])
			owner.free()
			quit(1)
			return
	owner.free()
	print("SHINE_BACKDROP_RENDER_OK")
	quit()
