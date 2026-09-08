class_name HitEffectRuntime
extends Node2D

signal pause_requested
signal resume_requested
signal shine_requested(color_rgb24: int)
signal shake_requested(axis: String, pixels: float)

var auto_advance: bool = true
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
	_events = _clip_events(effect_name)
	_preview = TimelinePreview.new()
	_preview.fighter_directory = _directory
	_preview.initial_frame = 1
	_preview.autoplay = false
	_preview.show_collision_shapes = false
	add_child(_preview)
	effect_frame = 1
	_apply_frame_events()


func _physics_process(_delta: float) -> void:
	if not auto_advance or _preview == null:
		return
	advance_effect()


func advance_effect() -> void:
	if _preview == null:
		return
	effect_frame += 1
	if effect_frame > _frame_count:
		queue_free()
		return
	_preview.play_source_frame(effect_frame)
	_apply_frame_events()


func _apply_frame_events() -> void:
	last_ops.clear()
	last_sound_ids.clear()
	_start_frame_sounds()
	for event: Dictionary in _events:
		if int(event.get("frame", -1)) != effect_frame:
			continue
		var event_key := "%d:%s" % [effect_frame, event.get("op", "")]
		if _applied.has(event_key):
			continue
		_applied[event_key] = true
		var op := str(event.get("op", ""))
		last_ops.append(op)
		match op:
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
				shake_requested.emit(str(event.get("axis", "x")), float(event.get("pixels", 0.0)))
			"unload":
				queue_free()


func _start_frame_sounds() -> void:
	# Source StartSound on the XG clip's own frame. The player is a child of
	# this node, so unloadMovie/queue_free stops it like the Flash clip does.
	for event: Dictionary in _sound_events.get(effect_frame, []):
		var sound_id := int(event.get("sound_id", -1))
		if not _sound_assets.has(sound_id):
			push_warning("Hit effect sound not materialized: %s/%d" % [_directory, sound_id])
			continue
		for key: String in ["loop_count", "in_point", "out_point", "sync_stop"]:
			if event.has(key):
				push_warning("Unhandled SOUNDINFO %s on %s" % [key, _directory])
		var stream: AudioStream = load("%s/%s" % [_directory, _sound_assets[sound_id]])
		if stream == null:
			continue
		var player := AudioStreamPlayer.new()
		player.stream = stream
		player.volume_db = _sound_volume_db(event)
		player.autoplay = true
		last_sound_ids.append(sound_id)
		add_child(player)


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
