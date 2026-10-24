extends SceneTree
var views: Array = []

func _initialize() -> void:
	_run.call_deferred()

func _shape(rgb: int, alpha: int) -> Dictionary:
	return {"type": "DefineShape3Tag", "shape_bounds_twips": {"Xmin": 0, "Ymin": 0, "Xmax": 160, "Ymax": 160}, "solid_fills": [{"red": (rgb >> 16) & 255, "green": (rgb >> 8) & 255, "blue": rgb & 255, "alpha": alpha}]}

func _run() -> void:
	var args := OS.get_cmdline_user_args()
	var cases: Array = JSON.parse_string(FileAccess.get_file_as_string(args[0]))
	for c in cases:
		var view := SubViewport.new()
		view.size = Vector2i(8, 8)
		view.transparent_bg = true
		view.render_target_update_mode = SubViewport.UPDATE_ALWAYS
		root.add_child(view)
		var renderer := TimelinePreview.new()
		renderer._definitions = {1: _shape(int(c.back), int(c.back_alpha)), 2: _shape(int(c.front), int(c.front_alpha)), 3: {"type": "DefineSpriteTag", "display_list_frames": [[{"depth": 1, "character_id": 2}]]}}
		renderer._render_display_list([{"depth": 1, "character_id": 1}, {"depth": 2, "character_id": 3, "blend_mode": int(c.mode), "color_transform": {"hasMultTerms": "true", "alphaMultTerm": int(c.opacity) * 256 / 100}}], Transform2D.IDENTITY, 1.0, 0, 1, 0, Color.WHITE, Color(0,0,0,0), [])
		for item in renderer.get_children():
			renderer.remove_child(item)
			view.add_child(item)
		renderer.free()
		views.append(view)
	for tick in 3:
		await process_frame
		await RenderingServer.frame_post_draw
	var result: Array = []
	for i in cases.size():
		var pixel: Color = views[i].get_texture().get_image().get_pixel(4, 4)
		result.append([roundi(pixel.r*255), roundi(pixel.g*255), roundi(pixel.b*255), roundi(pixel.a*255)])
	FileAccess.open(args[1], FileAccess.WRITE).store_string(JSON.stringify(result))
	quit()
