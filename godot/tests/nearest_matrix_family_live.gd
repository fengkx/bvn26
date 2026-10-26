extends SceneTree
# Diagnostic only: retain the actual filter and native post-transform composition.
const INPUT = preload("res://tests/affine_component_coverage.gdshader")
const GROUP = preload("res://filter_group.gd")
const RAW = preload("res://tests/raw_byte_texture.gdshader")
const COMPOSITE = preload("res://tests/native_nested_filter_composite.gdshader")

func _initialize() -> void:
	_run.call_deferred()

func _run() -> void:
	var args := OS.get_cmdline_user_args()
	assert(args.size() == 2)
	var fixture: Dictionary = JSON.parse_string(FileAccess.get_file_as_string(args[0]))
	assert(fixture.production_admitted == false)
	var bytes := PackedByteArray()
	bytes.resize(256 * 4)
	for i in 256:
		bytes.encode_float(i * 4, float(fixture.native_reciprocals[i]))
	var reciprocals := ImageTexture.create_from_image(Image.create_from_data(256, 1, false, Image.FORMAT_RF, bytes))
	for spec in fixture.cases:
		var directory := args[1].path_join(spec.folder)
		var view := SubViewport.new()
		view.size = Vector2i(600, 400)
		view.transparent_bg = true
		view.world_2d = World2D.new()
		view.render_target_update_mode = SubViewport.UPDATE_ALWAYS
		root.add_child(view)
		var background := ColorRect.new()
		background.size = Vector2(600, 400)
		background.color = Color(96.0 / 255, 96.0 / 255, 96.0 / 255, 1)
		view.add_child(background)
		var input_view: SubViewport
		var group: Node2D
		var sprite: Sprite2D
		var composite: Sprite2D
		var copy: BackBufferCopy
		if spec.active:
			var size := Vector2i(spec.size[0], spec.size[1])
			input_view = SubViewport.new()
			input_view.size = size
			input_view.transparent_bg = true
			input_view.world_2d = World2D.new()
			input_view.render_target_update_mode = SubViewport.UPDATE_ALWAYS
			root.add_child(input_view)
			var source := Image.create_from_data(137, 200, false, Image.FORMAT_RGBA8, FileAccess.get_file_as_bytes(directory.path_join("source.rgba")))
			var input_sprite := Sprite2D.new()
			input_sprite.centered = false
			var surface := Image.create(size.x, size.y, false, Image.FORMAT_RGBA8)
			surface.fill(Color.WHITE)
			input_sprite.texture = ImageTexture.create_from_image(surface)
			var sampler := ShaderMaterial.new()
			sampler.shader = INPUT
			sampler.set_shader_parameter("source_tex", ImageTexture.create_from_image(source))
			for name in ["coefficients", "coordinates"]:
				var format := Image.FORMAT_RGBAF if name == "coordinates" else Image.FORMAT_RGBA8
				var width := size.x if name == "coordinates" else size.x * 8
				var image := Image.create_from_data(width, size.y, false, format, FileAccess.get_file_as_bytes(directory.path_join(name + ".bin")))
				sampler.set_shader_parameter(name, ImageTexture.create_from_image(image))
			input_sprite.material = sampler
			input_view.add_child(input_sprite)
			sprite = Sprite2D.new()
			sprite.centered = false
			sprite.texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
			sprite.texture = input_view.get_texture()
			var raw := ShaderMaterial.new()
			raw.shader = RAW
			sprite.material = raw
			group = GROUP.new()
			group.set_meta("flash_filters", spec.filters)
			composite = group.setup([sprite], 1.0)
			var material := ShaderMaterial.new()
			material.shader = COMPOSITE
			material.set_shader_parameter("native_reciprocals", reciprocals)
			material.set_shader_parameter("post_mul", Vector3(spec.post_mul[0], spec.post_mul[1], spec.post_mul[2]) / 256.0)
			material.set_shader_parameter("post_add", Vector3(spec.post_add[0], spec.post_add[1], spec.post_add[2]) / 255.0)
			composite.material = material
			copy = BackBufferCopy.new()
			copy.copy_mode = BackBufferCopy.COPY_MODE_VIEWPORT
			group.add_child(copy)
			group.add_child(composite)
			group.position = Vector2(spec.origin[0], spec.origin[1])
			view.add_child(group)
		for tick in 12:
			await process_frame
			await RenderingServer.frame_post_draw
		if spec.active:
			var size := Vector2i(spec.size[0], spec.size[1])
			assert(sprite.texture == input_view.get_texture())
			assert(group.source_bounds() == Rect2(0, 0, size.x, size.y))
			var contents: SubViewport = group.get_node("Contents")
			assert(contents.size == size and copy.get_index() < composite.get_index())
			var passes := 0
			for child in group.get_children():
				if child is SubViewport and child.name.begins_with("FilterPass"):
					passes += 1
					assert(child.size == size and child.get_child(0).texture == contents.get_texture())
					assert(child.get_child(0).material.shader == GROUP.FILTER_SHADER)
					assert(child.get_child(0).material.get_shader_parameter("operation") == 2)
					assert(composite.texture == child.get_texture())
			assert(passes == 1)
			assert(input_view.get_texture().get_image().save_png(directory.path_join("local.png")) == OK)
			assert(contents.get_texture().get_image().save_png(directory.path_join("input.png")) == OK)
			assert(composite.texture.get_image().save_png(directory.path_join("filtered.png")) == OK)
		else:
			assert(view.get_child_count() == 1)
		assert(view.get_texture().get_image().save_png(directory.path_join("final.png")) == OK)
		view.queue_free()
		if input_view != null:
			input_view.queue_free()
		await process_frame
	print("NEAREST_MATRIX_FAMILY_LIVE_OK cases=", fixture.cases.size())
	quit()
