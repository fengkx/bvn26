extends "res://tests/move_case_reference.gd"


func _run() -> void:
	var args := OS.get_cmdline_user_args()
	assert(args.size() == 2)
	bitmap_directory = args[1]
	DirAccess.make_dir_recursive_absolute(bitmap_directory)
	assert(DirAccess.get_files_at(bitmap_directory).is_empty())
	assert(DisplayServer.get_name() != "headless")
	root.size = Vector2i(600, 400)
	root.content_scale_size = Vector2i(600, 400)
	RenderingServer.set_default_clear_color(Color.BLACK)
	var ticks := [0, 11, 15, 40, 43, 60, 80]
	for tick in ticks:
		bitmap_tick = tick
		await _run_case(args[0], bitmap_directory.path_join("state-%03d.json" % tick))
	FileAccess.open(bitmap_directory.path_join("phases.json"), FileAccess.WRITE).store_string(JSON.stringify({
		"ticks": ticks,
		"fixture_sha256": FileAccess.get_sha256(args[0]),
		"engine": Engine.get_version_info(),
		"scope": "Native root-observer snapshots; a separate match replay per image, not continuous lifecycle evidence",
		"native_parity_proven": false,
		"production_admitted": false,
	}, "  ") + "\n")
	print("SASUKEXZ_VISUAL_PHASES_OK")
	quit()
