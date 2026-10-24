extends "res://tests/grouped_blur_rows.gd"
const FAMILY_GROUP = preload("res://tests/grouped_family_filter_group.gd")

func _run() -> void:
	var args := OS.get_cmdline_user_args()
	assert(args.size() == 2)
	var data: Dictionary = JSON.parse_string(FileAccess.get_file_as_string(args[0]))
	assert(data.production_admitted == false and data.cases.size() > 0 and data.cases.size() <= 48)
	for spec in data.cases:
		var view := SubViewport.new()
		view.size = Vector2i(64, 64)
		view.transparent_bg = true
		view.world_2d = World2D.new()
		view.render_target_update_mode = SubViewport.UPDATE_ALWAYS
		root.add_child(view)
		var group := FAMILY_GROUP.new()
		group.set_meta("flash_filters", [{"type": "GLOWFILTER" if spec.family == 0 else "DROPSHADOWFILTER", "blurX": spec.bx, "blurY": spec.by, "passes": spec.quality,
			"color": [81.0/255, 211.0/255, 239.0/255, 1.0], "strength": 1.0, "distance": 0.0, "angle": 0.0}])
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
		assert(group.source_bounds() == Rect2(0, 0, 64, 64))
		var padding := Vector2(ceilf(maxf(0, (float(spec.bx)-1)/2)), ceilf(maxf(0, (float(spec.by)-1)/2))) * int(spec.quality)
		assert(contents.size == Vector2i(Vector2(64, 64) + padding*2) and composite.position == -padding)
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
					assert(material.shader == FAMILY_GROUP.FILTER_SHADER and material.get_shader_parameter("operation") == 1)
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
		rows.append({"id": i, "family": spec.family, "axes": axes, "operands": operands, "origin": [origin.x, origin.y],
			"size": [contents.size.x, contents.size.y], "input": _samples(contents.get_texture().get_image(), origin),
			"blur": _samples(blur_texture.get_image(), origin),
			"filtered": _samples(composite.texture.get_image(), origin),
			"final_copy": _samples(views[i].get_texture().get_image(), Vector2i.ZERO)})
	FileAccess.open(args[1], FileAccess.WRITE).store_string(JSON.stringify(rows))
	print("GROUPED_FAMILY_ROWS_OK cases=%s production_admitted=false" % groups.size())
	quit(0)
