class_name IntroClip
extends TimelinePreview

var round_number: int = 1


func _nested_frame(placement: Dictionary, timeline_frame: int, frame_count: int, clip_age: int = 0) -> int:
	var definition: Dictionary = _definitions.get(int(placement.get("character_id", -1)), {})
	if definition.has("intro_round_offset"):
		return round_number + int(definition["intro_round_offset"])
	if definition.has("intro_stop_frame"):
		var age := maxi(0, timeline_frame - int(placement.get("placed_frame", timeline_frame)))
		return mini(age + 1, int(definition["intro_stop_frame"]))
	return super._nested_frame(placement, timeline_frame, frame_count, clip_age)


func _render_solid_fills(definition: Dictionary, placement_transform: Transform2D,
	depth: int, rgb_mul: Color, rgb_add: Color, alpha: float, blend: int = 1) -> void:
	# Export the actual vector outline, including numeral gradients; its AABB
	# is only the registration rectangle, never a replacement filled polygon.
	var texture: Texture2D = load("%s/shape-%s.png" % [fighter_directory, int(definition["character_id"])])
	var bounds: Dictionary = definition["shape_bounds_twips"]
	var sprite := Sprite2D.new()
	sprite.centered = false
	sprite.texture = texture
	sprite.z_index = depth
	var local := Transform2D.IDENTITY
	local.origin = Vector2(float(bounds["Xmin"]), float(bounds["Ymin"])) / 20.0
	local.x.x = float(bounds["Xmax"] - bounds["Xmin"]) / 20.0 / texture.get_width()
	local.y.y = float(bounds["Ymax"] - bounds["Ymin"]) / 20.0 / texture.get_height()
	sprite.transform = placement_transform * local
	_apply_cxform(sprite, rgb_mul, rgb_add, alpha)
	_apply_blend(sprite, blend)
	add_child(sprite)


func _play_start_sounds() -> void:
	if _sound_played_frame == _current_frame:
		return
	_sound_played_frame = _current_frame
	last_sound_ids.clear()
	var sound_index := 0
	for event: Dictionary in _frames.get(_current_frame, {}).get("events", []):
		if str(event.get("type", "")) != "start_sound":
			continue
		var sound_id := int(event["sound_id"])
		assert(_assets.has(sound_id), "Missing intro sound %d" % sound_id)
		sound_index += 1
		last_sound_ids.append(sound_id)
		if not preload("res://rollback_presentation.gd").allow_sound(self, "%d:%d:%d" % [_source_entry_serial, sound_index, sound_id]):
			continue
		var player := AudioStreamPlayer.new()
		player.stream = load("%s/%s" % [fighter_directory, _assets[sound_id]])
		player.volume_db = _sound_volume_db(event)
		player.finished.connect(player.queue_free)
		_sound_layer().add_child(player)
		# SWF SOUNDINFO positions are always measured in 44.1 kHz samples.
		var start := float(event.get("in_point", 0)) / 44100.0
		player.play(start)
		preload("res://authority_audio.gd").accepted(self, player, start, float(event["out_point"]) / 44100.0 if event.has("out_point") else -1.0)
		if event.has("out_point"):
			var timer := Timer.new()
			timer.one_shot = true
			player.add_child(timer)
			timer.timeout.connect(player.queue_free)
			timer.start(float(event["out_point"]) / 44100.0 - start)
