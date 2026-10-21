extends "res://tests/move_case_reference.gd"

var visual_views: Dictionary = {}
var visual_children: Array = []
var visual_spec: Dictionary = {}
var visual_output: String
var visual_frames: Array[int] = []


func _run() -> void:
	var args := OS.get_cmdline_user_args()
	assert(args.size() == 3, "Expected move fixture, visual spec, output directory")
	visual_spec = JSON.parse_string(FileAccess.get_file_as_string(args[1]))
	for value in visual_spec.frames:
		visual_frames.append(int(value))
	visual_output = args[2]
	DirAccess.make_dir_recursive_absolute(visual_output)
	await _run_case(args[0], visual_output.path_join("states.json"))
	await RenderingServer.frame_post_draw
	for frame in visual_views:
		assert(visual_views[frame].get_texture().get_image().save_png(visual_output.path_join("frame-%s.png" % frame)) == OK)
	FileAccess.open(visual_output.path_join("children.json"), FileAccess.WRITE).store_string(JSON.stringify(visual_children, "", true, true))
	assert(visual_views.size() == visual_spec.frames.size())
	print("MOVE_VISUAL_REFERENCE_OK ", visual_views.keys())
	quit(2 if failed else 0)


func _observe(tick: int) -> void:
	_capture_visual(tick)
	super._observe(tick)


func _capture_visual(tick: int) -> void:
	var actor = game.naruto if visual_spec.get("slot", "p1") == "p1" else game.ichigo
	var frame: int = actor.current_source_frame()
	if frame >= int(visual_spec.observe_from) and frame <= int(visual_spec.observe_to):
		for placement: Dictionary in actor._frames[frame]["display_list"]:
			var definition: Dictionary = actor._definitions.get(int(placement.character_id), {})
			if int(definition.get("frame_count", 1)) > 1:
				visual_children.append({"tick": tick, "frame": frame, "depth": placement.depth,
					"symbol": placement.character_id, "child_frame": actor._nested_frame(placement, frame, int(definition.frame_count)),
					"placed_frame": placement.placed_frame})
	if frame not in visual_frames or visual_views.has(frame):
		return
	# Snapshot the production CanvasItems, including materials and backbuffer
	# copies, at the observer boundary. Normalize only the actor's stage position.
	var view := SubViewport.new()
	view.size = Vector2i(600, 400)
	view.render_target_update_mode = SubViewport.UPDATE_ALWAYS
	root.add_child(view)
	var background := ColorRect.new()
	background.color = Color.html(str(visual_spec.get("background", "606060")))
	background.size = Vector2(600, 400)
	view.add_child(background)
	var container := Node2D.new()
	container.position = Vector2(300, 300)
	container.scale = actor.scale
	view.add_child(container)
	for child in actor.get_children():
		if child is CanvasItem and not child.is_queued_for_deletion() and child.name not in ["SoundLayer", "RuntimeServices"]:
			container.add_child(child.duplicate())
	visual_views[frame] = view
