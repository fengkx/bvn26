extends SceneTree

var samples: Array = []
var views: Array = []

func _initialize() -> void:
	_run.call_deferred()

func _shape(rgb: int, alpha: int) -> Dictionary:
	return {"type": "DefineShape3Tag", "shape_bounds_twips": {"Xmin": 0, "Ymin": 0, "Xmax": 160, "Ymax": 160}, "solid_fills": [{"red": (rgb >> 16) & 255, "green": (rgb >> 8) & 255, "blue": rgb & 255, "alpha": alpha}]}

func _view(mode: int, opacity: int, nested: int = -1) -> void:
	var view := SubViewport.new()
	view.size = Vector2i(8, 8)
	view.transparent_bg = true
	view.render_target_update_mode = SubViewport.UPDATE_ALWAYS
	root.add_child(view)
	var renderer := TimelinePreview.new()
	var children: Array = [{"depth": 1, "character_id": 201}, {"depth": 2, "character_id": 202}]
	renderer._definitions = {200: _shape(3368652, 153), 201: _shape(13402026, 178), 202: _shape(6728294, 102), 203: _shape(8421504, 178)}
	if nested >= 0:
		var inner: Array = [{"depth": 1, "character_id": 202}]
		if nested == 1:
			inner.append({"depth": 2, "character_id": 203})
		renderer._definitions[102] = {"type": "DefineSpriteTag", "display_list_frames": [inner]}
		children[1] = {"depth": 2, "character_id": 102, "blend_mode": 4, "color_transform": {"hasMultTerms": "true", "alphaMultTerm": 128}}
	renderer._definitions[100] = {"type": "DefineSpriteTag", "display_list_frames": [children]}
	renderer._render_display_list([{"depth": 1, "character_id": 200}, {"depth": 2, "character_id": 100, "blend_mode": mode, "color_transform": {"hasMultTerms": "true", "alphaMultTerm": opacity * 256 / 100}}], Transform2D.IDENTITY, 1.0, 0, 1, 0, Color.WHITE, Color(0,0,0,0), [])
	for item in renderer.get_children():
		renderer.remove_child(item)
		view.add_child(item)
	renderer.free()
	views.append(view)
	samples.append({"mode": mode, "opacity": opacity, "nested": nested})

func _run() -> void:
	for mode in [1, 2, 3, 4, 5, 6, 8, 9, 14]:
		for opacity in [25, 50, 75, 100]:
			_view(mode, opacity)
	_view(4, 50, 0)
	_view(4, 50, 1)
	# Nested viewport dependencies need to reach their steady frame.
	for tick in 3:
		await process_frame
		await RenderingServer.frame_post_draw
	var fixture_path := ProjectSettings.globalize_path("res://").path_join("../evidence/characters/pain/visual-parity/review/native-blend-fixture.json")
	var native: Array = JSON.parse_string(FileAccess.get_file_as_string(fixture_path))
	assert(native.size() == samples.size())
	for index in samples.size():
		var c: Color = views[index].get_texture().get_image().get_pixel(4,4)
		samples[index].premultiplied = [roundi(c.r*255), roundi(c.g*255), roundi(c.b*255), roundi(c.a*255)]
		assert(int(native[index].mode) == int(samples[index].mode))
		assert(int(native[index].opacity) == int(samples[index].opacity))
		assert(int(native[index].nested) == int(samples[index].nested))
		# The normal-blend control accumulates up to two 8-bit rounding steps.
		# Apply the same bound to every blend and transparent nesting fixture.
		for channel in 4:
			assert(absi(int(samples[index].premultiplied[channel]) - int(native[index].premultiplied[channel])) <= 2, "Native blend mismatch at sample %d channel %d" % [index, channel])
		print("BLEND_NATIVE_SAMPLE ", JSON.stringify(samples[index]))
	var args := OS.get_cmdline_user_args()
	if not args.is_empty():
		FileAccess.open(args[0], FileAccess.WRITE).store_string(JSON.stringify(samples,"\t"))
	print("FLASH_BLEND_MODES_RENDER_OK ", samples.size())
	quit()
