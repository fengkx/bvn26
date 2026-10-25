extends RefCounted
# Consume the live sampler viewport texture; no PNG or native pixels enter this stage.
const GROUP = preload("res://tests/grouped_blur_filter_group.gd")
const RAW = preload("res://tests/raw_byte_texture.gdshader")
const NORMAL = preload("res://tests/nested_integer_composite.gdshader")

static func render(tree: SceneTree, texture: Texture2D, spec: Dictionary, output: String, index: int) -> void:
	assert(texture is ViewportTexture and texture.get_size() == Vector2(75, 74))
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
	group.set_meta("flash_filters", [{"type": "BLURFILTER", "blurX": 15.0, "blurY": 0.0, "passes": 3}])
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
	assert(group.source_bounds() == Rect2(0, 0, 75, 74))
	var contents: SubViewport = group.get_node("Contents")
	assert(contents.size == Vector2i(117, 74) and composite.position == Vector2(-21, 0))
	assert(copy.get_index() < composite.get_index())
	var previous: Texture2D = contents.get_texture()
	var axes: Array = []
	for child in group.get_children():
		if child is SubViewport and child.name.begins_with("FilterPass"):
			assert(child.size == contents.size and child.get_child(0).texture == previous)
			assert(child.get_child(0).material.shader == GROUP.INTEGER_BLUR)
			assert(child.get_child(0).material.get_shader_parameter("blur_size") == 15.0)
			axes.append(int(child.get_meta("flash_filter_axis")))
			previous = child.get_texture()
	assert(axes == [0, 0, 0] and composite.texture == previous)
	assert(contents.get_texture().get_image().save_png(output.path_join("input-%d.png" % index)) == OK)
	assert(composite.texture.get_image().save_png(output.path_join("filtered-%d.png" % index)) == OK)
	assert(view.get_texture().get_image().save_png(output.path_join("final-%d.png" % index)) == OK)
	view.queue_free()
	await tree.process_frame
