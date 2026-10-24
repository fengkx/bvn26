extends SceneTree
var views: Array = []
func _initialize() -> void:
	_run.call_deferred()
func _run() -> void:
	var args := OS.get_cmdline_user_args()
	var cases: Array = JSON.parse_string(FileAccess.get_file_as_string(args[0]))
	for c in cases:
		var view := SubViewport.new()
		view.size = Vector2i(32, 32)
		view.transparent_bg = true
		view.render_target_update_mode = SubViewport.UPDATE_ALWAYS
		root.add_child(view)
		var renderer := TimelinePreview.new()
		renderer._definitions = {1: {"type": "DefineShape3Tag", "shape_bounds_twips": {"Xmin": 160, "Ymin": 160, "Xmax": 320, "Ymax": 320}, "solid_fills": [{"red": 255, "green": 255, "blue": 255, "alpha": 255}]}}
		renderer._render_placement({"depth": 1, "character_id": 1, "filters": [{"type": "DROPSHADOWFILTER", "blurX": 3, "blurY": 3, "passes": 1, "color": [0,0,0,1], "strength": 3, "angle": c.angle, "distance": c.distance}]}, Transform2D.IDENTITY, 1.0, 0, 1)
		for item in renderer.get_children():
			renderer.remove_child(item)
			view.add_child(item)
		renderer.free()
		views.append(view)
	for tick in 8:
		await process_frame
		await RenderingServer.frame_post_draw
	var results: Array = []
	for i in cases.size():
		var pixels: Array = []
		var image: Image = views[i].get_texture().get_image()
		for y in 32:
			for x in 32:
				var c := image.get_pixel(x,y)
				pixels.append([roundi(c.r*255),roundi(c.g*255),roundi(c.b*255),roundi(c.a*255)])
		results.append(pixels)
	FileAccess.open(args[1], FileAccess.WRITE).store_string(JSON.stringify(results))
	quit()
