extends SceneTree
# Diagnostic only: retain source fill coverage and raw premultiplied texels.
const Sampler = preload("res://tests/bitmap_sampler_diagnostic.gd")

func _initialize() -> void:
	_run.call_deferred()

func _run() -> void:
	var args := OS.get_cmdline_user_args()
	if args.size() != 2:
		push_error("Expected source fixture and output directory")
		quit(1)
		return
	var fixture = JSON.parse_string(FileAccess.get_file_as_string(args[0]))
	assert(fixture.production_admitted == false)
	assert(int(fixture.fill.fillStyleType) == 65)
	assert(float(fixture.fill_matrix.scaleX) == 20 and float(fixture.fill_matrix.scaleY) == 20)
	var target := Vector2i(int(fixture.target_size[0]), int(fixture.target_size[1]))
	for case_index in fixture.cases.size():
		var c: Dictionary = fixture.cases[case_index]
		var images: Array[Image] = []
		for i in 5:
			images.append(Image.create(target.x, target.y, false, Image.FORMAT_RGBA8))
		# Only the source-proven full rectangle with integral transformed edges is admitted.
		var mask: Array = fixture.fill_masks[0][0]
		var minimum := Vector2(INF, INF)
		var maximum := Vector2(-INF, -INF)
		for point: Array in mask:
			minimum = minimum.min(Vector2(float(point[0]), float(point[1])))
			maximum = maximum.max(Vector2(float(point[0]), float(point[1])))
		var start := minimum * Vector2(c.sx, c.sy) + Vector2(c.tx, c.ty)
		var end := maximum * Vector2(c.sx, c.sy) + Vector2(c.tx, c.ty)
		assert(start == start.floor() and end == end.floor())
		var covered := Rect2i(Vector2i(start), Vector2i(end-start)).intersection(Rect2i(int(c.clip[0]), int(c.clip[1]), int(c.clip[2]), int(c.clip[3]))).intersection(Rect2i(Vector2i.ZERO, target))
		for y in target.y:
			# Transparent outside authored coverage, never clamp the entire destination.
			for x in target.x:
				images[4].set_pixel(x, y, Color(0, 0, 0, 1.0/255))
			if y < covered.position.y or y >= covered.end.y:
				continue
			var spec := {"repeat": false, "width": fixture.width, "height": fixture.height,
				"sx": c.sx, "sy": c.sy, "tx": c.tx, "ty": c.ty, "y": y,
				"left": covered.position.x, "right": covered.end.x, "shape_left": minimum.x}
			var row := Sampler.row(spec)
			for x in range(covered.position.x, covered.end.x):
				var index := x - int(row.left)
				var sx: float = row.xs[index]
				var sy: float = row.y
				var ix := floori(sx)
				var iy := floori(sy)
				for corner in 4:
					var px := clampi(ix + corner % 2, 0, int(fixture.width)-1)
					var py := clampi(iy + corner / 2, 0, int(fixture.height)-1)
					var rgba: Array = fixture.pixels_premultiplied[py*int(fixture.width)+px]
					images[corner].set_pixel(x, y, Color(rgba[0]/255.0, rgba[1]/255.0, rgba[2]/255.0, rgba[3]/255.0))
				images[4].set_pixel(x, y, Color(floor((sx-ix)*256)/255.0, floor((sy-iy)*256)/255.0, row.modes[index]/255.0, 1.0/255))
		var view := SubViewport.new()
		view.size = target
		view.transparent_bg = true
		view.render_target_update_mode = SubViewport.UPDATE_ALWAYS
		root.add_child(view)
		var rect := ColorRect.new()
		rect.size = Vector2(target)
		var material := ShaderMaterial.new()
		material.shader = load("res://tests/bitmap_sampler_diagnostic.gdshader")
		for i in 5:
			material.set_shader_parameter(["c00", "c10", "c01", "c11", "parameters"][i], ImageTexture.create_from_image(images[i]))
		rect.material = material
		view.add_child(rect)
		for tick in 3:
			await process_frame
			await RenderingServer.frame_post_draw
		var rendered := view.get_texture().get_image()
		assert(rendered.save_png(args[1].path_join("case-%d.png" % case_index)) == OK)
		view.queue_free()
		await process_frame
	print("BOUND_BITMAP_DIAGNOSTIC_RENDER_OK cases=%d" % fixture.cases.size())
	quit(0)
