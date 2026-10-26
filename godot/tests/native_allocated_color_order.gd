extends "res://tests/flash_filter_colors_render.gd"
# Keep the pinned source scene and replace only diagnostic buffer composition.
var reciprocal_texture: ImageTexture
var bindings := 0
var native_glow_rect: Rect2
var groups: Array[Node] = []
var tick := 0

func _initialize() -> void:
	var args := OS.get_cmdline_user_args()
	assert(args.size() == 4 and args[2] == "order")
	var fixture: Dictionary = JSON.parse_string(FileAccess.get_file_as_string(args[3]))
	assert(fixture.production_admitted == false and fixture.cpu_arithmetic_passed == true)
	var bounds: Array = fixture.native_glow_rect
	native_glow_rect = Rect2(bounds[0], bounds[1], bounds[2], bounds[3])
	var bytes := PackedByteArray()
	bytes.resize(256 * 4)
	for i in 256:
		bytes.encode_float(i * 4, float(fixture.native_reciprocals[i]))
	reciprocal_texture = ImageTexture.create_from_image(Image.create_from_data(256, 1, false, Image.FORMAT_RF, bytes))
	assert(reciprocal_texture.get_image().get_data() == bytes)
	node_added.connect(_bind_composite)
	process_frame.connect(_record_allocation)
	super._initialize()

func _bind_composite(node: Node) -> void:
	if not node is Sprite2D or node.name != "Composite":
		return
	assert(node.get_parent().get_script().resource_path == "res://filter_group.gd")
	var previous: ShaderMaterial = node.material
	assert(previous != null and previous.get_shader_parameter("cached_opacity") == true)
	var material := ShaderMaterial.new()
	material.shader = load("res://tests/native_nested_filter_composite.gdshader")
	material.set_shader_parameter("opacity_multiplier", floori(float(previous.get_shader_parameter("group_opacity")) * 256.0))
	for parameter in ["post_mul", "post_add"]:
		material.set_shader_parameter(parameter, previous.get_shader_parameter(parameter))
	material.set_shader_parameter("native_reciprocals", reciprocal_texture)
	var filters: Array = node.get_parent().get_meta("flash_filters")
	assert(filters.size() == 1)
	var group: Node = node.get_parent()
	if filters[0].type == "GLOWFILTER":
		assert(group.source_bounds() == Rect2(40, 40, 64, 64))
		# The base group stores its state in child nodes and metadata, not script fields.
		group.set_meta("native_filter_rect", native_glow_rect)
		group.set_script(load("res://tests/native_extent_filter_group.gd"))
	else:
		assert(filters[0].type == "COLORMATRIXFILTER")
	groups.append(group)
	node.material = material
	var copy := BackBufferCopy.new()
	copy.copy_mode = BackBufferCopy.COPY_MODE_VIEWPORT
	copy.show_behind_parent = true
	node.add_child(copy)
	bindings += 1
	assert(bindings <= 4)
	if bindings == 4:
		print("NATIVE_COLOR_ORDER_BINDINGS_OK groups=4 production_admitted=false")

func _record_allocation() -> void:
	tick += 1
	if tick != 7:
		return
	assert(groups.size() == 4)
	var records: Array = []
	var output := OS.get_cmdline_user_args()[0].get_base_dir()
	for i in groups.size():
		var group: Node = groups[i]
		var contents: SubViewport = group.get_node("Contents")
		var composite: Sprite2D = group.get_node("Composite")
		var expected := Vector2i(70, 70) if i < 2 else Vector2i(64, 64)
		assert(contents.size == expected)
		var expected_origin := Vector2(37, 37) if i < 2 else Vector2(40, 40)
		assert(composite.position == expected_origin)
		assert(contents.get_texture().get_image().save_png(output.path_join("input-%d.png" % i)) == OK)
		assert(composite.texture.get_image().save_png(output.path_join("filtered-%d.png" % i)) == OK)
		var passes: Array = []
		for child in group.get_children():
			if child is SubViewport and child.name.begins_with("FilterPass"):
				assert(child.size == expected)
				passes.append([child.size.x, child.size.y])
		records.append({"case": i, "size": [contents.size.x, contents.size.y],
			"origin": [composite.position.x, composite.position.y], "passes": passes})
	FileAccess.open(output.path_join("buffers.json"), FileAccess.WRITE).store_string(JSON.stringify(records))
	print("NATIVE_EXTENT_ALLOCATION_OK groups=4 production_admitted=false")
