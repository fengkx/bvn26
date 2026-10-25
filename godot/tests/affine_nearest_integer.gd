extends SceneTree
const SHADER = preload("res://tests/affine_nearest_integer.gdshader")

func _initialize() -> void:
	_run.call_deferred()

func _run() -> void:
	var args := OS.get_cmdline_user_args()
	assert(args.size() == 2)
	var fixture: Dictionary = JSON.parse_string(FileAccess.get_file_as_string(args[0]))
	assert(fixture.production_admitted == false)
	var size := Vector2i(fixture.size[0], fixture.size[1])
	var view := SubViewport.new()
	view.size = size
	view.transparent_bg = true
	view.world_2d = World2D.new()
	view.render_target_update_mode = SubViewport.UPDATE_ALWAYS
	root.add_child(view)
	var material := ShaderMaterial.new()
	material.shader = SHADER
	var source := Image.create_from_data(128, 256, false, Image.FORMAT_RGBA8, FileAccess.get_file_as_bytes(args[1].path_join("source.rgba")))
	material.set_shader_parameter("source_tex", ImageTexture.create_from_image(source))
	for name in ["coefficients", "coordinates", "phase"]:
		var format := Image.FORMAT_RGBAF if name in ["coordinates", "phase"] else Image.FORMAT_RGBA8
		var data := FileAccess.get_file_as_bytes(args[1].path_join(name + ".bin"))
		var texture_width := size.x * 8 if name == "coefficients" else size.x
		var values := Image.create_from_data(texture_width, size.y, false, format, data)
		assert(values != null)
		material.set_shader_parameter(name, ImageTexture.create_from_image(values))
	var surface := Image.create(size.x, size.y, false, Image.FORMAT_RGBA8)
	surface.fill(Color.WHITE)
	var sprite := Sprite2D.new()
	sprite.centered = false
	sprite.texture = ImageTexture.create_from_image(surface)
	sprite.material = material
	view.add_child(sprite)
	for tick in 4:
		await process_frame
		await RenderingServer.frame_post_draw
	assert(view.get_texture().get_image().save_png(args[1].path_join("actual.png")) == OK)
	view.queue_free()
	await process_frame
	print("AFFINE_NEAREST_INTEGER_OK samples=", fixture.samples)
	quit()
