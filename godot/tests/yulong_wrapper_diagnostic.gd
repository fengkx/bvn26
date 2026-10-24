extends SceneTree
# Whole-wrapper diagnostic only. Fractional coverage remains a measured candidate.
const Sampler = preload("res://tests/bitmap_sampler_diagnostic.gd")
var views: Array[SubViewport] = []

func _initialize() -> void:
	_run.call_deferred()

func _pass(images: Dictionary, shader: Shader, uniforms: Dictionary, size: Vector2i) -> SubViewport:
	var view := SubViewport.new()
	view.size = size
	view.transparent_bg = true
	view.world_2d = World2D.new()
	view.render_target_update_mode = SubViewport.UPDATE_ALWAYS
	root.add_child(view)
	var sprite := Sprite2D.new()
	sprite.centered = false
	sprite.texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
	sprite.texture = images.get("TEXTURE", ImageTexture.create_from_image(Image.create(size.x, size.y, false, Image.FORMAT_RGBA8)))
	var material := ShaderMaterial.new()
	material.shader = shader
	for key in images:
		if key != "TEXTURE":
			material.set_shader_parameter(key, images[key])
	for key in uniforms:
		material.set_shader_parameter(key, uniforms[key])
	sprite.material = material
	view.add_child(sprite)
	views.append(view)
	return view

func _run() -> void:
	var args := OS.get_cmdline_user_args()
	assert(args.size() == 2)
	var fixture: Dictionary = JSON.parse_string(FileAccess.get_file_as_string(args[0]))
	assert(fixture.production_admitted == false)
	var leaf: Dictionary = fixture.leaf
	var size := Vector2i(600, 400)
	for spec: Dictionary in fixture.cases:
		var normalization: Dictionary = spec.normalization
		var scale_value := float(normalization.scale)
		var translation := Vector2(normalization.x, normalization.y)
		var contour: Array = leaf.fill_masks[0][0]
		var minimum := Vector2(INF, INF)
		var maximum := Vector2(-INF, -INF)
		for point: Array in contour:
			minimum = minimum.min(Vector2(point[0], point[1]))
			maximum = maximum.max(Vector2(point[0], point[1]))
		var bounds := Rect2(translation + minimum * scale_value, (maximum-minimum) * scale_value)
		var images: Array[Image] = []
		for i in 6:
			images.append(Image.create(size.x, size.y, false, Image.FORMAT_RF if i == 5 else Image.FORMAT_RGBA8))
		for y in range(floori(bounds.position.y), ceili(bounds.end.y)):
			var row := Sampler.row({"repeat": false, "width": leaf.width, "height": leaf.height,
				"sx": scale_value, "sy": scale_value, "tx": translation.x, "ty": translation.y,
				"y": y, "left": floori(bounds.position.x), "right": ceili(bounds.end.x), "shape_left": 0})
			for x in range(int(row.left), ceili(bounds.end.x)):
				var i := x - int(row.left)
				var sx: float = row.xs[i]
				var sy: float = row.y
				var ix := floori(sx)
				var iy := floori(sy)
				for corner in 4:
					var px := clampi(ix + corner % 2, 0, int(leaf.width)-1)
					var py := clampi(iy + corner / 2, 0, int(leaf.height)-1)
					var rgba: Array = leaf.pixels_premultiplied[py * int(leaf.width)+px]
					images[corner].set_pixel(x, y, Color(rgba[0]/255.0, rgba[1]/255.0, rgba[2]/255.0, rgba[3]/255.0))
				images[4].set_pixel(x, y, Color(floor((sx-ix)*256)/255.0, floor((sy-iy)*256)/255.0, row.modes[i]/255.0, 0))
				var coverage := (minf(x+1, bounds.end.x)-maxf(x, bounds.position.x)) * (minf(y+1, bounds.end.y)-maxf(y, bounds.position.y))
				# Store coverage in RF, avoiding an extra 8-bit quantization of one half.
				images[5].set_pixel(x, y, Color(coverage, 0, 0, 1))
		var textures := {}
		for i in 6:
			textures[["c00", "c10", "c01", "c11", "parameters", "coverage_texture"][i]] = ImageTexture.create_from_image(images[i])
		var input := _pass(textures, load("res://tests/wrapper_bitmap_input.gdshader"), {}, size)
		var texture: Texture2D = input.get_texture()
		var filter: Dictionary = spec.placement.filters[0]
		for iteration in int(filter.passes):
			for axis in 2:
				var blur := _pass({"TEXTURE": texture}, load("res://flash_filter.gdshader"),
					{"operation": 0, "blur_size": float(filter.blurX if axis == 0 else filter.blurY), "direction": Vector2.RIGHT if axis == 0 else Vector2.DOWN}, size)
				texture = blur.get_texture()
		var color: Array = filter.color
		var glow := _pass({"TEXTURE": texture, "original_texture": input.get_texture()}, load("res://flash_filter.gdshader"),
			{"operation": 1, "glow_strength": float(filter.strength), "glow_color": Vector4(color[0], color[1], color[2], color[3])}, size)
		var composite_shader := Shader.new()
		composite_shader.code = """shader_type canvas_item;
render_mode blend_disabled;
void fragment() {
 vec4 p = floor(texture(TEXTURE, UV)*255.0+0.5);
 COLOR = vec4((p.rgb + floor(vec3(96.0)*(256.0-p.a)/256.0))/255.0, 1.0);
}
"""
		var composite := _pass({"TEXTURE": glow.get_texture()}, composite_shader, {}, size)
		for tick in 8:
			await process_frame
			await RenderingServer.frame_post_draw
		for sample in spec.samples:
			assert(composite.get_texture().get_image().save_png(args[1].path_join("%s-%03d.png" % [spec.id, int(sample)])) == OK)
		input.get_texture().get_image().save_png(args[1].path_join(spec.id+"-input.png"))
		glow.get_texture().get_image().save_png(args[1].path_join(spec.id+"-glow.png"))
		for view in views:
			view.queue_free()
		views.clear()
		await process_frame
	print("YULONG_WRAPPER_DIAGNOSTIC_RENDER_OK cases=%d" % fixture.cases.size())
	quit(0)
