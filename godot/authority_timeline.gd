extends TimelinePreview

# A renderer, never a source timeline/controller. Playheads refer to local
# compiled placements, not decoded copies or transmitted leaf geometry.
var intro_shapes := false
var _placement_x: Array = []
var _placement_frames: Array = []
var error := ""

func _ready() -> void:
	autoplay = false
	play_timeline_sounds = false
	if _frames.is_empty(): _load_data()
	set_physics_process(false)

func apply_inputs(value: Dictionary) -> String:
	error = ""
	if not value.get("frame") is int or not _frames.has(value.frame): return "invalid_display_frame"
	_current_frame = value.frame
	_instance_local_offsets.clear()
	for name in value.get("offsets", {}):
		var point: Array = value.offsets[name]
		_instance_local_offsets[name] = Vector2(point[0], point[1])
	hidden_instance_names = PackedStringArray(value.get("hidden", []))
	_source_color_mul = _color(value.mul)
	_source_color_add = _color(value.add)
	_source_color_matrix = value.matrix.duplicate()
	_source_placement_filters_cleared = value.filters_cleared
	preserve_root_depths = value.preserve_depths
	intro_shapes = value.intro
	_placement_x.clear()
	_placement_frames.clear()
	_retained_visual_clips = _bind(value.clips, _frames[_current_frame].display_list)
	if not error.is_empty(): return error
	_wrapper_visual_clips = _bind(value.wrapper_clips, _timeline.get("wrapper_siblings", []))
	if not error.is_empty(): return error
	materialize_display()
	return ""

func _bind(records: Array, placements: Array, level: int = 0) -> Dictionary:
	var clips := {}
	if level > 20:
		error = "display_clip_depth"
		return clips
	var expected := 0
	for placement: Dictionary in placements:
		if _definitions.get(int(placement.get("character_id", -1)), {}).get("type") == "DefineSpriteTag": expected += 1
	if records.size() != expected:
		error = "incomplete_display_playheads"
		return {}
	for record: Array in records:
		if record.size() != 6 or clips.has(int(record[0])):
			error = "invalid_display_clip"
			return {}
		var matches: Array = placements.filter(func(p: Dictionary) -> bool:
			return int(p.depth) == int(record[0]) and int(p.character_id) == int(record[1]) and int(p.get("placed_frame", 1)) == int(record[2]))
		if matches.size() != 1:
			error = "unbound_display_placement"
			return {}
		var placement: Dictionary = matches[0]
		var definition: Dictionary = _definitions.get(int(record[1]), {})
		if definition.get("type") != "DefineSpriteTag":
			error = "display_clip_not_sprite"
			return {}
		var frames: Array = definition.get("display_list_frames", [])
		var frame := int(record[3])
		if frame < 1 or (not frames.is_empty() and frame > frames.size()):
			error = "display_child_frame"
			return {}
		var children: Array = frames[frame - 1] if not frames.is_empty() else definition.get("first_frame_display_list", [])
		_placement_frames.append([placement, frame])
		clips[int(record[0])] = {"placement": placement, "frame": frame, "children": _bind(record[5], children, level + 1)}
		if record[4] != null: _placement_x.append([placement, float(record[4])])
	return clips

func _nested_frame(placement: Dictionary, _timeline_frame: int, _frame_count: int, _clip_age: int = 0) -> int:
	for item: Array in _placement_frames:
		if is_same(item[0], placement): return int(item[1])
	return 1

func _placement_transform(placement: Dictionary) -> Transform2D:
	var result := super._placement_transform(placement)
	for item: Array in _placement_x:
		if is_same(item[0], placement): result.origin.x = item[1]
	return result

func _render_solid_fills(definition: Dictionary, placement_transform: Transform2D,
	depth: int, rgb_mul: Color, rgb_add: Color, alpha: float, blend: int = 1) -> void:
	if not intro_shapes:
		super._render_solid_fills(definition, placement_transform, depth, rgb_mul, rgb_add, alpha, blend)
		return
	# Reuse IntroClip's pure raster renderer without its playback/sound lifecycle.
	var renderer := IntroClip.new()
	renderer.fighter_directory = fighter_directory
	renderer._source_color_matrix = _source_color_matrix
	renderer._render_solid_fills(definition, placement_transform, depth, rgb_mul, rgb_add, alpha, blend)
	for child in renderer.get_children():
		renderer.remove_child(child)
		add_child(child)
	renderer.free()

static func _color(value: Array) -> Color:
	return Color(value[0], value[1], value[2], value[3])
