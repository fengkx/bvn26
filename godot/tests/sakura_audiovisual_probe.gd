extends SceneTree

const OUTPUT := "/private/tmp/sakura-audiovisual-r01/runtime-audio-trace.json"
const FIGHTER_CASES := [
	{"label": "跳", "frame": 42, "sound_ids": [39]},
	{"label": "跳砍", "frame": 129, "sound_ids": [49]},
	{"label": "砍1", "frame": 207, "sound_ids": [49]},
	{"label": "砍技1", "frame": 317, "sound_ids": [147]},
	{"label": "招1", "frame": 423, "sound_ids": [232]},
	{"label": "必杀", "frame": 574, "sound_ids": [62]},
	{"label": "空中必杀", "frame": 660, "sound_ids": [124]},
	{"label": "砍技2", "frame": 386, "sound_ids": [62, 124]},
	{"label": "超必杀", "frame": 720, "sound_ids": [458]},
	{"label": "超必杀", "frame": 766, "sound_ids": [479]}
]

var failed := false


func _initialize() -> void:
	_run.call_deferred()


func check(condition: bool, message: String) -> void:
	if not condition:
		push_error(message)
		failed = true


func source_sound_ids(timeline: Dictionary, frame: int) -> Array[int]:
	var result: Array[int] = []
	for source_frame: Dictionary in timeline.get("frames", []):
		if int(source_frame.get("frame", -1)) != frame:
			continue
		for event: Dictionary in source_frame.get("events", []):
			if str(event.get("type", "")) == "start_sound":
				result.append(int(event.get("sound_id", -1)))
	return result


func audio_players(node: Node) -> Array[AudioStreamPlayer]:
	var result: Array[AudioStreamPlayer] = []
	for child: Node in node.find_children("*", "AudioStreamPlayer", true, false):
		if child is AudioStreamPlayer:
			result.append(child as AudioStreamPlayer)
	return result


func _run() -> void:
	var fighter_dir := "res://generated/fighters/sakura"
	var fighter_timeline: Dictionary = JSON.parse_string(
		FileAccess.get_file_as_string(fighter_dir + "/timeline.json"))
	var fighter: FighterRuntime = FighterRuntime.new()
	fighter.fighter_directory = fighter_dir
	fighter.autoplay = false
	fighter.play_timeline_sounds = true
	root.add_child(fighter)
	await process_frame
	var observations: Array[Dictionary] = []
	for item: Dictionary in FIGHTER_CASES:
		var expected: Array = item["sound_ids"]
		var source_ids := source_sound_ids(fighter_timeline, int(item["frame"]))
		check(source_ids == expected,
			"Source timeline sound tags differ at frame %d: %s" % [item["frame"], source_ids])
		fighter.play_source_frame(int(item["frame"]))
		var runtime_ids: Array = fighter.last_sound_ids.duplicate()
		var players := audio_players(fighter)
		var playing := players.filter(func(player: AudioStreamPlayer) -> bool:
			return player.playing and player.stream != null)
		check(runtime_ids == expected,
			"Sakura runtime StartSound mismatch at frame %d: %s" % [item["frame"], runtime_ids])
		check(not playing.is_empty(),
			"Sakura frame %d did not start an AudioStreamPlayer" % item["frame"])
		observations.append({
			"label": item["label"],
			"source_frame": item["frame"],
			"source_sound_ids": source_ids,
			"runtime_sound_ids": runtime_ids,
			"playing_streams": playing.size()
		})

	var helper_dir := "res://generated/helpers/jinye"
	var helper_timeline: Dictionary = JSON.parse_string(
		FileAccess.get_file_as_string(helper_dir + "/timeline.json"))
	var helper: HelperRuntime = HelperRuntime.new()
	helper.helper_directory = helper_dir
	helper.fighter_directory = helper_dir
	helper.play_timeline_sounds = true
	root.add_child(helper)
	await process_frame
	helper.activate({"x": 300.0, "y": -25.0, "facing": 1, "start_frame": 2}, fighter)
	while helper.current_source_frame() < 38:
		helper.advance_timeline()
	var helper_source_ids := source_sound_ids(helper_timeline, 38)
	var helper_runtime_ids: Array = helper.last_sound_ids.duplicate()
	var helper_playing := audio_players(helper).filter(func(player: AudioStreamPlayer) -> bool:
		return player.playing and player.stream != null)
	check(helper_source_ids == [49, 50], "Jinye frame 38 source sound tags changed")
	check(helper_runtime_ids == helper_source_ids,
		"Jinye runtime StartSound mismatch: %s" % [helper_runtime_ids])
	check(not helper_playing.is_empty(), "Jinye frame 38 did not start audio streams")
	var trace := {
		"format": "sakura-audiovisual-probe-v1",
		"fighter_source_swf_sha256": fighter_timeline.get("source_swf", {}).get("sha256", ""),
		"helper_source_swf_sha256": helper_timeline.get("source_swf", {}).get("sha256", ""),
		"fighter_cases": observations,
		"helper_case": {
			"helper_id": "jinye",
			"source_frame": 38,
			"source_sound_ids": helper_source_ids,
			"runtime_sound_ids": helper_runtime_ids,
			"playing_streams": helper_playing.size()
		}
	}
	DirAccess.make_dir_recursive_absolute(OUTPUT.get_base_dir())
	var file := FileAccess.open(OUTPUT, FileAccess.WRITE)
	check(file != null, "Failed to create audio trace")
	if file != null:
		file.store_string(JSON.stringify(trace, "  "))
		file.close()
	for player: AudioStreamPlayer in audio_players(root):
		player.stop()
	fighter.queue_free()
	helper.queue_free()
	await process_frame
	print("SAKURA_AUDIOVISUAL_PROBE_OK " + JSON.stringify(trace) if not failed else "SAKURA_AUDIOVISUAL_PROBE_FAILED")
	quit(1 if failed else 0)
