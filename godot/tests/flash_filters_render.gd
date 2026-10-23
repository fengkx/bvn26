extends SceneTree

var views: Array = []
var samples: Array = []

func _initialize() -> void:
	_run.call_deferred()

func _run() -> void:
	var args := OS.get_cmdline_user_args()
	var mode := args[1] if args.size() > 1 else "large"
	var names := {"large": "native-filter-rows.json", "small": "native-small-filter-rows.json",
		"bounds": "native-bounds-filter-rows.json"}
	if not names.has(mode):
		push_error("Unknown blur fixture: " + mode)
		quit(1)
		return
	var reference_path := ProjectSettings.globalize_path("res://").path_join("../evidence/importer-loud-fail/" + names[mode])
	var reference = JSON.parse_string(FileAccess.get_file_as_string(reference_path))
	var expected_count := 210 if mode == "bounds" else 16
	if not reference is Array or reference.size() != expected_count:
		push_error("Missing or incomplete native Flash blur reference: " + reference_path)
		quit(1)
		return
	var extent := 70 if mode == "small" else 160
	var start := 30 if mode == "small" else (60 if mode == "bounds" else 40)
	var sample_y := 34 if mode == "small" else (80 if mode == "bounds" else 70)
	for expected: Dictionary in reference:
		var end_x := start + int(expected.width) if mode == "bounds" else (38 if mode == "small" else 104)
		var end_y := 100 if mode == "bounds" else end_x
		var view := SubViewport.new()
		view.size = Vector2i(extent, extent)
		view.transparent_bg = true
		view.render_target_update_mode = SubViewport.UPDATE_ALWAYS
		root.add_child(view)
		var renderer := TimelinePreview.new()
		renderer._definitions = {1: {"type": "DefineShape3Tag",
			"shape_bounds_twips": {"Xmin": start * 20, "Ymin": start * 20, "Xmax": end_x * 20, "Ymax": end_y * 20},
			"solid_fills": [{"red": 255, "green": 0, "blue": 0, "alpha": 255}]}}
		renderer._render_placement({"depth": 1, "character_id": 1,
			"filters": [{"type": "BLURFILTER", "blurX": expected["size"], "blurY": 0, "passes": expected.passes}]},
			Transform2D.IDENTITY, 1.0, 0, 1)
		for item in renderer.get_children():
			renderer.remove_child(item)
			view.add_child(item)
		renderer.free()
		views.append(view)
		var sample := expected.duplicate()
		sample.erase("alpha")
		samples.append(sample)
	for tick in 8:
		await process_frame
		await RenderingServer.frame_post_draw
	for index in samples.size():
		var pixels: Array = []
		var image: Image = views[index].get_texture().get_image()
		for x in extent:
			pixels.append(roundi(image.get_pixel(x, sample_y).a * 255))
		samples[index]["alpha"] = pixels
	if not args.is_empty():
		FileAccess.open(args[0], FileAccess.WRITE).store_string(JSON.stringify(samples))
	for index in samples.size():
		var actual: Dictionary = samples[index]
		var expected: Dictionary = reference[index]
		if not _matches_reference(actual, expected):
			push_error("Native blur mismatch: size=%s passes=%s" % [actual.size, actual.passes])
			quit(1)
			return
	print("FLASH_FILTERS_REFERENCE_OK cases=", samples.size(), " alpha_samples=", extent * samples.size())
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
