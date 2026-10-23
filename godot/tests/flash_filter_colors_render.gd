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
	var order_test := args.size() > 2 and args[2] == "order"
	for type in (["glow", "matrix"] if order_test else ["glow", "matrix", "chain"]):
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
			var cx := {"hasMultTerms": "true", "alphaMultTerm": opacity * 256 / 100}
			if order_test:
				cx.merge({"hasAddTerms": "true", "redMultTerm": 0, "greenMultTerm": 0,
					"blueMultTerm": 0, "redAddTerm": 57, "greenAddTerm": 148, "blueAddTerm": 230})
			renderer._render_placement({"depth": 1, "character_id": 1, "filters": filters,
				"color_transform": cx},
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
	var reference_path := ProjectSettings.globalize_path("res://").path_join("../evidence/importer-loud-fail/r03/" + ("native-order-rows.json" if order_test else "native-color-rows.json"))
	var reference = JSON.parse_string(FileAccess.get_file_as_string(reference_path))
	if not reference is Array or reference.size() != samples.size():
		push_error("Missing native color reference: " + reference_path)
		quit(1)
		return
	for index in (range(2, 4) if order_test else range(2)):
		var expected: Dictionary = reference[index]
		var actual: Dictionary = samples[index]
		if expected.type != actual.type or expected.opacity != actual.opacity:
			push_error("Mismatched native GlowFilter case identity")
			quit(1)
			return
		for x in actual.pixels.size():
			for channel in 4:
				if actual.pixels[x][channel] != expected.premultiplied[x][channel]:
					push_error("Native filter mismatch: opacity=%s x=%s channel=%s" % [actual.opacity, x, channel])
					quit(1)
					return
	print("FLASH_MATRIX_CXFORM_REFERENCE_OK cases=2 channel_samples=1280" if order_test else "FLASH_GLOW_REFERENCE_OK cases=2 channel_samples=1280")
	print("FLASH_FILTERS_RENDER_OK ", samples.size())
	quit()
