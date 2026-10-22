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
	print("FLASH_FILTERS_RENDER_OK ", samples.size())
	quit()
