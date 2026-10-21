extends SceneTree

func _initialize() -> void:
	_run.call_deferred()

func _run() -> void:
	var view := SubViewport.new()
	view.size = Vector2i(64, 32)
	view.render_target_update_mode = SubViewport.UPDATE_ALWAYS
	root.add_child(view)
	var background := ColorRect.new()
	background.color = Color(0.25, 0.5, 0.75, 1.0)
	background.size = Vector2(64, 32)
	view.add_child(background)
	var renderer = load("res://timeline_preview.gd").new()
	renderer._definitions = {
		7: {"type": "DefineSpriteTag", "display_list_frames": [[{"character_id": 8, "depth": 1}]]},
		8: {"type": "DefineSpriteTag", "display_list_frames": [[{"character_id": 9, "depth": 1}]]},
		9: {"type": "DefineShape3Tag", "shape_bounds_twips": {"Xmin": 0, "Ymin": 0, "Xmax": 640, "Ymax": 640}, "solid_fills": [{"red": 0, "green": 0, "blue": 0}]}}
	renderer._render_display_list([{"character_id": 7, "depth": 1, "blend_mode": 4}],
		Transform2D.IDENTITY, 1.0, 0, 1, 0, Color.WHITE, Color(0,0,0,0), [])
	var color := Polygon2D.new()
	color.polygon = PackedVector2Array([Vector2(32,0), Vector2(64,0), Vector2(64,32), Vector2(32,32)])
	color.color = Color(0.5, 0.25, 0.5, 0.5)
	renderer._apply_blend(color, 4)
	renderer.add_child(color)
	# Move render children into the viewport without invoking data-loading _ready.
	for item in renderer.get_children():
		renderer.remove_child(item)
		view.add_child(item)
	renderer.free()
	var group_view := SubViewport.new()
	group_view.size = Vector2i(8, 8)
	group_view.render_target_update_mode = SubViewport.UPDATE_ALWAYS
	root.add_child(group_view)
	var gray := ColorRect.new()
	gray.color = Color(128.0/255.0, 128.0/255.0, 128.0/255.0, 1.0)
	gray.size = Vector2(8, 8)
	group_view.add_child(gray)
	var group_renderer = load("res://timeline_preview.gd").new()
	group_renderer._definitions = {
		1: {"type": "DefineSpriteTag", "display_list_frames": [[{"character_id": 2, "depth": 1}, {"character_id": 2, "depth": 2}]]},
		2: {"type": "DefineShape3Tag", "shape_bounds_twips": {"Xmin": 0, "Ymin": 0, "Xmax": 160, "Ymax": 160}, "solid_fills": [{"red": 128, "green": 128, "blue": 128}]}}
	group_renderer._render_display_list([{"character_id": 1, "depth": 1, "blend_mode": 4,
		"color_transform": {"hasMultTerms": "true", "alphaMultTerm": 128}}],
		Transform2D.IDENTITY, 1.0, 0, 1, 0, Color.WHITE, Color(0,0,0,0), [])
	for item in group_renderer.get_children():
		group_renderer.remove_child(item)
		group_view.add_child(item)
	group_renderer.free()
	await process_frame
	await RenderingServer.frame_post_draw
	var image := view.get_texture().get_image()
	var left := image.get_pixel(16,16)
	var right := image.get_pixel(48,16)
	var expected := Color(0.4375, 0.5625, 0.8125, 1.0)
	for component in 3:
		assert(absf(left[component] - background.color[component]) <= 1.0/255.0)
		assert(absf(right[component] - expected[component]) <= 2.0/255.0)
	var grouped := group_view.get_texture().get_image().get_pixel(4,4)
	print("SCREEN_GROUP_PIXEL ", grouped, " bytes=", grouped * 255.0)
	# Native Flash: one OR two opaque gray children at parent alpha 50 -> 159.
	assert(absi(roundi(grouped.r * 255.0) - 159) <= 1, "Screen must compose children before parent alpha")
	print("SCREEN_BLEND_RENDER_OK black neutral alpha compositing")
	quit()
