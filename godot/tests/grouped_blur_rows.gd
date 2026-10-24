extends SceneTree
const GROUP = preload("res://tests/grouped_blur_filter_group.gd")
const RAW = preload("res://tests/raw_byte_texture.gdshader")
var groups: Array[Node] = []
var views: Array[SubViewport] = []

func _initialize() -> void:
	_run.call_deferred()

func _source(spec: Dictionary) -> Sprite2D:
	var bytes := PackedByteArray()
	bytes.resize(64 * 64 * 4)
	for y in range(24, 41):
		for x in range(24, 41):
			var alpha := int(spec.alpha)
			if spec.pattern == 1 and (x != 32 or y != 32):
				alpha = 0
			elif spec.pattern == 2:
				alpha = floori(float(alpha * (x - 24)) / 16.0)
			for channel in 4:
				bytes[(y*64+x)*4+channel] = alpha
	var image := Image.create_from_data(64, 64, false, Image.FORMAT_RGBA8, bytes)
	var texture := ImageTexture.create_from_image(image)
	assert(texture.get_image().get_data() == bytes)
	var sprite := Sprite2D.new()
	sprite.centered = false
	sprite.texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
	sprite.texture = texture
	var material := ShaderMaterial.new()
	material.shader = RAW
	sprite.material = material
	return sprite

func _samples(image: Image, origin: Vector2i) -> Array:
	var result: Array = []
	for axis in 2:
		for i in 64:
			var point := (Vector2i(i, 32) if axis == 0 else Vector2i(32, i)) - origin
			assert(point.x >= 0 and point.y >= 0 and point.x < image.get_width() and point.y < image.get_height())
			var color := image.get_pixelv(point)
			result.append([roundi(color.r*255), roundi(color.g*255), roundi(color.b*255), roundi(color.a*255)])
	return result

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
		var group := GROUP.new()
		group.set_meta("flash_filters", [{"type": "BLURFILTER", "blurX": spec.bx, "blurY": spec.by, "passes": spec.quality}])
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
		for child in group.get_children():
			if child is SubViewport and child.name.begins_with("FilterPass"):
				assert(child.size == contents.size and child.get_child(0).texture == previous)
				previous = child.get_texture()
				var axis := int(child.get_meta("flash_filter_axis"))
				var material: ShaderMaterial = child.get_child(0).material
				assert(material.shader == GROUP.INTEGER_BLUR)
				axes.append(axis)
				operands.append(material.get_shader_parameter("blur_size"))
		var expected: Array = []
		for axis in 2:
			if float(spec.bx if axis == 0 else spec.by) > 1:
				for repeat in int(spec.quality):
					expected.append(axis)
		assert(axes == expected and composite.texture == previous)
		var origin := Vector2i(-padding)
		rows.append({"id": i, "axes": axes, "operands": operands, "origin": [origin.x, origin.y],
			"size": [contents.size.x, contents.size.y], "input": _samples(contents.get_texture().get_image(), origin),
			"filtered": _samples(composite.texture.get_image(), origin),
			"final_copy": _samples(views[i].get_texture().get_image(), Vector2i.ZERO)})
	FileAccess.open(args[1], FileAccess.WRITE).store_string(JSON.stringify(rows))
	print("GROUPED_BLUR_ROWS_OK cases=%s production_admitted=false" % groups.size())
	quit(0)
