class_name StageSound
extends Node

# Source: scripts/main.json :: DefineSprite_1900/frame_1/DoAction.as loadSound()
# picks the file with up to two Math.random() draws, then
# scripts/main.json :: frame_8/DoAction.as startGame() runs
# stageSound.start(0,999) followed by setVolume(80).
#
# The pick order, thresholds and playback numbers are compiled into
# generated/music/music.json by tools/importer/materialize_stage_music.py.
# This node only interprets them, so a different p2selt / curStage changes
# the manifest instead of this script.

const MUSIC_DIRECTORY := "res://generated/music"
# Flash Sound.setVolume takes a 0..100 percentage of amplitude.
const FLASH_VOLUME_MAX := 100.0

# Replay order for Math.random(). Draws fall back to rng once it runs out.
var random_tape: Array[float] = []
var rng := RandomNumberGenerator.new()
var random_source: SourceRandom
# Every draw in source order, so a run can be compared against a tape.
var draws: Array[float] = []
var selected_file: String = ""
var selected_source: String = ""

var _manifest: Dictionary = {}
var music_directory: String = MUSIC_DIRECTORY
var _player: AudioStreamPlayer


func _ready() -> void:
	if _manifest.is_empty():
		load_manifest()


func load_manifest(path: String = MUSIC_DIRECTORY + "/music.json") -> bool:
	music_directory = path.get_base_dir()
	var parsed: Variant = JSON.parse_string(FileAccess.get_file_as_string(path))
	if not parsed is Dictionary or not parsed.has("selection"):
		push_error("Missing compiled stage music manifest: %s" % path)
		return false
	_manifest = parsed
	return true


func select(steps: Array = _manifest.get("selection", {}).get("steps", [])) -> String:
	# loadSound(): the fighter step is skipped entirely when the catalog entry
	# has no music, so that case draws no random at all.
	draws.clear()
	selected_file = ""
	selected_source = ""
	for step: Dictionary in steps:
		if not step.has("random_below"):
			selected_file = str(step.get("file", ""))
			selected_source = str(step.get("source", ""))
			break
		var draw := _next_random(str(step["random_site"]))
		if is_nan(draw):
			return ""
		draws.append(draw)
		if draw < float(step["random_below"]):
			selected_file = str(step.get("file", ""))
			selected_source = str(step.get("source", ""))
			break
	return selected_file


func start() -> void:
	# startGame() calls start(0,999) before setVolume(80); the volume applies
	# to the same Sound object either way.
	if selected_file == "":
		select()
	if selected_file == "":
		push_error("loadSound found no music file")
		return
	var stream: AudioStream = load("%s/%s" % [music_directory, selected_file])
	if stream == null:
		push_error("Stage music not materialized: %s" % selected_file)
		return
	# start(0, 999) restarts on its own for 999 repetitions. A match never
	# reaches the 999th, so the stream loops instead of counting repetitions.
	if stream is AudioStreamMP3:
		stream.loop = true
	if _player == null:
		_player = AudioStreamPlayer.new()
		add_child(_player)
	_player.stream = stream
	_player.volume_db = volume_db()
	var offset := float(_manifest.get("playback", {}).get("start_offset_seconds", 0))
	_player.play(offset)
	preload("res://authority_audio.gd").accepted(self, _player, offset)


func stop() -> void:
	# Source DefineSprite_1989/frame_2/DoAction.as: stopAllSounds() then
	# _root.stageSound.stop(). Only the stage sound belongs to this node.
	if _player != null:
		_player.stop()


func playing() -> bool:
	return _player != null and _player.playing


func volume_db() -> float:
	var percent := float(_manifest.get("playback", {}).get("volume_percent", FLASH_VOLUME_MAX))
	if percent <= 0.0:
		return -80.0
	return linear_to_db(percent / FLASH_VOLUME_MAX)


func _next_random(site: String) -> float:
	if random_tape.is_empty() and random_source != null:
		return random_source.next_value(site)
	if random_tape.is_empty():
		return rng.randf()
	return random_tape.pop_front()
