extends RefCounted

const Wire = preload("res://authority_wire.gd")
const AudioLedger = preload("res://authority_audio.gd")
var audio := AudioLedger.new()
var _visual_root: Node

const RenderTimeline = preload("res://authority_timeline.gd")
const MAX_OWNERS := 256
const MAX_CLIPS := 2048
var error := ""
var resources: Array[String] = []
var _templates := {}
var nodes := {}
var _clip_count := 0
var _root: Node
var _last_frame := -1
var _host: Node
var _ids := {}
var _next_id := 0
var _health_spec: Dictionary = JSON.parse_string(FileAccess.get_file_as_string("res://generated/main/health/presentation.json"))
var _intro_spec: Dictionary = JSON.parse_string(FileAccess.get_file_as_string("res://generated/main/intro/intro.json"))
var _helper_spec: Dictionary = JSON.parse_string(FileAccess.get_file_as_string("res://generated/main/helper_portraits/presentation.json"))

func _init() -> void:
	for path in ["res://generated/fighters", "res://generated/forms", "res://generated/helpers", "res://generated/stages",
		"res://generated/main/player_markers", "res://generated/main/intro", "res://generated/main/blackMu", "res://generated/main/ts_face",
		"res://generated/main/ko", "res://generated/main/timeout", "res://generated/effects"]:
		_catalog(path)
	resources.sort()

func _catalog(path: String) -> void:
	if FileAccess.file_exists(path.path_join("timeline.json")): resources.append(path)
	for directory in DirAccess.get_directories_at(path): _catalog(path.path_join(directory))

static func matrix(value: Transform2D) -> Array:
	return [value.x.x, value.x.y, value.y.x, value.y.y, value.origin.x, value.origin.y]

static func transform_of(value: Array) -> Transform2D:
	return Transform2D(Vector2(value[0], value[1]), Vector2(value[2], value[3]), Vector2(value[4], value[5]))

static func color(value: Color) -> Array:
	return [value.r, value.g, value.b, value.a]

func capture_timeline(node: TimelinePreview) -> Dictionary:
	var resource := resources.find(node.fighter_directory)
	if resource < 0:
		error = "unregistered_display_resource:" + node.fighter_directory
		return {}
	var offsets := {}
	for name in node._instance_local_offsets:
		var offset: Vector2 = node._instance_local_offsets[name]
		offsets[name] = [offset.x, offset.y]
	return {"resource": resource, "frame": node._current_frame,
		"mul": color(node._source_color_mul), "add": color(node._source_color_add),
		"matrix": node._source_color_matrix.duplicate(), "filters_cleared": node._source_placement_filters_cleared,
		"preserve_depths": node.preserve_root_depths, "hidden": Array(node.hidden_instance_names),
		"offsets": offsets, "intro": node is IntroClip,
		"wrapper_clips": _capture_clips(node, node._timeline.get("wrapper_siblings", []), 1, 0, node._wrapper_visual_clips),
		"clips": _capture_clips(node, node._frames.get(node._current_frame, {}).get("display_list", []), node._current_frame, 0, node._retained_visual_clips)}

func _capture_clips(node: TimelinePreview, placements: Array, frame: int, age: int, retained: Dictionary, level: int = 0) -> Array:
	var result := []
	if level > 20:
		error = "display_clip_depth"
		return result
	for placement: Dictionary in placements:
		var definition: Dictionary = node._definitions.get(int(placement.get("character_id", -1)), {})
		if definition.get("type") != "DefineSpriteTag": continue
		_clip_count += 1
		if _clip_count > MAX_CLIPS:
			error = "display_clip_limit"
			return []
		var frames: Array = definition.get("display_list_frames", [])
		var clip: Dictionary = node._visual_clip_at(placement, retained)
		var local_frame := node._nested_frame(placement, frame, frames.size(), age)
		if not clip.is_empty(): local_frame = int(clip.frame)
		var child_age := age
		var name := str(placement.get("name", ""))
		if node._instance_local_frames.has(name): child_age = int(node._instance_local_frames[name].get("age", 0))
		var children: Array = frames[local_frame - 1] if not frames.is_empty() else definition.get("first_frame_display_list", [])
		var override_x: Variant = null
		if node is KoClip:
			var live: Dictionary = node._live_clip(placement)
			override_x = live.get("x_override")
		result.append([int(placement.depth), int(placement.character_id), int(placement.get("placed_frame", 1)), local_frame, override_x,
			_capture_clips(node, children, local_frame, child_age, clip.get("children", {}), level + 1)])
	return result

func _id(node: Node) -> int:
	var native_id := node.get_instance_id()
	if not _ids.has(native_id):
		_next_id += 1
		_ids[native_id] = _next_id
	return int(_ids[native_id])

func capture(game: Node) -> Dictionary:
	error = ""
	_clip_count = 0
	_host = game
	game.set_meta("authority_audio", audio)
	var records := []
	_capture_node(game, 0, records)
	if records.size() > MAX_OWNERS: error = "display_owner_limit"
	var sound_state := audio.capture(game.physics_tick)
	if not audio.error.is_empty(): error = audio.error
	return {"version": Wire.VERSION, "frame": game.physics_tick, "owners": records, "audio": sound_state,
		"intro_active": game.battle_intro.active, "intro_polling": game.battle_intro.polling,
		"terminal": game.ko_terminal_pending, "winner": null if game.ko_state.get("_root.p1ws", 1) == game.ko_state.get("_root.p2ws", 1) else (0 if game.ko_state.get("_root.p1ws", 1) > game.ko_state.get("_root.p2ws", 1) else 1)} if error.is_empty() else {}

func _capture_node(node: Node, parent: int, records: Array) -> void:
	if node.is_queued_for_deletion(): return
	if node in [_host.title_menu, _host.key_settings, _host.config_menu, _host.character_selection,
		_host.map_selection, _host.pause_menu, _host.fight_hud, _host.combo_hud]: return
	if node is AudioStreamPlayer or node is Timer: return
	var kind := "group"
	var state := {}
	var terminal := false
	if node is TimelinePreview:
		kind = "timeline"
		state = capture_timeline(node)
		terminal = true
	elif node is HealthHud:
		kind = "health"
		state = {"health": [[_host.naruto.health, _host.naruto.max_health], [_host.ichigo.health, _host.ichigo.max_health]],
			"trail": node.trail.duplicate(), "low_frame": node.low_frame.duplicate(), "low_health": node.low_health.duplicate(),
			"wins": Array(node.win_frames), "placement": _host.battle_intro.hud_frame,
			"timer": {"unlimited": node.countdown.unlimited, "digits": node.countdown.digit_frames.duplicate()} if node.countdown != null else {}}
		terminal = true
	elif node is EnergyBar:
		kind = "energy"
		state = {"energy": node._display_energy, "child_frame": node._qt_child_frame, "mirrored": node.mirrored, "helper": node.helper_id}
		terminal = true
	elif node is ShadowSnapshot:
		kind = "shadow"
		state = node.authority_pose.duplicate(true)
		state["alpha"] = node.source_alpha
		if state.is_empty() or not state.has("pose"): error = "missing_shadow_pose"
		terminal = true
	elif node == _host.screen_flash:
		kind = "flash"
		var tint: Variant = node.material.get_shader_parameter("tint")
		var opacity: Variant = node.material.get_shader_parameter("opacity")
		state = {"tint": [tint.x, tint.y, tint.z, 1.0] if tint is Vector3 else [1.0, 1.0, 1.0, 1.0], "opacity": opacity if opacity != null else 0.0}
		terminal = true
	elif node is ColorRect and node.name == "Background":
		kind = "background"
		state = {"color": color(node.color)}
		terminal = true
	elif node is Node2D and node.get_class() != "Node2D":
		error = "unregistered_display_geometry:" + str(node.get_path())
		return
	elif node is CanvasItem and not (node is Node2D or node == _host):
		error = "unregistered_display_owner:" + str(node.get_path())
		return
	var index := records.size()
	var identifier := _id(node)
	var common := {"id": identifier, "parent": parent, "kind": kind, "state": state,
		"transform": matrix(node.get_transform()) if node is CanvasItem else matrix(Transform2D.IDENTITY),
		"visible": node.visible if node is CanvasItem else true, "z": node.z_index if node is CanvasItem else 0,
		"modulate": color(node.modulate) if node is CanvasItem else color(Color.WHITE),
		"self_modulate": color(node.self_modulate) if node is CanvasItem else color(Color.WHITE)}
	records.append(common)
	if not terminal:
		for child in node.get_children(): _capture_node(child, identifier, records)
		if records.size() == index + 1 and node != _host: records.remove_at(index)

func configure_presenter(root: Node) -> void:
	_root = root
	_visual_root = Node2D.new()
	_root.add_child(_visual_root)
	_last_frame = -1

func apply(snapshot: Dictionary) -> String:
	error = ""
	if _root == null or snapshot.get("version") != Wire.VERSION or not snapshot.get("owners") is Array \
		or snapshot.owners.size() > MAX_OWNERS or not snapshot.get("frame") is int:
		return "invalid_display_snapshot"
	if snapshot.frame < _last_frame: return "stale_display_snapshot"
	if snapshot.size() != 8 or snapshot.frame < 0 or not snapshot.get("intro_active") is bool or not snapshot.get("intro_polling") is bool or not snapshot.get("terminal") is bool or snapshot.get("winner") not in [null, 0, 1]:
		return "invalid_display_envelope"
	var sound_problem := audio.validate(snapshot.get("audio"), snapshot.frame)
	if not sound_problem.is_empty(): return sound_problem
	_clip_count = 0
	var seen := {}
	for record in snapshot.owners:
		var problem := _validate_record(record, seen)
		if not problem.is_empty(): return problem
		seen[record.id] = true
	# Validate every resource and binding in a detached staging graph before
	# replacing the visible graph. No gameplay scene callbacks are instantiated.
	var staged := Node2D.new()
	var staged_nodes := {}
	for record: Dictionary in snapshot.owners:
		var node: Node = _new_owner(record)
		if node == null:
			staged.free()
			return error
		var parent: Node = staged if record.parent == 0 else staged_nodes[record.parent]
		parent.add_child(node)
		staged_nodes[record.id] = node
		var problem := _apply_owner(node, record)
		if not problem.is_empty():
			staged.free()
			return problem
	for child in _visual_root.get_children():
		_visual_root.remove_child(child)
		child.queue_free()
	_visual_root.add_child(staged)
	audio.apply(snapshot.audio, snapshot.frame, _root)
	nodes = staged_nodes
	_last_frame = snapshot.frame
	return ""

func _validate_record(value: Variant, seen: Dictionary) -> String:
	if not value is Dictionary or value.size() != 9: return "invalid_display_owner"
	if not value.get("id") is int or value.id <= 0 or seen.has(value.id): return "duplicate_display_owner"
	if not value.get("parent") is int or (value.parent != 0 and not seen.has(value.parent)): return "invalid_display_parent"
	if value.get("kind") not in ["group", "timeline", "health", "energy", "flash", "background", "shadow"]: return "unknown_display_owner"
	if not value.get("state") is Dictionary or not value.get("visible") is bool or not value.get("z") is int or absi(value.z) > 4096: return "invalid_display_fields"
	for pair in [["transform", 6], ["modulate", 4], ["self_modulate", 4]]:
		if not value.get(pair[0]) is Array or value[pair[0]].size() != pair[1]: return "invalid_display_transform"
		for number in value[pair[0]]:
			if typeof(number) not in [TYPE_INT, TYPE_FLOAT] or not is_finite(float(number)) or absf(float(number)) > 1e6: return "invalid_display_scalar"
	return _validate_state(value.kind, value.state)

static func _numbers(value: Variant, count: int) -> bool:
	if not value is Array or value.size() != count: return false
	for item in value:
		if typeof(item) not in [TYPE_INT, TYPE_FLOAT] or not is_finite(float(item)) or absf(float(item)) > 1e6: return false
	return true

static func _integers(value: Variant, count: int, minimum: int, maximum: int) -> bool:
	if not value is Array or value.size() != count: return false
	for item in value:
		if not item is int or item < minimum or item > maximum: return false
	return true

func _validate_state(kind: String, state: Dictionary) -> String:
	match kind:
		"group":
			if not state.is_empty(): return "invalid_display_group"
		"timeline": return _validate_timeline(state)
		"shadow":
			if state.size() != 4 or not state.get("pose") is Dictionary or not _numbers(state.get("scale"), 2) or not state.get("rgb") is Dictionary or not _numbers([state.get("alpha")], 1): return "invalid_display_shadow"
			for component in state.scale:
				if absf(float(component)) < 0.001 or absf(float(component)) > 8: return "invalid_shadow_scale"
			for key in state.rgb:
				if key not in ["R", "G", "B"] or not _numbers([state.rgb[key]], 1): return "invalid_display_shadow_tint"
			return _validate_timeline(state.pose)
		"background":
			if state.size() != 1 or not _numbers(state.get("color"), 4): return "invalid_display_background"
		"flash":
			if state.size() != 2 or not _numbers(state.get("tint"), 4) or not _numbers([state.get("opacity")], 1): return "invalid_display_flash"
		"energy":
			if state.size() != 4 or not _numbers([state.get("energy")], 1) or state.energy < 0 or state.energy > 300 or not _integers([state.get("child_frame")], 1, 1, 10) or not state.get("mirrored") is bool or not state.get("helper") is String or not _helper_spec.portraits.has(state.helper): return "invalid_display_energy"
		"health":
			if state.size() != 7 or not state.get("health") is Array or state.health.size() != 2: return "invalid_display_health"
			for pair in state.health:
				if not _numbers(pair, 2) or pair[1] <= 0: return "invalid_display_health"
			if not _numbers(state.get("trail"), 2) or not _integers(state.get("low_frame"), 2, 0, 19) or not state.get("low_health") is Array or state.low_health.size() != 2: return "invalid_display_health_trail"
			for low in state.low_health:
				if not low is bool: return "invalid_display_health_warning"
			if not _integers(state.get("wins"), 2, 1, 100): return "invalid_display_wins"
			for frame in state.wins:
				if not _health_spec.win_frames.has(str(frame)): return "invalid_display_wins"
			if not state.get("placement") is int or not _intro_spec.hud_frames.has(str(state.placement)): return "invalid_display_hud_placement"
			if not state.get("timer") is Dictionary: return "invalid_display_timer"
			if not state.timer.is_empty():
				if state.timer.size() != 2 or not state.timer.get("unlimited") is bool or not state.timer.get("digits") is Dictionary or state.timer.digits.size() != 2 or not _integers([state.timer.digits.get("十"), state.timer.digits.get("个")], 2, 1, 10): return "invalid_display_timer"
	return ""

func _validate_timeline(state: Dictionary) -> String:
	if state.size() != 12 or not state.get("resource") is int or state.resource < 0 or state.resource >= resources.size(): return "invalid_display_resource"
	if not state.get("frame") is int or state.frame < 1 or not state.get("clips") is Array or not state.get("wrapper_clips") is Array or not state.get("offsets") is Dictionary: return "invalid_display_playheads"
	if not _numbers(state.get("mul"), 4) or not _numbers(state.get("add"), 4) or not state.get("matrix") is Array or state.matrix.size() not in [0, 20] or not _numbers(state.matrix, state.matrix.size()): return "invalid_display_color"
	for key in ["filters_cleared", "preserve_depths", "intro"]:
		if not state.get(key) is bool: return "invalid_display_flags"
	if not state.get("hidden") is Array: return "invalid_display_hidden"
	for name in state.hidden:
		if not name is String or name.length() > 256: return "invalid_display_hidden"
	for name in state.offsets:
		if not name is String or name.length() > 256 or not _numbers(state.offsets[name], 2): return "invalid_display_offset"
	var problem := _validate_clips(state.clips)
	return problem if not problem.is_empty() else _validate_clips(state.wrapper_clips)

func _validate_clips(clips: Array, level: int = 0) -> String:
	if level > 20: return "display_clip_depth"
	for clip in clips:
		_clip_count += 1
		if _clip_count > MAX_CLIPS: return "display_clip_limit"
		if not clip is Array or clip.size() != 6: return "invalid_display_clip"
		if not _integers(clip.slice(0, 4), 4, 0, 1000000) or clip[3] < 1 or not clip[5] is Array: return "invalid_display_clip"
		if clip[4] != null and not _numbers([clip[4]], 1): return "invalid_display_clip_offset"
		var problem := _validate_clips(clip[5], level + 1)
		if not problem.is_empty(): return problem
	return ""

func _new_owner(record: Dictionary) -> Node:
	match record.kind:
		"timeline":
			var node := RenderTimeline.new()
			node.fighter_directory = resources[record.state.resource]
			if not _templates.has(record.state.resource):
				node._load_data()
				_templates[record.state.resource] = [node._timeline, node._fighter, node._definitions, node._assets, node._frames]
			else:
				var template: Array = _templates[record.state.resource]
				node._timeline = template[0]
				node._fighter = template[1]
				node._definitions = template[2]
				node._assets = template[3]
				node._frames = template[4]
			return node
		"health":
			var node := HealthHud.new()
			node._ready()
			return node
		"energy":
			var node := EnergyBar.new()
			node.mirrored = record.state.mirrored
			node._ready()
			return node
		"flash", "background": return ColorRect.new()
		"shadow": return ShadowSnapshot.new()
	return Node2D.new()

func _apply_owner(node: Node, record: Dictionary) -> String:
	var state: Dictionary = record.state
	node.visible = record.visible
	node.z_index = record.z
	node.modulate = RenderTimeline._color(record.modulate)
	node.self_modulate = RenderTimeline._color(record.self_modulate)
	if node is Node2D: node.transform = transform_of(record.transform)
	else:
		node.position = Vector2(record.transform[4], record.transform[5])
		node.size = Vector2(600, 400)
	match record.kind:
		"timeline": return node.apply_inputs(state)
		"shadow":
			var actor: Node = _new_owner({"kind": "timeline", "state": state.pose})
			var problem: String = actor.apply_inputs(state.pose)
			if not problem.is_empty():
				actor.free()
				return problem
			var bounds := Rect2()
			for placement: Dictionary in actor._frames[state.pose.frame].display_list:
				var placed: Rect2 = node._placement_bounds(actor, placement, state.pose.frame, actor._wrapper_transform())
				if placed.has_area(): bounds = bounds.merge(placed) if bounds.has_area() else placed
			var bitmap_size := Vector2i(int(bounds.size.x * absf(state.scale[0])), int(bounds.size.y * absf(state.scale[1])))
			if bitmap_size.x < 1 or bitmap_size.y < 1 or bitmap_size.x > 4096 or bitmap_size.y > 4096:
				actor.free()
				return "invalid_shadow_dimensions"
			node.captured_frame = state.pose.frame
			node._capture_visual(actor, state.rgb, Vector2(state.scale[0], state.scale[1]))
			node.source_alpha = state.alpha
			node.bitmap.modulate.a = maxf(state.alpha / 100.0, 0)
			actor.free()
		"health":
			node.presentation_health = state.health
			node.presentation_countdown = state.timer
			node.trail.assign(state.trail)
			node.low_frame.assign(state.low_frame)
			node.low_health.assign(state.low_health)
			node.win_frames = PackedInt32Array(state.wins)
			node.spec["placement"] = _intro_spec.hud_frames[str(state.placement)]
			node.queue_redraw()
		"energy":
			node.energy = state.energy
			node._qt_child_frame = state.child_frame
			node.set_helper(state.helper)
		"background": node.color = RenderTimeline._color(state.color)
		"flash":
			var shader := Shader.new()
			shader.code = load("res://main.gd").SHINE_SHADER
			var material := ShaderMaterial.new()
			material.shader = shader
			material.set_shader_parameter("tint", Vector3(state.tint[0], state.tint[1], state.tint[2]))
			material.set_shader_parameter("opacity", state.opacity)
			node.material = material
	return ""
