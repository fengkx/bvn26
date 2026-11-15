extends "res://tests/move_case_reference.gd"


func _run() -> void:
	var args := OS.get_cmdline_user_args()
	bitmap_directory = args[1]
	DirAccess.make_dir_recursive_absolute(bitmap_directory)
	root.size = Vector2i(600, 400)
	root.content_scale_size = Vector2i(600, 400)
	bitmap_tick = 43
	bitmap_settle_frames = 3
	await _run_case(args[0], bitmap_directory.path_join("state.json"))
	quit()


func _observe(tick: int) -> void:
	super._observe(tick)
	if tick == bitmap_tick:
		_save_groups.call_deferred()


func _save_groups() -> void:
	await RenderingServer.frame_post_draw
	var groups := []
	for actor in [game.naruto, game.current_world]:
		for child in actor.get_children():
			if child.has_method("source_bounds") and child.has_node("Contents"):
				var path := str(child.get_path())
				var filename := str(groups.size()) + ".png"
				child.get_node("Contents").get_texture().get_image().save_png(bitmap_directory.path_join(filename))
				groups.append({"path": path, "image": filename,
					"bounds": str(child.source_bounds()), "transform": str(child.global_transform),
					"viewport_size": str(child.get_node("Contents").size)})
	FileAccess.open(bitmap_directory.path_join("groups.json"), FileAccess.WRITE).store_string(JSON.stringify(groups, "  "))
