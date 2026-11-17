class_name TimelinePreview
extends Node2D

signal nested_source_sound_started(event: Dictionary)

@export var fighter_directory: String
@export var initial_action: String = "砍1"
@export var initial_frame: int = 1
@export var autoplay: bool = true
@export var show_collision_shapes: bool = false
@export var preserve_root_depths: bool = false
@export var play_timeline_sounds: bool = true

var _timeline: Dictionary
var _fighter: Dictionary
var _definitions: Dictionary = {}
var _assets: Dictionary = {}
var _frames: Dictionary = {}
var _action_start: int
var _action_end: int
var _current_frame: int
var _instance_local_offsets: Dictionary = {}
var _instance_local_frames: Dictionary = {}
var _retained_visual_clips: Dictionary = {}
var _wrapper_visual_clips: Dictionary = {}
var independent_visual_clock := false
var hidden_instance_names: PackedStringArray = []
# Source StartSound on the current timeline frame. Hit sparks use the
# same SOUNDENVELOPE scale in hit_effect_runtime.gd.
const SOUND_ENVELOPE_MAX := 32768.0
var last_sound_ids: Array[int] = []
var last_nested_sound_ids: Array[int] = []
var last_nested_sound_events: Array[Dictionary] = []
var _sound_played_frame: int = -1
var _nested_sound_observation_frame: int = -1
var _nested_sound_instance_frames: Dictionary = {}
var _nested_sound_container_states: Dictionary = {}
var _nested_sound_placement_generations: Dictionary = {}
var _source_entry_serial: int = 0
var _sound_segments: Dictionary = {}
var _nested_sound_segments: Dictionary = {}
# Shader programs are immutable render caches shared by all previews. Their
# lazy creation must not become per-instance rollback state.
static var _cxform_shader: Shader
var _source_color_mul := Color(1, 1, 1, 1)
var _source_color_add := Color(0, 0, 0, 0)
var _source_color_matrix: Array = []
var _source_placement_filters_cleared := false
static var _source_filter_shader: Shader
static var _blend_shaders: Dictionary = {}
static var _raster_input_shaders: Dictionary = {}
var _filter_input_depth := 0

const SourceBoundsMath = preload("res://source_matrix_bounds.gd")
const SourceMatrixTransform = preload("res://source_matrix_transform.gd")
const TWIPS_PER_PIXEL := 20.0
const BlendGroupScript = preload("res://blend_group.gd")
const FilterGroupScript = preload("res://filter_group.gd")

const SOURCE_FILTER_SHADER := """
shader_type canvas_item;
uniform vec4 cx_mul = vec4(1.0);
uniform vec4 cx_add = vec4(0.0);
uniform vec4 row_r;
uniform vec4 row_g;
uniform vec4 row_b;
uniform vec4 row_a;
uniform vec4 offsets;
void fragment() {
	vec4 tex = texture(TEXTURE, UV);
	vec4 c = vec4(tex.rgb * cx_mul.rgb + cx_add.rgb * tex.a, tex.a * cx_mul.a);
	COLOR = clamp(vec4(dot(row_r, c), dot(row_g, c), dot(row_b, c), dot(row_a, c)) + offsets, 0.0, 1.0);
}
"""

const SourceCoordinateMath = preload("res://source_coordinate.gd")

# Flash CXFORMWITHALPHA: src * (mult/256) + add. Add is 0-255 in the XML.
const CXFORM_SHADER := """
shader_type canvas_item;
uniform vec4 cx_mul = vec4(1.0);
uniform vec4 cx_add = vec4(0.0);

void fragment() {
	vec4 tex = texture(TEXTURE, UV);
	COLOR = vec4(tex.rgb * cx_mul.rgb + cx_add.rgb * tex.a, tex.a * cx_mul.a);
}
"""


func _ready() -> void:
	_load_data()
	if _frames.is_empty():
		return
	if not _fighter.is_empty():
		play_action(initial_action)
	else:
		_current_frame = initial_frame
		_source_entry_serial += 1
		_render_frame()


func _physics_process(_delta: float) -> void:
	if not autoplay or _fighter.is_empty():
		return
	if _current_frame >= _action_end:
		_current_frame = _action_start
	else:
		_current_frame += 1
	_source_entry_serial += 1
	_render_frame()


func play_action(label: String) -> void:
	_instance_local_offsets.clear()
	_instance_local_frames.clear()
	for group: Dictionary in _fighter["actions"].values():
		if group.has(label):
			_action_start = group[label]["start_frame"]
			_action_end = group[label]["end_frame"]
			_current_frame = _action_start
			_source_entry_serial += 1
			_render_frame()
			return
	push_error("Unknown extracted action label: %s" % label)


func play_source_frame(frame: int) -> void:
	_current_frame = frame
	_source_entry_serial += 1
	_render_frame()


func current_source_frame() -> int:
	return _current_frame


func action_range(label: String) -> Dictionary:
	for group: Dictionary in _fighter.get("actions", {}).values():
		if group.has(label):
			return group[label]
	return {}


func advance_source_frame(loop_action: bool = true) -> void:
	if _current_frame >= _action_end:
		if not loop_action:
			return
		_current_frame = _action_start
	else:
		_current_frame += 1
	_source_entry_serial += 1
	_render_frame()


func instance_local_bounds(instance_name: String) -> Rect2:
	if not _frames.has(_current_frame):
		return Rect2()
	for placement: Dictionary in _frames[_current_frame]["display_list"]:
		if str(placement.get("name", "")) == instance_name:
			return _rooted_placement_bounds(placement)
	return Rect2()


func instance_global_bounds(instance_name: String) -> Rect2:
	if not _frames.has(_current_frame):
		return Rect2()
	for placement: Dictionary in _frames[_current_frame]["display_list"]:
		if str(placement.get("name", "")) == instance_name:
			return _source_placement_bounds(placement, _current_frame, [], true, true)
	return Rect2()


func child_instance_global_bounds(parent_name: String, child_name: String) -> Rect2:
	if not _frames.has(_current_frame):
		return Rect2()
	for placement: Dictionary in _frames[_current_frame]["display_list"]:
		if str(placement.get("name", "")) != parent_name:
			continue
		var definition: Dictionary = _definitions.get(int(placement["character_id"]), {})
		var frames: Array = definition.get("display_list_frames", [])
		if frames.is_empty():
			return Rect2()
		var frame := _nested_frame(placement, _current_frame, frames.size())
		for child: Dictionary in frames[frame - 1]:
			if str(child.get("name", "")) == child_name:
				return _source_placement_bounds(child, frame, [placement], true, true)
	return Rect2()


func named_instances_global_bounds(prefix: String) -> Array[Rect2]:
	var result: Array[Rect2] = []
	if not _frames.has(_current_frame):
		return result
	for placement: Dictionary in _frames[_current_frame]["display_list"]:
		if not str(placement.get("name", "")).begins_with(prefix):
			continue
		var bounds := _source_placement_bounds(placement, _current_frame, [], true, true)
		if bounds.has_area():
			result.append(bounds)
	return result


func named_instances_local_bounds(prefix: String) -> Array[Rect2]:
	var result: Array[Rect2] = []
	if not _frames.has(_current_frame):
		return result
	for placement: Dictionary in _frames[_current_frame]["display_list"]:
		if not str(placement.get("name", "")).begins_with(prefix):
			continue
		var local_bounds := _rooted_placement_bounds(placement)
		if local_bounds.has_area():
			result.append(local_bounds)
	return result


func named_instance_ledges(prefix: String) -> Array[Rect2]:
	# Source isHitBan() in fighter DefineSprite_*/frame_1/DoAction.as:
	# stand on ban._y (clip registration), x in [ban._x, ban._x + ban._width].
	# Shape AABB top is not the walkable plane when Ymin != 0.
	var result: Array[Rect2] = []
	if not _frames.has(_current_frame):
		return result
	for placement: Dictionary in _frames[_current_frame]["display_list"]:
		var instance_name := str(placement.get("name", ""))
		if not instance_name.begins_with(prefix):
			continue
		var local_bounds := _placement_bounds(placement)
		if not local_bounds.has_area():
			continue
		var matrix: Dictionary = placement.get("matrix", {})
		result.append(
			Rect2(
				float(matrix.get("translateX", 0.0)) / 20.0,
				float(matrix.get("translateY", 0.0)) / 20.0,
				local_bounds.size.x,
				10.0
			)
		)
	return result


func wrapper_translation() -> Vector2:
	var wrapper = _timeline.get("wrapper", {})
	if typeof(wrapper) != TYPE_DICTIONARY or wrapper.is_empty():
		return Vector2.ZERO
	var matrix: Dictionary = wrapper.get("matrix", {})
	return Vector2(
		float(matrix.get("translateX", 0.0)) / 20.0,
		float(matrix.get("translateY", 0.0)) / 20.0
	)


func named_instance_origin(instance_name: String) -> Vector2:
	if not _frames.has(_current_frame):
		return Vector2.INF
	for placement: Dictionary in _frames[_current_frame]["display_list"]:
		if str(placement.get("name", "")) != instance_name:
			continue
		var matrix: Dictionary = placement.get("matrix", {})
		return Vector2(
			float(matrix.get("translateX", 0.0)) / 20.0,
			float(matrix.get("translateY", 0.0)) / 20.0
		)
	return Vector2.INF


func instance_local_offset(instance_name: String) -> Vector2:
	return _instance_local_offsets.get(instance_name, Vector2.ZERO)


func set_instance_local_offset(instance_name: String, offset: Vector2) -> void:
	_instance_local_offsets[instance_name] = offset


func set_instance_clip_frame(
	instance_name: String,
	local_frame: int,
	playing: bool = true,
	age: int = -1
) -> void:
	var previous: Dictionary = _instance_local_frames.get(instance_name, {})
	_instance_local_frames[instance_name] = {
		"anchor_timeline": _current_frame,
		"local_start": local_frame,
		"playing": playing,
		"age": int(previous.get("age", 0)) if age < 0 else age,
		"source_variables": previous.get("source_variables", {}).duplicate(true),
		"source_timeline_event_driver": bool(previous.get("source_timeline_event_driver", false)),
		"child_stop_frames": previous.get("child_stop_frames", {}).duplicate(true),
	}
	_update_child_clocks(instance_name, previous)


func _instance_children(instance_name: String, local_frame: int) -> Array:
	for placement: Dictionary in _frames.get(_current_frame, {}).get("display_list", []):
		if str(placement.get("name", "")) != instance_name:
			continue
		var definition: Dictionary = _definitions.get(int(placement.get("character_id", -1)), {})
		var frames: Array = definition.get("display_list_frames", [])
		if local_frame > 0 and local_frame <= frames.size():
			return frames[local_frame - 1]
	return []


func _update_child_clocks(instance_name: String, previous: Dictionary) -> void:
	var record: Dictionary = _instance_local_frames[instance_name]
	var elapsed := maxi(0, int(record["age"]) - int(previous.get("age", 0)))
	var old_clocks: Dictionary = previous.get("child_clocks", {})
	var clocks := {}
	for child: Dictionary in _instance_children(instance_name, int(record["local_start"])):
		# Only compiled child timelines opt into placement clocks; legacy
		# assets retain their recorded playback semantics until revalidated.
		if not record["child_stop_frames"].has(str(int(child["character_id"]))):
			continue
		var depth := int(child["depth"])
		var identity := [int(child["character_id"]), int(child.get("placed_frame", 1))]
		var old: Dictionary = old_clocks.get(depth, {})
		# A goto can replace a child after an arbitrary flight duration. Only
		# retained placements inherit their age; the new explosion starts at 1.
		clocks[depth] = {"identity": identity,
			"age": int(old.get("age", 0)) + elapsed if old.get("identity") == identity else 0}
	record["child_clocks"] = clocks
	_instance_local_frames[instance_name] = record


func mark_source_timeline_event_driver(instance_name: String) -> void:
	var record: Dictionary = _instance_local_frames.get(instance_name, {})
	if record.is_empty():
		return
	record["source_timeline_event_driver"] = true
	_instance_local_frames[instance_name] = record


func instance_clip_playing(instance_name: String) -> bool:
	return bool(_instance_local_frames.get(instance_name, {}).get("playing", false))


func instance_clip_age(instance_name: String) -> int:
	return int(_instance_local_frames.get(instance_name, {}).get("age", 0))


func instance_clip_frame(instance_name: String) -> int:
	if not _frames.has(_current_frame):
		return 0
	for placement: Dictionary in _frames[_current_frame]["display_list"]:
		if str(placement.get("name", "")) != instance_name:
			continue
		var definition: Dictionary = _definitions.get(int(placement.get("character_id", -1)), {})
		var sprite_frames: Array = definition.get("display_list_frames", [])
		return _nested_frame(placement, _current_frame, sprite_frames.size())
	return 0


func unnamed_sprite_local_frame(character_id: int) -> int:
	if not _frames.has(_current_frame):
		return 0
	for placement: Dictionary in _frames[_current_frame]["display_list"]:
		if int(placement.get("character_id", -1)) != character_id:
			continue
		if str(placement.get("name", "")) != "":
			continue
		var definition: Dictionary = _definitions.get(character_id, {})
		var sprite_frames: Array = definition.get("display_list_frames", [])
		return _nested_frame(placement, _current_frame, sprite_frames.size())
	return 0


func set_hidden_instances(names: PackedStringArray) -> void:
	hidden_instance_names = names
	refresh_display()


func refresh_display() -> void:
	_render_frame()


func current_named_instances() -> PackedStringArray:
	var result: PackedStringArray = []
	if not _frames.has(_current_frame):
		return result
	for placement: Dictionary in _frames[_current_frame]["display_list"]:
		var instance_name := str(placement.get("name", ""))
		if instance_name != "":
			result.append(instance_name)
	return result


func _load_data() -> void:
	if fighter_directory == "":
		return
	var timeline_path := "%s/timeline.json" % fighter_directory
	var timeline_source := FileAccess.get_file_as_string(timeline_path)
	if timeline_source == "":
		return
	_timeline = _read_json(timeline_path)
	if _timeline.is_empty() or not _timeline.has("frames"):
		return
	var segments_path := fighter_directory.path_join("sound_segments.json")
	if FileAccess.file_exists(segments_path):
		var segments := _read_json(segments_path)
		assert(segments["source_swf"] == _timeline["source_swf"])
		assert(segments["envelope_baked"])
		_sound_segments = segments["frames"]
		_nested_sound_segments = segments.get("nested_frames", {})
	var fighter_path := "%s/fighter.json" % fighter_directory
	if FileAccess.file_exists(fighter_path):
		_fighter = _read_json(fighter_path)
	var asset_manifest: Dictionary = {}
	var assets_path := "%s/assets.json" % fighter_directory
	var assets_source := FileAccess.get_file_as_string(assets_path)
	if assets_source != "":
		asset_manifest = _read_json(assets_path)
	for definition: Dictionary in _timeline.get("definitions", []):
		_definitions[int(definition["character_id"])] = definition
	for asset: Dictionary in asset_manifest.get("assets", []):
		_assets[int(asset["character_id"])] = asset["path"]
	for frame: Dictionary in _timeline["frames"]:
		_frames[int(frame["frame"])] = frame


func _read_json(path: String) -> Dictionary:
	var source := FileAccess.get_file_as_string(path)
	var value = JSON.parse_string(source)
	if not value is Dictionary:
		push_error("Cannot parse generated timeline data: %s" % path)
		return {}
	return value


func advance_retained_visual_clips() -> void:
	independent_visual_clock = true
	_sync_retained_visual_clips()
	for clip: Dictionary in _retained_visual_clips.values():
		_advance_visual_clip(clip)
	for clip: Dictionary in _wrapper_visual_clips.values():
		_advance_visual_clip(clip)


func _advance_visual_clip(clip: Dictionary) -> void:
	for child: Dictionary in clip.get("children", {}).values():
		_advance_visual_clip(child)
	var definition: Dictionary = _definitions[int(clip.placement.character_id)]
	var source := _visual_source_record(clip.placement)
	if not source.is_empty():
		clip.age = int(source.get("age", 0))
		clip.frame = int(source.local_start)
	else:
		VisualPlayhead.advance(clip, definition, _queue_visual_frame.bind(int(clip.placement.character_id)))
	_sync_visual_children(clip, definition)


func _queue_visual_frame(_frame: int, _sprite: int) -> void:
	pass


func _visual_source_record(placement: Dictionary) -> Dictionary:
	var name := str(placement.get("name", ""))
	if not _instance_local_frames.has(name):
		return {}
	for root_placement: Dictionary in _frames.get(_current_frame, {}).get("display_list", []):
		if is_same(placement, root_placement):
			return _instance_local_frames[name]
	return {}


func _sync_visual_children(clip: Dictionary, definition: Dictionary) -> void:
	var frames: Array = definition.get("display_list_frames", [])
	if not frames.is_empty():
		clip.children = _sync_visual_list(frames[clampi(int(clip.frame), 1, frames.size()) - 1], clip.children)


func _sync_visual_list(placements: Array, previous_clips: Dictionary) -> Dictionary:
	var retained := {}
	for placement: Dictionary in placements:
		var definition: Dictionary = _definitions.get(int(placement.get("character_id", -1)), {})
		if definition.get("type") != "DefineSpriteTag":
			continue
		var depth := int(placement["depth"])
		var identity := [placement["character_id"], placement.get("placed_frame", 1)]
		var previous: Dictionary = previous_clips.get(depth, {})
		var clip: Dictionary = previous if previous.get("identity") == identity else VisualPlayhead.create(definition, _queue_visual_frame.bind(int(placement.character_id)))
		clip.identity = identity
		clip.placement = placement
		var source := _visual_source_record(placement)
		if not source.is_empty():
			clip.frame = int(source.local_start)
		_sync_visual_children(clip, definition)
		retained[depth] = clip
	return retained


func _sync_retained_visual_clips() -> void:
	_wrapper_visual_clips = _sync_visual_list(_timeline.get("wrapper_siblings", []), _wrapper_visual_clips)
	if independent_visual_clock and _frames.has(_current_frame):
		_retained_visual_clips = _sync_visual_list(_frames[_current_frame]["display_list"], _retained_visual_clips)


func _visual_clip_at(placement: Dictionary, clips: Dictionary) -> Dictionary:
	var clip: Dictionary = clips.get(int(placement.get("depth", -1)), {})
	return clip if is_same(clip.get("placement"), placement) else {}


func _visual_clip_for_path(placement: Dictionary, ancestors: Array[Dictionary]) -> Dictionary:
	var clips := _retained_visual_clips
	for ancestor: Dictionary in ancestors:
		clips = _visual_clip_at(ancestor, clips).get("children", {})
	return _visual_clip_at(placement, clips)


func refresh_checkpoint_display() -> void:
	_render_frame(true)


func _render_frame(restoring: bool = false) -> void:
	if not restoring:
		_sync_retained_visual_clips()
	if not has_meta("suppress_display"):
		var checkpoint: Variant = preload("res://rollback_lifetime.gd").owner(self)
		var deferred: bool = checkpoint != null and checkpoint.defer_display(self)
		if not deferred:
			materialize_display()
	if not restoring and _frames.has(_current_frame):
		_play_start_sounds()
		_play_nested_start_sounds()


func materialize_display() -> void:
	# Display nodes are derived; source clocks and sound observations stay in
	# _render_frame and must still run on every replayed source frame.
	if has_meta("suppress_display"):
		return
	for child in get_children():
		if child.name in ["SoundLayer", "RuntimeServices"]:
			continue
		child.queue_free()
	if not _frames.has(_current_frame):
		return
	var frame: Dictionary = _frames[_current_frame]
	var wrapper := _wrapper_transform()
	var wrapper_blend := int(_timeline.get("wrapper", {}).get("blend_mode", 1))
	var filters: Array = [] if _source_placement_filters_cleared else _timeline.get("wrapper", {}).get("filters", [])
	var first_child := get_child_count()
	if not filters.is_empty():
		# Filter the body cache before its source color transform, like a child
		# placement. resColor() can retire the authored filter at initialization.
		_filter_input_depth += 1
		_render_display_list(frame["display_list"], wrapper, 1.0, 0, _current_frame,
			0, Color.WHITE, Color(0, 0, 0, 0), [], true, 1, _retained_visual_clips)
		_filter_input_depth -= 1
		_compose_blend_group(first_child, _source_color_mul.a, 0, wrapper_blend,
			filters, true, _source_color_mul, _source_color_add)
	else:
		_render_display_list(frame["display_list"], wrapper, 1.0, 0, _current_frame,
			0, _source_color_mul, _source_color_add, [], true,
			1 if wrapper_blend not in [0, 1] else wrapper_blend, _retained_visual_clips)
		if wrapper_blend not in [0, 1]:
			_compose_blend_group(first_child, 1.0, 0, wrapper_blend)
	# These authored siblings live outside mc: its transform, color and
	# paused playhead must not affect their independently retained clocks.
	_render_display_list(_timeline.get("wrapper_siblings", []), Transform2D.IDENTITY, 1.0,
		0, 1, 0, Color.WHITE, Color(0, 0, 0, 0), [], true, 1, _wrapper_visual_clips)
	queue_redraw()


func set_source_color(transform: Dictionary, matrix: Array) -> void:
	# Current source palettes affect RGB only. Preserve unsupported alpha
	# transforms as an explicit gap instead of silently dropping them.
	assert(float(transform.get("aa", 100)) == 100 and float(transform.get("ab", 0)) == 0)
	_source_color_mul = Color(float(transform.get("ra", 100)) / 100.0, float(transform.get("ga", 100)) / 100.0, float(transform.get("ba", 100)) / 100.0, 1)
	_source_color_add = Color(float(transform.get("rb", 0)) / 255.0, float(transform.get("gb", 0)) / 255.0, float(transform.get("bb", 0)) / 255.0, 0)
	assert(matrix.is_empty() or matrix.size() == 20)
	_source_color_matrix = matrix.duplicate()
	_render_frame()


func runtime_services() -> Node:
	# Render replacement is not timeline-instance destruction. Timers and
	# controllers must survive drawing the next source frame.
	var layer := get_node_or_null("RuntimeServices")
	if layer == null:
		layer = Node.new()
		layer.name = "RuntimeServices"
		add_child(layer)
	return layer


func _sound_layer() -> Node:
	var layer := get_node_or_null("SoundLayer")
	if layer == null:
		layer = Node.new()
		layer.name = "SoundLayer"
		add_child(layer)
	return layer


func _play_start_sounds() -> void:
	if not play_timeline_sounds:
		return
	if _sound_played_frame == _current_frame:
		return
	_sound_played_frame = _current_frame
	last_sound_ids.clear()
	if not _frames.has(_current_frame):
		return
	var segments: Array = _sound_segments.get(str(_current_frame), [])
	var sound_index := 0
	for event: Dictionary in _frames[_current_frame].get("events", []):
		if str(event.get("type", "")) != "start_sound":
			continue
		var sound_id := int(event.get("sound_id", -1))
		if not _assets.has(sound_id):
			continue
		var sound_file: String = _assets[sound_id]
		if not segments.is_empty():
			assert(sound_index < segments.size() and segments[sound_index]["source_event"] == event)
			sound_file = segments[sound_index]["stream"]
		sound_index += 1
		if _start_sound_player(event, sound_file, segments.is_empty(), "root:%d" % sound_index):
			last_sound_ids.append(sound_id)


func _start_sound_player(
	event: Dictionary, sound_file: String, use_source_volume: bool = true, event_identity: String = "root"
) -> bool:
	var stream: AudioStream = load("%s/%s" % [fighter_directory, sound_file])
	if stream == null:
		return false
	if not preload("res://rollback_presentation.gd").allow_sound(self, "%d:%s:%s" % [_source_entry_serial, event_identity, sound_file]):
		return true
	var player := AudioStreamPlayer.new()
	player.stream = stream
	player.volume_db = _sound_volume_db(event) if use_source_volume else 0.0
	player.finished.connect(player.queue_free)
	_sound_layer().add_child(player)
	player.play()
	preload("res://authority_audio.gd").accepted(self, player)
	return true


func _play_nested_start_sounds() -> void:
	if not play_timeline_sounds or not _frames.has(_current_frame):
		return
	if _nested_sound_observation_frame != _current_frame:
		_nested_sound_observation_frame = _current_frame
		last_nested_sound_ids.clear()
		last_nested_sound_events.clear()
	var active_instances: Dictionary = {}
	var active_placements: Dictionary = {}
	for placement: Dictionary in _frames[_current_frame]["display_list"]:
		_collect_nested_start_sounds(
			placement,
			_current_frame,
			0,
			"root",
			active_instances,
			active_placements,
			_source_entry_serial,
			_visual_clip_at(placement, _retained_visual_clips)
		)
	for instance_id in _nested_sound_instance_frames.keys():
		if not active_instances.has(instance_id):
			_nested_sound_instance_frames.erase(instance_id)
			_nested_sound_container_states.erase(instance_id)
	for placement_id in _nested_sound_placement_generations.keys():
		if not active_placements.has(placement_id):
			_nested_sound_placement_generations.erase(placement_id)


func _collect_nested_start_sounds(
	placement: Dictionary,
	timeline_frame: int,
	clip_age: int,
	parent_instance_id: String,
	active_instances: Dictionary,
	active_placements: Dictionary,
	parent_entry_serial: int,
	visual_clip: Dictionary = {}
) -> void:
	var character_id := int(placement.get("character_id", -1))
	if not _definitions.has(character_id):
		return
	var definition: Dictionary = _definitions[character_id]
	if str(definition.get("type", "")) != "DefineSpriteTag":
		return
	var sprite_frames: Array = definition.get("display_list_frames", [])
	if sprite_frames.is_empty():
		return
	var placement_id := "%s/%d:%d:%d" % [
		parent_instance_id,
		int(placement.get("depth", -1)),
		character_id,
		int(placement.get("placed_frame", timeline_frame)),
	]
	var generation: Dictionary = _nested_sound_placement_generations.get(
		placement_id, {"entry_serial": -1, "generation": 0}
	)
	active_placements[placement_id] = true
	if int(placement.get("placed_frame", timeline_frame)) == timeline_frame \
			and int(generation["entry_serial"]) != parent_entry_serial:
		generation["entry_serial"] = parent_entry_serial
		generation["generation"] = int(generation["generation"]) + 1
		_nested_sound_placement_generations[placement_id] = generation
	var instance_id := "%s#%d" % [placement_id, int(generation["generation"])]
	active_instances[instance_id] = true
	var local_frame := _visual_nested_frame(placement, timeline_frame, sprite_frames.size(), clip_age, visual_clip)
	var container_state: Dictionary = _nested_sound_container_states.get(
		instance_id, {"frame": -1, "entry_serial": 0}
	)
	if int(container_state["frame"]) != local_frame:
		container_state["frame"] = local_frame
		container_state["entry_serial"] = int(container_state["entry_serial"]) + 1
	_nested_sound_container_states[instance_id] = container_state
	var previous_frame := int(_nested_sound_instance_frames.get(instance_id, -1))
	if previous_frame != local_frame:
		var instance_name := str(placement.get("name", ""))
		var child_playhead: Dictionary = _instance_local_frames.get(instance_name, {})
		if not bool(child_playhead.get("source_timeline_event_driver", false)):
			var frame_events: Array = definition.get("display_list_frame_events", [])
			if local_frame > 0 and local_frame <= frame_events.size():
				for event: Dictionary in frame_events[local_frame - 1]:
					if str(event.get("type", "")) == "start_sound":
						_play_nested_source_sound(event, instance_id, character_id, local_frame)
		_nested_sound_instance_frames[instance_id] = local_frame
	var child_age := clip_age
	var instance_name := str(placement.get("name", ""))
	if instance_name != "" and _instance_local_frames.has(instance_name):
		child_age = int(_instance_local_frames[instance_name].get("age", 0))
	for child: Dictionary in sprite_frames[local_frame - 1]:
		_collect_nested_start_sounds(
			child,
			local_frame,
			child_age,
			instance_id,
			active_instances,
			active_placements,
			int(container_state["entry_serial"]),
			_visual_clip_at(child, visual_clip.get("children", {}))
		)


func play_source_timeline_sound(
	event: Dictionary,
	instance_id: String,
	sprite_id: int,
	frame: int,
	source_name: String
) -> bool:
	return _play_nested_source_sound(
		event,
		instance_id,
		sprite_id,
		frame,
		source_name
	)


func _play_nested_source_sound(
	event: Dictionary,
	instance_id: String,
	sprite_id: int,
	frame: int,
	source_name: String = ""
) -> bool:
	var sound_id := int(event.get("sound_id", -1))
	var sound_file := str(_assets.get(sound_id, ""))
	var baked := false
	for segment: Dictionary in _nested_sound_segments.get("%d:%d" % [sprite_id, frame], []):
		if segment["source_event"] == event:
			sound_file = str(segment["stream"])
			baked = true
			break
	var supported_sound_info := baked or _nested_sound_info_supported(event)
	if not supported_sound_info:
		push_error(
			"Unsupported nested StartSound SOUNDINFO: sprite %d frame %d sound %d fields=%s"
			% [sprite_id, frame, sound_id, _nested_sound_info_flags(event)]
		)
	elif sound_file.is_empty():
		push_error("Missing nested StartSound asset: sprite %d frame %d sound %d" % [sprite_id, frame, sound_id])
	var started := (
		supported_sound_info
		and not sound_file.is_empty()
		and _start_sound_player(event, sound_file, not baked, "%s:%d:%d" % [instance_id, sprite_id, frame])
	)
	last_nested_sound_events.append({
		"instance_id": instance_id,
		"sprite_id": sprite_id,
		"frame": frame,
		"sound_id": sound_id,
		"started": started,
	})
	if started:
		last_nested_sound_ids.append(sound_id)
		nested_source_sound_started.emit({
			"instance_id": instance_id,
			"sprite_id": sprite_id,
			"frame": frame,
			"root_frame": _current_frame,
			"sound_id": sound_id,
			"source_name": source_name,
			"source_event": event,
		})
	return started


func _nested_sound_info_supported(event: Dictionary) -> bool:
	for flag in ["sync_stop", "sync_no_multiple"]:
		if bool(event.get(flag, false)):
			return false
	for field in ["in_point", "out_point", "loop_count", "envelope"]:
		if event.has(field):
			return false
	return true


func _nested_sound_info_flags(event: Dictionary) -> PackedStringArray:
	var unsupported: PackedStringArray = []
	for flag in ["sync_stop", "sync_no_multiple"]:
		if bool(event.get(flag, false)):
			unsupported.append(flag)
	for field in ["in_point", "out_point", "loop_count", "envelope"]:
		if event.has(field):
			unsupported.append(field)
	return unsupported


func _sound_volume_db(event: Dictionary) -> float:
	var envelope: Array = event.get("envelope", [])
	if envelope.is_empty():
		return 0.0
	var record: Dictionary = envelope[0]
	var level := (
		float(record.get("left_level", SOUND_ENVELOPE_MAX))
		+ float(record.get("right_level", SOUND_ENVELOPE_MAX))
	) / 2.0
	if level <= 0.0:
		return -80.0
	return linear_to_db(level / SOUND_ENVELOPE_MAX)


func _render_display_list(placements: Array, parent_transform: Transform2D,
		alpha: float, depth: int, frame: int, age: int, rgb_mul: Color,
		rgb_add: Color, inherited_masks: Array, root_list: bool = false, inherited_blend: int = 1, visual_clips: Dictionary = {}) -> void:
	var active: Array = []
	for placement: Dictionary in placements:
		var local_depth := int(placement["depth"])
		active = active.filter(func(mask: Dictionary) -> bool: return local_depth <= int(mask.end))
		var definition: Dictionary = _definitions.get(int(placement.get("character_id", -1)), {})
		if placement.has("clip_depth") and definition.has("mask_polygon"):
			var polygon := PackedVector2Array()
			var transform := parent_transform * _placement_transform(placement)
			for point: Array in definition["mask_polygon"]:
				polygon.append(transform * Vector2(float(point[0]), float(point[1])))
			active.append({"end": int(placement["clip_depth"]), "polygon": polygon})
			continue
		var masks := inherited_masks.duplicate()
		for mask: Dictionary in active:
			masks.append(mask.polygon)
		_render_placement(placement, parent_transform, alpha,
			local_depth if root_list and preserve_root_depths else depth,
			frame, age, rgb_mul, rgb_add, masks, inherited_blend, visual_clips.get(local_depth, {}))


func _clip_bitmap_masks(fill_masks: Array, bitmap_transform: Transform2D,
		placement_transform: Transform2D, texture: Texture2D, masks: Array) -> Array:
	var contours: Array = []
	if fill_masks.is_empty():
		var size := texture.get_size()
		contours.append(bitmap_transform * PackedVector2Array([
			Vector2.ZERO, Vector2(size.x, 0), size, Vector2(0, size.y)]))
	else:
		for contour: Array in fill_masks:
			var polygon := PackedVector2Array()
			for point: Array in contour:
				polygon.append(Vector2(float(point[0]), float(point[1])))
			contours.append(polygon)
	var inverse := placement_transform.affine_inverse()
	for mask: PackedVector2Array in masks:
		var clipped: Array = []
		for contour: PackedVector2Array in contours:
			clipped.append_array(Geometry2D.intersect_polygons(contour, inverse * mask))
		contours = clipped
	var result: Array = []
	for contour: PackedVector2Array in contours:
		var points: Array = []
		for point: Vector2 in contour:
			points.append([point.x, point.y])
		result.append(points)
	return result


func _render_placement(
	placement: Dictionary,
	parent_transform: Transform2D,
	parent_alpha: float,
	parent_depth: int,
	timeline_frame: int,
	clip_age: int = 0,
	parent_rgb_mul: Color = Color(1, 1, 1, 1),
	parent_rgb_add: Color = Color(0, 0, 0, 0),
	clip_masks: Array = [],
	inherited_blend: int = 1,
	visual_clip: Dictionary = {}
) -> void:
	if bool(placement.get("replaced_by_external_movie", false)):
		return
	var character_id := int(placement.get("character_id", -1))
	if not _definitions.has(character_id):
		return
	var filters: Array = placement.get("filters", [])
	if not filters.is_empty() or bool(placement.get("cache_as_bitmap", false)):
		var unfiltered := placement.duplicate()
		unfiltered.erase("filters")
		unfiltered.erase("cache_as_bitmap")
		unfiltered["blend_mode"] = 1
		var filter_cx: Dictionary = placement.get("color_transform", {})
		var filter_mul := _cxform_mul(filter_cx)
		var filter_add := _cxform_add(filter_cx)
		var filter_alpha := parent_alpha * filter_mul.a
		# The display-object CXFORM operates on the filtered cache.
		unfiltered.erase("color_transform")
		var first_child := get_child_count()
		_filter_input_depth += 1
		_render_placement(unfiltered, parent_transform, 1.0, parent_depth,
			timeline_frame, clip_age, Color.WHITE, Color(0, 0, 0, 0), clip_masks, 1, visual_clip)
		_filter_input_depth -= 1
		_compose_blend_group(first_child, filter_alpha, parent_depth,
			int(placement.get("blend_mode", inherited_blend)), filters, true,
			_cxform_combine_mul(parent_rgb_mul, filter_mul),
			_cxform_combine_add(parent_rgb_mul, parent_rgb_add, filter_mul, filter_add))
		return
	var definition: Dictionary = _definitions[character_id]
	if not bool(definition.get("initial_visible", true)):
		return
	var blend := int(placement.get("blend_mode", inherited_blend))
	var placement_transform := parent_transform * _placement_transform(placement)
	var color_transform: Dictionary = placement.get("color_transform", {})
	var placement_mul := _cxform_mul(color_transform)
	var placement_add := _cxform_add(color_transform)
	var alpha := parent_alpha * placement_mul.a
	var rgb_mul := _cxform_combine_mul(parent_rgb_mul, placement_mul)
	var rgb_add := _cxform_combine_add(
		parent_rgb_mul, parent_rgb_add, placement_mul, placement_add
	)
	# Display lists are depth-sorted. Traverse each subtree contiguously;
	# child depths are local to their SWF container, never added globally.
	var depth := parent_depth
	var instance_name := str(placement.get("name", ""))
	if instance_name != "":
		for hidden_name in hidden_instance_names:
			if hidden_name == instance_name:
				return
	if definition["type"] == "DefineSpriteTag":
		var sprite_frames: Array = definition.get("display_list_frames", [])
		var local_frame := _nested_frame(
			placement, timeline_frame, sprite_frames.size(), clip_age
		)
		if not visual_clip.is_empty():
			local_frame = int(visual_clip.frame)
		var child_age := clip_age
		if instance_name != "" and _instance_local_frames.has(instance_name):
			child_age = int(_instance_local_frames[instance_name].get("age", 0))
		var children: Array = (
			sprite_frames[local_frame - 1]
			if not sprite_frames.is_empty()
			else definition.get("first_frame_display_list", [])
		)
		var first_child := get_child_count()
		_render_display_list(children, placement_transform, 1.0 if blend not in [0, 1] else alpha, depth,
			local_frame, child_age, rgb_mul, rgb_add, clip_masks, false,
			1 if blend not in [0, 1] else blend, visual_clip.get("children", {}))
		if blend not in [0, 1]:
			_compose_blend_group(first_child, alpha, depth, blend)
		return
	var fills: Array = definition.get("bitmap_fills", [])
	if not definition["type"].begins_with("DefineShape"):
		return
	var usable_fills: Array = fills.filter(
		func(fill: Dictionary) -> bool: return _assets.has(int(fill["bitmap_id"]))
	)
	var compiled_fill_masks: Array = definition.get("bitmap_clip_polygons", [])
	for fill_index in fills.size():
		var fill: Dictionary = fills[fill_index]
		var bitmap_id := int(fill["bitmap_id"])
		if not _assets.has(bitmap_id):
			continue
		var source_texture: Texture2D = load("%s/%s" % [fighter_directory, _assets[bitmap_id]])
		var bitmap_transform := _matrix_transform(fill.get("matrix", {}), 0.05)
		var fill_masks: Array = []
		if compiled_fill_masks.size() == fills.size():
			fill_masks = compiled_fill_masks[fill_index]
			# An explicit empty mask paints nothing; only absent masks may fall back.
			if fill_masks.is_empty():
				continue
		elif fills.size() == 1 and definition.has("bitmap_clip_polygon"):
			fill_masks = [definition["bitmap_clip_polygon"]]
		if not clip_masks.is_empty():
			fill_masks = _clip_bitmap_masks(fill_masks, bitmap_transform,
				placement_transform, source_texture, clip_masks)
			if fill_masks.is_empty():
				continue
		var full_bitmap := _mask_is_full_bitmap(fill_masks, bitmap_transform, source_texture)
		if not fill_masks.is_empty() and not full_bitmap:
			var inverse_bitmap := bitmap_transform.affine_inverse()
			for contour: Array in fill_masks:
				var polygon := Polygon2D.new()
				var vertices := PackedVector2Array()
				var uvs := PackedVector2Array()
				for point: Array in contour:
					var vertex := Vector2(float(point[0]), float(point[1]))
					vertices.append(vertex)
					uvs.append(inverse_bitmap * vertex)
				polygon.polygon = vertices
				polygon.uv = uvs
				polygon.texture = source_texture
				polygon.texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
				polygon.transform = placement_transform
				polygon.z_index = depth
				_apply_cxform(polygon, rgb_mul, rgb_add, alpha)
				_apply_blend(polygon, blend)
				add_child(polygon)
			continue
		var sprite := Sprite2D.new()
		sprite.centered = false
		sprite.texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
		sprite.z_index = depth
		var draw_transform := bitmap_transform
		var texture_region := _shape_texture_region(definition, bitmap_transform, source_texture)
		if not full_bitmap and texture_region.has_area():
			var atlas := AtlasTexture.new()
			atlas.atlas = source_texture
			atlas.region = texture_region
			sprite.texture = atlas
			draw_transform.origin = bitmap_transform * texture_region.position
		else:
			sprite.texture = source_texture
		sprite.transform = placement_transform * draw_transform
		_apply_cxform(sprite, rgb_mul, rgb_add, alpha)
		_apply_blend(sprite, blend)
		add_child(sprite)
	if not usable_fills.is_empty():
		return
	_render_solid_fills(definition, placement_transform, depth, rgb_mul, rgb_add, alpha, blend)


func _mask_is_full_bitmap(masks: Array, bitmap_transform: Transform2D, texture: Texture2D) -> bool:
	if masks.size() != 1 or masks[0].size() != 4 or bitmap_transform.determinant() == 0.0:
		return false
	var inverse := bitmap_transform.affine_inverse()
	var size := texture.get_size()
	var corners := [Vector2.ZERO, Vector2(size.x, 0), size, Vector2(0, size.y)]
	var indices: Array[int] = []
	for point: Array in masks[0]:
		var uv := inverse * Vector2(float(point[0]), float(point[1]))
		var corner_index := -1
		for index in corners.size():
			if uv.distance_to(corners[index]) < 0.0001:
				corner_index = index
		if corner_index < 0 or corner_index in indices:
			return false
		indices.append(corner_index)
	# Only a perimeter walk covers the rectangle; reject crossing diagonals.
	for index in indices.size():
		if absi(indices[index] - indices[(index + 1) % 4]) == 2:
			return false
	return true


func _render_solid_fills(
	definition: Dictionary,
	placement_transform: Transform2D,
	depth: int,
	rgb_mul: Color,
	rgb_add: Color,
	alpha: float,
	blend: int = 1
) -> void:
	# Older packages retain only bounds; newly compiled solids carry the
	# actual directed fill contours, including explicit empty paint slots.
	if not definition.has("shape_bounds_twips"):
		return
	var fills: Array = definition.get("solid_fills", [])
	if fills.is_empty():
		return
	var bounds: Dictionary = definition["shape_bounds_twips"]
	var x0 := float(bounds["Xmin"]) / 20.0
	var y0 := float(bounds["Ymin"]) / 20.0
	var x1 := float(bounds["Xmax"]) / 20.0
	var y1 := float(bounds["Ymax"]) / 20.0
	for fill_index in fills.size():
		var fill: Dictionary = fills[fill_index]
		var fill_color := Color(
			float(fill.get("red", 0)) / 255.0,
			float(fill.get("green", 0)) / 255.0,
			float(fill.get("blue", 0)) / 255.0,
			float(fill.get("alpha", 255)) / 255.0
		)
		fill_color = Color(
			fill_color.r * rgb_mul.r + rgb_add.r * fill_color.a,
			fill_color.g * rgb_mul.g + rgb_add.g * fill_color.a,
			fill_color.b * rgb_mul.b + rgb_add.b * fill_color.a,
			fill_color.a * alpha
		)
		var contours: Array = [[[x0, y0], [x1, y0], [x1, y1], [x0, y1]]]
		if definition.has("solid_fill_polygons"):
			contours = definition.solid_fill_polygons[fill_index]
		for contour: Array in contours:
			var poly := Polygon2D.new()
			var vertices := PackedVector2Array()
			for point: Array in contour:
				vertices.append(Vector2(float(point[0]), float(point[1])))
			poly.polygon = vertices
			poly.color = fill_color
			poly.z_index = depth
			poly.transform = placement_transform
			_apply_blend(poly, blend)
			add_child(poly)
	for stroke: Dictionary in definition.get("solid_closed_strokes", []):
		var color := Color(float(stroke.color.red) / 255.0, float(stroke.color.green) / 255.0,
			float(stroke.color.blue) / 255.0, float(stroke.color.alpha) / 255.0)
		color = Color(color.r * rgb_mul.r + rgb_add.r * color.a,
			color.g * rgb_mul.g + rgb_add.g * color.a,
			color.b * rgb_mul.b + rgb_add.b * color.a, color.a * alpha)
		for contour: Array in stroke.paths:
			var line := Line2D.new()
			for point: Array in contour:
				line.add_point(Vector2(float(point[0]), float(point[1])))
			line.closed = true
			line.width = float(stroke.width)
			line.joint_mode = Line2D.LINE_JOINT_ROUND
			line.default_color = color
			line.transform = placement_transform
			line.z_index = depth
			_apply_blend(line, blend)
			add_child(line)


func _cxform_mul(color_transform: Dictionary) -> Color:
	if color_transform.is_empty() or str(color_transform.get("hasMultTerms", "false")) != "true":
		return Color(1, 1, 1, 1)
	return Color(
		float(color_transform.get("redMultTerm", 256)) / 256.0,
		float(color_transform.get("greenMultTerm", 256)) / 256.0,
		float(color_transform.get("blueMultTerm", 256)) / 256.0,
		float(color_transform.get("alphaMultTerm", 256)) / 256.0
	)


func _cxform_add(color_transform: Dictionary) -> Color:
	if color_transform.is_empty() or str(color_transform.get("hasAddTerms", "false")) != "true":
		return Color(0, 0, 0, 0)
	return Color(
		float(color_transform.get("redAddTerm", 0)) / 255.0,
		float(color_transform.get("greenAddTerm", 0)) / 255.0,
		float(color_transform.get("blueAddTerm", 0)) / 255.0,
		float(color_transform.get("alphaAddTerm", 0)) / 255.0
	)


func _cxform_combine_mul(parent_mul: Color, child_mul: Color) -> Color:
	return Color(
		parent_mul.r * child_mul.r,
		parent_mul.g * child_mul.g,
		parent_mul.b * child_mul.b,
		parent_mul.a * child_mul.a
	)


func _cxform_combine_add(
	parent_mul: Color, parent_add: Color, child_mul: Color, child_add: Color
) -> Color:
	return Color(
		parent_mul.r * child_add.r + parent_add.r,
		parent_mul.g * child_add.g + parent_add.g,
		parent_mul.b * child_add.b + parent_add.b,
		parent_mul.a * child_add.a + parent_add.a
	)


func _cxform_is_identity(rgb_mul: Color, rgb_add: Color) -> bool:
	return (
		is_equal_approx(rgb_mul.r, 1.0)
		and is_equal_approx(rgb_mul.g, 1.0)
		and is_equal_approx(rgb_mul.b, 1.0)
		and is_equal_approx(rgb_add.r, 0.0)
		and is_equal_approx(rgb_add.g, 0.0)
		and is_equal_approx(rgb_add.b, 0.0)
	)


func _apply_cxform(sprite: CanvasItem, rgb_mul: Color, rgb_add: Color, alpha: float) -> void:
	sprite.modulate.a = alpha
	if _cxform_is_identity(rgb_mul, rgb_add) and _source_color_matrix.is_empty():
		return
	if _cxform_shader == null:
		_cxform_shader = Shader.new()
		_cxform_shader.code = CXFORM_SHADER
	var material := ShaderMaterial.new()
	material.shader = _cxform_shader
	material.set_shader_parameter("cx_mul", Vector4(rgb_mul.r, rgb_mul.g, rgb_mul.b, 1.0))
	material.set_shader_parameter("cx_add", Vector4(rgb_add.r, rgb_add.g, rgb_add.b, 0.0))
	if not _source_color_matrix.is_empty():
		if _source_filter_shader == null:
			_source_filter_shader = Shader.new()
			_source_filter_shader.code = SOURCE_FILTER_SHADER
		material.shader = _source_filter_shader
		material.set_shader_parameter("cx_mul", Vector4(rgb_mul.r, rgb_mul.g, rgb_mul.b, 1.0))
		material.set_shader_parameter("cx_add", Vector4(rgb_add.r, rgb_add.g, rgb_add.b, 0.0))
		for row in 4:
			var i := row * 5
			material.set_shader_parameter(["row_r", "row_g", "row_b", "row_a"][row], Vector4(_source_color_matrix[i], _source_color_matrix[i + 1], _source_color_matrix[i + 2], _source_color_matrix[i + 3]))
		material.set_shader_parameter("offsets", Vector4(_source_color_matrix[4], _source_color_matrix[9], _source_color_matrix[14], _source_color_matrix[19]) / 255.0)
	sprite.material = material


func _compose_blend_group(
	first_child: int, opacity: float, depth: int, blend: int,
	filters: Array = [], isolate: bool = false,
	post_mul: Color = Color.WHITE, post_add: Color = Color(0, 0, 0, 0)
) -> void:
	var items := get_children().slice(first_child)
	if items.is_empty():
		return
	# Non-normal blends cache their input before applying group opacity, even
	# for a single leaf. Distributing opacity into that leaf quantizes too early.
	if blend in [0, 1] and not isolate and filters.is_empty() and items.size() == 1 and (items[0] is Sprite2D or items[0] is Polygon2D):
		var item: CanvasItem = items[0]
		remove_child(item)
		item.modulate.a *= opacity
		_apply_blend(item, blend)
		add_child(item)
		return
	for item: Node in items:
		remove_child(item)
	var group = BlendGroupScript.new() if filters.is_empty() else FilterGroupScript.new()
	if not filters.is_empty():
		group.set_meta("flash_filters", filters.duplicate(true))
	group.z_index = depth
	var composite: Sprite2D = group.setup(items, opacity)
	# Viewport textures hold premultiplied RGB. Decode once before blending;
	# the blend_mix pipeline then applies source alpha exactly once.
	var material := ShaderMaterial.new()
	var shader := Shader.new()
	shader.code = """
shader_type canvas_item;
uniform float group_opacity = 1.0;
uniform bool cached_opacity = false;
uniform vec3 post_mul = vec3(1.0);
uniform vec3 post_add = vec3(0.0);
void fragment() {
	vec4 pixel = texture(TEXTURE, UV);
	if (pixel.a > 0.0) {
		pixel.rgb = clamp(pixel.rgb / pixel.a * post_mul + post_add, vec3(0.0), vec3(1.0)) * pixel.a;
	}
	if (cached_opacity) {
		pixel = floor(pixel * 255.0 * group_opacity + 0.0001) / 255.0;
	}
	if (pixel.a > 0.0) { pixel.rgb /= pixel.a; }
	if (!cached_opacity) { pixel.a *= group_opacity; }
	COLOR = pixel;
}
"""
	material.shader = shader
	material.set_shader_parameter("group_opacity", opacity)
	material.set_shader_parameter("cached_opacity", isolate)
	material.set_shader_parameter("post_mul", Vector3(post_mul.r, post_mul.g, post_mul.b))
	material.set_shader_parameter("post_add", Vector3(post_add.r, post_add.g, post_add.b))
	composite.modulate.a = 1.0
	composite.material = material
	_apply_blend(composite, blend, group)
	group.add_child(composite)
	add_child(group)


func _quantize_raster_input(item: CanvasItem) -> void:
	if item.has_meta("flash_raster_input"):
		return
	item.set_meta("flash_raster_input", true)
	var material := item.material as ShaderMaterial
	var original := material.shader.code if material != null else "shader_type canvas_item; void fragment() { }"
	var opacity := item.modulate.a if material != null else 1.0
	if not _raster_input_shaders.has(original):
		var shader := Shader.new()
		var code := original.replace("shader_type canvas_item;", "shader_type canvas_item; uniform float filter_input_opacity = 1.0;")
		code = code.insert(code.rfind("}"), """
float input_alpha = floor(clamp(COLOR.a * filter_input_opacity, 0.0, 1.0) * 255.0 + 0.5);
vec3 input_rgb = floor(clamp(COLOR.rgb, vec3(0.0), vec3(1.0)) * 255.0 + 0.5);
// Flash's cached raster uses the integer multiply (channel * (alpha + 1)) >> 8.
vec3 premultiplied = floor(input_rgb * (input_alpha + 1.0) / 256.0);
COLOR = vec4(input_alpha > 0.0 ? premultiplied / input_alpha : vec3(0.0), input_alpha / 255.0);
""")
		shader.code = code
		_raster_input_shaders[original] = shader
	material = material.duplicate() if material != null else ShaderMaterial.new()
	material.shader = _raster_input_shaders[original]
	material.set_shader_parameter("filter_input_opacity", opacity)
	item.modulate.a = 1.0 if opacity != 1.0 else item.modulate.a
	item.material = material


func _apply_blend(item: CanvasItem, blend: int, copy_parent: Node = null) -> void:
	# Blends sample the already-composited backdrop. Preserve Flash byte inputs
	# for ordinary leaves too; their rounded GPU colors cannot be recovered later.
	if copy_parent == null:
		_quantize_raster_input(item)
	assert(blend in [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 13, 14], "Unsupported Flash blend mode: %d" % blend)
	if blend in [0, 1]:
		return
	# Copy at each object's depth, so earlier blended siblings are included.
	var copy := BackBufferCopy.new()
	copy.copy_mode = BackBufferCopy.COPY_MODE_VIEWPORT
	copy.z_index = item.z_index
	if copy_parent == null:
		copy_parent = self
	copy_parent.add_child(copy)
	var material := item.material as ShaderMaterial
	var opacity := item.modulate.a if material != null else 1.0
	var original := material.shader.code if material != null else "shader_type canvas_item;\nvoid fragment() { }"
	var arithmetic := blend in [7, 8, 9, 13]
	var shader_key := original + ("|arithmetic" if arithmetic else "|over")
	if not _blend_shaders.has(shader_key):
		var shader := Shader.new()
		var code := original.replace("shader_type canvas_item;", "shader_type canvas_item;\nrender_mode blend_mix;\nuniform sampler2D blend_background : hint_screen_texture, repeat_disable, filter_nearest;\nuniform float blend_opacity = 1.0;\nuniform int flash_blend_mode = 1;")
		if arithmetic:
			code = code.replace("render_mode blend_mix;", "render_mode blend_disabled;")
		var end := code.rfind("}")
		# The backbuffer is premultiplied when its viewport is transparent.
		# Blend only the overlap; uncovered source retains its original color.
		code = code.insert(end, """
vec4 backdrop = textureLod(blend_background, SCREEN_UV, 0.0);
vec3 cb = backdrop.a > 0.0 ? backdrop.rgb / backdrop.a : vec3(0.0);
vec3 cs = clamp(COLOR.rgb, vec3(0.0), vec3(1.0));
vec3 mixed = cs;
if (flash_blend_mode == 3) { mixed = cb * cs; }
else if (flash_blend_mode == 4) { mixed = 1.0 - (1.0 - cb) * (1.0 - cs); }
else if (flash_blend_mode == 5) { mixed = max(cb, cs); }
else if (flash_blend_mode == 6) { mixed = min(cb, cs); }
else if (flash_blend_mode == 8) { mixed = min(vec3(1.0), cb + cs); }
else if (flash_blend_mode == 9) { mixed = max(vec3(0.0), cb - cs); }
else if (flash_blend_mode == 14) {
    mixed = mix(2.0 * cb * cs, 1.0 - 2.0 * (1.0 - cb) * (1.0 - cs), step(vec3(0.5), cs));
}
COLOR.rgb = mix(cs, mixed, backdrop.a);
COLOR.a = clamp(COLOR.a * blend_opacity, 0.0, 1.0);
// Keep all products in byte units and truncate only the final quotient.
if (flash_blend_mode == 7 || flash_blend_mode == 13) {
    float sa = floor(COLOR.a * 255.0 + 0.0001);
    float ba = floor(backdrop.a * 255.0 + 0.5);
    vec3 sp = floor(cs * COLOR.a * 255.0 + 0.0001);
    vec3 bp = floor(backdrop.rgb * 255.0 + 0.5);
    vec3 numerator = (bp + sp) * 255.0 - 2.0 * min(bp * sa, sp * ba);
    if (flash_blend_mode == 13) {
        vec3 base = (bp + sp) * 255.0 - bp * sa - sp * ba;
        vec3 low = base + 2.0 * bp * sp;
        vec3 high = base + sa * ba - 2.0 * (ba - bp) * (sa - sp);
        // Native overlay high branch is an open upper bound at integer results.
        if (sa > 0.0 && ba > 0.0) { high -= 1.0; }
        numerator = mix(low, high, step(vec3(ba + 1.0), 2.0 * bp));
    }
    COLOR = vec4(floor(numerator / 255.0) / 255.0, floor(((sa + ba) * 255.0 - sa * ba) / 255.0) / 255.0);
}

if (flash_blend_mode == 8 || flash_blend_mode == 9) {
    vec3 source_premultiplied = cs * COLOR.a;
    vec3 result = flash_blend_mode == 8 ? backdrop.rgb + source_premultiplied : backdrop.rgb - source_premultiplied;
    COLOR = vec4(clamp(result, vec3(0.0), vec3(1.0)), min(1.0, backdrop.a + COLOR.a));
}
""")
		shader.code = code
		_blend_shaders[shader_key] = shader
	if material == null:
		material = ShaderMaterial.new()
	else:
		material = material.duplicate()
	material.shader = _blend_shaders[shader_key]
	material.set_shader_parameter("blend_opacity", opacity)
	material.set_shader_parameter("flash_blend_mode", blend)
	item.material = material


func _shape_texture_region(
	definition: Dictionary,
	bitmap_transform: Transform2D,
	texture: Texture2D
) -> Rect2:
	if not definition.has("shape_bounds_twips") or bitmap_transform.determinant() == 0.0:
		return Rect2()
	var bounds: Dictionary = definition["shape_bounds_twips"]
	var shape_rect := Rect2(
		Vector2(float(bounds["Xmin"]), float(bounds["Ymin"])) / 20.0,
		Vector2(
			float(bounds["Xmax"] - bounds["Xmin"]),
			float(bounds["Ymax"] - bounds["Ymin"])
		) / 20.0
	)
	var raw_region := _transform_rect(bitmap_transform.affine_inverse(), shape_rect)
	var start := Vector2(floorf(raw_region.position.x), floorf(raw_region.position.y))
	var finish := Vector2(ceilf(raw_region.end.x), ceilf(raw_region.end.y))
	start = start.max(Vector2.ZERO)
	finish = finish.min(Vector2(texture.get_width(), texture.get_height()))
	if finish.x <= start.x or finish.y <= start.y:
		return Rect2()
	return Rect2(start, finish - start)


func _placement_transform(placement: Dictionary) -> Transform2D:
	var transform_2d := _matrix_transform(placement.get("matrix", {}), 1.0)
	transform_2d.origin += instance_local_offset(str(placement.get("name", "")))
	return transform_2d


func _matrix_transform(matrix: Dictionary, basis_scale: float) -> Transform2D:
	return SourceMatrixTransform.matrix_transform(matrix, basis_scale)


func _wrapper_transform() -> Transform2D:
	# Fighter SWF root places the inner timeline as `mc`. Player `_x/_y`
	# stays on the wrapper; this matrix is the missing visual/hitbox offset.
	var wrapper = _timeline.get("wrapper", {})
	if typeof(wrapper) != TYPE_DICTIONARY or wrapper.is_empty():
		return Transform2D.IDENTITY
	return _matrix_transform(wrapper.get("matrix", {}), 1.0)


func source_placement_global_bounds(
	placement: Dictionary,
	timeline_frame: int = _current_frame,
	ancestor_placements: Array[Dictionary] = []
) -> Rect2:
	return _source_placement_bounds(placement, timeline_frame, ancestor_placements, true, true)


func source_placement_local_bounds(
	placement: Dictionary,
	timeline_frame: int = _current_frame,
	ancestor_placements: Array[Dictionary] = []
) -> Rect2:
	return _source_placement_bounds(placement, timeline_frame, ancestor_placements, true, false)


func _rooted_placement_bounds(placement: Dictionary, timeline_frame: int = _current_frame) -> Rect2:
	var local_bounds := _placement_bounds(placement, timeline_frame)
	if not local_bounds.has_area():
		return local_bounds
	return _transform_rect(_wrapper_transform(), local_bounds)


func _placement_bounds(placement: Dictionary, timeline_frame: int = _current_frame, visual_clip: Dictionary = {}) -> Rect2:
	var definition: Dictionary = _definitions.get(int(placement.get("character_id", -1)), {})
	if definition.is_empty():
		return Rect2()
	var clock := visual_clip if not visual_clip.is_empty() else _visual_clip_at(placement, _retained_visual_clips)
	var local_bounds := _definition_bounds(definition, placement, timeline_frame, clock)
	if not local_bounds.has_area():
		return Rect2()
	return _transform_rect(_placement_transform(placement), local_bounds)


func _source_placement_bounds(
	placement: Dictionary,
	timeline_frame: int,
	ancestor_placements: Array[Dictionary],
	include_wrapper: bool,
	include_node_transforms: bool
) -> Rect2:
	var matrices: Array[Dictionary] = []
	for ancestor: Dictionary in ancestor_placements:
		matrices.append(_source_placement_matrix(ancestor))
	var bounds_twips := _collect_source_bounds(
		placement,
		timeline_frame,
		matrices,
		0,
		include_wrapper,
		include_node_transforms,
		_visual_clip_for_path(placement, ancestor_placements)
	)
	if bounds_twips.size.x <= 0 or bounds_twips.size.y <= 0:
		return Rect2()
	return Rect2(
		Vector2(bounds_twips.position) / TWIPS_PER_PIXEL,
		Vector2(bounds_twips.size) / TWIPS_PER_PIXEL
	)


func _collect_source_bounds(
	placement: Dictionary,
	timeline_frame: int,
	ancestor_matrices: Array[Dictionary],
	clip_age: int,
	include_wrapper: bool,
	include_node_transforms: bool,
	visual_clip: Dictionary = {}
) -> Rect2i:
	var matrices := ancestor_matrices.duplicate()
	matrices.append(_source_placement_matrix(placement))
	var definition: Dictionary = _definitions.get(int(placement.get("character_id", -1)), {})
	if definition.is_empty():
		return Rect2i()
	if definition.has("shape_bounds_twips"):
		var source_bounds: Dictionary = definition["shape_bounds_twips"]
		var shape_bounds := Rect2i(
			int(source_bounds.get("Xmin", 0)),
			int(source_bounds.get("Ymin", 0)),
			int(source_bounds.get("Xmax", 0)) - int(source_bounds.get("Xmin", 0)),
			int(source_bounds.get("Ymax", 0)) - int(source_bounds.get("Ymin", 0))
		)
		if shape_bounds.size.x <= 0 or shape_bounds.size.y <= 0:
			return Rect2i()
		var leaf_to_root: Array[Dictionary] = []
		for index in range(matrices.size() - 1, -1, -1):
			leaf_to_root.append(matrices[index])
		if include_wrapper:
			var wrapper: Dictionary = _timeline.get("wrapper", {})
			if not wrapper.is_empty():
				leaf_to_root.append(SourceBoundsMath.from_swf(wrapper.get("matrix", {})))
		if include_node_transforms:
			leaf_to_root.append_array(_source_node_matrices())
		return SourceBoundsMath.bounds_for_chain(shape_bounds, leaf_to_root)
	if str(definition.get("type", "")) != "DefineSpriteTag":
		return Rect2i()
	var sprite_frames: Array = definition.get("display_list_frames", [])
	var local_frame := _visual_nested_frame(placement, timeline_frame, sprite_frames.size(), clip_age, visual_clip)
	var children: Array = (
		sprite_frames[local_frame - 1]
		if not sprite_frames.is_empty()
		else definition.get("first_frame_display_list", [])
	)
	var child_clip_age := clip_age
	var instance_name := str(placement.get("name", ""))
	if instance_name != "" and _instance_local_frames.has(instance_name):
		child_clip_age = int(_instance_local_frames[instance_name].get("age", clip_age))
	var result := Rect2i()
	var has_result := false
	for child: Dictionary in children:
		var child_bounds := _collect_source_bounds(
			child,
			local_frame,
			matrices,
			child_clip_age,
			include_wrapper,
			include_node_transforms,
			_visual_clip_at(child, visual_clip.get("children", {}))
		)
		if child_bounds.size.x <= 0 or child_bounds.size.y <= 0:
			continue
		result = child_bounds if not has_result else result.merge(child_bounds)
		has_result = true
	return result


func _source_placement_matrix(placement: Dictionary) -> Dictionary:
	var instance_name := str(placement.get("name", ""))
	return SourceBoundsMath.from_swf(
		placement.get("matrix", {}), instance_local_offset(instance_name)
	)


func _source_node_matrices() -> Array[Dictionary]:
	var matrices: Array[Dictionary] = []
	var node: Node = self
	while node is Node2D:
		matrices.append(_source_node_matrix(node as Node2D))
		node = node.get_parent()
	return matrices


func _source_node_matrix(node: Node2D) -> Dictionary:
	var transform_2d := node.transform
	var scale_x := float(transform_2d.x.x)
	var skew_y := float(transform_2d.x.y)
	var skew_x := float(transform_2d.y.x)
	var scale_y := float(transform_2d.y.y)
	if _has_property(node, "game_scale"):
		var game_scale := GameWorld.store_scale(float(node.get("game_scale")))
		scale_x = game_scale
		scale_y = game_scale
	var translation_x := _node_translation_twips(node, "source_x", "game_x", node.position.x)
	var translation_y := _node_translation_twips(node, "source_y", "game_y", node.position.y)
	return SourceBoundsMath.from_components(
		scale_x,
		skew_y,
		skew_x,
		scale_y,
		translation_x,
		translation_y
	)


func _node_translation_twips(
	node: Node2D, source_property: String, camera_property: String, fallback: float
) -> int:
	var value := fallback
	if _has_property(node, source_property):
		value = float(node.get(source_property))
	elif _has_property(node, camera_property):
		value = float(node.get(camera_property))
	else:
		value = SourceCoordinateMath.from_projection(value)
	# Source-coordinate setters store integer twips. Keep this property assignment
	# step separate from the ties-even rounding used when matrices are composed.
	# Generic Node2D positions are float32 projections, so recover their twips
	# with SourceCoordinate.from_projection before reading the source transform.
	return int(value * TWIPS_PER_PIXEL)


func _has_property(object: Object, property_name: String) -> bool:
	for property: Dictionary in object.get_property_list():
		if str(property.get("name", "")) == property_name:
			return true
	return false


func _definition_bounds(
	definition: Dictionary,
	placement: Dictionary,
	timeline_frame: int,
	visual_clip: Dictionary = {}
) -> Rect2:
	if definition.has("shape_bounds_twips"):
		var bounds: Dictionary = definition["shape_bounds_twips"]
		return Rect2(
			Vector2(float(bounds["Xmin"]), float(bounds["Ymin"])) / 20.0,
			Vector2(
				float(bounds["Xmax"] - bounds["Xmin"]),
				float(bounds["Ymax"] - bounds["Ymin"])
			) / 20.0
		)
	if definition["type"] != "DefineSpriteTag":
		return Rect2()
	var sprite_frames: Array = definition.get("display_list_frames", [])
	var local_frame := _visual_nested_frame(placement, timeline_frame, sprite_frames.size(), 0, visual_clip)
	var children: Array = (
		sprite_frames[local_frame - 1]
		if not sprite_frames.is_empty()
		else definition.get("first_frame_display_list", [])
	)
	var result := Rect2()
	for child: Dictionary in children:
		var child_bounds := _placement_bounds(child, local_frame, _visual_clip_at(child, visual_clip.get("children", {})))
		if not child_bounds.has_area():
			continue
		result = child_bounds if not result.has_area() else result.merge(child_bounds)
	return result


func _visual_nested_frame(placement: Dictionary, timeline_frame: int,
		frame_count: int, clip_age: int, visual_clip: Dictionary) -> int:
	if not visual_clip.is_empty():
		return int(visual_clip.frame)
	return _nested_frame(placement, timeline_frame, frame_count, clip_age)


func _nested_frame(
	placement: Dictionary,
	timeline_frame: int,
	frame_count: int,
	clip_age: int = 0
) -> int:
	var instance_name := str(placement.get("name", ""))
	if instance_name != "" and _instance_local_frames.has(instance_name):
		return maxi(1, int(_instance_local_frames[instance_name]["local_start"]))
	if frame_count <= 1:
		return 1
	for parent_name: String in _instance_local_frames:
		var parent: Dictionary = _instance_local_frames[parent_name]
		for child: Dictionary in _instance_children(parent_name, int(parent["local_start"])):
			if not is_same(child, placement):
				continue
			var clock: Dictionary = parent.get("child_clocks", {}).get(int(child["depth"]), {})
			if not clock.is_empty():
				var elapsed_frame := int(clock["age"]) + 1
				for stop_frame in parent.get("child_stop_frames", {}).get(str(int(child["character_id"])), []):
					if elapsed_frame >= int(stop_frame):
						return int(stop_frame)
				return posmod(elapsed_frame - 1, frame_count) + 1
	if independent_visual_clock:
		var retained := _visual_clip_at(placement, _retained_visual_clips)
		if not retained.is_empty():
			return int(retained.frame)
	# Unnamed clips inside a projectile playhead keep that clip's age so they
	# do not follow the fighter timeline. Root unnamed clips (walk body, etc.)
	# have clip_age 0 and must sync from placed_frame, otherwise they stay
	# on local frame 1 and the character only translates.
	if instance_name == "" and clip_age > 0:
		return posmod(clip_age, frame_count) + 1
	var placed_frame := int(placement.get("placed_frame", timeline_frame))
	return posmod(maxi(0, timeline_frame - placed_frame), frame_count) + 1


func _transform_rect(transform_2d: Transform2D, rectangle: Rect2) -> Rect2:
	var corners := [
		transform_2d * rectangle.position,
		transform_2d * Vector2(rectangle.end.x, rectangle.position.y),
		transform_2d * rectangle.end,
		transform_2d * Vector2(rectangle.position.x, rectangle.end.y),
	]
	var minimum: Vector2 = corners[0]
	var maximum: Vector2 = corners[0]
	for corner: Vector2 in corners.slice(1):
		minimum = minimum.min(corner)
		maximum = maximum.max(corner)
	return Rect2(minimum, maximum - minimum)


func _draw() -> void:
	if not show_collision_shapes or not _frames.has(_current_frame):
		return
	for placement: Dictionary in _frames[_current_frame]["display_list"]:
		var instance_name := str(placement.get("name", ""))
		if instance_name == "bdmn" or instance_name.ends_with("atm"):
			_draw_collision_shape(placement, instance_name.ends_with("atm"))


func _draw_collision_shape(placement: Dictionary, is_attack: bool) -> void:
	var definition: Dictionary = _definitions.get(int(placement.get("character_id", -1)), {})
	var references: Array = definition.get("referenced_character_ids", [])
	if references.size() != 1:
		return
	var shape: Dictionary = _definitions.get(int(references[0]), {})
	if not shape.has("shape_bounds_twips"):
		return
	var bounds: Dictionary = shape["shape_bounds_twips"]
	var rectangle := Rect2(
		Vector2(float(bounds["Xmin"]), float(bounds["Ymin"])) / 20.0,
		Vector2(
			float(bounds["Xmax"] - bounds["Xmin"]),
			float(bounds["Ymax"] - bounds["Ymin"])
		) / 20.0
	)
	var transform_2d := _wrapper_transform() * _placement_transform(placement)
	var color := Color(1.0, 0.2, 0.16, 0.28) if is_attack else Color(0.2, 0.65, 1.0, 0.18)
	draw_set_transform_matrix(transform_2d)
	draw_rect(rectangle, color, true)
	draw_rect(rectangle, color.lightened(0.35), false, 1.0)
	draw_set_transform_matrix(Transform2D.IDENTITY)
