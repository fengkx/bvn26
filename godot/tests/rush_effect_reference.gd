extends SceneTree

func _initialize() -> void:
	_run.call_deferred()

func _run() -> void:
	var args := OS.get_cmdline_user_args()
	var view := SubViewport.new()
	view.size = Vector2i(256, 256)
	view.render_target_update_mode = SubViewport.UPDATE_ALWAYS
	root.add_child(view)
	var background := ColorRect.new()
	background.color = Color.BLACK
	background.size = Vector2(256, 256)
	view.add_child(background)
	var effect := HitEffectRuntime.new()
	effect.auto_advance = false
	view.add_child(effect)
	effect.configure("XG_rush", Vector2(128, 128), 1, 0)
	var rows: Array = []
	for tick in 21:
		if tick > 0 and is_instance_valid(effect):
			effect.advance_effect()
		if args.size() > 1 and args[1] == "linear" and is_instance_valid(effect):
			_probe_linear_sampling(effect)
		# Record the entered source frame before deferred node destruction.
		var entered_frame := effect.effect_frame if is_instance_valid(effect) else 0
		for settle in 2:
			await process_frame
			await RenderingServer.frame_post_draw
		var pixels: Array = []
		var captured := view.get_texture().get_image()
		for y in range(64, 193, 16):
			for x in range(64, 193, 16):
				var color := captured.get_pixel(x, y)
				pixels.append((roundi(color.r * 255) << 16) | (roundi(color.g * 255) << 8) | roundi(color.b * 255))
		rows.append({"tick": tick, "frame": entered_frame, "pixels": pixels})
	var reference_path := ProjectSettings.globalize_path("res://").path_join("../evidence/importer-loud-fail/r05/native-rush-rows.json")
	var reference = JSON.parse_string(FileAccess.get_file_as_string(reference_path))
	if not reference is Array or reference.size() != rows.size():
		push_error("Missing native rush frame reference")
		quit(1)
		return
	for index in rows.size():
		if rows[index].tick != reference[index].tick or rows[index].frame != reference[index].frame:
			push_error("Native rush entered-frame mismatch at tick %s" % index)
			quit(1)
			return
	print("RUSH_CLOCK_REFERENCE_OK samples=21")
	FileAccess.open(args[0], FileAccess.WRITE).store_string(JSON.stringify(rows))
	print("RUSH_EFFECT_REFERENCE_CAPTURE_OK rows=21")
	view.queue_free()
	await process_frame
	await process_frame
	quit()

# Diagnostic only: production rendering remains the default capture path.
func _probe_linear_sampling(node: Node) -> void:
	if node is Sprite2D or node is Polygon2D:
		node.texture_filter = CanvasItem.TEXTURE_FILTER_LINEAR
	for child in node.get_children():
		_probe_linear_sampling(child)
