extends "res://tests/flash_filter_colors_render.gd"
# Keep the pinned source scene and replace only diagnostic buffer composition.
var reciprocal_texture: ImageTexture
var bindings := 0
var native_glow_rect: Rect2

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
	super._initialize()

func _bind_composite(node: Node) -> void:
	if not node is Sprite2D or node.name != "Composite":
		return
	assert(node.get_parent().get_script().resource_path == "res://filter_group.gd")
	var previous: ShaderMaterial = node.material
	assert(previous != null and previous.get_shader_parameter("cached_opacity") == true)
	var material := ShaderMaterial.new()
	material.shader = load("res://tests/native_color_order_composite.gdshader")
	material.set_shader_parameter("opacity_multiplier", floori(float(previous.get_shader_parameter("group_opacity")) * 256.0))
	for parameter in ["post_mul", "post_add"]:
		material.set_shader_parameter(parameter, previous.get_shader_parameter(parameter))
	material.set_shader_parameter("native_reciprocals", reciprocal_texture)
	var filters: Array = node.get_parent().get_meta("flash_filters")
	assert(filters.size() == 1)
	var padding := 0
	if filters[0].type == "GLOWFILTER":
		assert(filters[0].blurX == 5 and filters[0].blurY == 5 and filters[0].passes == 1)
		var group: Node = node.get_parent()
		var bounds: Rect2 = group.source_bounds()
		assert(bounds == Rect2(40, 40, 64, 64))
		var native_padding := bounds.position.x - native_glow_rect.position.x
		assert(native_glow_rect == bounds.grow(native_padding))
		padding = int(native_padding - group.buffer_padding().x)
		assert(padding >= 0)
	else:
		assert(filters[0].type == "COLORMATRIXFILTER")
	material.set_shader_parameter("native_span_padding", padding)
	node.material = material
	var copy := BackBufferCopy.new()
	copy.copy_mode = BackBufferCopy.COPY_MODE_VIEWPORT
	copy.show_behind_parent = true
	node.add_child(copy)
	bindings += 1
	assert(bindings <= 4)
	if bindings == 4:
		print("NATIVE_COLOR_ORDER_BINDINGS_OK groups=4 production_admitted=false")
