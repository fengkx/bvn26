class_name HitEffectRuntime
extends Node2D

var _preview: TimelinePreview
var _frame_count: int = 1
var _frame: int = 1


func configure(effect_name: String, source_position: Vector2, source_facing: int) -> void:
	position = source_position + Vector2(0.0, -25.0)
	scale.x = 1.0 if source_facing >= 0 else -1.0
	z_index = 20
	var directory := "res://generated/effects/%s" % effect_name
	_frame_count = _read_frame_count("%s/timeline.json" % directory)
	_preview = TimelinePreview.new()
	_preview.fighter_directory = directory
	_preview.initial_frame = 1
	_preview.autoplay = false
	_preview.show_collision_shapes = false
	add_child(_preview)


func _physics_process(_delta: float) -> void:
	if _preview == null:
		return
	_frame += 1
	if _frame > _frame_count:
		queue_free()
		return
	_preview.play_source_frame(_frame)


func _read_frame_count(path: String) -> int:
	var file := FileAccess.open(path, FileAccess.READ)
	if file == null:
		push_error("Missing hit effect timeline: %s" % path)
		return 1
	var parsed: Variant = JSON.parse_string(file.get_as_text())
	if parsed is Dictionary:
		return maxi(1, int(parsed.get("frame_count", 1)))
	return 1
