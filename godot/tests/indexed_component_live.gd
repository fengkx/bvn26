extends SceneTree
# Diagnostic only: sampling metadata comes from geometry; pixels come from original tags.
const INPUT = preload("res://tests/quarter_grid_bitmap_input.gdshader")
const LIVE = preload("res://tests/live_rect_cache_filter.gd")
const MASK = preload("res://tests/rect_mask_binding.gd")

func _initialize() -> void:
	_run.call_deferred()

func _run() -> void:
	var args := OS.get_cmdline_user_args()
	assert(args.size() == 2)
	var fixture: Dictionary = JSON.parse_string(FileAccess.get_file_as_string(args[0]))
	assert(fixture.production_admitted == false)
	for index in fixture.cases.size():
		var spec: Dictionary = fixture.cases[index]
		var leaf: Dictionary = spec.leaf
		assert(leaf.indexed_storage_verified == true)
		assert(MASK.matches(leaf.fill_masks[0][0], float(leaf.fill_matrix.translateX) / 20, float(leaf.fill_matrix.translateY) / 20, leaf.width, leaf.height))
		var size := Vector2i(spec.local_size[0], spec.local_size[1])
		assert(spec.samples.size() == size.x * size.y)
		var images: Array[Image] = []
		for i in 6:
			images.append(Image.create(size.x, size.y, false, Image.FORMAT_RF if i == 5 else Image.FORMAT_RGBA8))
		for y in size.y:
			for x in size.x:
				var sample: Array = spec.samples[y * size.x + x]
				for i in 4:
					var ix := clampi(int(sample[0]) + i % 2, 0, leaf.width - 1)
					var iy := clampi(int(sample[1]) + i / 2, 0, leaf.height - 1)
					var raw: Array = leaf.pixels_premultiplied[iy * int(leaf.width) + ix]
					images[i].set_pixel(x, y, Color(raw[0] / 255.0, raw[1] / 255.0, raw[2] / 255.0, raw[3] / 255.0))
				assert(sample[2] >= 0 and sample[2] <= 255 and sample[3] >= 0 and sample[3] <= 255)
				assert(sample[4] >= 0 and sample[4] <= 1 and sample[4] * 16 == floorf(sample[4] * 16))
				images[4].set_pixel(x, y, Color(sample[2] / 255.0, sample[3] / 255.0, 0, 0))
				images[5].set_pixel(x, y, Color(sample[4], 0, 0, 1))
		var view := SubViewport.new()
		view.size = size
		view.transparent_bg = true
		view.world_2d = World2D.new()
		view.render_target_update_mode = SubViewport.UPDATE_ALWAYS
		root.add_child(view)
		var sprite := Sprite2D.new()
		sprite.centered = false
		sprite.texture = ImageTexture.create_from_image(images[0])
		var material := ShaderMaterial.new()
		material.shader = INPUT
		for i in 6:
			material.set_shader_parameter(["c00", "c10", "c01", "c11", "parameters", "coverage_texture"][i], ImageTexture.create_from_image(images[i]))
		sprite.material = material
		view.add_child(sprite)
		for tick in 4:
			await process_frame
			await RenderingServer.frame_post_draw
		assert(view.get_texture().get_image().save_png(args[1].path_join("local-%d.png" % index)) == OK)
		await LIVE.render(self, view.get_texture(), spec, args[1], index)
		view.queue_free()
		await process_frame
	print("INDEXED_COMPONENT_LIVE_OK cases=", fixture.cases.size())
	quit()
