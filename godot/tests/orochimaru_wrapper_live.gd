extends SceneTree
# Diagnostic-only binding: texture bytes come from the unchanged source JPEG/alpha.
const INPUT = preload("res://tests/affine_component_coverage.gdshader")
const LIVE = preload("res://tests/live_rect_cache_filter.gd")

func _initialize() -> void:
	_run.call_deferred()

func _run() -> void:
	var args := OS.get_cmdline_user_args()
	assert(args.size() == 2)
	var fixture: Dictionary = JSON.parse_string(FileAccess.get_file_as_string(args[0]))
	assert(fixture.production_admitted == false and fixture.leaf.fill.fillStyleType == "67")
	for spec in fixture.cases:
		var directory := args[1].path_join(spec.folder)
		var size := Vector2i(spec.size[0], spec.size[1])
		var view := SubViewport.new()
		view.size = size
		view.transparent_bg = true
		view.world_2d = World2D.new()
		view.render_target_update_mode = SubViewport.UPDATE_ALWAYS
		root.add_child(view)
		var bytes := FileAccess.get_file_as_bytes(directory.path_join("source.rgba"))
		assert(bytes.size() == 186 * 378 * 4)
		var source := Image.create_from_data(186, 378, false, Image.FORMAT_RGBA8, bytes)
		var sprite := Sprite2D.new()
		sprite.centered = false
		var surface := Image.create(size.x, size.y, false, Image.FORMAT_RGBA8)
		surface.fill(Color.WHITE)
		sprite.texture = ImageTexture.create_from_image(surface)
		var sampler := ShaderMaterial.new()
		sampler.shader = INPUT
		sampler.set_shader_parameter("source_tex", ImageTexture.create_from_image(source))
		for name in ["coefficients", "coordinates"]:
			var format := Image.FORMAT_RGBAF if name == "coordinates" else Image.FORMAT_RGBA8
			var width := size.x if name == "coordinates" else size.x * 8
			var image := Image.create_from_data(width, size.y, false, format, FileAccess.get_file_as_bytes(directory.path_join(name + ".bin")))
			sampler.set_shader_parameter(name, ImageTexture.create_from_image(image))
		sprite.material = sampler
		view.add_child(sprite)
		for tick in 4:
			await process_frame
			await RenderingServer.frame_post_draw
		assert(view.get_texture().get_image().save_png(directory.path_join("local.png")) == OK)
		await LIVE.render(self, view.get_texture(), spec, directory, 0)
		view.queue_free()
		await process_frame
	print("OROCHIMARU_WRAPPER_LIVE_OK cases=", fixture.cases.size())
	quit()
