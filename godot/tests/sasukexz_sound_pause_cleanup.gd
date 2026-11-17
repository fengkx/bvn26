extends SceneTree

const Fixture = preload("res://tests/rollback_fixture.gd")
const Inputs = preload("res://rollback_test_session.gd")
var voice: AudioStreamPlayer
var starts := 0


func _initialize() -> void:
	_run.call_deferred()


func _sound_added(node: Node) -> void:
	if node is AudioStreamPlayer and node.stream.resource_path.ends_with("331-d389ac68a4fff187.wav"):
		voice = node
		starts += 1


func _run() -> void:
	var fixture := Fixture.create(self, ["佐助须佐", "一护"], ["我爱罗", "魂"], "现世")
	var game: Node = fixture.game
	var battle: RefCounted = fixture.battle
	game.naruto.energy = 300
	game.naruto.position.x = 300
	game.ichigo.position.x = 350
	game.naruto._sound_layer().child_entered_tree.connect(_sound_added)
	var attack_start := -1
	var reached_frame := 0
	for frame in range(1, 901):
		if not game.battle_intro.active and attack_start < 0:
			attack_start = frame
		var players := {"p1": {}, "p2": {}}
		for slot in players:
			for button in Inputs.BUTTONS:
				players[slot][button] = false
		players.p1.special = attack_start > 0 and frame <= attack_start + 3
		var callbacks := []
		if game.battle_intro.polling and frame % 15 == 0:
			callbacks.append({"kind": "intro_poll", "phase": "after_actor_advance", "sequence": frame, "time_ms": frame * 33})
		assert(battle.set_frame_events(frame, frame * 33, false, callbacks).is_empty())
		assert(battle.advance(frame, players).is_empty())
		if is_instance_valid(voice):
			reached_frame = game.naruto.current_source_frame()
			break
		if frame % 60 == 0:
			await process_frame
	assert(is_instance_valid(voice) and starts == 1)
	assert(reached_frame == 776)
	assert(voice.playing and not voice.stream_paused)
	var before_playing: bool = game.naruto.timeline_playing
	var stop_allowed: bool = game.naruto.hited == 0 and game.naruto.bs == 0 and game.naruto.sw == false
	var pause_inputs := {"hited": game.naruto.hited, "bs": game.naruto.bs, "sw": game.naruto.sw}
	game._pause_battle()
	assert(game.super_runtime.game_paused)
	assert(game.naruto.timeline_playing == (false if stop_allowed else before_playing))
	# Source pauseGame2 stops MovieClips, not existing event-sound streams.
	assert(voice.playing and not voice.stream_paused)
	await create_timer(0.15).timeout
	assert(is_instance_valid(voice) and voice.playing and not voice.stream_paused)
	game._resume_battle()
	assert(not game.super_runtime.game_paused and game.naruto.timeline_playing)
	assert(starts == 1)
	var voice_id := voice.get_instance_id()
	Fixture.dispose(game, battle)
	await process_frame
	assert(not is_instance_id_valid(voice_id))
	var report := {"scope": "Native source-invariant diagnostic only; no original waveform or audible output acceptance", "source_frame": reached_frame, "sound_id": 331, "starts": starts, "pause_inputs": pause_inputs, "stop_mc_condition": stop_allowed, "event_sound_not_paused": true, "resume_no_restart": true, "voice_freed_with_scene": true, "audio_driver": AudioServer.get_driver_name(), "native_parity_proven": false, "production_admitted": false}
	var args := OS.get_cmdline_user_args()
	assert(args.size() == 1)
	FileAccess.open(args[0], FileAccess.WRITE).store_string(JSON.stringify(report, "  ") + "\n")
	print("SASUKEXZ_SOUND_PAUSE_CLEANUP_OK ", JSON.stringify(report))
	quit()
