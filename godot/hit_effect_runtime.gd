class_name HitEffectRuntime
extends Node2D

signal pause_requested
signal resume_requested
signal shine_requested(color_rgb24: int)
signal root_position_requested(axis: String, operator: String, pixels: float)

var auto_advance: bool = true
var defer_initial_frame: bool = false
var source_random: SourceRandom
var effect_frame: int = 1
var game_paused: bool = false
var last_shine_color: int = -1
var last_ops: Array[String] = []
var last_sound_ids: Array[int] = []

# SOUNDENVELOPE levels are 0..32768 volume scales (SWF spec).
const SOUND_ENVELOPE_MAX := 32768.0

var _preview: TimelinePreview
var _frame_count: int = 1
var _events: Array = []
var _applied: Dictionary = {}
var _directory: String
var _sound_events: Dictionary = {}
var _sound_assets: Dictionary = {}
var _sound_segments: Dictionary = {}
var _initial_frame_pending: bool = false
var _callback_registry: SourceCallbackRegistry
var _registration: int = 0


func register_source_frames(registry: SourceCallbackRegistry, placed_tick: int) -> void:
	assert(_callback_registry == null)
	auto_advance = false
	_callback_registry = registry
	_registration = registry.register(self, "advance_effect", placed_tick)


func _exit_tree() -> void:
	unregister_source_frames()


func unregister_source_frames() -> void:
	if _callback_registry != null:
		_callback_registry.unregister(_registration)
		_callback_registry = null


func configure(effect_name: String, source_position: Vector2, source_facing: int, offset_y: float = -25.0) -> void:
	position = source_position + Vector2(0.0, offset_y)
	scale.x = 1.0 if source_facing >= 0 else -1.0
	z_index = 20
	_directory = "res://generated/effects/%s" % effect_name
	var timeline := _read_json("%s/timeline.json" % _directory)
	if timeline.is_empty():
		push_error("Missing hit effect timeline: %s/timeline.json" % _directory)
	_frame_count = maxi(1, int(timeline.get("frame_count", 1)))
	_sound_events = _collect_sound_events(timeline)
	_sound_assets = _collect_sound_assets()
	var segments_path := _directory.path_join("sound_segments.json")
	if FileAccess.file_exists(segments_path):
		var segments := _read_json(segments_path)
		assert(segments["source_swf"] == timeline["source_swf"] and segments["envelope_baked"])
		_sound_segments = segments["frames"]
	_events = _clip_events(effect_name)
	_preview = TimelinePreview.new()
	_preview.fighter_directory = _directory
	_preview.initial_frame = 1
	_preview.autoplay = false
	_preview.independent_visual_clock = true
	# The effect's source-frame scheduler owns sound playback, including frame 1.
	_preview.play_timeline_sounds = false
	_preview.show_collision_shapes = false
	add_child(_preview)
	effect_frame = 1
	_initial_frame_pending = true
	if not defer_initial_frame:
		run_initial_frame()


func run_initial_frame() -> void:
	if not _initial_frame_pending:
		return
	_initial_frame_pending = false
	_apply_frame_events()


func _physics_process(_delta: float) -> void:
	if not auto_advance or _preview == null:
		return
	advance_effect()


func advance_effect() -> void:
	if _preview == null or is_queued_for_deletion():
		return
	run_initial_frame()
	_preview.advance_retained_visual_clips()
	effect_frame += 1
	if effect_frame > _frame_count:
		preload("res://rollback_lifetime.gd").retire(self)
		return
	_preview.play_source_frame(effect_frame)
	_apply_frame_events()


func _apply_frame_events() -> void:
	last_ops.clear()
	last_sound_ids.clear()
	_start_frame_sounds()
	for event_index in _events.size():
		var event: Dictionary = _events[event_index]
		if int(event.get("frame", -1)) != effect_frame:
			continue
		var event_key := event_index
		if _applied.has(event_key):
			continue
		_applied[event_key] = true
		var op := str(event.get("op", ""))
		last_ops.append(op)
		match op:
			"random_rotation":
				var angle := source_random.effect_angle(int(event.limit), str(event.source_path))
				# Flash rotates the signed X axis of the attached clip. Decomposing
				# a mirrored Godot basis can instead move its reflection onto Y.
				var facing := signf(transform.determinant())
				transform = Transform2D(deg_to_rad(angle), Vector2(facing, 1.0), 0.0, position)
			"random_offset":
				assert(source_random != null, "Hit effect requires the shared source random stream")
				var positive := source_random.next_value(event["random_sites"][0])
				var negative := source_random.next_value(event["random_sites"][1])
				if source_random.failure != "":
					return
				var offset := positive * float(event["positive_factor"]) - negative * float(event["negative_factor"])
				if event["axis"] == "x":
					position.x += offset
				else:
					assert(event["axis"] == "y")
					position.y += offset
			"pause_game":
				game_paused = true
				pause_requested.emit()
			"resume_game":
				game_paused = false
				resume_requested.emit()
			"shine":
				last_shine_color = int(event.get("color_rgb24", 0xFFFFFF))
				shine_requested.emit(last_shine_color)
			"shake_root":
				root_position_requested.emit(event["axis"], event["operator"], float(event["pixels"]))
			"unload":
				preload("res://rollback_lifetime.gd").retire(self)


func _start_frame_sounds() -> void:
	# Source StartSound on the XG clip's own frame. The player is a child of
	# this node, so unloadMovie/queue_free stops it like the Flash clip does.
	var segments: Array = _sound_segments.get(str(effect_frame), [])
	var sound_index := 0
	for event: Dictionary in _sound_events.get(effect_frame, []):
		var sound_id := int(event.get("sound_id", -1))
		if not _sound_assets.has(sound_id):
			push_warning("Hit effect sound not materialized: %s/%d" % [_directory, sound_id])
			continue
		var sound_file: String = _sound_assets[sound_id]
		if not segments.is_empty():
			assert(sound_index < segments.size() and segments[sound_index]["source_event"] == event)
			sound_file = segments[sound_index]["stream"]
		else:
			for key: String in ["loop_count", "in_point", "out_point", "sync_stop"]:
				if event.has(key):
					push_warning("Unhandled SOUNDINFO %s on %s" % [key, _directory])
		sound_index += 1
		var stream: AudioStream = load("%s/%s" % [_directory, sound_file])
		if stream == null:
			continue
		last_sound_ids.append(sound_id)
		if not preload("res://rollback_presentation.gd").allow_sound(self, "%d:%d:%d:%s" % [_registration, effect_frame, sound_index, sound_file]):
			continue
		var player := AudioStreamPlayer.new()
		player.stream = stream
		player.volume_db = 0.0 if not segments.is_empty() else _sound_volume_db(event)
		player.autoplay = true
		add_child(player)
		preload("res://authority_audio.gd").accepted(self, player)


func _sound_volume_db(event: Dictionary) -> float:
	var envelope: Array = event.get("envelope", [])
	if envelope.is_empty():
		return 0.0
	# One record = constant level. Flash scales the channels separately;
	# AudioStreamPlayer has a single gain, so use the channel mean.
	var record: Dictionary = envelope[0]
	var level := (
		float(record.get("left_level", SOUND_ENVELOPE_MAX))
		+ float(record.get("right_level", SOUND_ENVELOPE_MAX))
	) / 2.0
	if level <= 0.0:
		return -80.0
	return linear_to_db(level / SOUND_ENVELOPE_MAX)


func _collect_sound_events(timeline: Dictionary) -> Dictionary:
	var by_frame: Dictionary = {}
	for frame: Dictionary in timeline.get("frames", []):
		for event: Dictionary in frame.get("events", []):
			if str(event.get("type", "")) != "start_sound":
				continue
			var number := int(frame.get("frame", 0))
			if not by_frame.has(number):
				by_frame[number] = []
			by_frame[number].append(event)
	return by_frame


func _collect_sound_assets() -> Dictionary:
	var manifest := _read_json("%s/assets.json" % _directory)
	var paths: Dictionary = {}
	for asset: Dictionary in manifest.get("assets", []):
		var path := str(asset.get("path", ""))
		if path.get_extension().to_lower() == "mp3":
			paths[int(asset.get("character_id", -1))] = path
	return paths


func _clip_events(effect_name: String) -> Array:
	var effect_path := "%s/effect.json" % _directory
	if FileAccess.file_exists(effect_path):
		var effect := _read_json(effect_path)
		assert(effect.get("clip") == effect_name)
		return effect["presentation_events"]
	var parsed := _read_json("res://generated/main/hit_receive.json")
	if parsed.is_empty():
		return []
	var clips: Dictionary = parsed.get("hit_fx", {}).get("clips", {})
	if not clips.has(effect_name):
		return []
	return clips[effect_name].get("presentation_events", [])


func _read_json(path: String) -> Dictionary:
	var file := FileAccess.open(path, FileAccess.READ)
	if file == null:
		return {}
	var parsed: Variant = JSON.parse_string(file.get_as_text())
	return parsed if parsed is Dictionary else {}
