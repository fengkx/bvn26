extends "res://tests/grouped_blur_rows.gd"
const FAMILY_GROUP = preload("res://tests/integer_shadow_filter_group.gd")

func _run() -> void:
	var args := OS.get_cmdline_user_args()
	assert(args.size() == 2)
	var data: Dictionary = JSON.parse_string(FileAccess.get_file_as_string(args[0]))
	assert(data.production_admitted == false and data.cases.size() > 0 and data.cases.size() <= 48)
	for spec in data.cases:
		var view := SubViewport.new()
		view.size = Vector2i(spec.width, spec.height)
		view.transparent_bg = true
		view.world_2d = World2D.new()
		view.render_target_update_mode = SubViewport.UPDATE_ALWAYS
		root.add_child(view)
		var group := FAMILY_GROUP.new()
		group.set_meta("flash_filters", [{"type": "DROPSHADOWFILTER", "blurX": spec.bx, "blurY": spec.by, "passes": spec.quality,
			"color": [spec.color[0]/255.0, spec.color[1]/255.0, spec.color[2]/255.0, spec.alpha_byte/255.0], "strength": spec.strength, "distance": spec.distance, "angle": deg_to_rad(spec.angle)}])
		group.set_meta("shadow_diagnostic", spec)
		var composite: Sprite2D = group.setup([_source(spec)], 1.0)
		var material := ShaderMaterial.new()
		material.shader = RAW
		composite.material = material
		group.add_child(composite)
		view.add_child(group)
		groups.append(group)
		views.append(view)
	for tick in 12:
		await process_frame
		await RenderingServer.frame_post_draw
	var rows: Array = []
	for i in groups.size():
		var group: Node = groups[i]
		var spec: Dictionary = data.cases[i]
		var contents: SubViewport = group.get_node("Contents")
		var composite: Sprite2D = group.get_node("Composite")
		assert(group.source_bounds() == Rect2(0, 0, spec.width, spec.height))
		var padding := Vector2(ceilf(maxf(0, (float(spec.bx)-1)/2)), ceilf(maxf(0, (float(spec.by)-1)/2))) * int(spec.quality) + Vector2.ONE * ceilf(absf(spec.distance))
		assert(contents.size == Vector2i(Vector2(spec.width, spec.height) + padding*2) and composite.position == -padding)
		var axes: Array = []
		var operands: Array = []
		var previous: Texture2D = contents.get_texture()
		var blur_texture: Texture2D
		var compositions := 0
		for child in group.get_children():
			if child is SubViewport and child.name.begins_with("FilterPass"):
				assert(child.size == contents.size and child.get_child(0).texture == previous)
				var axis := int(child.get_meta("flash_filter_axis"))
				var material: ShaderMaterial = child.get_child(0).material
				if int(child.get_meta("flash_filter_index")) == 0:
					assert(material.shader == FAMILY_GROUP.INTEGER_BLUR)
					axes.append(axis)
					operands.append(material.get_shader_parameter("blur_size"))
				else:
					assert(material.shader == FAMILY_GROUP.SHADOW_BYTES)
					assert(material.get_shader_parameter("original_texture") == contents.get_texture())
					blur_texture = previous
					compositions += 1
				previous = child.get_texture()
		var expected: Array = []
		for axis in 2:
			if float(spec.bx if axis == 0 else spec.by) > 1:
				for repeat in int(spec.quality):
					expected.append(axis)
		assert(axes == expected and composite.texture == previous and compositions == 1 and blur_texture != null)
		var origin := Vector2i(-padding)
		rows.append({"id": i, "api": spec.api, "axes": axes, "operands": operands, "origin": [origin.x, origin.y],
			"size": [contents.size.x, contents.size.y], "input": _read_samples(contents.get_texture().get_image(), origin, spec),
			"blur": _read_samples(blur_texture.get_image(), origin, spec),
			"filtered": _read_samples(composite.texture.get_image(), origin, spec),
			"final_copy": _read_samples(views[i].get_texture().get_image(), Vector2i.ZERO, spec)})
	FileAccess.open(args[1], FileAccess.WRITE).store_string(JSON.stringify(rows))
	print("INTEGER_SHADOW_ROWS_OK cases=%s production_admitted=false" % groups.size())
	quit(0)

func _source(spec: Dictionary) -> Sprite2D:
	if spec.width == 64:
		return super._source(spec)
	assert(spec.width == 256 and spec.height == 4)
	var bytes := PackedByteArray()
	for y in 4:
		for x in 256:
			for channel in 4:
				bytes.append(x)
	var texture := ImageTexture.create_from_image(Image.create_from_data(256, 4, false, Image.FORMAT_RGBA8, bytes))
	assert(texture.get_image().get_data() == bytes)
	var sprite := Sprite2D.new()
	sprite.centered = false
	sprite.texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
	sprite.texture = texture
	var material := ShaderMaterial.new()
	material.shader = RAW
	sprite.material = material
	return sprite

func _read_samples(image: Image, origin: Vector2i, spec: Dictionary) -> Array:
	if spec.width == 64:
		return _samples(image, origin)
	var result: Array = []
	for x in 256:
		var color := image.get_pixelv(Vector2i(x, 1)-origin)
		result.append([roundi(color.r*255), roundi(color.g*255), roundi(color.b*255), roundi(color.a*255)])
	return result
