extends SceneTree

func _initialize() -> void:
	_run.call_deferred()

func _run() -> void:
	var reference_path := ProjectSettings.globalize_path("res://").path_join("../evidence/importer-loud-fail/r03/raster-reference.json")
	var reference = JSON.parse_string(FileAccess.get_file_as_string(reference_path))
	if not reference is Array or reference.size() != 36:
		push_error("Missing native cached raster reference")
		quit(1)
		return
	var views: Array[SubViewport] = []
	for sample: Dictionary in reference:
		var color := int(sample.color)
		var view := SubViewport.new()
		view.size = Vector2i(4, 4)
		view.transparent_bg = true
		view.render_target_update_mode = SubViewport.UPDATE_ALWAYS
		root.add_child(view)
		var renderer := TimelinePreview.new()
		renderer._definitions = {1: {"type": "DefineShape3Tag",
			"shape_bounds_twips": {"Xmin": 0, "Ymin": 0, "Xmax": 80, "Ymax": 80},
			"solid_fills": [{"red": (color >> 16) & 255, "green": (color >> 8) & 255,
				"blue": color & 255, "alpha": int(sample.fill_alpha)}]}}
		renderer._render_placement({"depth": 1, "character_id": 1, "cache_as_bitmap": true},
			Transform2D.IDENTITY, 1.0, 0, 1)
		for item in renderer.get_children():
			renderer.remove_child(item)
			view.add_child(item)
		renderer.free()
		views.append(view)
	for tick in 8:
		await process_frame
		await RenderingServer.frame_post_draw
	for index in views.size():
		var c := views[index].get_texture().get_image().get_pixel(2, 2)
		var actual := [roundi(c.r * 255), roundi(c.g * 255), roundi(c.b * 255), roundi(c.a * 255)]
		for channel in 4:
			if actual[channel] != reference[index].premultiplied[channel]:
				push_error("Native cached raster mismatch at case %s channel %s" % [index, channel])
				quit(1)
				return
	print("FLASH_FILTER_RASTER_REFERENCE_OK cases=36 channel_samples=144")
	quit()
