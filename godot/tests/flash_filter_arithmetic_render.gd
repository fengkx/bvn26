extends SceneTree

const COEFFICIENTS = [-0.5946631, 1.0937881, 0.5008749, 0.4649421, 0.50735843, 0.027699426, 0.10156211, 1.6525338, -0.75409585]

var views: Array[SubViewport] = []
var samples: Array[Dictionary] = []


func _initialize() -> void:
	_run.call_deferred()


func _run() -> void:
	for opacity in [100, 80]:
		for row in 3:
			for component in 4:
				var coefficients := Vector3.ZERO
				for channel in 3:
					if component == channel or component == 3:
						coefficients[channel] = COEFFICIENTS[row * 3 + channel]
				var offset := 9 if component == 3 else (128 if minf(coefficients.x, minf(coefficients.y, coefficients.z)) < 0.0 else 0)
				var matrix := [coefficients.x, coefficients.y, coefficients.z, 0, offset,
					0, 1, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 1, 0]
				var view := SubViewport.new()
				view.size = Vector2i(160, 160)
				view.transparent_bg = true
				view.render_target_update_mode = SubViewport.UPDATE_ALWAYS
				root.add_child(view)
				var renderer := TimelinePreview.new()
				renderer._definitions = {1: {"type": "DefineShape3Tag",
					"shape_bounds_twips": {"Xmin": 800, "Ymin": 800, "Xmax": 2080, "Ymax": 2080},
					"solid_fills": [{"red": 204, "green": 127, "blue": 170, "alpha": 255 * opacity / 100}]}}
				renderer._render_placement({"depth": 1, "character_id": 1,
					"filters": [{"type": "COLORMATRIXFILTER", "matrix": matrix}]},
					Transform2D.IDENTITY, 1.0, 0, 1)
				for item in renderer.get_children():
					renderer.remove_child(item)
					view.add_child(item)
				renderer.free()
				views.append(view)
				samples.append({"opacity": opacity, "row": row, "component": component})
	for tick in 8:
		await process_frame
		await RenderingServer.frame_post_draw
	for index in samples.size():
		var color := views[index].get_texture().get_image().get_pixel(70, 70)
		samples[index]["premultiplied"] = [roundi(color.r * 255), roundi(color.g * 255), roundi(color.b * 255), roundi(color.a * 255)]
	var args := OS.get_cmdline_user_args()
	assert(args.size() == 1, "Expected output JSON path")
	FileAccess.open(args[0], FileAccess.WRITE).store_string(JSON.stringify(samples))
	# This is a measurement, not a parity assertion; run the strict comparator.
	print("FLASH_FILTER_ARITHMETIC_MEASURED cases=24 channels=96")
	quit()
