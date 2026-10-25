extends RefCounted
# Consume the live sampler viewport texture; no PNG or native pixels enter this stage.
const GROUP = preload("res://tests/grouped_blur_filter_group.gd")
const RAW = preload("res://tests/raw_byte_texture.gdshader")
const NORMAL = preload("res://tests/nested_integer_composite.gdshader")

static func render(tree: SceneTree, texture: Texture2D, spec: Dictionary, output: String, index: int) -> void:
	assert(texture is ViewportTexture and texture.get_size() == Vector2(spec.local_size[0], spec.local_size[1]))
	var filters: Array = spec.filters
	assert(filters.size() == 1 and filters[0].type == "BLURFILTER")
	var bx := float(filters[0].blurX)
	var by := float(filters[0].blurY)
	var passes := int(filters[0].passes)
	assert(bx >= 0 and bx <= 64 and by >= 0 and by <= 64 and passes >= 1 and passes <= 3)
	var padding := Vector2i(ceili(maxf(0, (bx - 1) / 2)) * passes, ceili(maxf(0, (by - 1) / 2)) * passes)
	var view := SubViewport.new()
	view.size = Vector2i(600, 400)
	view.transparent_bg = true
	view.world_2d = World2D.new()
	view.render_target_update_mode = SubViewport.UPDATE_ALWAYS
	tree.root.add_child(view)
	var background := ColorRect.new()
	background.size = Vector2(600, 400)
	background.color = Color(96.0 / 255, 96.0 / 255, 96.0 / 255, 1)
	view.add_child(background)
	var sprite := Sprite2D.new()
	sprite.centered = false
	sprite.texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
	sprite.texture = texture
	var raw := ShaderMaterial.new()
	raw.shader = RAW
	sprite.material = raw
	var group := GROUP.new()
	group.set_meta("flash_filters", filters)
	var composite: Sprite2D = group.setup([sprite], 1.0)
	var material := ShaderMaterial.new()
	material.shader = NORMAL
	composite.material = material
	var copy := BackBufferCopy.new()
	copy.copy_mode = BackBufferCopy.COPY_MODE_VIEWPORT
	group.add_child(copy)
	group.add_child(composite)
	group.position = Vector2(spec.x_bounds[0], spec.y_bounds[0])
	view.add_child(group)
	for tick in 12:
		await tree.process_frame
		await RenderingServer.frame_post_draw
	assert(sprite.texture == texture)
	assert(group.source_bounds() == Rect2(0, 0, spec.local_size[0], spec.local_size[1]))
	var contents: SubViewport = group.get_node("Contents")
	assert(contents.size == Vector2i(spec.local_size[0], spec.local_size[1]) + padding * 2 and composite.position == -Vector2(padding))
	assert(copy.get_index() < composite.get_index())
	var previous: Texture2D = contents.get_texture()
	var axes: Array = []
	for child in group.get_children():
		if child is SubViewport and child.name.begins_with("FilterPass"):
			assert(child.size == contents.size and child.get_child(0).texture == previous)
			assert(child.get_child(0).material.shader == GROUP.INTEGER_BLUR)
			var axis := int(child.get_meta("flash_filter_axis"))
			assert(child.get_child(0).material.get_shader_parameter("blur_size") == (bx if axis == 0 else by))
			axes.append(int(child.get_meta("flash_filter_axis")))
			previous = child.get_texture()
	var expected: Array = []
	for axis in 2:
		if (bx if axis == 0 else by) > 1:
			for repeat in passes:
				expected.append(axis)
	assert(axes == expected and composite.texture == previous)
	assert(contents.get_texture().get_image().save_png(output.path_join("input-%d.png" % index)) == OK)
	assert(composite.texture.get_image().save_png(output.path_join("filtered-%d.png" % index)) == OK)
	assert(view.get_texture().get_image().save_png(output.path_join("final-%d.png" % index)) == OK)
	view.queue_free()
	await tree.process_frame
