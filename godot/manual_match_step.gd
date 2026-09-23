extends RefCounted

# Developer boundary for already configured, externally clocked PvP scenes.
# It delegates the existing phase order; it neither invents timer deadlines nor
# promises that Main's object graph can yet be restored.
const Inputs := preload("res://rollback_test_session.gd")
var _game: Node
var _players := {}
var _skip := false


func configure(game: Node) -> String:
	if _game != null:
		return "Manual step already configured"
	var problem := _check_scene(game)
	if not problem.is_empty():
		return problem
	if game.match_input.source.is_valid() or game.match_input.intro_source.is_valid():
		return "Input producer already installed"
	_game = game
	_game.match_input.source = _sample
	_game.match_input.intro_source = _sample_skip
	return ""


func advance(frame: int, players: Dictionary, skip_intro: bool, callbacks: Array = []) -> String:
	if not is_instance_valid(_game):
		return "Manual match not configured"
	var problem := _check_scene(_game)
	if not problem.is_empty():
		return problem
	if _game.match_input.source != _sample or _game.match_input.intro_source != _sample_skip:
		return "Manual input producer was replaced"
	if frame != _game.physics_tick + 1 or players.size() != 2:
		return "Non-contiguous frame or missing players"
	for slot in ["p1", "p2"]:
		if not players.get(slot) is Dictionary:
			return "Missing player slot"
		problem = Inputs.validate_input(players[slot])
		if not problem.is_empty():
			return problem
	# Only the existing measured intro callback path is exposed here. Countdown,
	# KO and user controls need their own phase/eligibility contract before use.
	var sequence: int = _game.battle_intro.last_poll_sequence
	var time_ms: int = _game.battle_intro.last_poll_time_ms
	for event in callbacks:
		if not event is Dictionary or event.get("kind") != "intro_poll" or event.get("phase") != "after_actor_advance":
			return "Unsupported manual callback"
		if not event.get("sequence") is int or not event.get("time_ms") is int:
			return "Invalid intro callback"
		if event.sequence <= sequence or event.time_ms < time_ms:
			return "Non-monotonic intro callback"
		if not _game.battle_intro.polling or not _game.battle_intro.active:
			return "Intro callback has no active interval"
		sequence = event.sequence
		time_ms = event.time_ms
	if callbacks.size() > 1:
		return "Multiple intro callbacks require phase-specific validation"
	if not callbacks.is_empty() and skip_intro and _game.battle_intro.step > 1 and _game.battle_intro.step < 4:
		return "Skip cancels this intro interval before callback delivery"
	_players = players.duplicate(true)
	_skip = skip_intro
	_game.pause_menu.tick()
	_game._advance_fight(callbacks.duplicate(true))
	if not _game.match_input.error.is_empty():
		return _game.match_input.error
	return "" if _game.physics_tick == frame else "Battle did not complete the requested frame"


func detach() -> void:
	if is_instance_valid(_game):
		if _game.match_input.source == _sample:
			_game.match_input.source = Callable()
		if _game.match_input.intro_source == _sample_skip:
			_game.match_input.intro_source = Callable()
	_game = null


func _sample(slot: String, _frame: int) -> Dictionary:
	return _players[slot].duplicate()


func _sample_skip(_frame: int) -> bool:
	return _skip


func _check_scene(game: Node) -> String:
	if game.session.root_label != "游戏场景" or game.session.p1cpu or game.session.p2cpu:
		return "Manual stepping requires an initialized PvP match"
	if game.is_physics_processing() or game.match_input.playback or game.match_input.recording:
		return "Automatic stepping or input recording/playback is active"
	if not game.battle_intro.recorded_polling or not game.ko_recorded_timers or not game.recorded_training_timers:
		return "Battle timer delivery is not externally controlled"
	if not game.source_clock.validate_state(game.source_clock.save_state()).is_empty():
		return "Battle clock is live"
	if not game.source_random.failure.is_empty() or not game.source_clock.failure.is_empty():
		return "Random or clock stream has failed"
	if game.ko_active or game.ko_terminal_pending or game.nextfight_from_timeout:
		return "Round transition is not supported by this manual adapter"
	for timer in game.find_children("*", "Timer", true, false):
		# IntroClip's SOUNDINFO out-point timer only frees its audio player.
		# This is presentation, not a source gameplay interval.
		var player: Node = timer.get_parent()
		if player is AudioStreamPlayer and player.get_parent().get_parent() is IntroClip:
			var connections: Array = timer.timeout.get_connections()
			if connections.size() == 1 and connections[0].callable == Callable(player, "queue_free"):
				continue
		if not timer.is_stopped():
			return "Live timer in manual match: " + str(timer.get_path())
	return ""
