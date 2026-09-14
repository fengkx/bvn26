extends SceneTree

func _initialize() -> void:
	_run.call_deferred()

func _run() -> void:
	root.transparent_bg = true
	root.size = Vector2i(920, 260)
	var background := ColorRect.new()
	background.color = Color("171a22")
	background.size = Vector2(920, 260)
	root.add_child(background)
	var before := _make_preview()
	var after := _make_preview()
	root.add_child(before)
	root.add_child(after)
	var before_label := Label.new()
	before_label.text = "Frame 420 / Shape 230 — current renderer"
	before_label.position = Vector2(20, 10)
	root.add_child(before_label)
	var after_label := Label.new()
	after_label.text = "Frame 420 / Shape 230 — source masks"
	after_label.position = Vector2(475, 10)
	root.add_child(after_label)
	await process_frame
	var previews: Array[TimelinePreview] = [before, after]
	var panel_origins := [Vector2(20, 55), Vector2(475, 55)]
	for index in previews.size():
		var preview: TimelinePreview = previews[index]
		preview._frames[420]["display_list"] = preview._frames[420]["display_list"].filter(
			func(placement: Dictionary) -> bool: return int(placement.get("character_id", -1)) == 230
		)
		var placement: Dictionary = preview._frames[420]["display_list"][0]
		var source_transform := preview._wrapper_transform() * preview._placement_transform(placement)
		preview.position = panel_origins[index] - preview.scale * source_transform.origin
	before._definitions[230].erase("bitmap_clip_polygons")
	before.play_source_frame(420)
	after.play_source_frame(420)
	await process_frame
	await RenderingServer.frame_post_draw
	var before_sprites := 0
	for child in before.get_children():
		if child is Sprite2D:
			before_sprites += 1
	var after_polygons := 0
	for child in after.get_children():
		if child is Polygon2D:
			after_polygons += 1
	assert(before_sprites == 3, "Expected the unmasked Shape 230 to draw its three complete bitmap fills")
	assert(after_polygons == 3, "Expected the fixed Shape 230 to draw one polygon per compiled bitmap fill")
	var rendered := root.get_texture().get_image()
	assert(rendered != null and not rendered.is_empty(), "Could not capture Shape 230 comparison")
	var args := OS.get_cmdline_user_args()
	var output_path := args[0] if not args.is_empty() else "/tmp/rukia-u-bitmap-fill-before-after.png"
	var error := rendered.save_png(output_path)
	assert(error == OK, "Could not save Shape 230 comparison: %s" % error)
	print("RUKIA_U_BITMAP_FILL_SMOKE_OK %s" % output_path)
	quit()

func _make_preview() -> TimelinePreview:
	var preview := TimelinePreview.new()
	preview.fighter_directory = "res://generated/fighters/rukia"
	preview.autoplay = false
	preview.scale = Vector2(2, 2)
	return preview
