extends SceneTree
const LIVE = preload("res://tests/live_rect_cache_filter.gd")
# Source-bound diagnostic only. Fractional coverage with nonzero texels rejects.
const Sampler = preload("res://tests/half_even_bitmap_sampler.gd")

func _initialize() -> void:
	_run.call_deferred()

func _run() -> void:
	var args := OS.get_cmdline_user_args()
	assert(args.size() == 2)
	var fixture: Dictionary = JSON.parse_string(FileAccess.get_file_as_string(args[0]))
	assert(fixture.production_admitted == false)
	assert(int(fixture.fill.fillStyleType) == 65)
	assert(float(fixture.fill_matrix.scaleX) == 20 and float(fixture.fill_matrix.scaleY) == 20)
	assert(float(fixture.fill_matrix.get("rotateSkew0", 0)) == 0 and float(fixture.fill_matrix.get("rotateSkew1", 0)) == 0)
	assert(fixture.fill_masks.size() == 1 and fixture.fill_masks[0].size() == 1)
	var fill_x := float(fixture.fill_matrix.translateX) / 20.0
	var fill_y := float(fixture.fill_matrix.translateY) / 20.0
	var mask: Array = fixture.fill_masks[0][0]
	assert(mask == [[fill_x, fill_y], [fill_x + fixture.width, fill_y], [fill_x + fixture.width, fill_y + fixture.height], [fill_x, fill_y + fixture.height]])
	var width := int(fixture.target_size[0])
	var height := int(fixture.target_size[1])
	for case_index in fixture.cases.size():
		var c: Dictionary = fixture.cases[case_index]
		assert(float(c.sx) > 0 and float(c.sy) > 0)
		# Keep these bounds in double precision; Vector2 narrows them to float32.
		var left: float = fill_x * float(c.sx) + float(c.tx)
		var right: float = (fill_x + float(fixture.width)) * float(c.sx) + float(c.tx)
		var top: float = fill_y * float(c.sy) + float(c.ty)
		var bottom: float = (fill_y + float(fixture.height)) * float(c.sy) + float(c.ty)
		var images: Array[Image] = []
		for i in 5:
			images.append(Image.create(width, height, false, Image.FORMAT_RGBA8))
		images[4].fill(Color(0, 0, 0, 2.0/255))
		for y in range(maxi(0, floori(top)), mini(height, ceili(bottom))):
			var spec := {"repeat": false, "width": fixture.width, "height": fixture.height,
				"sx": c.sx, "sy": c.sy, "tx": c.tx, "ty": c.ty, "y": y,
				"left": maxi(0, ceili(left)), "right": mini(width, floori(right)),
				"shape_left": fill_x, "fill_x": fill_x, "fill_y": fill_y}
			var row := Sampler.row(spec)
			for x in range(maxi(0, floori(left)), mini(width, ceili(right))):
				var index := x - int(row.left)
				var sx: float = row.xs[index] if index >= 0 and index < row.xs.size() else Sampler.axis(c.sx, c.tx, x, int(fixture.width), false) - fill_x
				var sy: float = row.y
				var mode: int = int(row.modes[index]) if index >= 0 and index < row.modes.size() else 0
				var ix := floori(sx)
				var iy := floori(sy)
				var fringe := x < left or x + 1 > right or y < top or y + 1 > bottom
				for corner in 4:
					var px := clampi(ix + corner % 2, 0, int(fixture.width)-1)
					var py := clampi(iy + corner / 2, 0, int(fixture.height)-1)
					var rgba: Array = fixture.pixels_premultiplied[py*int(fixture.width)+px]
					assert(not fringe or (float(rgba[0]) == 0 and float(rgba[1]) == 0 and float(rgba[2]) == 0 and float(rgba[3]) == 0), "Nontransparent fractional coverage: case=%d x=%d y=%d rgba=%s" % [case_index, x, y, rgba])
					images[corner].set_pixel(x, y, Color(rgba[0]/255.0, rgba[1]/255.0, rgba[2]/255.0, rgba[3]/255.0))
				images[4].set_pixel(x, y, Color(floor((sx-ix)*256)/255.0, floor((sy-iy)*256)/255.0, mode/255.0, 2.0/255))
		var view := SubViewport.new()
		view.size = Vector2i(width, height)
		view.transparent_bg = true
		view.render_target_update_mode = SubViewport.UPDATE_ALWAYS
		root.add_child(view)
		var rect := ColorRect.new()
		rect.size = Vector2(width, height)
		var material := ShaderMaterial.new()
		material.shader = load("res://tests/half_even_bitmap_sampler.gdshader")
		for i in 5:
			material.set_shader_parameter(["c00", "c10", "c01", "c11", "parameters"][i], ImageTexture.create_from_image(images[i]))
		rect.material = material
		view.add_child(rect)
		for tick in 3:
			await process_frame
			await RenderingServer.frame_post_draw
		var rendered := view.get_texture().get_image()
		assert(rendered.save_png(args[1].path_join("case-%d.png" % case_index)) == OK)
		await LIVE.render(self, view.get_texture(), fixture.cache_metadata[case_index], args[1], case_index)
		view.queue_free()
		await process_frame
	print("HALF_EVEN_BOUND_BITMAP_RENDER_OK cases=%d" % fixture.cases.size())
	quit(0)
