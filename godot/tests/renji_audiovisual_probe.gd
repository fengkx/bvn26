extends SceneTree

const CASES := [

	{"label": "瞬步", "source_frame": 21, "sound_ids": [38]},
	{"label": "砍1", "source_frame": 177, "sound_ids": [60]},
	{"label": "必杀", "source_frame": 516, "sound_ids": [69]},
	{"label": "上必杀", "source_frame": 606, "sound_ids": [386]},
	{"label": "超必杀", "source_frame": 689, "sound_ids": [446]},
	{"label": "超必杀", "source_frame": 832, "sound_ids": [504]}
]
const OUTPUT_ROOT := "/tmp/renji-audiovisual-r01"


func _initialize() -> void:
	_run.call_deferred()


func _run() -> void:
	var output := DirAccess.open("res://")
	assert(output != null)
	DirAccess.make_dir_recursive_absolute(OUTPUT_ROOT)
	root.transparent_bg = true
	var preview := TimelinePreview.new()
	preview.fighter_directory = "res://generated/fighters/renji"
	preview.autoplay = false
	preview.play_timeline_sounds = true
	root.add_child(preview)
	await process_frame
	var observations: Array[Dictionary] = []
	for item: Dictionary in CASES:
		preview.play_source_frame(int(item["source_frame"]))
		await process_frame
		var filename := "%s/%s-frame-%d.png" % [OUTPUT_ROOT, item["label"], int(item["source_frame"])]
		var screenshot := ""
		if DisplayServer.get_name() != "headless":
			var viewport_texture := root.get_texture()
			if viewport_texture != null:
				var image := viewport_texture.get_image()
				if image != null:
					image.save_png(filename)
					screenshot = filename
		var players := preview._sound_layer().get_children()
		var lengths: Array[float] = []
		for player: Node in players:
			if player is AudioStreamPlayer and player.stream is AudioStream:
				lengths.append((player.stream as AudioStream).get_length())
		observations.append({
			"label": item["label"],
			"source_frame": int(item["source_frame"]),
			"source_sound_ids": item["sound_ids"],
			"runtime_sound_ids": preview.last_sound_ids.duplicate(),
			"audio_stream_length_seconds": lengths.back() if not lengths.is_empty() else 0.0,
			"screenshot": screenshot
		})
	var trace := {
		"format": "renji-audiovisual-probe-v1",
		"fighter_directory": preview.fighter_directory,
		"source_timeline": "data/slices/Renji-base.timeline.json",
		"observations": observations
	}
	var file := FileAccess.open("%s/runtime-audio-trace.json" % OUTPUT_ROOT, FileAccess.WRITE)
	assert(file != null)
	file.store_string(JSON.stringify(trace, "  "))
	file.close()
	print("RENJI_AUDIOVISUAL_PROBE_OK ", JSON.stringify(trace))
	quit()
