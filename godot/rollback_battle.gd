extends RefCounted

# Battle adapter for rollback_session. Timer/control deliveries are an immutable
# external journal: replay delivers the same event at the same source phase.
const State = preload("res://simulation_state.gd")
const Inputs = preload("res://rollback_session.gd")
const Checkpoint = preload("res://battle_checkpoint.gd")
var checkpoint := Checkpoint.new()
var game: Node
var _players := {}
var _skip := false
var _journal := {}
var _clock_journal := {}
var _intro_skip_journal := {}
var _event_supplier: Callable
var _confirmed := 0
var _terminal_frame := -1
var _input_enabled := false
var _unhandled_enabled := false
var _advancing := false
var _retain_checkpoints := true

func configure(scene: Node, retain_checkpoints: bool = true) -> String:
	if game != null or scene.physics_tick != 0 or scene.session.root_label != "游戏场景" or scene.session.p1cpu or scene.session.p2cpu:
		return "Rollback requires a fresh PvP battle"
	if scene.is_physics_processing() or not scene.ko_recorded_timers or not scene.recorded_training_timers:
		return "Rollback requires external stepping and timer delivery"
	if not scene.battle_intro.recorded_polling or not scene.source_clock.validate_state(scene.source_clock.save_state()).is_empty():
		return "Rollback requires an explicit clock and intro delivery"
	if scene.match_input.playback or scene.match_input.recording or scene.match_input.source.is_valid() or scene.match_input.intro_source.is_valid():
		return "Another input producer already owns the battle"
	for driver in [scene.player_body_driver._driver, scene.opponent_driver]:
		if driver.timeouts.pending_count() != 0:
			return "Cannot adopt live BODY timeout registrations"
	if scene.source_root_intervals != null and scene.source_root_intervals.pending_count() != 0:
		return "Cannot adopt live root interval registrations"
	scene.recorded_form_timers = true
	if scene.source_root_intervals != null:
		scene.source_root_intervals.recorded = true
	for driver in [scene.player_body_driver._driver, scene.opponent_driver]:
		driver.timeouts.recorded = true
	game = scene
	_input_enabled = game.is_processing_input()
	_unhandled_enabled = game.is_processing_unhandled_input()
	game.set_process_input(false)
	game.set_process_unhandled_input(false)
	game.match_input.source = _sample
	game.match_input.intro_source = _sample_intro
	game.set_meta("rollback_terminal_barrier", true)
	_retain_checkpoints = retain_checkpoints
	if _retain_checkpoints: checkpoint.configure(game)
	return ""

func set_frame_events(frame: int, time_ms: int, skip: bool = false, events: Array = []) -> String:
	if frame <= game.physics_tick or time_ms < 0:
		return "Cannot replace an already simulated frame envelope"
	var value := {"time_ms": time_ms, "skip": skip, "events": events.duplicate(true)}
	if _journal.has(frame):
		return "" if _journal[frame] == value else "Conflicting immutable frame envelope"
	for event in events:
		if not event is Dictionary or event.get("kind", "") not in ["intro_poll", "nextfight", "countdown", "body_timeout", "root_interval"]:
			return "Invalid battle callback envelope"
		var phase := "before_root_observer" if event.kind == "nextfight" else "after_actor_advance"
		if event.get("phase") != phase: return "Invalid battle callback phase"
		if event.kind == "intro_poll" and (not event.get("sequence") is int or not event.get("time_ms") is int):
			return "Invalid intro callback coordinates"
		if event.kind == "body_timeout" and (event.get("slot") not in ["p1", "p2"] or not event.get("id") is int or event.id <= 0):
			return "Invalid BODY timeout reference"
		if event.kind == "root_interval" and (not event.get("id") is int or event.id <= 0):
			return "Invalid root interval reference"
	_journal[frame] = value
	return ""


func set_event_supplier(supplier: Callable) -> String:
	if not supplier.is_valid():
		return "Online event supplier must be valid"
	_event_supplier = supplier
	return ""


func set_frame_clock(frame: int, elapsed_ms: int) -> String:
	if game == null or frame <= game.physics_tick or elapsed_ms < 0:
		return "Cannot replace an already simulated frame clock"
	if not _event_supplier.is_valid():
		return "Online frame clock requires an event supplier"
	if _clock_journal.has(frame):
		return "" if int(_clock_journal[frame]) == elapsed_ms else "Conflicting immutable frame clock"
	_clock_journal[frame] = elapsed_ms
	return ""


func set_intro_skip(frame: int) -> String:
	if game == null or frame <= game.physics_tick:
		return "Cannot add an intro-skip event to an already simulated frame"
	_intro_skip_journal[frame] = true
	return ""

func advance(frame: int, players: Dictionary) -> String:
	if game.ko_terminal_pending:
		return "match_finished" if _confirmed >= _terminal_frame else "waiting_for_confirmation"
	var online_clock := _clock_journal.has(frame)
	if frame != game.physics_tick + 1 or (not online_clock and not _journal.has(frame)):
		return "Missing contiguous battle frame envelope"
	for slot in ["p1", "p2"]:
		if not players.get(slot) is Dictionary or not Inputs.validate_input(players[slot]).is_empty():
			return "Invalid battle inputs"
	var elapsed_ms: int = int(_clock_journal[frame]) if online_clock else int(_journal[frame].time_ms)
	if not game.source_clock.set_explicit_time(elapsed_ms):
		return "Non-monotonic simulation time"
	_players = players.duplicate(true)
	_skip = bool(_intro_skip_journal.has(frame)) if online_clock else bool(_journal[frame].skip)
	_advancing = true
	game.pause_menu.tick()
	if online_clock:
		game._advance_fight([], Callable(), _event_supplier)
	else:
		game._advance_fight(_journal[frame].events)
	_advancing = false
	if game.ko_terminal_pending: _terminal_frame = frame
	if not _retain_checkpoints:
		_journal.clear()
		_clock_journal.clear()
		_intro_skip_journal.clear()
		confirm_through(frame)
	return game.match_input.error if not game.match_input.error.is_empty() else ("" if game.physics_tick == frame else "Battle did not advance")

func save_state() -> Dictionary:
	if _advancing: return {"error": "Checkpoint requested during battle advancement"}
	var battle := checkpoint.save_state()
	if battle.has("error"): return battle
	return State.pack_state("rollback-battle-v1", game.physics_tick,
		{"battle": battle, "terminal_frame": _terminal_frame})

func validate_state(snapshot: Dictionary) -> String:
	var problem := State.validate_snapshot(snapshot, "rollback-battle-v1", ["battle", "terminal_frame"])
	if not problem.is_empty(): return problem
	if not snapshot.owners.battle is Dictionary:
		return "Missing battle checkpoint"
	problem = checkpoint.validate_state(snapshot.owners.battle)
	if not problem.is_empty(): return problem
	if snapshot.frame != snapshot.owners.battle.frame or not snapshot.owners.terminal_frame is int or snapshot.owners.terminal_frame < -1 or snapshot.owners.terminal_frame > snapshot.frame:
		return "Invalid battle frame boundary"
	return ""

func load_state(snapshot: Dictionary) -> String:
	if _advancing: return "Cannot restore during battle advancement"
	var problem := validate_state(snapshot)
	if not problem.is_empty(): return problem
	problem = checkpoint.load_state(snapshot.owners.battle)
	if problem.is_empty(): _terminal_frame = snapshot.owners.terminal_frame
	return problem


func profile_counters() -> Dictionary:
	return {
		"rebuild_count": int(checkpoint.profile.get("rebuild_count", 0)),
		"rebuild_us": int(checkpoint.profile.get("rebuild_us", 0)),
	}


func begin_replay() -> void:
	checkpoint.replaying = true
	game.diagnostics.replaying = true


func end_replay() -> void:
	checkpoint.replaying = false
	game.diagnostics.replaying = false
	checkpoint.flush_displays()

func confirm_through(frame: int) -> void:
	_confirmed = maxi(_confirmed, frame)

func retain_states(states: Array) -> void:
	var battles := []
	for state in states: battles.append(state.owners.battle)
	checkpoint.retain_states(battles)
	var oldest: int = states[0].frame
	for state in states: oldest = mini(oldest, state.frame)
	for frame in _journal.keys():
		if frame <= oldest: _journal.erase(frame)
	for frame in _clock_journal.keys():
		if frame <= oldest: _clock_journal.erase(frame)
	for frame in _intro_skip_journal.keys():
		if frame <= oldest: _intro_skip_journal.erase(frame)

func close() -> void:
	checkpoint.replaying = false
	if game == null: return
	game.diagnostics.replaying = false
	game.set_process_input(_input_enabled)
	game.set_process_unhandled_input(_unhandled_enabled)
	game.match_input.source = Callable()
	game.match_input.intro_source = Callable()
	game.remove_meta("rollback_terminal_barrier")
	if _retain_checkpoints: checkpoint.close()
	_journal.clear()
	_clock_journal.clear()
	_intro_skip_journal.clear()
	_event_supplier = Callable()
	game = null

func _sample(slot: String, _frame: int) -> Dictionary:
	return _players[slot].duplicate()

func _sample_intro(_frame: int) -> bool:
	return _skip

func commit_result() -> String:
	if not game.ko_terminal_pending or _terminal_frame < 0 or _confirmed < _terminal_frame:
		return "Result is not confirmed"
	var scene := game
	close()
	scene._ko_return_to_fixed_selection()
	return ""
