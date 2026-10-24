extends SceneTree

func _initialize() -> void:
	_run.call_deferred()

func _run() -> void:
	var args := OS.get_cmdline_user_args()
	assert(args.size() == 2)
	var data: Dictionary = JSON.parse_string(FileAccess.get_file_as_string(args[0]))
	assert(data.rows.size() == 4032 and data.production_admitted == false)
	var inputs := Image.create(3, 4032, false, Image.FORMAT_RGBA8)
	var parameters := Image.create(1, 4032, false, Image.FORMAT_RGBA8)
	var colors := Image.create(2, 4032, false, Image.FORMAT_RGBA8)
	for i in data.rows.size():
		var row: Dictionary = data.rows[i]
		for j in 3:
			var p: Array = row.pixels[j]
			inputs.set_pixel(j, i, Color8(p[0], p[1], p[2], p[3]))
		parameters.set_pixel(0, i, Color8(row.key[0], row.key[4], row.key[5], row.vector))
		for j in 2:
			var p: Array = row.colors[j]
			colors.set_pixel(j, i, Color8(p[0], p[1], p[2], 255))
	var view := SubViewport.new()
	view.size = Vector2i(64, 63)
	view.transparent_bg = true
	view.render_target_update_mode = SubViewport.UPDATE_ALWAYS
	root.add_child(view)
	var rect := ColorRect.new()
	rect.size = Vector2(64, 63)
	var material := ShaderMaterial.new()
	material.shader = load("res://tests/normal_composition.gdshader")
	material.set_shader_parameter("inputs", ImageTexture.create_from_image(inputs))
	material.set_shader_parameter("parameters", ImageTexture.create_from_image(parameters))
	material.set_shader_parameter("colors", ImageTexture.create_from_image(colors))
	rect.material = material
	view.add_child(rect)
	for tick in 4:
		await process_frame
		await RenderingServer.frame_post_draw
	assert(view.get_texture().get_image().save_png(args[1]) == OK)
	print("NORMAL_COMPOSITION_DIAGNOSTIC_OK samples=4032")
	quit(0)
