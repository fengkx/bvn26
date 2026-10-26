extends SceneTree
# Diagnostic only: GPU-produced cache pixels, actual FilterGroup allocation, raw final copy.
const GROUP = preload("res://tests/grouped_blur_filter_group.gd")
const RAW = preload("res://tests/raw_byte_texture.gdshader")

func _initialize() -> void:
	_run.call_deferred()

func _run() -> void:
	var args := OS.get_cmdline_user_args()
	assert(args.size() == 2)
	var data: Dictionary = JSON.parse_string(FileAccess.get_file_as_string(args[0]))
	assert(data.production_admitted == false)
	var groups: Array[Node] = []
	var views: Array[SubViewport] = []
	for i in data.cases.size():
		var spec: Dictionary = data.cases[i]
		var image := Image.load_from_file(spec.cache_png)
		assert(image.get_size() == Vector2i(spec.local_size[0], spec.local_size[1]))
		var texture := ImageTexture.create_from_image(image)
		assert(texture.get_image().get_data() == image.get_data())
		var sprite := Sprite2D.new()
		sprite.centered = false
		sprite.texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
		sprite.texture = texture
		var raw := ShaderMaterial.new()
		raw.shader = RAW
		sprite.material = raw
		var view := SubViewport.new()
		view.size = Vector2i(600, 400)
		view.transparent_bg = true
		view.world_2d = World2D.new()
		view.render_target_update_mode = SubViewport.UPDATE_ALWAYS
		root.add_child(view)
		var group := GROUP.new()
		group.set_meta("flash_filters", [{"type": "BLURFILTER", "blurX": 15.0, "blurY": 0.0, "passes": 3}])
		var composite: Sprite2D = group.setup([sprite], 1.0)
		composite.material = raw
		group.add_child(composite)
		group.position = Vector2(spec.x_bounds[0], spec.y_bounds[0])
		view.add_child(group)
		groups.append(group)
		views.append(view)
	for tick in 12:
		await process_frame
		await RenderingServer.frame_post_draw
	var allocations: Array = []
	for i in groups.size():
		var group: Node = groups[i]
		var spec: Dictionary = data.cases[i]
		var contents: SubViewport = group.get_node("Contents")
		var composite: Sprite2D = group.get_node("Composite")
		assert(group.source_bounds() == Rect2(0, 0, spec.local_size[0], spec.local_size[1]))
		assert(contents.size == Vector2i(spec.local_size[0] + 42, spec.local_size[1]))
		assert(composite.position == Vector2(-21, 0))
		var axes: Array = []
		var previous: Texture2D = contents.get_texture()
		for child in group.get_children():
			if child is SubViewport and child.name.begins_with("FilterPass"):
				assert(child.size == contents.size and child.get_child(0).texture == previous)
				assert(child.get_child(0).material.shader == GROUP.INTEGER_BLUR)
				assert(child.get_child(0).material.get_shader_parameter("blur_size") == 15.0)
				axes.append(int(child.get_meta("flash_filter_axis")))
				previous = child.get_texture()
		assert(axes == [0, 0, 0] and composite.texture == previous)
		assert(contents.get_texture().get_image().save_png(args[1].path_join("input-%d.png" % i)) == OK)
		assert(composite.texture.get_image().save_png(args[1].path_join("filtered-%d.png" % i)) == OK)
		assert(views[i].get_texture().get_image().save_png(args[1].path_join("final-%d.png" % i)) == OK)
		allocations.append({"size": [contents.size.x, contents.size.y], "padding": [21, 0], "axes": axes})
	FileAccess.open(args[1].path_join("allocations.json"), FileAccess.WRITE).store_string(JSON.stringify(allocations))
	for view in views:
		view.queue_free()
	await process_frame
	print("SOURCE_CACHE_FILTER_OK production_admitted=false")
	quit(0)
