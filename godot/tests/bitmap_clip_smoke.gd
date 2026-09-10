extends SceneTree

func _initialize() -> void:
	_run.call_deferred()

func _run() -> void:
	root.transparent_bg = true
	var preview := TimelinePreview.new()
	preview.fighter_directory = "res://generated/fighters/rifagu"
	preview.autoplay = false
	preview.position = Vector2(200, 150)
	preview.scale = Vector2(3, 3)
	preview.hidden_instance_names = ["tzatm"]
	root.add_child(preview)
	if "--legacy-aabb" in OS.get_cmdline_user_args():
		preview._definitions[107].erase("bitmap_clip_polygon")
	preview.play_source_frame(157)
	await process_frame
	await RenderingServer.frame_post_draw
	var rendered := root.get_texture().get_image()
	# Bitmap 79's ice at (65.5, 68.5) is inside shape 107's AABB, outside its path.
	var ice_point := Vector2(65.5, 68.5) + Vector2(348, 1170) / 20 - Vector2(1437, 1715) / 20
	var screen_point := root.get_final_transform() * preview.global_transform * preview._wrapper_transform() * ice_point
	if rendered.get_pixelv(screen_point).a != 0.0:
		if not OS.has_feature("web"):
			rendered.save_png("/tmp/bvn-bitmap-clip-before.png")
		push_error("Shape 107 leaked bitmap 79's ice")
		quit(1)
		return
	var polygon: Array = preview._definitions[107]["bitmap_clip_polygon"]
	var vertices := PackedVector2Array()
	for point: Array in polygon:
		vertices.append(Vector2(point[0], point[1]))
	assert(not Geometry2D.is_point_in_polygon(Vector2(82.9, 127.0), vertices))
	assert(Geometry2D.is_point_in_polygon(Vector2(77.4, 78.5), vertices))
	print("BITMAP_CLIP_SMOKE_OK")
	if not OS.has_feature("web"):
		rendered.save_png("/tmp/bvn-bitmap-clip-fixed.png")
		quit()
