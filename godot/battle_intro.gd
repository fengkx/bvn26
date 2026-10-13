class_name BattleIntro
extends Node

signal interval_cleared(interval_name: String)
signal fight_started

const DIRECTORY := "res://generated/main/intro"
var spec: Dictionary
var clips: Dictionary = {}
var playing: Dictionary = {}
var fighters: Array[FighterRuntime] = []
var states: Array[int] = [0, 0]
var step: int = 0
var focus: String = "p1"
var active: bool = false
var poll_elapsed_ms: float = 0.0
var polling: bool = false
var fighters_loaded: bool = true
var recorded_polling: bool = false
var last_poll_sequence: int = -1
var last_poll_time_ms: int = -1
var poll_replay_error: String = ""
var hud_visible: bool = false
var hud_frame: int = 1
var hud_playing: bool = false
var hud_stop_frames: PackedInt32Array
var _defer_frame_actions: bool = false
var _pending_frame_actions: Array = []
var _deferred_play_advances: Dictionary = {}


func _ready() -> void:
	spec = JSON.parse_string(FileAccess.get_file_as_string(DIRECTORY + "/intro.json"))
	hud_stop_frames = PackedInt32Array(spec["hud_stop_frames"])
	for name: String in spec["clips"]:
		var clip := IntroClip.new()
		clip.fighter_directory = DIRECTORY + "/" + name
		clip.autoplay = false
		var placement: Dictionary = spec["clips"][name]["placement"]
		clip.z_index = int(placement["depth"])
		clip.transform = clip._matrix_transform(placement["matrix"], 1.0)
		add_child(clip)
		clips[name] = clip
		playing[name] = false
	cancel()


func cancel() -> void:
	_pending_frame_actions.clear()
	_deferred_play_advances.clear()
	_defer_frame_actions = false
	active = false
	hud_playing = false
	polling = false
	for name: String in clips:
		clips[name].visible = false
		playing[name] = false
		var layer: Node = clips[name].get_node_or_null("SoundLayer")
		if layer != null:
			for sound in layer.get_children():
				sound.queue_free()


func begin(players: Array[FighterRuntime], recorded: bool = false, loaded: bool = true) -> void:
	cancel()
	fighters_loaded = loaded
	recorded_polling = recorded
	last_poll_sequence = -1
	last_poll_time_ms = -1
	poll_replay_error = ""
	fighters = players
	states = [0, 0]
	step = 0
	focus = "p1"
	poll_elapsed_ms = 0.0
	polling = true
	active = true
	hud_visible = false
	hud_frame = 1
	hud_playing = false
	for fighter in fighters:
		fighter.root_zhanting = true
	for name: String in clips:
		clips[name].visible = true
	_goto("ready", 1, false)
	_goto("qjxg", int(spec["clips"]["qjxg"]["labels"]["关闭"]), false)


func _goto(name: String, frame: int, play: bool) -> void:
	_deferred_play_advances.erase(name)
	playing[name] = play
	clips[name].play_source_frame(frame)
	if _defer_frame_actions:
		_pending_frame_actions.append([name, frame])
	else:
		_apply_event(name, frame)


func set_clip_playing(name: String, play: bool, defer_first_advance: bool = false) -> void:
	playing[name] = play
	_deferred_play_advances.erase(name)
	if play and defer_first_advance:
		# An external interval resumes the stopped clip after that display's
		# timeline advance. Its first new frame belongs to the next display.
		_deferred_play_advances[name] = true


func tick(delta: float, skip: bool = false, defer_frame_actions: bool = false) -> void:
	assert(_pending_frame_actions.is_empty(), "Undrained intro frame actions")
	_defer_frame_actions = defer_frame_actions
	# setInterval(kaichang, 500) belongs to elapsed time, not a guessed
	# character duration. At the fixed 30 Hz step its normal cadence is 15 ticks.
	if hud_playing:
		hud_frame = hud_frame % int(spec["hud_frame_count"]) + 1
		if hud_frame in hud_stop_frames:
			hud_playing = false
	for name: String in clips:
		if playing[name]:
			if _deferred_play_advances.erase(name):
				continue
			var next: int = clips[name].current_source_frame() + 1
			if next > int(spec["clips"][name]["frame_count"]):
				next = 1
			_goto(name, next, true)
	if not active:
		return
	if skip and step > 1 and step < 4:
		polling = false
		step = 4
		_goto("ready", 1, false)
		_goto("qjxg", int(spec["clips"]["qjxg"]["labels"]["skipintro"]), true)
	if polling and not recorded_polling:
		poll_elapsed_ms += delta * 1000.0
		while polling and poll_elapsed_ms + 0.00001 >= float(spec["poll_ms"]):
			poll_elapsed_ms -= float(spec["poll_ms"])
			_poll()


func run_frame_actions() -> void:
	_defer_frame_actions = false
	while not _pending_frame_actions.is_empty():
		var event: Array = _pending_frame_actions.pop_front()
		_apply_event(str(event[0]), int(event[1]))


func deliver_recorded_poll(sequence: int, time_ms: int) -> bool:
	# The replay host owns the callback phase. A display tick must not create
	# another poll, or quantize the recorded 15/16-frame intervals to 15.
	if not recorded_polling or not active or not polling or poll_replay_error != "":
		return false
	if sequence <= last_poll_sequence or time_ms < last_poll_time_ms:
		poll_replay_error = "Non-monotonic intro poll event"
		return false
	last_poll_sequence = sequence
	last_poll_time_ms = time_ms
	_poll()
	return true


func observe_fighter_frames() -> void:
	# Sample before FighterRuntime applies the same frame's goto back to stand.
	for i in fighters.size():
		var fighter := fighters[i]
		var name := fighter.fighter_directory.get_file()
		var frames: Dictionary = spec["fighters"][name]["state_frames"]
		var key := str(fighter.current_source_frame())
		if frames.has(key):
			states[i] = int(frames[key])


func _poll() -> void:
	# Source kaichang returns before reading either kcplayed while p2loaded=false.
	if not fighters_loaded:
		return
	match step:
		0:
			if states == [0, 0]:
				_go_step(1)
		1:
			if states[0] == 0:
				_go_step(2)
		2:
			if states[0] == 2:
				if states[1] == 0:
					_go_step(3)
			elif fighters[0].current_source_frame() < 10:
				_go_step(2)
		3:
			if states[1] == 2:
				_go_step(4)
			elif fighters[1].current_source_frame() < 10:
				_go_step(3)


func _go_step(value: int) -> void:
	step = value
	match step:
		1:
			_goto("qjxg", int(spec["clips"]["qjxg"]["labels"]["开"]), true)
		2, 3:
			focus = "p%d" % (step - 1)
			fighters[step - 2].start_action("开场")
		4:
			focus = "all"
			polling = false
			# goStep(4) calls ready.play(); frame 2 executes on the next advance.
			playing["ready"] = true


func _apply_event(name: String, frame: int) -> void:
	var event: Dictionary = spec["clips"][name]["events"].get(str(frame), {})
	for interval_name: String in event.get("clear_intervals", []):
		interval_cleared.emit(interval_name)
	if bool(event.get("stop", false)):
		playing[name] = false
	if bool(event.get("fade_hud", false)):
		goto_hud("in")
	if bool(event.get("reset_fighters", false)):
		focus = "all"
		for fighter in fighters:
			fighter.start_action("站立")
	if bool(event.get("start_fight", false)):
		active = false
		for fighter in fighters:
			fighter.root_zhanting = false
		fight_started.emit()
	if bool(event.get("rewind", false)):
		clips[name].play_source_frame(1)


func goto_hud(label: String) -> void:
	hud_visible = true
	hud_frame = int(spec["hud_labels"][label])
	hud_playing = hud_frame not in hud_stop_frames
