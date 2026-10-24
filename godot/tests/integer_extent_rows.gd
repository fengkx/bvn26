extends SceneTree
var data: Dictionary
var reciprocal_texture: ImageTexture
var groups: Array[Node] = []
var views: Array[SubViewport] = []

func _initialize() -> void:
	_run.call_deferred()

func _bind(node: Node) -> void:
	if not node is Sprite2D or node.name != "Composite":
		return
	var group: Node = node.get_parent()
	assert(group.get_script().resource_path == "res://filter_group.gd")
	var spec: Dictionary = data.cases[groups.size()]
	assert(group.source_bounds() == Rect2(spec.left, 40, spec.width, 64))
	var r: Array = spec.rect
	group.set_meta("native_filter_rect", Rect2(r[0], r[1], r[2], r[3]))
	group.set_script(load("res://tests/integer_extent_filter_group.gd"))
	var previous: ShaderMaterial = node.material
	assert(previous.get_shader_parameter("cached_opacity") == true)
	var material := ShaderMaterial.new()
	material.shader = load("res://tests/native_nested_filter_composite.gdshader")
	for parameter in ["post_mul", "post_add"]:
		material.set_shader_parameter(parameter, previous.get_shader_parameter(parameter))
	material.set_shader_parameter("opacity_multiplier", floori(float(previous.get_shader_parameter("group_opacity")) * 256))
	material.set_shader_parameter("native_reciprocals", reciprocal_texture)
	node.material = material
	var copy := BackBufferCopy.new()
	copy.copy_mode = BackBufferCopy.COPY_MODE_VIEWPORT
	copy.show_behind_parent = true
	node.add_child(copy)
	groups.append(group)

func _row(image: Image, origin: Vector2i) -> Array:
	var result: Array = []
	for x in 160:
		var p := Vector2i(x, 70) - origin
		var c := Color(0, 0, 0, 0)
		if p.x >= 0 and p.y >= 0 and p.x < image.get_width() and p.y < image.get_height():
			c = image.get_pixelv(p)
		result.append([roundi(c.r*255), roundi(c.g*255), roundi(c.b*255), roundi(c.a*255)])
	return result

func _run() -> void:
	var args := OS.get_cmdline_user_args()
	assert(args.size() == 2)
	data = JSON.parse_string(FileAccess.get_file_as_string(args[0]))
	assert(data.production_admitted == false and data.cpu_arithmetic_passed == true and data.cases.size() > 0 and data.cases.size() <= 64)
	var bytes := PackedByteArray()
	bytes.resize(1024)
	for i in 256:
		bytes.encode_float(i*4, float(data.native_reciprocals[i]))
	reciprocal_texture = ImageTexture.create_from_image(Image.create_from_data(256, 1, false, Image.FORMAT_RF, bytes))
	assert(reciprocal_texture.get_image().get_data() == bytes)
	node_added.connect(_bind)
	for spec in data.cases:
		var view := SubViewport.new()
		view.size = Vector2i(160, 160)
		view.transparent_bg = true
		view.render_target_update_mode = SubViewport.UPDATE_ALWAYS
		root.add_child(view)
		var renderer := TimelinePreview.new()
		renderer._definitions = {1: {"type": "DefineShape3Tag", "shape_bounds_twips": {
			"Xmin": spec.left*20, "Ymin": 800, "Xmax": (spec.left+spec.width)*20, "Ymax": 2080},
			"solid_fills": [{"red": 204, "green": 127, "blue": 170, "alpha": spec.alpha}]}}
		renderer._render_placement({"depth": 1, "character_id": 1, "filters": [{"type": "GLOWFILTER",
			"blurX": spec.kernel, "blurY": spec.kernel, "passes": 1, "color": [81.0/255, 211.0/255, 239.0/255, 1.0], "strength": 1.0}],
			"color_transform": {"hasMultTerms": "true", "hasAddTerms": "true", "redMultTerm": 0,
			"greenMultTerm": 0, "blueMultTerm": 0, "alphaMultTerm": spec.opacity*256/100,
			"redAddTerm": 57, "greenAddTerm": 148, "blueAddTerm": 230}}, Transform2D.IDENTITY, 1.0, 0, 1)
		for item in renderer.get_children():
			renderer.remove_child(item)
			view.add_child(item)
		renderer.free()
		views.append(view)
	for tick in 8:
		await process_frame
		await RenderingServer.frame_post_draw
	assert(groups.size() == data.cases.size())
	var rows: Array = []
	for i in groups.size():
		var group: Node = groups[i]
		var rect: Array = data.cases[i].rect
		var contents: SubViewport = group.get_node("Contents")
		var composite: Sprite2D = group.get_node("Composite")
		assert(contents.size == Vector2i(rect[2], rect[3]) and composite.position == Vector2(rect[0], rect[1]))
		var passes := 0
		for child in group.get_children():
			if child is SubViewport and child.name.begins_with("FilterPass"):
				assert(child.size == contents.size)
				passes += 1
		assert(passes == (3 if data.cases[i].kernel > 1 else 1))
		var origin := Vector2i(rect[0], rect[1])
		rows.append({"id": i, "rect": rect, "input": _row(contents.get_texture().get_image(), origin),
			"filtered": _row(composite.texture.get_image(), origin),
			"final": _row(views[i].get_texture().get_image(), Vector2i.ZERO)})
	FileAccess.open(args[1], FileAccess.WRITE).store_string(JSON.stringify(rows))
	print("INTEGER_EXTENT_ROWS_OK cases=%s production_admitted=false" % groups.size())
	quit(0)
