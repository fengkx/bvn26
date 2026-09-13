extends SceneTree

var failed := false


func _initialize() -> void:
	_run.call_deferred()


func _check(condition: bool, message: String) -> void:
	if not condition:
		push_error(message)
		failed = true


func _source_sound_ids(timeline: Dictionary, frame: int) -> Array[int]:
	var ids: Array[int] = []
	for source_frame: Dictionary in timeline.get("frames", []):
		if int(source_frame.get("frame", -1)) != frame:
			continue
		for event: Dictionary in source_frame.get("events", []):
			if str(event.get("type", "")) == "start_sound":
				ids.append(int(event.get("sound_id", -1)))
	return ids


func _audio_players(node: Node) -> Array[AudioStreamPlayer]:
	var result: Array[AudioStreamPlayer] = []
	for child: Node in node.find_children("*", "AudioStreamPlayer", true, false):
		if child is AudioStreamPlayer:
			result.append(child as AudioStreamPlayer)
	return result


func _run() -> void:
	var args := OS.get_cmdline_user_args()
	assert(args.size() == 1, "Expected one probe specification JSON path")
	var spec: Dictionary = JSON.parse_string(FileAccess.get_file_as_string(args[0]))
	var fighter_directory := str(spec.get("fighter_directory", ""))
	var timeline_path := fighter_directory.path_join("timeline.json")
	var timeline: Dictionary = JSON.parse_string(FileAccess.get_file_as_string(timeline_path))
	var output_directory := str(spec.get("output_directory", ""))
	assert(not fighter_directory.is_empty() and not output_directory.is_empty())
	DirAccess.make_dir_recursive_absolute(output_directory)
	root.size = Vector2i(1280, 720)
	root.transparent_bg = true
	var rendered_viewport := DisplayServer.get_name() != "headless"
	var capture_viewport := SubViewport.new()
	capture_viewport.size = root.size
	capture_viewport.transparent_bg = false
	capture_viewport.render_target_update_mode = SubViewport.UPDATE_ALWAYS
	root.add_child(capture_viewport)

	var fighter := FighterRuntime.new()
	fighter.fighter_directory = fighter_directory
	fighter.autoplay = false
	fighter.play_timeline_sounds = true
	fighter.show_collision_shapes = false
	fighter.position = Vector2(320, 480)
	capture_viewport.add_child(fighter)
	await process_frame

	var observations: Array[Dictionary] = []
	var visual_capture_status := "pending"
	for value: Variant in spec.get("frames", []):
		var frame := int(value)
		var source_ids := _source_sound_ids(timeline, frame)
		var prior_players := _audio_players(fighter)
		fighter.play_source_frame(frame)
		await process_frame
		if rendered_viewport:
			await RenderingServer.frame_post_draw
		var runtime_ids: Array = fighter.last_sound_ids.duplicate()
		var all_players := _audio_players(fighter)
		var new_players: Array[AudioStreamPlayer] = []
		for player: AudioStreamPlayer in all_players:
			if not prior_players.has(player) and player.playing and player.stream != null:
				new_players.append(player)
		var playing := all_players.filter(func(player: AudioStreamPlayer) -> bool:
			return player.playing and player.stream != null)
		_check(source_ids == runtime_ids,
			"StartSound ID mismatch at source frame %d: source=%s runtime=%s" % [frame, source_ids, runtime_ids])
		_check(source_ids.size() == new_players.size(),
			"Expected %d newly playing streams at source frame %d, got %d" %
			[source_ids.size(), frame, new_players.size()])
		var expected_stream_paths: Array[String] = []
		var source_sound_index := 0
		var source_sound_events: Array[Dictionary] = []
		for source_frame: Dictionary in timeline.get("frames", []):
			if int(source_frame.get("frame", -1)) == frame:
				for event: Dictionary in source_frame.get("events", []):
					if str(event.get("type", "")) == "start_sound":
						source_sound_events.append(event)
		var segments: Array = fighter._sound_segments.get(str(frame), [])
		var fighter_resource_directory: String
		if fighter_directory.begins_with("res://"):
			fighter_resource_directory = fighter_directory.trim_suffix("/")
		else:
			var project_root := ProjectSettings.globalize_path("res://").trim_suffix("/")
			fighter_resource_directory = "res://" + fighter_directory.trim_prefix(project_root).trim_prefix("/")
		for sound_event: Dictionary in source_sound_events:
			var relative_path: String = fighter._assets.get(int(sound_event.get("sound_id", -1)), "")
			if not segments.is_empty():
				_check(source_sound_index < segments.size(), "Missing baked sound segment at frame %d" % frame)
				if source_sound_index < segments.size():
					_check(segments[source_sound_index].get("source_event") == sound_event,
						"Baked sound segment does not match source SOUNDINFO at frame %d" % frame)
					relative_path = str(segments[source_sound_index].get("stream", ""))
			source_sound_index += 1
			expected_stream_paths.append(fighter_resource_directory.path_join(relative_path))
		var actual_stream_paths: Array = new_players.map(func(player: AudioStreamPlayer) -> String:
			return player.stream.resource_path)
		_check(actual_stream_paths == expected_stream_paths,
			"Audio resource mismatch at source frame %d: expected=%s actual=%s" %
			[frame, expected_stream_paths, actual_stream_paths])
		var image_path := output_directory.path_join("frame-%d.png" % frame)
		var viewport_texture := capture_viewport.get_texture()
		var screenshot_written := false
		if rendered_viewport and viewport_texture != null:
			var image := viewport_texture.get_image()
			if image != null:
				screenshot_written = image.save_png(image_path) == OK
				if not screenshot_written:
					_check(false, "Could not save key frame image: " + image_path)
				visual_capture_status = "captured" if screenshot_written else "failed"
			else:
				visual_capture_status = "unavailable_without_rendered_viewport"
		elif rendered_viewport:
			visual_capture_status = "unavailable_without_rendered_viewport"
		else:
			visual_capture_status = "skipped_headless"
		observations.append({
			"source_frame": frame,
			"source_sound_ids": source_ids,
			"godot_frame_sound_ids": runtime_ids,
			"expected_stream_paths": expected_stream_paths,
			"new_playing_streams": new_players.size(),
			"all_playing_streams": playing.size(),
			"player_stream_paths": new_players.map(func(player: AudioStreamPlayer) -> String:
				return player.stream.resource_path),
			"screenshot": image_path if screenshot_written else ""
		})

	var trace := {
		"format": "source-audiovisual-probe-v1",
		"scope": "Godot AudioStreamPlayer start observation and optional rendered key frames; not an original Flash audio playback observation",
		"fighter_directory": fighter_directory,
		"source_swf": timeline.get("source_swf", {}),
		"observations": observations,
		"audio_player_status": "passed" if not failed else "failed",
		"visual_capture_status": visual_capture_status,
		"display_server": DisplayServer.get_name()
	}
	var trace_path := output_directory.path_join("trace.json")
	var trace_file := FileAccess.open(trace_path, FileAccess.WRITE)
	_check(trace_file != null, "Could not create audio/visual trace JSON")
	if trace_file != null:
		trace_file.store_string(JSON.stringify(trace, "  ") + "\n")
		trace_file.close()
	for player: AudioStreamPlayer in _audio_players(fighter):
		player.stop()
		player.queue_free()
	fighter.queue_free()
	await process_frame
	await process_frame
	print("GODOT_AUDIO_PLAYER_PROBE_" + str(trace.audio_player_status).to_upper() + " " + JSON.stringify(trace))
	quit(1 if failed else 0)
