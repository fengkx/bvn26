extends SceneTree

var views: Array = []
var samples: Array = []

func _initialize() -> void:
	_run.call_deferred()

func _run() -> void:
	var args := OS.get_cmdline_user_args()
	var matrix_path := ProjectSettings.globalize_path("res://").path_join("../tools/probes/flash_filters/color-matrix.json")
	if args.size() > 1:
		matrix_path = args[1]
	var parsed = JSON.parse_string(FileAccess.get_file_as_string(matrix_path))
	if not parsed is Array or parsed.size() != 20:
		push_error("Missing or invalid 20-value filter matrix: " + matrix_path)
		quit(1)
		return
	var matrix: Array = parsed
	for type in ["glow", "matrix", "chain"]:
		for opacity in ([100] if type == "chain" else [100, 50]):
			var view := SubViewport.new()
			view.size = Vector2i(160, 160)
			view.transparent_bg = true
			view.render_target_update_mode = SubViewport.UPDATE_ALWAYS
			root.add_child(view)
			var renderer := TimelinePreview.new()
			renderer._definitions = {1: {"type": "DefineShape3Tag",
				"shape_bounds_twips": {"Xmin": 800, "Ymin": 800, "Xmax": 2080, "Ymax": 2080},
				"solid_fills": [{"red": 204, "green": 127, "blue": 170, "alpha": 204}]}}
			var filters: Array = []
			if type in ["glow", "chain"]:
				filters.append({"type": "GLOWFILTER", "blurX": 5, "blurY": 5, "passes": 1,
					"color": [81.0/255,211.0/255,239.0/255,1.0], "strength": 1.0})
			if type in ["matrix", "chain"]:
				filters.append({"type": "COLORMATRIXFILTER", "matrix": matrix})
			renderer._render_placement({"depth": 1, "character_id": 1, "filters": filters,
				"color_transform": {"hasMultTerms": "true", "alphaMultTerm": opacity * 256 / 100}},
				Transform2D.IDENTITY, 1.0, 0, 1)
			for item in renderer.get_children():
				renderer.remove_child(item)
				view.add_child(item)
			renderer.free()
			views.append(view)
			samples.append({"type": type, "opacity": opacity})
	for tick in 8:
		await process_frame
		await RenderingServer.frame_post_draw
	for index in samples.size():
		var pixels: Array = []
		var image: Image = views[index].get_texture().get_image()
		for x in 160:
			var c := image.get_pixel(x, 70)
			pixels.append([roundi(c.r*255),roundi(c.g*255),roundi(c.b*255),roundi(c.a*255)])
		samples[index]["pixels"] = pixels
	if not args.is_empty():
		FileAccess.open(args[0], FileAccess.WRITE).store_string(JSON.stringify(samples))
	print("FLASH_FILTERS_RENDER_OK ", samples.size())
	quit()
