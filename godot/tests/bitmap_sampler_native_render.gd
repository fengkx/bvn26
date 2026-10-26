extends SceneTree
const Sampler = preload("res://tests/bitmap_sampler_diagnostic.gd")

func _initialize() -> void:
	_run.call_deferred()

func _run() -> void:
	var args := OS.get_cmdline_user_args()
	if args.size() != 2:
		push_error("Expected fixture JSON and report JSON")
		quit(1)
		return
	var fixture = JSON.parse_string(FileAccess.get_file_as_string(args[0]))
	if not fixture is Dictionary or fixture.get("format") != "bitmap-native-godot-v1":
		push_error("Invalid native bitmap fixture")
		quit(1)
		return
	var count := int(fixture.samples)
	var width := 256
	var height := int(ceil(float(count) / width))
	var images: Array[Image] = []
	for i in 5:
		images.append(Image.create(width, height, false, Image.FORMAT_RGBA8))
	var expected: Array = []
	var identities: Array = []
	for c: Dictionary in fixture.cases:
		var row := Sampler.row(c)
		var pixels: Array = c.get("row_expected", [c.get("expected")])
		for offset in pixels.size():
			var x := int(c.left) + offset if c.has("row_expected") else int(c.x)
			var index := x - int(row.left)
			if index < 0 or index >= row.xs.size():
				push_error("Sample outside admitted coverage")
				quit(1)
				return
			var sx: float = row.xs[index]
			var sy: float = row.y
			var ix := int(floor(sx))
			var iy := int(floor(sy))
			var target := Vector2i(expected.size() % width, expected.size() / width)
			for corner in 4:
				images[corner].set_pixelv(target, Sampler.texel(c, ix + corner % 2, iy + corner / 2))
			images[4].set_pixelv(target, Color(floor((sx-ix)*256) / 255.0, floor((sy-iy)*256) / 255.0, float(row.modes[index]) / 255.0, (1.0 if bool(c.get("straight_rgba", false)) else 0.0) / 255.0))
			var native: Array[int] = []
			for channel in pixels[offset]:
				assert(float(channel) == floor(float(channel)))
				native.append(int(channel))
			expected.append(native)
			identities.append({"suite": c.suite, "case": identities.size(), "x": x, "y": c.y})
	if expected.size() != count:
		push_error("Native sample count mismatch")
		quit(1)
		return
	var view := SubViewport.new()
	view.size = Vector2i(width, height)
	view.transparent_bg = true
	view.render_target_update_mode = SubViewport.UPDATE_ALWAYS
	root.add_child(view)
	var rect := ColorRect.new()
	rect.size = Vector2(width, height)
	var material := ShaderMaterial.new()
	material.shader = load("res://tests/bitmap_sampler_diagnostic.gdshader")
	for i in 5:
		material.set_shader_parameter(["c00", "c10", "c01", "c11", "parameters"][i], ImageTexture.create_from_image(images[i]))
	rect.material = material
	view.add_child(rect)
	for tick in 4:
		await process_frame
		await RenderingServer.frame_post_draw
	var rendered := view.get_texture().get_image()
	var failures: Array = []
	var scores: Dictionary = {}
	for i in count:
		var color := rendered.get_pixel(i % width, i / width)
		var actual := [roundi(color.r*255), roundi(color.g*255), roundi(color.b*255), roundi(color.a*255)]
		var suite: String = identities[i].suite
		if not scores.has(suite):
			scores[suite] = {"samples": 0, "exact": 0}
		scores[suite].samples += 1
		if actual == expected[i]:
			scores[suite].exact += 1
		else:
			failures.append({"identity": identities[i], "native": expected[i], "actual": actual})
	rendered.save_png(args[1].get_basename() + ".png")
	var report := {"fixture_sha256": FileAccess.get_sha256(args[0]), "samples": count, "exact": count-failures.size(), "scores": scores, "failures": failures, "production_admitted": false}
	FileAccess.open(args[1], FileAccess.WRITE).store_string(JSON.stringify(report, "\t") + "\n")
	print("BITMAP_NATIVE_GPU_REFERENCE_%s samples=%d exact=%d" % ["OK" if failures.is_empty() else "FAIL", count, count-failures.size()])
	quit(0 if failures.is_empty() else 1)
