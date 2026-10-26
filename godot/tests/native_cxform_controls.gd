extends SceneTree

func _initialize() -> void:
	_run.call_deferred()

func _texture(path: String, size: Vector2i, format: Image.Format) -> ImageTexture:
	var bytes := FileAccess.get_file_as_bytes(path)
	var image := Image.create_from_data(size.x, size.y, false, format, bytes)
	var texture := ImageTexture.create_from_image(image)
	assert(texture.get_image().get_data() == bytes)
	return texture

func _run() -> void:
	var args := OS.get_cmdline_user_args()
	assert(args.size() == 1)
	var data: Dictionary = JSON.parse_string(FileAccess.get_file_as_string(args[0]))
	assert(data.production_admitted == false and data.cpu_arithmetic_passed == true)
	var size := Vector2i(data.width, data.height)
	var material := ShaderMaterial.new()
	material.shader = load("res://tests/native_cxform_controls.gdshader")
	material.set_shader_parameter("inputs", _texture(data.inputs, size, Image.FORMAT_RGBAF))
	material.set_shader_parameter("opacities", _texture(data.opacities, size, Image.FORMAT_RF))
	material.set_shader_parameter("reciprocals", _texture(data.reciprocals, Vector2i(256, 1), Image.FORMAT_RF))
	var view := SubViewport.new()
	view.size = size
	view.transparent_bg = true
	view.render_target_update_mode = SubViewport.UPDATE_ALWAYS
	root.add_child(view)
	var rect := ColorRect.new()
	rect.size = Vector2(size)
	rect.material = material
	view.add_child(rect)
	for tick in 4:
		await process_frame
		await RenderingServer.frame_post_draw
	assert(view.get_texture().get_image().save_png(data.output) == OK)
	print("NATIVE_CXFORM_CONTROLS_OK samples=%s production_admitted=false" % data.samples)
	quit(0)
