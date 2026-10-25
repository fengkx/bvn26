extends SceneTree
# Bounded diagnostic only; raw source data enters a live buffer, never native reference pixels.
const INPUT = preload("res://tests/quarter_grid_bitmap_input.gdshader")
const GROUP = preload("res://tests/integer_shadow_filter_group.gd")
const RAW = preload("res://tests/raw_byte_texture.gdshader")
const NORMAL = preload("res://tests/nested_integer_composite.gdshader")

func _initialize() -> void:
	_run.call_deferred()

func _view(size: Vector2i) -> SubViewport:
	var view := SubViewport.new()
	view.size = size
	view.transparent_bg = true
	view.world_2d = World2D.new()
	view.render_target_update_mode = SubViewport.UPDATE_ALWAYS
	root.add_child(view)
	return view

func _texel(raw: Array, x: int, y: int) -> Color:
	var p: Array = raw[clampi(y, 0, 2) * 34 + clampi(x, 0, 33)]
	return Color(p[0] / 255.0, p[1] / 255.0, p[2] / 255.0, p[3] / 255.0)

func _run() -> void:
	var args := OS.get_cmdline_user_args()
	assert(args.size() == 2)
	var fixture: Dictionary = JSON.parse_string(FileAccess.get_file_as_string(args[0]))
	assert(fixture.production_admitted == false)
	var source: Dictionary = fixture.source
	assert(source.fills.size() == 2 and source.fills[0].directed_edge_count == 0 and source.fills[1].directed_edge_count == 4)
	var fill: Dictionary = source.fills[1]
	assert(fill.contours == [[[3.0, 0.0], [3.0, 34.0], [0.0, 34.0], [0.0, 0.0]]])
	var matrix: Dictionary = fill.matrix
	assert(float(matrix.scaleX) == 0 and float(matrix.scaleY) == 0 and float(matrix.rotateSkew0) == 20 and float(matrix.rotateSkew1) == -20)
	assert(float(matrix.translateX) == 60 and float(matrix.translateY) == 0)
	assert(fixture.raw.size() == 102)
	var filters: Array = source.case.placement.filters
	assert(filters.size() == 1 and filters[0].type == "GLOWFILTER")
	assert(filters[0].blurX == 5 and filters[0].blurY == 5 and filters[0].passes == 1 and filters[0].strength == 1)
	for index in fixture.cases.size():
		var spec: Dictionary = fixture.cases[index]
		var local := Vector2(float(spec.origin[0]) - floorf(spec.origin[0]), float(spec.origin[1]) - floorf(spec.origin[1]))
		assert(local == Vector2(0.5, 0.75))
		var images: Array[Image] = []
		for i in 6:
			images.append(Image.create(4, 35, false, Image.FORMAT_RF if i == 5 else Image.FORMAT_RGBA8))
		for y in 35:
			for x in 4:
				var u := y - local.y
				var v := 2 + local.x - x
				var ix := floori(u)
				var iy := floori(v)
				for i in 4:
					images[i].set_pixel(x, y, _texel(fixture.raw, ix + i % 2, iy + i / 2))
				images[4].set_pixel(x, y, Color(floorf((u - ix) * 256) / 255, floorf((v - iy) * 256) / 255, 0, 0))
				var coverage := (minf(x + 1, local.x + 3) - maxf(x, local.x)) * (minf(y + 1, local.y + 34) - maxf(y, local.y))
				assert(coverage * 16 == floorf(coverage * 16))
				images[5].set_pixel(x, y, Color(coverage, 0, 0, 1))
		var input := _view(Vector2i(4, 35))
		var sprite := Sprite2D.new()
		sprite.centered = false
		sprite.texture = ImageTexture.create_from_image(images[0])
		var sampler := ShaderMaterial.new()
		sampler.shader = INPUT
		for i in 6:
			sampler.set_shader_parameter(["c00", "c10", "c01", "c11", "parameters", "coverage_texture"][i], ImageTexture.create_from_image(images[i]))
		sprite.material = sampler
		input.add_child(sprite)
		var stage := _view(Vector2i(600, 400))
		var background := ColorRect.new()
		background.size = Vector2(600, 400)
		background.color = Color(96.0 / 255, 96.0 / 255, 96.0 / 255, 1)
		stage.add_child(background)
		var raw_sprite := Sprite2D.new()
		raw_sprite.centered = false
		raw_sprite.texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
		raw_sprite.texture = input.get_texture()
		var raw_material := ShaderMaterial.new()
		raw_material.shader = RAW
		raw_sprite.material = raw_material
		var group := GROUP.new()
		group.set_meta("flash_filters", filters)
		var color: Array = filters[0].color
		var color_bytes := [roundi(color[0] * 255), roundi(color[1] * 255), roundi(color[2] * 255)]
		assert(color_bytes == [99, 233, 247] and color[3] == 1)
		group.set_meta("shadow_diagnostic", {"strength": filters[0].strength, "color": color_bytes, "alpha_byte": floori(color[3] * 255), "api": "display", "hidden": false})
		var composite: Sprite2D = group.setup([raw_sprite], 1.0)
		var material := ShaderMaterial.new()
		material.shader = NORMAL
		composite.material = material
		var copy := BackBufferCopy.new()
		copy.copy_mode = BackBufferCopy.COPY_MODE_VIEWPORT
		group.add_child(copy)
		group.add_child(composite)
		group.position = Vector2(floorf(spec.origin[0]), floorf(spec.origin[1]))
		stage.add_child(group)
		for tick in 12:
			await process_frame
			await RenderingServer.frame_post_draw
		assert(raw_sprite.texture == input.get_texture())
		assert(group.source_bounds() == Rect2(0, 0, 4, 35))
		var contents: SubViewport = group.get_node("Contents")
		assert(contents.size == Vector2i(8, 39) and composite.position == Vector2(-2, -2))
		assert(copy.get_index() < composite.get_index())
		var previous: Texture2D = contents.get_texture()
		var axes: Array = []
		var compositions := 0
		for child in group.get_children():
			if child is SubViewport and child.name.begins_with("FilterPass"):
				assert(child.size == contents.size and child.get_child(0).texture == previous)
				var pass_material: ShaderMaterial = child.get_child(0).material
				if int(child.get_meta("flash_filter_index")) == 0:
					assert(pass_material.shader == preload("res://tests/integer_blur.gdshader"))
					axes.append(int(child.get_meta("flash_filter_axis")))
				else:
					assert(int(child.get_meta("flash_filter_index")) == -1)
					assert(pass_material.shader == preload("res://tests/integer_shadow.gdshader"))
					assert(pass_material.get_shader_parameter("original_texture") == contents.get_texture())
					assert(pass_material.get_shader_parameter("shadow_offset") == Vector2.ZERO)
					compositions += 1
				previous = child.get_texture()
		assert(axes == [0, 1] and compositions == 1 and composite.texture == previous)
		assert(input.get_texture().get_image().save_png(args[1].path_join("local-%d.png" % index)) == OK)
		assert(contents.get_texture().get_image().save_png(args[1].path_join("input-%d.png" % index)) == OK)
		assert(composite.texture.get_image().save_png(args[1].path_join("glow-%d.png" % index)) == OK)
		assert(stage.get_texture().get_image().save_png(args[1].path_join("final-%d.png" % index)) == OK)
		stage.queue_free()
		await process_frame
		input.queue_free()
		await process_frame
	print("ROTATED_GLOW_COMPONENT_OK")
	quit(0)
