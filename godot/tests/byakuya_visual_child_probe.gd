extends SceneTree

var _game: Node
var _target_frame := 0
var _fight_start_tick := -1

func _initialize() -> void:
	_run.call_deferred()

func _run() -> void:
	var args := OS.get_cmdline_user_args()
	assert(args.size() == 2, "Expected frame and output directory")
	_target_frame = int(args[0])
	var output := str(args[1])
	DirAccess.make_dir_recursive_absolute(output)
	_game = load("res://main.tscn").instantiate()
	root.add_child(_game)
	# Manual fixed ticks keep the replay deterministic; the final GUI frame is
	# flushed after the complete main-scene callback sequence.
	_game.set_physics_process(false)
	await process_frame
	_game._on_menu_confirmed("vs_com")
	# Lee remains out of the shared public roster until integration's gate.
	_game.character_selection.available.fighters["白哉"] = "byakuya"
	_game._on_characters_confirmed(["白哉", "一护"], ["魂", "魂"])
	_game._on_map_confirmed("现世")
	_game.diagnostic_input_provider = Callable(self, "_input_tape")
	var fighter: FighterRuntime = _game.naruto
	var reached := false
	for _tick in 900:
		if not _game.battle_intro.active and _fight_start_tick < 0:
			# Establish fixture state before the first post-intro production tick,
			# so the command catalog sees the intended energy and coordinates.
			_fight_start_tick = _game.physics_tick
			fighter.source_x = 300.0
			fighter.source_y = -25.0
			_game.ichigo.source_x = 350.0
			_game.ichigo.source_y = -25.0
			fighter.sync_body_collision_position()
			_game.ichigo.sync_body_collision_position()
			# Same fixture setup point as move_case_reference observation tick 0.
			fighter.energy = 300.0
			_game.ichigo.energy = 300.0
		_game._advance_fight()
		if _fight_start_tick >= 0 and int(fighter.current_source_frame()) == _target_frame:
			reached = true
			break
	assert(reached, "Production input tape did not reach requested source frame")
	# Read-only recursive observation from the live TimelinePreview display list.
	# _nested_frame is the same source placement rule used by rendering; every
	# child frame is recorded, never copied from the root frame.
	var child_paths: Array = []
	_collect_child_paths(fighter, fighter._frames[int(fighter.current_source_frame())].get("display_list", []), int(fighter.current_source_frame()), "root", child_paths)
	FileAccess.open(output.path_join("child-map.json"), FileAccess.WRITE).store_string(JSON.stringify({
		"scope": "read_only_live_timeline_display_list", "source_frame": int(fighter.current_source_frame()), "target_frame": _target_frame,
		"capture_tick": _game.physics_tick, "child_paths": child_paths,
		"existing_compiled_instance_frames": fighter._instance_local_frames.duplicate(true),
		"fixture": {"p1": "白哉", "p2": "一护", "helpers": ["魂", "魂"], "stage": "现世"}
	}, "  ") + "\n")
	# Preserve the live runtime placement dictionaries at the target frame. This
	# is deliberately emitted from FighterRuntime, rather than re-reading the
	# generated JSON after the run, so matrix/bitmap evidence is tied to the
	# actual fixture execution.
	FileAccess.open(output.path_join("runtime-display-list.json"), FileAccess.WRITE).store_string(JSON.stringify({
		"source_frame": _target_frame,
		"capture_tick": _game.physics_tick,
		"fighter": "白哉",
		"display_list": fighter._frames[int(fighter.current_source_frame())].get("display_list", []).duplicate(true),
		"instance_local_frames": fighter._instance_local_frames.duplicate(true),
		"instance_local_offsets": fighter._instance_local_offsets.duplicate(true),
		"render_nodes": _collect_render_nodes(fighter)
	}, "  ") + "\n")
	# Flush the complete main-scene tick sequence through the renderer once the
	# deterministic replay reaches its observation frame.
	await process_frame
	await RenderingServer.frame_post_draw

	var image := root.get_texture().get_image()
	image.save_png(output.path_join("godot-full.png"))
	var size := image.get_size()
	var canvas_transform := root.get_viewport().get_canvas_transform()
	var stage: Image = image.duplicate()
	stage.resize(600, 400, Image.INTERPOLATE_NEAREST)
	stage.save_png(output.path_join("godot-stage-600x400.png"))
	stage.save_png(output.path_join("godot-600x400.png"))
	FileAccess.open(output.path_join("metadata.json"), FileAccess.WRITE).store_string(JSON.stringify({
		"source_frame": _target_frame,
		"fighter": "白哉",
		"opponent": "一护",
		"helper_ids": ["魂", "魂"],
		"stage": "现世",
		"initial_positions": {"p1": 300, "p2": 350},
		"actual_source_frame": fighter.current_source_frame(),
		"actual_action": fighter.action,
		"actual_energy": fighter.energy,
		"capture_tick": _game.physics_tick,
		"relative_fight_tick": _game.physics_tick - _fight_start_tick,
		"actual_positions": {
			"p1_source": {"x": fighter.source_x, "y": fighter.source_y},
			"p2_source": {"x": _game.ichigo.source_x, "y": _game.ichigo.source_y},
			"p1_render": {"x": fighter.position.x, "y": fighter.position.y},
			"p2_render": {"x": _game.ichigo.position.x, "y": _game.ichigo.position.y}
		},
		"visual_child_frames": fighter._instance_local_frames.duplicate(true),
		"super_presentation": {
			"black_mu_frame": _game.super_presentation.black_mu_frame,
			"bgmc_visible": _game.super_presentation.bgmc_visible,
			"fgmc_visible": _game.super_presentation.fgmc_visible,
			"face_label": _game.super_presentation.face_label,
			"bg_frame": _game.super_presentation.bg_frame,
			"face_p1_frame": _game.super_presentation.face_p1_frame,
			"face_p2_frame": _game.super_presentation.face_p2_frame
		},
		"camera_canvas_transform": {
			"origin": {"x": canvas_transform.origin.x, "y": canvas_transform.origin.y},
			"scale_x": canvas_transform.x.x,
			"scale_y": canvas_transform.y.y
		},
		"viewport": {"width": size.x, "height": size.y},
		"stage_runtime": {
			"selected_stage": _game.selected_stage,
			"background_directory": _game.stage_background.fighter_directory if _game.stage_background != null else "",
			"world_directory": _game.current_world.fighter_directory if _game.current_world != null else "",
			"world_focus": _game.game_world.focus
		},
		"timer_runtime": {
			"available": _game.countdown != null,
			"locals": _game.countdown.locals.duplicate(true) if _game.countdown != null else {},
			"digit_frames": _game.countdown.digit_frames.duplicate(true) if _game.countdown != null else {}
		},
		"fight_start_tick": _fight_start_tick,
		"capture_path": "main_scene_fixed_tick_input_tape"
	}, "  ") + "\n")
	_game.queue_free()
	await process_frame
	quit()

func _collect_child_paths(fighter: FighterRuntime, placements: Array, parent_frame: int, parent_path: String, result: Array) -> void:
	for placement: Dictionary in placements:
		var symbol := int(placement.get("character_id", -1))
		var definition: Dictionary = fighter._definitions.get(symbol, {})
		var frames: Array = definition.get("display_list_frames", [])
		var child_frame := 1
		if not frames.is_empty():
			child_frame = fighter._nested_frame(placement, parent_frame, frames.size())
		var name := str(placement.get("name", ""))
		var segment := name if name != "" else ("#" + str(placement.get("depth", -1)))
		var path := parent_path + "/" + segment
		result.append({"path": path, "name": name, "symbol": symbol, "depth": int(placement.get("depth", -1)), "placed_frame": int(placement.get("placed_frame", -1)), "parent_frame": parent_frame, "child_frame": child_frame, "frame_count": frames.size(), "has_live_timeline": not frames.is_empty()})
		if not frames.is_empty() and child_frame >= 1 and child_frame <= frames.size():
			_collect_child_paths(fighter, frames[child_frame - 1], child_frame, path, result)

func _transform_record(value: Transform2D) -> Dictionary:
	return {
		"x": {"x": value.x.x, "y": value.x.y},
		"y": {"x": value.y.x, "y": value.y.y},
		"origin": {"x": value.origin.x, "y": value.origin.y}
	}

func _collect_render_nodes(node: Node, parent_path: String = "root") -> Array:
	var result: Array = []
	for child: Node in node.get_children():
		if child.name in ["SoundLayer", "RuntimeServices"]:
			continue
		var path := parent_path + "/" + str(child.name)
		var row := {"path": path, "type": child.get_class()}
		if child is Node2D:
			row["local_transform"] = _transform_record(child.transform)
			row["global_transform"] = _transform_record(child.global_transform)
			row["z_index"] = child.z_index
		if child is Sprite2D:
			row["texture"] = child.texture.resource_path if child.texture != null else ""
		elif child is Polygon2D:
			row["texture"] = child.texture.resource_path if child.texture != null else ""
		result.append(row)
		result.append_array(_collect_render_nodes(child, path))
	return result

func _input_tape(slot: String, tick: int) -> Dictionary:
	var keys := {"up": false, "down": false, "left": false, "right": false,
		"attack": false, "jump": false, "dash": false, "ranged": false,
		"special": false, "summon": false}
	if _fight_start_tick < 0 or slot != "p1":
		return keys
	var relative := tick - _fight_start_tick
	if _target_frame == 158:
		keys["attack"] = relative >= 10 and relative < 13
	elif _target_frame == 464:
		keys["jump"] = relative >= 5 and relative < 6
		keys["special"] = relative >= 20 and relative < 23
	elif _target_frame == 333:
		keys["ranged"] = relative >= 10 and relative < 13
	elif _target_frame == 576:
		keys["up"] = relative >= 10 and relative < 13
		keys["special"] = relative >= 10 and relative < 13
	elif _target_frame == 819:
		keys["summon"] = relative >= 10 and relative < 13
	else:
		keys["down"] = relative >= 10 and relative < 13
		keys["special"] = relative >= 10 and relative < 13
	return keys
