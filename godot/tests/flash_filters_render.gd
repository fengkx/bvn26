extends SceneTree

var views: Array = []
var samples: Array = []

func _initialize() -> void:
	_run.call_deferred()

func _run() -> void:
	for amount in [0, 1, 2, 3, 5, 10, 15, 20]:
		for passes in [1, 3]:
			var view := SubViewport.new()
			view.size = Vector2i(160, 160)
			view.transparent_bg = true
			view.render_target_update_mode = SubViewport.UPDATE_ALWAYS
			root.add_child(view)
			var renderer := TimelinePreview.new()
			renderer._definitions = {1: {"type": "DefineShape3Tag",
				"shape_bounds_twips": {"Xmin": 800, "Ymin": 800, "Xmax": 2080, "Ymax": 2080},
				"solid_fills": [{"red": 255, "green": 0, "blue": 0, "alpha": 255}]}}
			renderer._render_placement({"depth": 1, "character_id": 1,
				"filters": [{"type": "BLURFILTER", "blurX": amount, "blurY": 0, "passes": passes}]},
				Transform2D.IDENTITY, 1.0, 0, 1)
			for item in renderer.get_children():
				renderer.remove_child(item)
				view.add_child(item)
			renderer.free()
			views.append(view)
			samples.append({"size": amount, "passes": passes})
	for tick in 8:
		await process_frame
		await RenderingServer.frame_post_draw
	for index in samples.size():
		var pixels: Array = []
		var image: Image = views[index].get_texture().get_image()
		for x in 160:
			pixels.append(roundi(image.get_pixel(x, 70).a * 255))
		samples[index]["alpha"] = pixels
	var args := OS.get_cmdline_user_args()
	if not args.is_empty():
		FileAccess.open(args[0], FileAccess.WRITE).store_string(JSON.stringify(samples))
	var reference_path := ProjectSettings.globalize_path("res://").path_join("../evidence/importer-loud-fail/native-filter-rows.json")
	var reference = JSON.parse_string(FileAccess.get_file_as_string(reference_path))
	if not reference is Array or reference.size() != samples.size():
		push_error("Missing or incomplete native Flash blur reference: " + reference_path)
		quit(1)
		return
	for index in samples.size():
		var actual: Dictionary = samples[index]
		var expected: Dictionary = reference[index]
		if not _matches_reference(actual, expected):
			push_error("Native blur mismatch: size=%s passes=%s" % [actual.size, actual.passes])
			quit(1)
			return
	print("FLASH_FILTERS_REFERENCE_OK cases=16 alpha_samples=2560")
	quit()

func _matches_reference(actual: Dictionary, expected: Dictionary) -> bool:
	if actual["size"] != expected.get("size") or actual["passes"] != expected.get("passes"):
		return false
	var expected_alpha = expected.get("alpha")
	if not expected_alpha is Array or expected_alpha.size() != actual.alpha.size():
		return false
	for x in actual.alpha.size():
		if actual.alpha[x] != expected_alpha[x]:
			return false
	return true
