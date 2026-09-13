extends SceneTree

var preview: TimelinePreview
var sound_events: Array[Dictionary] = []
var failed := false


func _initialize() -> void:
	_run.call_deferred()


func _check(condition: bool, message: String) -> void:
	if not condition:
		push_error(message)
		failed = true


func _placement(placed_frame: int, tx: int = 0) -> Dictionary:
	return {
		"character_id": 185,
		"depth": 28,
		"placed_frame": placed_frame,
		"name": "nested_test",
		"matrix": {"tx": tx, "ty": 0, "scale_x": 1.0, "scale_y": 1.0},
	}


func _root_frame(frame: int, placement: Dictionary) -> Dictionary:
	return {
		"frame": frame,
		"display_list": [placement],
		"events": [],
		"changes": [],
	}


func _root_sprite_instances() -> Array[String]:
	var result: Array[String] = []
	for instance_id: String in preview._nested_sound_instance_frames.keys():
		if instance_id.count("/") == 1:
			result.append(instance_id)
	return result


func _run() -> void:
	preview = TimelinePreview.new()
	preview.fighter_directory = "res://generated/fighters/yulong"
	preview.autoplay = false
	preview.play_timeline_sounds = true
	root.add_child(preview)
	await process_frame
	preview.nested_source_sound_started.connect(_on_nested_sound_started)
	var original := _placement(1)
	var synthetic_frames: Dictionary = {}
	for frame in range(1, 11):
		var current := original
		if frame == 9 or frame == 10:
			current = _placement(1, frame * 20)
		synthetic_frames[frame] = _root_frame(frame, current)
	preview._frames = synthetic_frames
	preview.play_source_frame(8)
	_check(sound_events.size() == 1, "Child frame 8 should start sound 164 once")
	_check(sound_events[0].get("sound_id") == 164, "Unexpected nested sound id")
	var first_instance := str(sound_events[0].get("instance_id", ""))
	preview.refresh_display()
	preview.refresh_display()
	_check(sound_events.size() == 1, "Redrawing the same playhead restarted nested audio")
	preview.play_source_frame(9)
	preview.play_source_frame(10)
	var retained_ids := _root_sprite_instances()
	_check(retained_ids.size() == 1 and str(retained_ids[0]) == first_instance,
		"MOVE at the same depth should retain the original nested instance")
	var replacement := _placement(11)
	for frame in range(11, 19):
		synthetic_frames[frame] = _root_frame(frame, replacement)
	preview._frames = synthetic_frames
	preview.play_source_frame(11)
	var first_generation := _root_sprite_instances()
	preview.play_source_frame(11)
	var repeated_generation := _root_sprite_instances()
	_check(first_generation.size() == 1 and repeated_generation.size() == 1,
		"Expected exactly one active instance at the source depth")
	_check(str(first_generation[0]) != str(repeated_generation[0]),
		"A new PlaceObject at the same depth/frame reentry reused the old generation")
	for frame in range(12, 19):
		preview.play_source_frame(frame)
	_check(sound_events.size() == 2, "New same-depth instance should play sound 164 once")
	if sound_events.size() >= 2:
		_check(sound_events[1].get("sound_id") == 164, "Replacement instance played wrong sound")
		_check(sound_events[1].get("instance_id") != first_instance,
			"Replacement instance reused the earlier child identity")
	var trace := {
		"format": "bvn26-nested-start-sound-smoke-v1",
		"scope": "source child frame dispatch, redraw idempotence, MOVE identity, and same-depth PlaceObject generation",
		"events": sound_events,
		"active_instances": preview._nested_sound_instance_frames,
		"status": "passed" if not failed else "failed",
	}
	print("NESTED_START_SOUND_SMOKE_" + str(trace.status).to_upper() + " " + JSON.stringify(trace))
	preview.queue_free()
	await process_frame
	quit(1 if failed else 0)


func _on_nested_sound_started(event: Dictionary) -> void:
	sound_events.append(event.duplicate(true))
