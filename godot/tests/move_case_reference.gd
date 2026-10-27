extends SceneTree

var game
var bitmap_tick := -1
var bitmap_directory := ""
var fixture: Dictionary
var mode: int
var rows: Array = []
var helper_rows: Array = []
var presentation_rows: Array = []
var geometry_rows: Array = []
var contact_rows: Array = []
var projectile_rows: Array = []
var recovery_events: Dictionary = {}
var intervention_rows: Array = []
var applied_interventions: Dictionary = {}
var failed := false
var drive_source_timers := false
var source_timer_required := false
var _source_timer_id: int = -1
var _source_timer_elapsed_ms: float = 0.0
var _source_timer_registered_this_tick := false

func _initialize() -> void:
	_run.call_deferred()

func _run() -> void:
	var args := OS.get_cmdline_user_args()
	if args[0] == "--bitmap-sequence":
		bitmap_directory = args[2]
		assert(DirAccess.get_files_at(bitmap_directory).is_empty(), "Use a fresh bitmap output directory")
		assert(not DisplayServer.get_name() == "headless", "Bitmap capture requires a real renderer")
		root.size = Vector2i(600, 400)
		root.content_scale_size = Vector2i(600, 400)
		RenderingServer.set_default_clear_color(Color.BLACK)
		var spec: Dictionary = JSON.parse_string(FileAccess.get_file_as_string(args[1]))
		for tick in range(int(spec.frames) + 1):
			bitmap_tick = tick
			await _run_case(args[1], bitmap_directory.path_join("state-%03d.json" % tick))
		var images := []
		for tick in range(int(spec.frames) + 1):
			var filename := "%03d.png" % tick
			images.append({"tick": tick, "file": filename,
				"sha256": FileAccess.get_sha256(bitmap_directory.path_join(filename))})
		var manifest := {"case_id": spec.id, "case_sha256": FileAccess.get_sha256(args[1]),
			"phase": "root-observer", "format": "RGBA8", "background": "opaque-black",
			"width": 600, "height": 400, "images": images,
			"engine": Engine.get_version_info(),
			"engine_sha256": FileAccess.get_sha256(OS.get_executable_path()),
			"runner_sha256": FileAccess.get_sha256("res://tests/move_case_reference.gd"),
			"native_parity_proven": false, "production_admitted": false}
		FileAccess.open(bitmap_directory.path_join("bitmap.json"), FileAccess.WRITE).store_string(JSON.stringify(manifest))
	elif args[0] == "--batch":
		var paths: Array = JSON.parse_string(FileAccess.get_file_as_string(args[1]))
		for path in paths:
			var spec: Dictionary = JSON.parse_string(FileAccess.get_file_as_string(path))
			await _run_case(path, args[2].path_join(str(spec.id) + ".json"))
		print("MOVE_CASE_BATCH_OK ", paths.size())
	else:
		await _run_case(args[0], args[1])
	quit(2 if failed else 0)


func _run_case(fixture_path: String, output_path: String) -> void:
	rows = []
	helper_rows = []
	presentation_rows = []
	geometry_rows = []
	contact_rows = []
	projectile_rows = []
	recovery_events = {}
	intervention_rows = []
	applied_interventions = {}
	fixture = JSON.parse_string(FileAccess.get_file_as_string(fixture_path))
	drive_source_timers = bool(fixture.get("drive_source_timers", false))
	source_timer_required = bool(fixture.get("source_timer_required", false))
	if source_timer_required and not drive_source_timers:
		push_error("Fixture requires source timer input but drive_source_timers is false")
		failed = true
		return
	if drive_source_timers:
		var timer_provenance: Dictionary = fixture.get("timer_input_provenance", {})
		if timer_provenance.is_empty() or str(timer_provenance.get("route", "")).is_empty():
			push_error("Timer-driven fixture must declare timer_input_provenance.route")
			failed = true
			return
	_source_timer_id = -1
	_source_timer_elapsed_ms = 0.0
	_source_timer_registered_this_tick = false
	_validate_resource_interventions()
	mode = 3
	game = load("res://main.tscn").instantiate()
	root.add_child(game)
	game.set_physics_process(false)
	game.diagnostics.event_recorded.connect(_on_diagnostic_event)
	game.recorded_training_timers = true
	if fixture.has("fighters"):
		for helper_key in ["p1_helper", "p2_helper"]:
			if not fixture.has(helper_key) or str(fixture[helper_key]).is_empty():
				push_error("Acceptance fixture must declare %s; implicit helper defaults are invalid" % helper_key)
				failed = true
				return
		var names: Array = []
		for slot in ["p1", "p2"]:
			var display := _fixture_display_id("fighters", str(fixture.fighters[slot]))
			if display.is_empty():
				return
			names.append(display)
		var helpers := ["我爱罗", "魂"]
		for index in 2:
			var key := "p%d_helper" % (index + 1)
			if not fixture.has(key):
				continue
			var requested := str(fixture[key])
			var helper_name := ""
			for display_name in game.character_selection.available.helpers:
				if display_name == requested or str(game.character_selection.available.helpers[display_name]) == requested:
					helper_name = display_name
					break
			if helper_name.is_empty():
				helper_name = _fixture_display_id("helpers", requested)
			helpers[index] = helper_name
		game._replace_selected_actors(names, helpers)
	var requested_stage := str(fixture.get("stage", "现世"))
	game._load_selected_stage(requested_stage)
	if game.selected_stage != requested_stage:
		push_error("Fixture stage was not loaded: requested=%s actual=%s" % [requested_stage, game.selected_stage])
		failed = true
		return
	game._enter_current_fight(mode)
	for tick in 700:
		game._advance_fight([], func() -> bool:
			if not game.battle_intro.active:
				_drive_source_timers(1000.0 / Engine.physics_ticks_per_second)
				_observe(0)
			return bitmap_tick == 0 and rows.size() == 2)
		# The intro can become inactive after the root callback but before the
		# first post-intro observer runs. Keep one more tick so tick 0 retains
		# both fighter snapshots instead of producing an empty trace.
		if not game.battle_intro.active and rows.size() == 2: break
	assert(not game.battle_intro.active and rows.size() == 2)
	for tick in range(1, (bitmap_tick if bitmap_tick >= 0 else int(fixture.frames)) + 1):
		# Timer callbacks occur after the preceding source snapshot and before
		# the next fight advance. Deliver the external clock at that boundary.
		_drive_source_timers(1000.0 / Engine.physics_ticks_per_second)
		game._advance_fight(recovery_events.get(tick, []), func() -> bool:
			_observe(tick)
			return tick == bitmap_tick)
	if bitmap_tick >= 0:
		# Terminal observer skips deferred frame scripts; pause all processing
		# while pending CanvasItem draws settle, without advancing gameplay.
		game.process_mode = Node.PROCESS_MODE_DISABLED
		await process_frame
		await RenderingServer.frame_post_draw
		var image := root.get_texture().get_image()
		assert(image.get_size() == Vector2i(600, 400), "Unexpected bitmap size")
		image.convert(Image.FORMAT_RGBA8)
		assert(image.save_png(bitmap_directory.path_join("%03d.png" % bitmap_tick)) == OK)
	assert(applied_interventions.size() == fixture.get("resource_interventions", []).size(),
		"one or more resource interventions did not execute")
	FileAccess.open(output_path, FileAccess.WRITE).store_string(JSON.stringify(rows, "", true, true))
	var first_tick_rows: Array = rows.filter(func(row: Dictionary) -> bool: return int(row.get("tick", -1)) == 0)
	var stage_metadata := {
		"fixture_id": str(fixture.get("id", "")),
		"stage_requested": requested_stage,
		"stage_loaded": game.selected_stage,
		"background_directory": game.stage_background.fighter_directory if game.stage_background != null else "",
		"world_directory": game.current_world.fighter_directory if game.current_world != null else "",
		"tick0_fighters": first_tick_rows,
	}
	FileAccess.open(output_path + ".metadata.json", FileAccess.WRITE).store_string(
		JSON.stringify(stage_metadata, "", true, true))
	FileAccess.open(output_path + ".helpers.json", FileAccess.WRITE).store_string(JSON.stringify(helper_rows, "", true, true))
	FileAccess.open(output_path + ".presentation.json", FileAccess.WRITE).store_string(JSON.stringify(presentation_rows, "", true, true))
	if not geometry_rows.is_empty():
		FileAccess.open(output_path + ".geometry.json", FileAccess.WRITE).store_string(JSON.stringify(geometry_rows, "", true, true))
	if not contact_rows.is_empty():
		FileAccess.open(output_path + ".contacts.json", FileAccess.WRITE).store_string(JSON.stringify(contact_rows, "", true, true))
	if fixture.has("projectile_probe"):
		FileAccess.open(output_path + ".projectiles.json", FileAccess.WRITE).store_string(JSON.stringify(projectile_rows, "", true, true))
	FileAccess.open(output_path + ".interventions.json", FileAccess.WRITE).store_string(JSON.stringify(intervention_rows, "", true, true))
	game._goto_menu()
	game.queue_free()
	await process_frame
	print("MOVE_CASE_REFERENCE_OK ", fixture.id)


func _drive_source_timers(delta_ms: float) -> void:
	# The acceptance runner disables SceneTree physics and advances the source
	# clock explicitly. When a fixture opts in, deliver registered source Timer
	# callbacks by their authored wait_time instead of a fixture-specific tick.
	if not drive_source_timers or game == null:
		return
	if game.ko_nextfight_timer == null:
		if _source_timer_id >= 0:
			print("SOURCE_TIMER_CANCEL id=", _source_timer_id,
				" elapsed_ms=", _source_timer_elapsed_ms)
		_source_timer_id = -1
		_source_timer_elapsed_ms = 0.0
		_source_timer_registered_this_tick = false
		return
	var timer: Timer = game.ko_nextfight_timer
	var id := timer.get_instance_id()
	if id != _source_timer_id:
		_source_timer_id = id
		_source_timer_elapsed_ms = 0.0
		# SceneTree physics is disabled by this runner; freeze the real Timer so
		# only the authored source-clock deadline below can deliver the callback.
		timer.paused = true
		print("SOURCE_TIMER_REGISTER id=", id, " wait_ms=", timer.wait_time * 1000.0)
		# Registration starts the authored interval immediately; the current
		# fight boundary contributes to the external source clock.
		_source_timer_registered_this_tick = false
	if timer.is_stopped():
		return
	var elapsed := _source_timer_elapsed_ms + delta_ms
	while elapsed + 0.00001 >= timer.wait_time * 1000.0:
		elapsed -= timer.wait_time * 1000.0
		var before_frame := int(game.ko_timeline.root_clip.frame) if game.ko_timeline != null else -1
		print("SOURCE_TIMER_FIRE ", JSON.stringify({
			"id": id, "deadline_ms": timer.wait_time * 1000.0,
			"physics_tick": game.physics_tick, "session": game.session.root_label,
			"ko_active": game.ko_active, "ko_paused": game.ko_paused,
			"ko_frame": before_frame, "p1_frame": game.naruto.current_source_frame(),
			"p2_frame": game.ichigo.current_source_frame(), "p1_sw": game.naruto.sw,
			"p2_sw": game.ichigo.sw}))
		timer.timeout.emit()
		print("SOURCE_TIMER_AFTER ", JSON.stringify({
			"id": id, "physics_tick": game.physics_tick,
			"session": game.session.root_label,
			"ko_active": game.ko_active, "ko_paused": game.ko_paused,
			"ko_frame": int(game.ko_timeline.root_clip.frame) if game.ko_timeline != null else -1,
			"p1_frame": game.naruto.current_source_frame(), "p2_frame": game.ichigo.current_source_frame(),
			"p1_sw": game.naruto.sw, "p2_sw": game.ichigo.sw}))
		if game.ko_nextfight_timer == null or not is_instance_valid(timer):
			break
	_source_timer_elapsed_ms = elapsed


func _fixture_display_id(kind: String, fixture_id: String) -> String:
	var available: Dictionary = game.character_selection.available[kind]
	for display_id in available:
		if str(available[display_id]) == fixture_id:
			return str(display_id)
	var directory := "res://generated/%s/%s" % [kind, fixture_id]
	var metadata_path := directory.path_join("fighter.json" if kind == "fighters" else "combat.json")
	var timeline_path := directory.path_join("timeline.json")
	var assets_path := directory.path_join("assets.json")
	if not FileAccess.file_exists(metadata_path):
		push_error("Missing fixture metadata: " + metadata_path)
		failed = true
		return ""
	assert(FileAccess.file_exists(timeline_path), "Missing fixture timeline: " + timeline_path)
	assert(FileAccess.file_exists(assets_path), "Missing fixture assets: " + assets_path)
	var metadata: Dictionary = JSON.parse_string(FileAccess.get_file_as_string(metadata_path))
	var timeline: Dictionary = JSON.parse_string(FileAccess.get_file_as_string(timeline_path))
	var assets: Dictionary = JSON.parse_string(FileAccess.get_file_as_string(assets_path))
	var display_id := str(metadata.get("fighter_id" if kind == "fighters" else "helper_id", ""))
	assert(not display_id.is_empty(), "Missing source display id: " + metadata_path)
	var source_swf: Dictionary = timeline.get("source_swf", {})
	var source_path := str(source_swf.get("path", ""))
	assert(source_path.get_file().get_basename().to_lower() == fixture_id.to_lower(),
		"Fixture id/source SWF mismatch: %s != %s" % [fixture_id, source_path])
	var source_file := "res://../" + source_path
	assert(FileAccess.file_exists(source_file), "Missing frozen fixture source: " + source_file)
	var manifest: Dictionary = JSON.parse_string(FileAccess.get_file_as_string("res://../manifest.json"))
	var expected_sha := str(manifest.get("file_sha256", {}).get(source_path, ""))
	assert(not expected_sha.is_empty() and expected_sha == str(source_swf.get("sha256", "")),
		"Fixture source hash/manifest mismatch: " + source_path)
	assert(FileAccess.get_sha256(source_file) == expected_sha,
		"Fixture source hash differs from the frozen input: " + source_path)
	if kind == "fighters" and not game.battle_intro.spec["fighters"].has(fixture_id):
		var intro_path := directory.path_join("intro.json")
		if not FileAccess.file_exists(intro_path):
			push_error("Missing fixture opening metadata: " + intro_path)
			failed = true
			return ""
		var intro: Dictionary = JSON.parse_string(FileAccess.get_file_as_string(intro_path))
		assert(str(intro.get("fighter_id", "")) == fixture_id,
			"Fixture id/opening metadata mismatch: " + fixture_id)
		assert(int(intro.get("source_sprite_id", -1)) == int(timeline.get("sprite_id", -2)),
			"Fixture timeline/opening sprite mismatch: " + fixture_id)
		game.battle_intro.spec["fighters"][fixture_id] = {"state_frames": intro.get("state_frames", {})}
	assert(not assets.get("assets", []).is_empty(), "No materialized source assets: " + assets_path)
	for asset in assets.assets:
		var asset_path := directory.path_join(str(asset.get("path", "")))
		assert(FileAccess.file_exists(asset_path), "Missing materialized asset: " + asset_path)
	assert(not available.has(display_id) or str(available[display_id]) == fixture_id,
		"Fixture display id conflicts with the existing roster: " + display_id)
	available[display_id] = fixture_id
	return display_id

func _observe(tick: int) -> void:
	_apply_resource_interventions(tick)
	presentation_rows.append({"tick": tick, "x": game.position.x, "y": game.position.y})
	if tick == 0:
		for actor in [game.naruto, game.ichigo]:
			var setup: Dictionary = fixture.setup[actor.player_slot]
			actor.goto_ai_label("站立", true)
			actor.position.x = setup.x
			actor.energy = setup.energy
			_apply_source_state_preconditions(actor)
	for actor in [game.naruto, game.ichigo]:
		rows.append({"tick": tick, "slot": actor.player_slot, "frame": actor.current_source_frame(),
			"x": actor.source_x, "y": actor.source_y, "xscale": actor.scale.x * 100,
			"action": actor.ai_source_state.read_field("动作"), "hp": actor.health,
			"ql": actor.energy, "sw": actor.sw, "touch": actor.ai_source_state.read_field("touch"),
			"touchFloor": actor.ai_source_state.read_field("touchFloor"), "hits": actor.hits,
			"paused": actor.root_zhanting, "hstm": actor.ai_source_state.read_field("hstm"),
			"hurtSkling": actor.ai_source_state.read_field("hurtSkling")})
	_capture_geometry(tick)
	for actor: FighterRuntime in [game.naruto, game.ichigo]:
		for instance_name: String in fixture.get("projectile_probe", {}).get(actor.player_slot, []):
			var origin := actor.named_instance_origin(instance_name)
			if not origin.is_finite():
				continue
			var offset := actor.instance_local_offset(instance_name)
			var variables := actor.instance_source_variables(instance_name)
			# Read authored twips directly; Vector2 origins lose source precision.
			var matrix: Dictionary = {}
			for placement: Dictionary in actor._frames[actor.current_source_frame()]["display_list"]:
				if str(placement.get("name", "")) == instance_name:
					matrix = placement.get("matrix", {})
					break
			projectile_rows.append({"tick": tick, "slot": actor.player_slot, "name": instance_name,
				"frame": actor.instance_clip_frame(instance_name),
				"x": float(matrix.get("translateX", 0)) / 20.0 + offset.x,
				"y": float(matrix.get("translateY", 0)) / 20.0 + offset.y,
				"played": variables.get("played"), "movspeed": variables.get("movspeed")})
	for helper in [game.naruto_helper, game.ichigo_helper]:
		helper_rows.append({"tick": tick, "slot": "p1" if helper == game.naruto_helper else "p2",
			"frame": helper.current_source_frame(), "x": helper.position.x, "y": helper.position.y,
			"facing": helper.facing, "attacking": helper.attacking,
			"action": helper.source_action, "visible": helper.visible,
			"root_paused": helper.owner_fighter.root_zhanting if is_instance_valid(helper.owner_fighter) else false,
			"parent_frame": helper.owner_fighter.current_source_frame() if is_instance_valid(helper.owner_fighter) else -1,
			"atm1": helper.instance_clip_frame("atm1"), "atm2": helper.instance_clip_frame("atm2"),
			"atm3": helper.instance_clip_frame("atm3")})
	var bindings := {
		"p1": {"up": KEY_W, "down": KEY_S, "left": KEY_A, "right": KEY_D,
			"attack": KEY_J, "jump": KEY_K, "dash": KEY_L, "ranged": KEY_U, "special": KEY_I, "summon": KEY_O},
		"p2": {"up": KEY_UP, "down": KEY_DOWN, "left": KEY_LEFT, "right": KEY_RIGHT,
			"attack": KEY_KP_1, "jump": KEY_KP_2, "dash": KEY_KP_3, "ranged": KEY_KP_4, "special": KEY_KP_5, "summon": KEY_KP_6}}
	var held := {}
	for item in fixture.inputs:
		if tick >= int(item.start) and tick < int(item.end):
			for key in item["keys"]: held[bindings[item.slot][key]] = true
	for slot in bindings.values():
		for key in slot.values():
			var event := InputEventKey.new()
			event.keycode = key
			event.physical_keycode = key
			event.pressed = held.has(key)
			Input.parse_input_event(event)
	Input.flush_buffered_events()


func _capture_geometry(tick: int) -> void:
	var probe: Dictionary = fixture.get("geometry_probe", {})
	if probe.is_empty():
		return
	var frame_ranges: Dictionary = probe.get("source_frame_ranges", {})
	var instance_names: Dictionary = probe.get("instances", {})
	for actor: FighterRuntime in [game.naruto, game.ichigo]:
		var slot := str(actor.player_slot)
		var frame := actor.current_source_frame()
		var watched_frames: Array = frame_ranges.get(slot, [])
		var watch_frame := false
		for watched_frame in watched_frames:
			if int(watched_frame) == frame:
				watch_frame = true
				break
		if not watch_frame:
			continue
		var current_frame: Dictionary = actor._frames.get(frame, {})
		var placements: Array = current_frame.get("display_list", [])
		var placement_rows: Array = []
		var bounds_rows: Dictionary = {}
		for instance_name_variant in instance_names.get(slot, []):
			var instance_name := str(instance_name_variant)
			var placement: Dictionary = {}
			for candidate: Dictionary in placements:
				if str(candidate.get("name", "")) == instance_name:
					placement = candidate
					break
			var local_bounds := actor.instance_local_bounds(instance_name)
			var global_bounds := actor.instance_global_bounds(instance_name)
			var definition_chain: Array = []
			var character_id := int(placement.get("character_id", -1))
			while character_id >= 0:
				var definition: Dictionary = actor._definitions.get(character_id, {})
				if definition.is_empty():
					break
				var definition_record := {"character_id": character_id,
					"type": definition.get("type", "")}
				if definition.has("shape_bounds_twips"):
					definition_record["shape_bounds_twips"] = definition["shape_bounds_twips"]
				definition_chain.append(definition_record)
				var references: Array = definition.get("referenced_character_ids", [])
				if references.size() != 1:
					break
				character_id = int(references[0])
			bounds_rows[instance_name] = {
				"live": not placement.is_empty(),
				"placement": placement,
				"definition_chain": definition_chain,
				"local_bounds": _rect_record(local_bounds),
				"global_bounds": _rect_record(global_bounds),
				"clip_frame": actor.instance_clip_frame(instance_name),
			}
			if not placement.is_empty():
				placement_rows.append(placement)
		var defender: FighterRuntime = actor.opponent
		var body_bounds := defender.instance_global_bounds("bdmn") if defender != null else Rect2()
		var body_local_bounds := defender.instance_local_bounds("bdmn") if defender != null else Rect2()
		var body_placement: Dictionary = {}
		if defender != null:
			var defender_frame: Dictionary = defender._frames.get(defender.current_source_frame(), {})
			for candidate: Dictionary in defender_frame.get("display_list", []):
				if str(candidate.get("name", "")) == "bdmn":
					body_placement = candidate
					break
		var attack_name := str(probe.get("attack_by_slot", {}).get(slot, ""))
		var attack_bounds: Rect2 = global_bounds_for(bounds_rows, attack_name)
		geometry_rows.append({
			"tick": tick,
			"slot": slot,
			"fighter": actor.fighter_name,
			"source_frame": frame,
			"action": actor.action,
			"position": {"x": actor.source_x, "y": actor.source_y},
			"facing": actor.facing,
			"scale": {"x": actor.scale.x, "y": actor.scale.y},
			"root_transform": _transform_record(actor.global_transform),
			"source_node_matrices_leaf_to_root": actor._source_node_matrices(),
			"source_wrapper_matrix": actor._timeline.get("wrapper", {}).get("matrix", {}),
			"node_path": str(actor.get_path()),
			"named_instances": actor.current_named_instances(),
			"watched_placements": placement_rows,
			"bounds": bounds_rows,
			"defender": {
				"slot": defender.player_slot if defender != null else "",
				"frame": defender.current_source_frame() if defender != null else -1,
				"action": defender.action if defender != null else -1,
				"hp": defender.health if defender != null else -1,
				"ql": defender.energy if defender != null else -1,
				"position": {"x": defender.source_x, "y": defender.source_y} if defender != null else {},
				"facing": defender.facing if defender != null else 0,
				"named_instances": defender.current_named_instances() if defender != null else [],
				"body_placement": body_placement,
				"body_local_bounds": _rect_record(body_local_bounds),
				"body_bounds": _rect_record(body_bounds),
			},
			"attack_body_intersects": SourceHitTest.intersects(attack_bounds, body_bounds)
				if attack_bounds.has_area() and body_bounds.has_area() else false,
		})


func global_bounds_for(bounds_rows: Dictionary, instance_name: String) -> Rect2:
	if not bounds_rows.has(instance_name):
		return Rect2()
	var record: Dictionary = bounds_rows[instance_name]
	var raw: Dictionary = record.get("global_bounds", {})
	return Rect2(Vector2(float(raw.get("x", 0.0)), float(raw.get("y", 0.0))),
		Vector2(float(raw.get("width", 0.0)), float(raw.get("height", 0.0))))


func _rect_record(rectangle: Rect2) -> Dictionary:
	return {"x": rectangle.position.x, "y": rectangle.position.y,
		"width": rectangle.size.x, "height": rectangle.size.y}


func _transform_record(transform: Transform2D) -> Dictionary:
	return {
		"x_axis": [transform.x.x, transform.x.y],
		"y_axis": [transform.y.x, transform.y.y],
		"origin": [transform.origin.x, transform.origin.y],
	}


func _on_diagnostic_event(event: Dictionary) -> void:
	if str(event.get("type", "")) != "hit_contact":
		return
	var payload: Dictionary = event.get("payload", {})
	if str(payload.get("kind", "")) != "fighter":
		return
	var slot := str(payload.get("slot", ""))
	var attacker: FighterRuntime = game.naruto if slot == "p1" else game.ichigo
	var defender: FighterRuntime = attacker.opponent
	var instance_name := str(payload.get("instanceName", ""))
	var placement: Dictionary = {}
	for candidate: Dictionary in attacker._frames.get(attacker.current_source_frame(), {}).get("display_list", []):
		if str(candidate.get("name", "")) == instance_name:
			placement = candidate
			break
	var attack_local := attacker.instance_local_bounds(instance_name)
	var attack_global := attacker.instance_global_bounds(instance_name)
	var body_local := defender.instance_local_bounds("bdmn")
	var body_global := defender.instance_global_bounds("bdmn")
	contact_rows.append({
		"event": event,
		"source_frame": attacker.current_source_frame(),
		"facing": attacker.facing,
		"attacker_position": {"x": attacker.source_x, "y": attacker.source_y},
		"attacker_node_path": str(attacker.get_path()),
		"attacker_node_matrices_leaf_to_root": attacker._source_node_matrices(),
		"attack_placement": placement,
		"attack_local_bounds": _rect_record(attack_local),
		"attack_global_bounds": _rect_record(attack_global),
		"attack_game_bounds": _source_game_rect(attack_local, attacker),
		"defender": {
			"source_frame": defender.current_source_frame(),
			"action": defender.action,
			"hp": defender.health,
			"ql": defender.energy,
			"position": {"x": defender.source_x, "y": defender.source_y},
			"facing": defender.facing,
			"node_matrices_leaf_to_root": defender._source_node_matrices(),
			"named_instances": defender.current_named_instances(),
			"body_placement": _named_placement(defender, "bdmn"),
			"body_local_bounds": _rect_record(body_local),
			"body_global_bounds": _rect_record(body_global),
			"body_game_bounds": _source_game_rect(body_local, defender),
		},
	})


func _named_placement(actor: FighterRuntime, instance_name: String) -> Dictionary:
	for placement: Dictionary in actor._frames.get(actor.current_source_frame(), {}).get("display_list", []):
		if str(placement.get("name", "")) == instance_name:
			return placement
	return {}


func _source_game_rect(local_bounds: Rect2, actor: FighterRuntime) -> Dictionary:
	var actor_matrices := actor._source_node_matrices()
	if actor_matrices.is_empty():
		return _rect_record(Rect2())
	var local_twips := Rect2i(
		Vector2i(roundi(local_bounds.position.x * 20.0), roundi(local_bounds.position.y * 20.0)),
		Vector2i(roundi(local_bounds.size.x * 20.0), roundi(local_bounds.size.y * 20.0)))
	var world_twips := SourceMatrixBounds.bounds_for_chain(local_twips, [actor_matrices[0]])
	return _rect_record(Rect2(Vector2(world_twips.position) / 20.0, Vector2(world_twips.size) / 20.0))


func _validate_resource_interventions() -> void:
	var interventions: Variant = fixture.get("resource_interventions", [])
	assert(interventions is Array, "resource_interventions must be an array")
	var ids: Dictionary = {}
	for intervention: Variant in interventions:
		assert(intervention is Dictionary, "resource intervention must be an object")
		var intervention_id := str(intervention.get("id", ""))
		var tick := int(intervention.get("tick", 0))
		var slot := str(intervention.get("slot", ""))
		var resource := str(intervention.get("resource", ""))
		var value: Variant = intervention.get("value")
		assert(not intervention_id.is_empty() and not ids.has(intervention_id), "resource intervention id must be unique")
		assert(tick >= 1 and tick <= int(fixture.get("frames", 0)), "resource intervention tick is out of range")
		assert(slot in ["p1", "p2"] and resource == "energy", "unsupported resource intervention")
		assert(value is int or value is float, "resource intervention value must be numeric")
		ids[intervention_id] = true
	var preconditions: Variant = fixture.get("source_state_preconditions", {})
	assert(preconditions is Dictionary, "source_state_preconditions must be an object")
	for slot in preconditions:
		assert(str(slot) in ["p1", "p2"], "source state precondition slot must be p1 or p2")
		assert(preconditions[slot] is Dictionary, "source state precondition must be an object")
		for field in preconditions[slot]:
			assert(str(field) in ["health", "wudi"], "unsupported source state precondition: " + str(field))
			var value: Variant = preconditions[slot][field]
			if field == "health":
				assert(value is int or value is float, "health precondition must be numeric")
			else:
				assert(value is bool, "wudi precondition must be boolean")


func _apply_source_state_preconditions(actor: FighterRuntime) -> void:
	var slot := str(actor.player_slot)
	var preconditions: Dictionary = fixture.get("source_state_preconditions", {}).get(slot, {})
	for field in preconditions:
		var value: Variant = preconditions[field]
		var previous: Variant = actor.health if field == "health" else actor.ai_source_state.read_field(str(field))
		if field == "health":
			actor.health = float(value)
		else:
			actor.ai_source_state.apply_write({"field": str(field), "value": value})
		intervention_rows.append({"id": "source_state:%s:%s" % [slot, field], "tick": 0,
			"slot": slot, "resource": str(field), "previous": previous, "value": value,
			"phase": "source_state_precondition_before_first_observation"})


func _apply_resource_interventions(tick: int) -> void:
	for intervention: Dictionary in fixture.get("resource_interventions", []):
		if int(intervention.tick) != tick:
			continue
		var intervention_id := str(intervention.id)
		assert(not applied_interventions.has(intervention_id), "resource intervention executed twice: " + intervention_id)
		var actor: FighterRuntime = game.naruto if str(intervention.slot) == "p1" else game.ichigo
		var previous: float = float(actor.energy)
		actor.energy = float(intervention.value)
		applied_interventions[intervention_id] = true
		intervention_rows.append({"id": intervention_id, "tick": tick, "slot": intervention.slot,
			"resource": intervention.resource, "previous": previous, "value": actor.energy,
			"phase": "after_actor_advance_before_root_observation_and_next_tick_input"})
