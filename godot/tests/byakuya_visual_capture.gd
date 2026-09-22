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
	# Record the runtime state before renderer flushing. Headless SceneTree runs
	# do not guarantee a process_frame signal after manual fixed-tick replay.
	var helper: HelperRuntime = _game.naruto_helper
	var diagnostic := {
		"source_frame": _target_frame,
		"actual_source_frame": fighter.current_source_frame(),
		"actual_action": fighter.action,
		"actual_energy": fighter.energy,
		"capture_tick": _game.physics_tick,
		"relative_fight_tick": _game.physics_tick - _fight_start_tick,
		"fighter_instance_local_frames": fighter._instance_local_frames.duplicate(true),
		"helper": _timeline_state(helper),
		"helper_tree": _node_tree(helper),
		"game_world_tree": _node_tree(_game.game_world),
		"effect_candidates": _effect_candidates(_game.game_world),
		"runtime_hash_scope": "diagnostic-only-current-worktree",
	}
	var diagnostic_text := JSON.stringify(diagnostic, "  ")
	print("BYAKUYA_DIAGNOSTIC_BYTES ", diagnostic_text.length())
	var diagnostic_file := FileAccess.open(output.path_join("runtime-diagnostic.json"), FileAccess.WRITE)
	assert(diagnostic_file != null, "Cannot open diagnostic output: %s" % output)
	diagnostic_file.store_string(diagnostic_text + "\n")
	diagnostic_file.flush()
	# Flush the complete main-scene tick sequence through the renderer once the
	# deterministic replay reaches its observation frame.
	await process_frame
	await RenderingServer.frame_post_draw

	var viewport_texture := root.get_texture()
	if viewport_texture == null:
		push_warning("Headless run has no viewport texture; metadata remains authoritative.")
		_game.queue_free()
		await process_frame
		quit()
		return
	var image := viewport_texture.get_image()
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

func _timeline_state(actor: Node) -> Dictionary:
	if actor == null:
		return {}
	var result := {"name": actor.name, "class": actor.get_class(), "path": str(actor.get_path())}
	for property_name in ["helper_id", "source_action", "attacking", "facing", "bs", "hited", "timeline_playing", "_current_frame", "_source_entry_serial", "_activation_generation", "_nested_dispatch_frame", "_instance_local_frames", "_instance_local_offsets", "_retained_visual_clips"]:
		if _has_property(actor, property_name):
			result[property_name] = actor.get(property_name)
	return result

func _has_property(actor: Object, property_name: String) -> bool:
	for item in actor.get_property_list():
		if str(item.get("name", "")) == property_name:
			return true
	return false

func _node_tree(node: Node, depth: int = 0) -> Array:
	if node == null or depth > 8:
		return []
	var row := {"name": node.name, "class": node.get_class(), "path": str(node.get_path()), "children": []}
	if node is Node2D:
		row["position"] = {"x": node.position.x, "y": node.position.y}
		row["scale"] = {"x": node.scale.x, "y": node.scale.y}
		row["rotation"] = node.rotation
	if node is CanvasItem:
		row["visible"] = node.visible
		row["z_index"] = node.z_index
	for property_name in ["_current_frame", "_source_entry_serial", "source_frame", "current_source_frame", "local_frame", "character_id"]:
		if _has_property(node, property_name):
			row[property_name] = node.get(property_name)
	for child in node.get_children():
		row["children"].append_array(_node_tree(child, depth + 1))
	return [row]

func _effect_candidates(node: Node) -> Array:
	var rows: Array = []
	if node == null:
		return rows
	for child in node.get_children():
		var path := str(child.get_path()).to_lower()
		var label := str(child.name).to_lower()
		if label.contains("effect") or label.contains("smoke") or label.contains("xg") or path.contains("effect") or path.contains("smoke") or path.contains("xg"):
			rows.append({"path": str(child.get_path()), "class": child.get_class(), "state": _timeline_state(child), "tree": _node_tree(child)})
		rows.append_array(_effect_candidates(child))
	return rows

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
