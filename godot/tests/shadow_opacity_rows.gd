extends "res://tests/colored_shadow_rows.gd"
const PREVIEW = preload("res://tests/nested_buffer_preview.gd")
var layers: Array = []

func _view() -> SubViewport:
	var view := SubViewport.new()
	view.size = Vector2i(64, 64)
	view.transparent_bg = true
	view.world_2d = World2D.new()
	view.render_target_update_mode = SubViewport.UPDATE_ALWAYS
	root.add_child(view)
	return view

func _sprite(texture: Texture2D) -> Sprite2D:
	var sprite := Sprite2D.new()
	sprite.centered = false
	sprite.texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
	sprite.texture = texture
	return sprite

func _solid(pixel: Array) -> Texture2D:
	var image := Image.create(64, 64, false, Image.FORMAT_RGBA8)
	image.fill(Color8(pixel[0], pixel[1], pixel[2], pixel[3]))
	var texture := ImageTexture.create_from_image(image)
	assert(texture.get_image().get_data() == image.get_data())
	return texture

func _preview() -> Node:
	var preview := PREVIEW.new()
	preview.autoplay = false
	preview.play_timeline_sounds = false
	preview.show_collision_shapes = false
	return preview

func _add(preview: Node, texture: Texture2D) -> Sprite2D:
	var sprite := _sprite(texture)
	preview._apply_blend(sprite, 1)
	preview.add_child(sprite)
	return sprite

func _run() -> void:
	var args := OS.get_cmdline_user_args()
	assert(args.size() == 2)
	var data: Dictionary = JSON.parse_string(FileAccess.get_file_as_string(args[0]))
	assert(data.production_admitted == false and data.cases.size() > 0 and data.cases.size() <= 24)
	assert(data.copy_order in ["fresh", "stale"])
	for spec in data.cases:
		var f: Dictionary = spec.filter
		var filtered_view := _view()
		var filter_group := FAMILY_GROUP.new()
		filter_group.set_meta("flash_filters", [{"type": "DROPSHADOWFILTER", "blurX": f.bx, "blurY": f.by, "passes": f.quality,
			"color": [f.color[0]/255.0, f.color[1]/255.0, f.color[2]/255.0, f.alpha_byte/255.0],
			"strength": f.strength, "distance": f.distance, "angle": deg_to_rad(f.angle)}])
		filter_group.set_meta("shadow_diagnostic", f)
		var filter_composite: Sprite2D = filter_group.setup([_source(f)], 1.0)
		var material := ShaderMaterial.new()
		material.shader = RAW
		filter_composite.material = material
		filter_group.add_child(filter_composite)
		filtered_view.add_child(filter_group)
		var child_view := _view()
		var child_preview := _preview()
		var filter_leaf := _add(child_preview, filtered_view.get_texture())
		child_preview._compose_blend_group(0, float(spec.child_opacity)/100.0, 0, 1, [], true)
		assert(child_preview.diagnostic_groups.size() == 1)
		var child: Node = child_preview.diagnostic_groups[0]
		child_view.add_child(child_preview)
		var final_view := _view()
		var preview := _preview()
		var back := _solid(spec.back)
		var middle := _solid(spec.middle)
		_add(preview, back)
		_add(preview, middle)
		var child_leaf := _add(preview, child_view.get_texture())
		preview._compose_blend_group(1, float(spec.parent_opacity)/100.0, 0, 1, [], true)
		assert(preview.diagnostic_groups.size() == 1)
		var parent: Node = preview.diagnostic_groups[0]
		if data.copy_order == "stale":
			var copy := child_leaf.get_node("DestinationCopy")
			child_leaf.remove_child(copy)
			copy.set_meta("blend_source_transform", Transform2D.IDENTITY)
			parent.get_node("Contents").add_child(copy)
			parent.get_node("Contents").move_child(copy, 0)
		final_view.add_child(preview)
		layers.append({"filter": filter_group, "filtered": filtered_view, "child_view": child_view,
			"child": child, "parent": parent, "final": final_view, "middle": middle, "back": back,
			"filter_leaf": filter_leaf, "child_leaf": child_leaf})
	for tick in 16:
		await process_frame
		await RenderingServer.frame_post_draw
	var rows: Array = []
	for i in layers.size():
		var layer: Dictionary = layers[i]
		var f: Dictionary = data.cases[i].filter
		var padding := Vector2(ceilf(maxf(0, (float(f.bx)-1)/2)), ceilf(maxf(0, (float(f.by)-1)/2))) * int(f.quality) + Vector2.ONE * ceilf(absf(f.distance))
		assert(layer.filter.get_node("Contents").size == Vector2i(Vector2(64,64)+padding*2))
		assert(layer.filter.source_bounds() == Rect2(0,0,64,64))
		assert(layer.filter_leaf.texture == layer.filtered.get_texture())
		assert(layer.child_leaf.texture == layer.child_view.get_texture())
		for group in [layer.child, layer.parent]:
			assert(group.get_script().resource_path == "res://blend_group.gd")
			assert(group.get_node("Contents").size == Vector2i(64,64))
			assert(group.get_node("Composite").position == Vector2.ZERO)
			assert(group.get_node("Composite").texture == group.get_node("Contents").get_texture())
		rows.append({"id": i, "copy_order": data.copy_order, "sizes": [[64,64],[64,64]],
			"input": _samples(layer.filter.get_node("Contents").get_texture().get_image(), Vector2i(-padding)),
			"middle": _samples(layer.middle.get_image(), Vector2i.ZERO), "back": _samples(layer.back.get_image(), Vector2i.ZERO),
			"filtered": _samples(layer.filtered.get_texture().get_image(), Vector2i.ZERO),
			"child": _samples(layer.child_view.get_texture().get_image(), Vector2i.ZERO),
			"parent": _samples(layer.parent.get_node("Contents").get_texture().get_image(), Vector2i.ZERO),
			"final": _samples(layer.final.get_texture().get_image(), Vector2i.ZERO)})
	FileAccess.open(args[1], FileAccess.WRITE).store_string(JSON.stringify(rows))
	print("SHADOW_OPACITY_ROWS_OK cases=%s order=%s production_admitted=false" % [layers.size(), data.copy_order])
	quit(0)
