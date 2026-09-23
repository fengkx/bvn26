extends RefCounted
class_name OnlineMatchCoordinator

signal started
signal recovery_changed(state: String)
signal pause_changed(paused: bool)
signal pause_requested(request: Dictionary)
signal resume_requested(request: Dictionary)
signal result_confirmed(result: Dictionary)
signal room_result_committed(result: Dictionary)
signal diagnostic_abort(report: Dictionary)
signal room_match_aborted(report: Dictionary)
signal page_visibility_changed(visible: bool)

const State = preload("res://simulation_state.gd")
const Battle = preload("res://rollback_battle.gd")
const Rollback = preload("res://rollback_session.gd")
const TimerAuthority = preload("res://online_timer_authority.gd")
const HASH_INTERVAL := 30
const RECOVERY_MS := 10_000
const MAX_HASH_HISTORY := 256
const HEARTBEAT_INTERVAL_MS := 1_000
const HEARTBEAT_TIMEOUT_MS := 5_000
const CONTROL_FRAME_LEAD := 2
const STARTUP_CANCEL_TIMEOUT_MS := 20_000
const NO_WINNER_TERMINAL_REASONS := ["aborted", "result_mismatch", "participant_left", "start_timeout", "initial_state_mismatch"]
const PERMANENT_ROOM_ERRORS := ["room_closed", "room_expired", "room_not_found", "not_in_room", "membership_ended", "unauthorized"]

var game: Node
var room_client: Object
var peer_transport: Object
var local_slot := ""
var remote_slot := ""
var setup: Dictionary = {}
var epoch := ""
var profile: Dictionary = {}
var clock_authority_slot := "p1"
var battle: RefCounted
var rollback: RefCounted
var timers: RefCounted
var error := ""
var running := false
var recovering := false
var paused := false
var page_visible := true
var _configured := false
var _startup_context_eligible := false
var _startup_hidden_seen := false
var _startup_active := false
var _startup_cancel_requested := false
var _startup_cancel_in_progress := false
var _startup_cancel_cleanup_complete := false
var _startup_cancel_abort_submitted := false
var _startup_cancel_abort_accepted := false
var _peer_ready := false
var _clock_origin_ms := -1
var _clock_paused_total_ms := 0
var _pause_started_ms := -1
var _process_now_ms := -1
var _disconnect_started_ms := -1
var _clock_samples := {}
var _intro_skip_frames := {}
var _local_inputs := {}
var _local_hashes := {}
var _remote_hashes := {}
var _local_results := {}
var _remote_result: Dictionary = {}
var _received_sequences := {}
var _next_hash_frame := HASH_INTERVAL
var _control_counter := 0
var _pause_state: Dictionary = {}
var _resume_state: Dictionary = {}
var _room_command_in_flight := false
var _room_service_available := true
var _room_state: Dictionary = {}
var _generation := 0
var _sampled_frontier := -1
var _sampled_held: Dictionary = {}
var _peer_channel_open := false
var _peer_configured := false
var _last_heartbeat_sent_ms := -1
var _last_heartbeat_received_ms := -1
var _recovery_sync_sent_ms := -1
var _recovery_counter := 0
var _recovery_id := ""
var _last_completed_recovery_id := ""
var _last_completed_recovery_counter := 0
var _recovery_sync_reply_sent := false
var _recovery_started_ms := -1
var _result_submission_started := false
var _result_submission_complete := false
var _abort_submission_started := false
var _recovery_state: Dictionary = {}
var _pending_signals := {}
var _pending_peer_messages: Array[Dictionary] = []
var _signal_retry_queue: Array[Dictionary] = []
var _early_signals: Array[Dictionary] = []
var _signal_error := ""
var _startup_pending_messages: Array[Dictionary] = []
var _signaling_reconnect_active := false


func configure(scene: Node, room_setup: Dictionary, player_slot: String, room: Object, transport: Object) -> String:
	if _configured:
		return "Online match is already configured"
	if player_slot not in ["p1", "p2"] or room == null or transport == null:
		return "Online match dependencies or player slot are invalid"
	var normalized_setup := _normalize_setup(room_setup)
	if normalized_setup.is_empty() or not _valid_setup(normalized_setup):
		return "Online room setup is incomplete"
	if scene == null or scene.session.root_label != "游戏场景" or scene.session.p1cpu or scene.session.p2cpu:
		return "Online match requires a configured human-vs-human battle"
	if scene.physics_tick != 0 or scene.is_physics_processing():
		return "Online match must configure before its first battle tick"
	game = scene
	setup = State.canonical(normalized_setup)
	local_slot = player_slot
	remote_slot = "p2" if player_slot == "p1" else "p1"
	room_client = room
	peer_transport = transport
	battle = Battle.new()
	var problem: String = battle.configure(game)
	if not problem.is_empty():
		battle = null
		return problem
	timers = TimerAuthority.new()
	problem = timers.configure(game, 0)
	if not problem.is_empty():
		battle.close()
		battle = null
		timers = null
		return problem
	problem = battle.set_event_supplier(Callable(timers, "events_for_phase"))
	if not problem.is_empty():
		battle.close()
		battle = null
		timers = null
		return problem
	_configured = true
	_connect_dependencies()
	return ""


func start(match_epoch: String, agreed_profile: Dictionary, authority_slot: String = "p1") -> String:
	if not _configured or running or _startup_active or not _valid_epoch(match_epoch):
		return "Online match cannot start in its current state"
	var normalized_profile := _normalize_profile(agreed_profile)
	if authority_slot != "p1" or normalized_profile.is_empty() or normalized_profile != setup.get("profile", {}):
		return "Unsupported online authority/profile"
	_startup_active = true
	_startup_cancel_requested = false
	_startup_cancel_in_progress = false
	_startup_cancel_cleanup_complete = false
	_startup_cancel_abort_submitted = false
	_startup_cancel_abort_accepted = false
	var startup_generation := _generation
	var result := await _run_startup(match_epoch, normalized_profile, authority_slot, startup_generation)
	_startup_active = false
	_startup_context_eligible = false
	return result


func _run_startup(match_epoch: String, normalized_profile: Dictionary, authority_slot: String, startup_generation: int) -> String:
	epoch = match_epoch
	profile = normalized_profile
	clock_authority_slot = authority_slot
	_startup_context_eligible = true
	_startup_hidden_seen = not page_visible
	page_visibility_changed.emit(page_visible)
	_clock_origin_ms = -1
	var service_state: Dictionary = await _refresh_room_state()
	if _startup_cancelled(startup_generation): return "Online match closed during startup"
	if service_state.has("error"):
		return await _abort_start_for_generation(startup_generation, "room_state", service_state)
	var service_match: Dictionary = service_state.get("match", {}) if service_state.get("match") is Dictionary else {}
	var service_profile := _normalize_profile(service_match.get("profile"))
	if service_match.get("epoch") != epoch or service_profile.is_empty() or service_profile != profile:
		return await _abort_start_for_generation(startup_generation, "profile_barrier", {"error": "Room epoch/profile differs from the local setup"})
	var snapshot := save_state()
	if snapshot.has("error"):
		return snapshot.error
	var initial_hash := _start_hash(snapshot)
	var reply: Dictionary = await _room_command({"type": "loaded", "epoch": epoch, "initialHash": initial_hash})
	if _startup_cancelled(startup_generation): return "Online match closed during startup"
	if not _command_accepted(reply):
		return await _abort_start_for_generation(startup_generation, "loaded", reply)
	var problem := await _wait_for_loaded_barrier(initial_hash, startup_generation)
	if _startup_cancelled(startup_generation): return "Online match closed during startup"
	if not problem.is_empty():
		problem = _startup_timeout_context(problem)
		return await _abort_start_for_generation(startup_generation, "loaded_barrier", {"error": problem})
	reply = await _room_command({"type": "start_ack", "epoch": epoch})
	if _startup_cancelled(startup_generation): return "Online match closed during startup"
	if not _command_accepted(reply):
		return await _abort_start_for_generation(startup_generation, "start_ack", reply)
	problem = await _wait_for_active_barrier(startup_generation)
	if _startup_cancelled(startup_generation): return "Online match closed during startup"
	if not problem.is_empty():
		problem = _startup_timeout_context(problem)
		return await _abort_start_for_generation(startup_generation, "active_barrier", {"error": problem})
	problem = await _open_peer_transport(startup_generation)
	if _startup_cancelled(startup_generation): return "Online match closed during startup"
	if not problem.is_empty():
		problem = _startup_timeout_context(problem)
		return await _abort_start_for_generation(startup_generation, "peer_setup", {"error": problem})
	# The game clock begins on the first actual simulation step, after loading,
	# service barriers, negotiation and channel establishment have completed.
	if _startup_cancelled(startup_generation): return "Online match closed during startup"
	timers.configure(game, 0)
	_clock_origin_ms = -1
	_clock_paused_total_ms = 0
	_clock_samples.clear()
	var match_state := Rollback.new()
	problem = match_state.configure(self, epoch, int(profile.predictionWindow), maxi(32, int(profile.predictionWindow) + int(profile.inputDelay) + 8), int(profile.inputDelay))
	if not problem.is_empty():
		return await _abort_start_for_generation(startup_generation, "rollback_setup", {"error": problem})
	rollback = match_state
	if not _send_peer("match_ready", {"epoch": epoch, "initialHash": initial_hash}):
		return await _abort_start_for_generation(startup_generation, "peer_ready_send", {"error": "reliable_channel_not_open"})
	var ready_deadline := Time.get_ticks_msec() + 30_000
	var startup_client := room_client
	while Time.get_ticks_msec() < ready_deadline:
		if _startup_cancelled(startup_generation): return "Online match closed during startup"
		if _peer_ready:
			running = true
			_startup_context_eligible = false
			_last_heartbeat_received_ms = Time.get_ticks_msec()
			_last_heartbeat_sent_ms = _last_heartbeat_received_ms
			started.emit()
			_drain_startup_messages()
			return ""
		await startup_client.get_tree().create_timer(0.1).timeout
		if _startup_cancelled(startup_generation): return "Online match closed during startup"
	return await _abort_start_for_generation(startup_generation, "peer_ready", {
		"error": _startup_timeout_context("peer start barrier timed out")})


func cancel_startup() -> String:
	if running or (not _startup_active and not _startup_cancel_requested) or _startup_cancel_cleanup_complete:
		return "Online startup is no longer cancellable"
	if _startup_cancel_in_progress:
		return "Online startup cancellation is already in progress"
	var generation := _generation
	var cancel_epoch := epoch
	var client := room_client
	if client == null or not is_instance_valid(client) or not client.has_method("get_tree"):
		return "Startup cancellation could not be confirmed: room client is unavailable"
	var tree: SceneTree = client.get_tree()
	if tree == null:
		return "Startup cancellation could not be confirmed: room client is unavailable"
	_startup_cancel_requested = true
	_startup_cancel_in_progress = true
	var deadline := Time.get_ticks_msec() + STARTUP_CANCEL_TIMEOUT_MS
	while _startup_active:
		if generation != _generation or not is_instance_valid(client):
			return _finish_startup_cancel("Startup cancellation could not be confirmed: coordinator was closed")
		if Time.get_ticks_msec() >= deadline:
			return _finish_startup_cancel("Startup request is still unresolved; cancellation is not confirmed")
		await tree.create_timer(0.05).timeout
	if generation != _generation or room_client != client or not is_instance_valid(client):
		return _finish_startup_cancel("Startup cancellation could not be confirmed: coordinator was closed")
	var pending_outcome := await _settle_cancel_pending_command(client, generation, deadline)
	if generation != _generation or room_client != client:
		return _finish_startup_cancel("Startup cancellation could not be confirmed: coordinator was closed")
	if pending_outcome.has("error"):
		return _finish_startup_cancel("Startup cancellation could not be confirmed: " + str(pending_outcome.error))
	if _startup_cancel_abort_submitted and bool(pending_outcome.get("had_pending", false)):
		if bool(pending_outcome.get("accepted", false)):
			_startup_cancel_abort_accepted = true
		else:
			_startup_cancel_abort_submitted = false
	if _startup_cancel_abort_submitted and not bool(pending_outcome.get("had_pending", false)) and not _startup_cancel_abort_accepted:
		_startup_cancel_abort_submitted = false
	var latest_state: Dictionary = await _refresh_room_state()
	if generation != _generation or room_client != client:
		return _finish_startup_cancel("Startup cancellation could not be confirmed: coordinator was closed")
	if latest_state.has("error"):
		return _finish_startup_cancel("Startup cancellation could not be confirmed: " + str(latest_state.error))
	if not _startup_state_is_live(latest_state):
		return _finish_startup_cancel("")
	if _startup_cancel_abort_accepted:
		return _finish_startup_cancel("Startup abort was accepted but the room still reports this epoch as active")
	if Time.get_ticks_msec() >= deadline:
		return _finish_startup_cancel("Startup cancellation could not be confirmed before the deadline")
	# This flag identifies an abort whose HTTP outcome is still being retried.
	# A later cancellation settles that same request before considering a new one.
	_startup_cancel_abort_submitted = true
	var reply: Dictionary = await _room_command({"type": "abort", "epoch": cancel_epoch}, deadline)
	if generation != _generation or room_client != client:
		return _finish_startup_cancel("Startup cancellation could not be confirmed: coordinator was closed")
	var reply_state: Variant = reply.get("state")
	if _command_accepted(reply):
		_startup_cancel_abort_accepted = true
		if reply_state is Dictionary and not _startup_state_is_live(reply_state):
			_room_state = reply_state.duplicate(true)
			return _finish_startup_cancel("")
	elif not bool(reply.get("uncertain", false)) and reply.get("error") != "command_outcome_uncertain":
		_startup_cancel_abort_submitted = false
	var check_state: Dictionary = {"error": "command_settlement_timeout", "uncertain": true}
	if Time.get_ticks_msec() < deadline:
		check_state = await _refresh_room_state()
		if generation != _generation or room_client != client:
			return _finish_startup_cancel("Startup cancellation could not be confirmed: coordinator was closed")
	if not check_state.has("error") and not _startup_state_is_live(check_state):
		return _finish_startup_cancel("")
	var cause := str(check_state.get("error", reply.get("error", "abort_unconfirmed")))
	return _finish_startup_cancel("Startup cancellation could not be confirmed: " + cause)


func _settle_cancel_pending_command(client: Object, generation: int, deadline_ms: int) -> Dictionary:
	if not is_instance_valid(client) or not client.has_method("has_uncertain_command"):
		return {"error": "room_client_unavailable", "uncertain": false}
	while _room_command_in_flight:
		if generation != _generation or not is_instance_valid(client):
			return {"error": "match_closed", "uncertain": false}
		if Time.get_ticks_msec() >= deadline_ms:
			return {"error": "command_settlement_timeout", "uncertain": true}
		var tree: SceneTree = client.get_tree()
		if tree == null:
			return {"error": "room_client_unavailable", "uncertain": false}
		await tree.create_timer(0.05).timeout
	if generation != _generation or not is_instance_valid(client):
		return {"error": "match_closed", "uncertain": false}
	_room_command_in_flight = true
	var had_pending := bool(client.has_uncertain_command())
	var last_reply: Dictionary = {}
	while had_pending and bool(client.has_uncertain_command()):
		if generation != _generation or not is_instance_valid(client):
			_room_command_in_flight = false
			return {"error": "match_closed", "uncertain": false}
		if Time.get_ticks_msec() >= deadline_ms:
			_room_command_in_flight = false
			return {"error": "command_settlement_timeout", "uncertain": true}
		if client.has_method("is_command_in_flight") and bool(client.is_command_in_flight()):
			var in_flight_tree: SceneTree = client.get_tree()
			if in_flight_tree == null:
				_room_command_in_flight = false
				return {"error": "room_client_unavailable", "uncertain": false}
			await in_flight_tree.create_timer(0.05).timeout
			continue
		last_reply = await client.retry_pending_command()
		if generation != _generation or not is_instance_valid(client):
			_room_command_in_flight = false
			return {"error": "match_closed", "uncertain": false}
		if _command_accepted(last_reply):
			_room_command_in_flight = false
			return {"had_pending": true, "accepted": true, "reply": last_reply}
		if last_reply.get("error") == "request_in_flight" or last_reply.get("error") == "command_outcome_uncertain" or bool(last_reply.get("uncertain", false)):
			_room_service_available = false
			var retry_tree: SceneTree = client.get_tree()
			if retry_tree == null:
				_room_command_in_flight = false
				return {"error": "room_client_unavailable", "uncertain": false}
			await retry_tree.create_timer(0.5).timeout
			continue
		if not bool(client.has_uncertain_command()):
			_room_command_in_flight = false
			return {"had_pending": true, "accepted": false, "reply": last_reply}
		_room_command_in_flight = false
		return {"error": "prior_command_unresolved", "uncertain": false}
	_room_command_in_flight = false
	return {"had_pending": had_pending, "accepted": false, "reply": last_reply}


func _finish_startup_cancel(result: String) -> String:
	_startup_cancel_in_progress = false
	if result.is_empty():
		_startup_cancel_cleanup_complete = true
	return result


func process_tick(monotonic_now_ms: int, local_held: Dictionary) -> String:
	if not _configured:
		return "Online match is not configured"
	if not running:
		return ""
	if monotonic_now_ms < _process_now_ms:
		return _abort_local("clock_regression", {"previous_ms": _process_now_ms, "now_ms": monotonic_now_ms})
	_process_now_ms = monotonic_now_ms
	_check_recovery_deadline(monotonic_now_ms)
	if not error.is_empty(): return error
	_poll_heartbeat(monotonic_now_ms)
	if recovering or paused:
		_poll_control_barriers(monotonic_now_ms)
		return ""
	var next_frame: int = rollback.frontier + 1
	if _control_frame_pending():
		var control_frame := _pending_control_frame()
		if rollback.frontier > control_frame:
			return _abort_local("control_frame_overshot", {"target": control_frame, "frontier": rollback.frontier})
		if rollback.frontier == control_frame:
			_report_control_ready()
			_poll_control_barriers(monotonic_now_ms)
			return ""
	if not _sample_local_once(local_held): return error
	if local_slot != clock_authority_slot and not _clock_samples.has(next_frame):
		_poll_control_barriers(monotonic_now_ms)
		return ""
	var previous_frontier: int = rollback.frontier
	var result: String = rollback.step()
	if not result.is_empty() and result not in ["waiting_for_input", "waiting_for_confirmation", "match_finished"]:
		return _abort_local("simulation", {"error": result, "frame": rollback.frontier + 1})
	if rollback.frontier > previous_frontier:
		_sampled_frontier = -1
		_sampled_held.clear()
		_maybe_hash_confirmed()
		_maybe_finish_result()
	_poll_control_barriers(monotonic_now_ms)
	return ""


func receive_peer_message(channel: String, type: String, payload: Dictionary, sequence: int) -> void:
	if channel != "reliable" or not payload is Dictionary or not error.is_empty():
		return
	if _received_sequences.has(sequence): return
	_received_sequences[sequence] = true
	if _received_sequences.size() > 4096:
		_received_sequences.erase(_received_sequences.keys().min())
	if not running and type not in ["match_ready", "match_abort"]:
		if _startup_pending_messages.size() >= 512:
			_abort_local("startup_message_overflow", {"type": type})
			return
		_startup_pending_messages.append({"channel": channel, "type": type, "payload": payload.duplicate(true), "sequence": sequence})
		return
	_dispatch_peer_message(channel, type, payload)


func _dispatch_peer_message(channel: String, type: String, payload: Dictionary) -> void:
	match type:
		"input_frame": _receive_input(payload)
		"clock_sample": _receive_clock_sample(payload)
		"state_hash": _receive_state_hash(payload)
		"match_ready": _receive_match_ready(payload)
		"control": _receive_control(payload)
		"result": _receive_result(payload)
		"heartbeat": _last_heartbeat_received_ms = _process_now_ms
		"recovery_sync": _receive_recovery_sync(payload)
		"recovery_compare_request": _receive_recovery_compare_request(payload)
		"recovery_compare": _receive_recovery_compare(payload)
		"recovery_commit": _receive_recovery_commit(payload)
		"match_abort": _abort_local("peer_abort", payload, false)
		_: _abort_local("peer_protocol", {"type": type})


func _drain_startup_messages() -> void:
	while running and not _startup_pending_messages.is_empty():
		var message: Dictionary = _startup_pending_messages.pop_front()
		_dispatch_peer_message(str(message.channel), str(message.type), message.payload)


func request_pause() -> String:
	return _request_control("pause")


func request_resume() -> String:
	return _request_control("resume")


func respond_pause(request_id: String, accepted: bool) -> String:
	return _respond_control("pause", request_id, accepted)


func respond_resume(request_id: String, accepted: bool) -> String:
	return _respond_control("resume", request_id, accepted)


func request_intro_skip() -> String:
	if not running or not game.battle_intro.active or not game.battle_intro.polling:
		return "Intro skip is not available now"
	if local_slot == "p1":
		return _schedule_intro_skip(maxi(rollback.frontier + CONTROL_FRAME_LEAD, rollback.confirmed + CONTROL_FRAME_LEAD))
	return "" if _send_peer("control", {"action": "intro_skip_request", "frame": rollback.frontier}) else "Could not send intro-skip request"


func close(reason: String = "") -> void:
	_generation += 1
	_room_command_in_flight = false
	running = false
	_startup_context_eligible = false
	_disconnect_dependencies()
	if peer_transport != null and peer_transport.has_method("close_peer"):
		peer_transport.close_peer()
	if battle != null:
		battle.close()
	battle = null
	rollback = null
	timers = null
	_configured = false
	_peer_channel_open = false
	_pending_peer_messages.clear()
	room_client = null
	peer_transport = null
	game = null
	if reason != "": error = reason


func save_state() -> Dictionary:
	if battle == null or timers == null:
		return {"error": "Online match has no local battle"}
	var battle_state: Dictionary = battle.save_state()
	if battle_state.has("error"): return battle_state
	var timer_state: Dictionary = timers.save_state(battle_state.frame)
	return State.pack_state("online-match-v1", battle_state.frame, {"battle": battle_state, "timers": timer_state})


func validate_state(snapshot: Dictionary) -> String:
	var problem := State.validate_snapshot(snapshot, "online-match-v1", ["battle", "timers"])
	if not problem.is_empty(): return problem
	problem = battle.validate_state(snapshot.owners.battle)
	if not problem.is_empty(): return problem
	if snapshot.frame != snapshot.owners.battle.frame:
		return "Online battle/timer frame mismatch"
	return timers.validate_state(snapshot.owners.timers, snapshot.frame)


func load_state(snapshot: Dictionary) -> String:
	var problem := validate_state(snapshot)
	if not problem.is_empty(): return problem
	problem = battle.load_state(snapshot.owners.battle)
	if not problem.is_empty(): return problem
	return timers.load_state(snapshot.owners.timers)


func advance(frame: int, players: Dictionary) -> String:
	if not _clock_samples.has(frame):
		if local_slot == clock_authority_slot:
			if _clock_origin_ms < 0:
				_clock_origin_ms = _process_now_ms
			var elapsed := maxi(0, _process_now_ms - _clock_origin_ms - _clock_paused_total_ms)
			if not _clock_samples.is_empty():
				elapsed = maxi(elapsed, int(_clock_samples[_clock_samples.keys().max()]))
			_clock_samples[frame] = elapsed
			if not _send_peer("clock_sample", {"frame": frame, "elapsed_ms": elapsed}):
				return "Could not publish authoritative clock sample"
		else:
			return "waiting_for_clock_sample"
	var elapsed_ms := int(_clock_samples[frame])
	var problem: String = timers.set_time(elapsed_ms)
	if not problem.is_empty(): return problem
	problem = battle.set_frame_clock(frame, elapsed_ms)
	if not problem.is_empty(): return problem
	if _intro_skip_frames.has(frame):
		problem = battle.set_intro_skip(frame)
		if not problem.is_empty(): return problem
	problem = battle.advance(frame, players)
	timers.finish_frame()
	if not timers.error.is_empty(): return timers.error
	return problem


func confirm_through(frame: int) -> void:
	if battle != null: battle.confirm_through(frame)


func retain_states(states: Array) -> void:
	if battle != null: battle.retain_states(states.map(func(item: Dictionary) -> Dictionary: return item.owners.battle))
	var oldest: int = int(states[0].frame) if not states.is_empty() else 0
	for frame in _clock_samples.keys():
		if frame <= oldest: _clock_samples.erase(frame)
	for frame in _local_inputs.keys():
		if frame <= oldest: _local_inputs.erase(frame)
	for frame in _intro_skip_frames.keys():
		if frame <= oldest: _intro_skip_frames.erase(frame)


func _connect_dependencies() -> void:
	var diagnostic_value: Variant = game.get("diagnostics") if game != null and is_instance_valid(game) else null
	if diagnostic_value is Object:
		var diagnostics: Object = diagnostic_value
		var visible_value: Variant = diagnostics.get("page_visible")
		page_visible = visible_value if visible_value is bool else true
		if diagnostics.has_signal("visibility_changed"):
			diagnostics.visibility_changed.connect(_on_page_visibility_changed)
	if room_client.has_signal("state_changed"):
		room_client.state_changed.connect(_on_room_state)
	if room_client.has_signal("socket_state_changed"):
		room_client.socket_state_changed.connect(_on_signaling_state)
	if room_client.has_signal("signaling_message"):
		room_client.signaling_message.connect(_on_signaling_message)
	if room_client.has_signal("error"):
		room_client.error.connect(_on_room_error)
	if peer_transport.has_signal("peer_message"):
		peer_transport.peer_message.connect(receive_peer_message)
	if peer_transport.has_signal("peer_state_changed"):
		peer_transport.peer_state_changed.connect(_on_peer_state)
	if peer_transport.has_signal("outgoing_signal"):
		peer_transport.outgoing_signal.connect(_on_outgoing_signal)
	if peer_transport.has_signal("transport_error"):
		peer_transport.transport_error.connect(_on_peer_error)


func _disconnect_dependencies() -> void:
	var diagnostic_value: Variant = game.get("diagnostics") if game != null and is_instance_valid(game) else null
	if diagnostic_value is Object:
		var diagnostics: Object = diagnostic_value
		if diagnostics.has_signal("visibility_changed") and diagnostics.is_connected("visibility_changed", _on_page_visibility_changed):
			diagnostics.disconnect("visibility_changed", _on_page_visibility_changed)
	if room_client != null:
		for pair in [["state_changed", _on_room_state], ["socket_state_changed", _on_signaling_state],
			["signaling_message", _on_signaling_message], ["error", _on_room_error]]:
			var signal_name: String = pair[0]
			var callback: Callable = pair[1]
			if room_client.has_signal(signal_name) and room_client.is_connected(signal_name, callback):
				room_client.disconnect(signal_name, callback)
	if peer_transport != null:
		for pair in [["peer_message", receive_peer_message], ["peer_state_changed", _on_peer_state],
			["outgoing_signal", _on_outgoing_signal], ["transport_error", _on_peer_error]]:
			var signal_name: String = pair[0]
			var callback: Callable = pair[1]
			if peer_transport.has_signal(signal_name) and peer_transport.is_connected(signal_name, callback):
				peer_transport.disconnect(signal_name, callback)


func _on_page_visibility_changed(visible: bool) -> void:
	page_visible = visible
	if _startup_context_eligible and not visible:
		_startup_hidden_seen = true
	page_visibility_changed.emit(visible)


func _startup_timeout_context(reason: String) -> String:
	if not _startup_hidden_seen or reason not in [
		"Room initial-state barrier timed out",
		"Room start acknowledgement timed out",
		"Data channels did not open before timeout",
		"peer start barrier timed out",
		"Room startup ended: start_timeout",
	]:
		return reason
	return reason + "（本页在开局期间进入过后台；建议双方把游戏窗口并排并保持可见，再取消本次开局后重试。）"


func _valid_setup(value: Dictionary) -> bool:
	if not value.get("members") is Array or value.members.size() != 2:
		return false
	if not value.get("stage") is String or not value.get("rules") is Dictionary:
		return false
	if not value.get("profile") is Dictionary or not _valid_profile(value.profile):
		return false
	if not value.get("seed") is int or value.seed < 0 or value.seed > 4_294_967_295:
		return false
	if value.rules.get("time") not in [30, 60, 90, 100] or value.rules.get("life") not in [1, 2, 3, 4, 5]:
		return false
	for member in value.members:
		if not member is Dictionary or not member.get("choice") is Dictionary:
			return false
		if not member.choice.get("fighter") is String or not member.choice.get("helper") is String:
			return false
	return true


func _normalize_setup(value: Dictionary) -> Dictionary:
	if not value.get("rules") is Dictionary or not value.get("profile") is Dictionary:
		return {}
	var normalized := value.duplicate(true)
	var rules: Dictionary = normalized.rules
	var time_value: Variant = _wire_integer(rules.get("time"), 30, 100)
	var life_value: Variant = _wire_integer(rules.get("life"), 1, 5)
	if time_value == null or time_value not in [30, 60, 90, 100] or life_value == null:
		return {}
	rules.time = time_value
	rules.life = life_value
	normalized.rules = rules
	var normalized_profile := _normalize_profile(normalized.profile)
	if normalized_profile.is_empty():
		return {}
	normalized.profile = normalized_profile
	var seed_value: Variant = _wire_integer(normalized.get("seed"), 0, 4_294_967_295)
	if seed_value == null:
		return {}
	normalized.seed = seed_value
	for key in ["clockBaseline", "setupRevision"]:
		if normalized.has(key):
			var metadata_value: Variant = _wire_integer(normalized[key], 0, 9_007_199_254_740_991)
			if metadata_value == null:
				return {}
			normalized[key] = metadata_value
	return normalized


func _normalize_profile(value: Variant) -> Dictionary:
	if not value is Dictionary:
		return {}
	var normalized: Dictionary = value.duplicate(true)
	if not normalized.get("id") is String or normalized.id.is_empty():
		return {}
	var delay_value: Variant = _wire_integer(normalized.get("inputDelay"), 0, 8)
	var window_value: Variant = _wire_integer(normalized.get("predictionWindow"), 0, 15)
	if delay_value == null or window_value == null:
		return {}
	normalized.inputDelay = delay_value
	normalized.predictionWindow = window_value
	return normalized


func _wire_integer(value: Variant, minimum: int, maximum: int) -> Variant:
	if value is bool:
		return null
	var normalized: int
	if value is int:
		normalized = value
	elif value is float and is_finite(value) and value == floor(value) \
		and absf(value) <= 9_007_199_254_740_991.0:
		normalized = int(value)
	else:
		return null
	if normalized < minimum or normalized > maximum:
		return null
	return normalized


func _valid_profile(value: Dictionary) -> bool:
	return value.get("id") is String and value.get("inputDelay") is int and value.inputDelay >= 0 and value.inputDelay <= 8 \
		and value.get("predictionWindow") is int and value.predictionWindow >= 0 and value.predictionWindow <= 15


func _new_recovery_id() -> String:
	_recovery_counter += 1
	return "%s:%d" % [epoch, _recovery_counter]


func _valid_recovery_id(value: String) -> bool:
	var prefix := epoch + ":"
	if not value.begins_with(prefix):
		return false
	var suffix := value.substr(prefix.length())
	return suffix.is_valid_int() and int(suffix) > 0 and str(int(suffix)) == suffix


func _is_completed_recovery_id(value: String) -> bool:
	if value.is_empty() or not _valid_recovery_id(value):
		return false
	return int(value.substr((epoch + ":").length())) <= _last_completed_recovery_counter


func _valid_epoch(value: String) -> bool:
	if value.length() != 36:
		return false
	for index in range(36):
		var codepoint := value.unicode_at(index)
		if index in [8, 13, 18, 23]:
			if codepoint != 45: return false
		elif not ((codepoint >= 48 and codepoint <= 57) or (codepoint >= 65 and codepoint <= 70) or (codepoint >= 97 and codepoint <= 102)):
			return false
	return true


func _start_hash(snapshot: Dictionary) -> String:
	var choices: Array = []
	for member in setup.members:
		choices.append(member.choice.duplicate(true))
	var room_state: Dictionary = room_client.get_room_state() if room_client != null else {}
	var compatibility: Dictionary = room_state.get("compatibility", {})
	return State.fingerprint({
		"setup": {"choices": choices, "stage": setup.stage, "rules": setup.rules, "seed": setup.seed,
			"profile": profile, "build": compatibility.get("build", ""), "content": compatibility.get("content", "")},
		"state": snapshot,
	})


func _wait_for_loaded_barrier(initial_hash: String, startup_generation: int) -> String:
	var client := room_client
	if client == null:
		return "Room client is unavailable"
	var deadline := Time.get_ticks_msec() + 30_000
	while Time.get_ticks_msec() < deadline:
		var state := await _refresh_room_state()
		if _startup_cancelled(startup_generation): return "Online match closed during startup"
		if state.has("error"): return str(state.error)
		var terminal_problem := _startup_state_problem(state)
		if not terminal_problem.is_empty(): return terminal_problem
		var match_state: Dictionary = state.get("match", {}) if state.get("match") is Dictionary else {}
		var loaded: Array = match_state.get("loaded", [])
		if loaded.size() == 2 and loaded[0] != null and loaded[1] != null:
			if loaded[0] != initial_hash or loaded[1] != initial_hash:
				return "Peer initial causal state differs"
			return ""
		await client.get_tree().create_timer(0.25).timeout
		if _startup_cancelled(startup_generation): return "Online match closed during startup"
	return "Room initial-state barrier timed out"


func _wait_for_active_barrier(startup_generation: int) -> String:
	var client := room_client
	if client == null:
		return "Room client is unavailable"
	var deadline := Time.get_ticks_msec() + 30_000
	while Time.get_ticks_msec() < deadline:
		var state := await _refresh_room_state()
		if _startup_cancelled(startup_generation): return "Online match closed during startup"
		if state.has("error"): return str(state.error)
		var terminal_problem := _startup_state_problem(state)
		if not terminal_problem.is_empty(): return terminal_problem
		if state.get("phase") == "active": return ""
		await client.get_tree().create_timer(0.25).timeout
		if _startup_cancelled(startup_generation): return "Online match closed during startup"
	return "Room start acknowledgement timed out"


func _startup_state_problem(state: Dictionary) -> String:
	var match_state: Dictionary = state.get("match", {}) if state.get("match") is Dictionary else {}
	if state.get("phase") in ["preparing", "active"]:
		if match_state.get("epoch") == epoch:
			return ""
		return "Room match epoch changed during startup"
	if state.get("phase") == "closed":
		return "Room closed during startup"
	var last_result: Dictionary = state.get("lastResult", {}) if state.get("lastResult") is Dictionary else {}
	if last_result.get("epoch") == epoch:
		var reason := str(last_result.get("reason", "match_ended"))
		return "Room startup ended: " + reason
	return "Room left preparation before startup completed"


func _refresh_room_state() -> Dictionary:
	var generation := _generation
	var client := room_client
	if client == null or not client.has_method("refresh_state"):
		return {"error": "Room state refresh is unavailable"}
	var response: Dictionary = await client.refresh_state()
	if generation != _generation or not is_instance_valid(client):
		return {"error": "match_closed"}
	if response.has("error"):
		var failure := {"error": str(response.error)}
		for key in ["httpStatus", "phase", "transportResult", "uncertain"]:
			if response.has(key): failure[key] = response[key]
		return failure
	var refreshed_state: Variant = response.get("state")
	if not refreshed_state is Dictionary:
		refreshed_state = client.get_room_state()
	if not refreshed_state is Dictionary:
		return {"error": "Room state refresh returned invalid state"}
	_room_state = refreshed_state
	return _room_state.duplicate(true)


func _room_command(operation: Dictionary, deadline_ms: int = -1) -> Dictionary:
	var generation := _generation
	var client := room_client
	if client == null:
		return {"error": "room_client_unavailable", "uncertain": false}
	var is_startup_command := _startup_active and str(operation.get("type", "")) != "abort"
	while _room_command_in_flight:
		if generation != _generation:
			return {"error": "match_closed", "uncertain": false}
		if not is_instance_valid(client):
			return {"error": "room_client_unavailable", "uncertain": false}
		if is_startup_command and _startup_cancel_requested:
			return {"error": "startup_cancelled", "uncertain": false}
		if deadline_ms >= 0 and Time.get_ticks_msec() >= deadline_ms:
			return {"error": "command_settlement_timeout", "uncertain": true}
		var client_tree: SceneTree = client.get_tree()
		if client_tree == null:
			return {"error": "room_client_unavailable", "uncertain": false}
		await client_tree.create_timer(0.05).timeout
	if generation != _generation or not is_instance_valid(client):
		return {"error": "match_closed", "uncertain": false}
	if is_startup_command and _startup_cancel_requested:
		return {"error": "startup_cancelled", "uncertain": false}
	_room_command_in_flight = true
	var pending_problem: Dictionary = await _settle_pending_room_command(client, generation, deadline_ms, is_startup_command)
	if generation != _generation or not is_instance_valid(client):
		_room_command_in_flight = false
		return {"error": "match_closed", "uncertain": false}
	if not pending_problem.is_empty():
		_room_command_in_flight = false
		return pending_problem
	if is_startup_command and _startup_cancel_requested:
		_room_command_in_flight = false
		return {"error": "startup_cancelled", "uncertain": false}
	if deadline_ms >= 0 and Time.get_ticks_msec() >= deadline_ms:
		_room_command_in_flight = false
		return {"error": "command_settlement_timeout", "uncertain": true}
	var reply: Dictionary = await client.command(operation)
	while generation == _generation and (reply.get("error") == "command_outcome_uncertain" or bool(reply.get("uncertain", false))):
		if is_startup_command and _startup_cancel_requested:
			break
		if deadline_ms >= 0 and Time.get_ticks_msec() >= deadline_ms:
			break
		_room_service_available = false
		await client.get_tree().create_timer(0.5).timeout
		if generation != _generation:
			break
		reply = await client.retry_pending_command()
	_room_command_in_flight = false
	if generation != _generation:
		return {"error": "match_closed"}
	if is_startup_command and _startup_cancel_requested and (reply.get("error") == "command_outcome_uncertain" or bool(reply.get("uncertain", false))):
		return {"error": "command_outcome_uncertain", "uncertain": true}
	if deadline_ms >= 0 and Time.get_ticks_msec() >= deadline_ms and (reply.get("error") == "command_outcome_uncertain" or bool(reply.get("uncertain", false))):
		return {"error": "command_settlement_timeout", "uncertain": true}
	if reply.has("error") and reply.get("error") in ["network_error", "socket_closed", "socket_timeout", "http_transport_failed"]:
		_room_service_available = false
	return reply


func _settle_pending_room_command(client: Object, generation: int, deadline_ms: int = -1, stop_on_startup_cancel: bool = false) -> Dictionary:
	if not is_instance_valid(client) or not client.has_method("has_uncertain_command"):
		return {"error": "match_closed", "uncertain": false} if generation != _generation else {}
	var deadline := deadline_ms if deadline_ms >= 0 else Time.get_ticks_msec() + 30_000
	while true:
		if generation != _generation or not is_instance_valid(client):
			return {"error": "match_closed", "uncertain": false}
		if stop_on_startup_cancel and _startup_cancel_requested:
			return {"error": "startup_cancelled", "uncertain": bool(client.has_uncertain_command())}
		if not bool(client.has_uncertain_command()):
			break
		if Time.get_ticks_msec() >= deadline:
			return {"error": "prior_command_settlement_timeout", "uncertain": true}
		if client.has_method("is_command_in_flight") and bool(client.is_command_in_flight()):
			await client.get_tree().create_timer(0.05).timeout
			continue
		var prior_reply: Dictionary = await client.retry_pending_command()
		if generation != _generation or not is_instance_valid(client):
			return {"error": "match_closed", "uncertain": false}
		if _command_accepted(prior_reply):
			continue
		if prior_reply.get("error") == "request_in_flight":
			await client.get_tree().create_timer(0.05).timeout
			continue
		if prior_reply.get("error") == "command_outcome_uncertain" or bool(prior_reply.get("uncertain", false)):
			_room_service_available = false
			await client.get_tree().create_timer(0.5).timeout
			continue
		return {"error": "prior_command_unresolved", "cause": str(prior_reply.get("error", "unknown")), "uncertain": false}
	return {}


func _command_accepted(reply: Dictionary) -> bool:
	return not reply.has("error") and reply.get("acceptedSeq") is int


func _sample_local_once(local_held: Dictionary) -> bool:
	var next_frame: int = rollback.frontier + 1
	if _sampled_frontier == next_frame:
		return true
	var problem := Rollback.validate_input(local_held)
	if not problem.is_empty():
		_abort_local("local_input", {"error": problem})
		return false
	var sample: Dictionary = rollback.sample_local(local_slot, next_frame, local_held)
	if sample.has("error"):
		_abort_local("local_input", {"error": sample.error})
		return false
	_sampled_frontier = next_frame
	_sampled_held = sample.held.duplicate(true)
	_local_inputs[int(sample.frame)] = sample.held.duplicate(true)
	if not _send_peer("input_frame", {"frame": int(sample.frame), "held": sample.held}):
		_abort_local("peer_send_input", {"frame": sample.frame})
		return false
	return true


func _poll_heartbeat(now_ms: int) -> void:
	_flush_pending_peer_messages(now_ms)
	if _last_heartbeat_sent_ms < 0 or now_ms - _last_heartbeat_sent_ms >= HEARTBEAT_INTERVAL_MS:
		if _send_peer("heartbeat", {"epoch": epoch, "frontier": rollback.frontier, "confirmed": rollback.confirmed}):
			_last_heartbeat_sent_ms = now_ms
	if _last_heartbeat_received_ms >= 0 and now_ms - _last_heartbeat_received_ms >= HEARTBEAT_TIMEOUT_MS and not recovering:
		_begin_recovery("heartbeat_timeout", now_ms)
	if recovering and _peer_link_connected() and (_recovery_sync_sent_ms < 0 or now_ms - _recovery_sync_sent_ms >= 500):
		_send_recovery_sync(now_ms)


func _begin_recovery(reason: String, now_ms: int) -> void:
	if recovering:
		return
	recovering = true
	_disconnect_started_ms = now_ms
	_recovery_started_ms = now_ms
	_recovery_sync_sent_ms = -1
	_recovery_sync_reply_sent = false
	_recovery_state.clear()
	_recovery_id = _new_recovery_id() if local_slot == "p1" else ""
	recovery_changed.emit("recovering:" + reason)
	_attempt_signaling_reconnect.call_deferred(_generation)
	_send_recovery_sync(now_ms)


func _send_recovery_sync(now_ms: int) -> void:
	if peer_transport == null or not _peer_link_connected():
		return
	if _recovery_id.is_empty() and local_slot != "p2":
		return
	var remote_sync: Dictionary = _recovery_state.get("remote_sync", {})
	var remote_matches: bool = remote_sync.get("recovery_id", "") == _recovery_id and not _recovery_id.is_empty()
	if local_slot == "p1" and remote_matches:
		return
	if local_slot == "p2" and _recovery_sync_reply_sent and remote_matches:
		return
	if _recovery_sync_sent_ms >= 0 and now_ms - _recovery_sync_sent_ms < 500:
		return
	var confirmed_frame: int = mini(rollback.confirmed, rollback.frontier)
	var snapshot: Dictionary = rollback.state_at(confirmed_frame)
	if snapshot.is_empty():
		_abort_local("recovery_state_pruned", {"confirmed": confirmed_frame})
		return
	if not _send_peer("recovery_sync", {"epoch": epoch, "recovery_id": _recovery_id,
		"frontier": rollback.frontier, "confirmed": rollback.confirmed,
		"oldest": rollback.oldest_frame(), "confirmedFrame": confirmed_frame,
		"confirmedHash": State.fingerprint(snapshot)}):
		return
	_recovery_sync_sent_ms = now_ms
	if local_slot == "p2" and remote_matches:
		_recovery_sync_reply_sent = true
	if not remote_matches:
		return
	var remote_oldest := int(remote_sync.get("oldest", 0))
	var remote_frontier := int(remote_sync.get("frontier", 0))
	var resend_limit := remote_frontier + maxi(32, int(profile.predictionWindow) + int(profile.inputDelay) + 8)
	for frame in _local_inputs.keys():
		if int(frame) > remote_oldest and int(frame) <= resend_limit:
			_send_peer("input_frame", {"frame": int(frame), "held": _local_inputs[frame]})
	for frame in _clock_samples.keys():
		if local_slot == clock_authority_slot and int(frame) > remote_oldest and int(frame) <= resend_limit:
			_send_peer("clock_sample", {"frame": int(frame), "elapsed_ms": int(_clock_samples[frame])})
	if local_slot == "p1" and _recovery_state.has("remote_sync"):
		_propose_recovery_comparison()


func _propose_recovery_comparison() -> void:
	if local_slot != "p1" or not _recovery_state.has("remote_sync"):
		return
	var remote: Dictionary = _recovery_state.remote_sync
	var local_confirmed := mini(rollback.confirmed, rollback.frontier)
	var frame := mini(local_confirmed, int(remote.get("confirmedFrame", -1)))
	var earliest := maxi(rollback.oldest_frame(), int(remote.get("oldest", 0)))
	if frame < earliest:
		_abort_local("invalid_recovery_frame", remote)
		return
	if int(_recovery_state.get("requested_frame", -1)) == frame:
		return
	var snapshot: Dictionary = rollback.state_at(frame)
	if snapshot.is_empty():
		_abort_local("recovery_state_pruned", {"frame": frame})
		return
	var digest := State.fingerprint(snapshot)
	_recovery_state.requested_frame = frame
	_recovery_state.local_hash = digest
	_send_peer("recovery_compare_request", {"epoch": epoch, "recovery_id": _recovery_id, "frame": frame, "hash": digest})


func _receive_recovery_sync(payload: Dictionary) -> void:
	if payload.get("epoch") != epoch:
		_abort_local("recovery_epoch_mismatch", {"epoch": payload.get("epoch")})
		return
	var incoming_id := str(payload.get("recovery_id", ""))
	if not incoming_id.is_empty() and not _valid_recovery_id(incoming_id):
		_abort_local("invalid_recovery_generation", {"recovery_id": incoming_id})
		return
	if _is_completed_recovery_id(incoming_id):
		return
	for field in ["frontier", "confirmed", "oldest", "confirmedFrame"]:
		if not _integral_number(payload.get(field)):
			_abort_local("invalid_recovery_sync", payload)
			return
	if not _is_digest(str(payload.get("confirmedHash", ""))):
		_abort_local("invalid_recovery_sync_hash", payload)
		return
	if not recovering:
		_begin_recovery("peer_recovery", _process_now_ms)
	if local_slot == "p1":
		if incoming_id.is_empty():
			_send_recovery_sync(_process_now_ms)
			return
		if incoming_id != _recovery_id:
			return
	else:
		if incoming_id.is_empty():
			return
		if not _recovery_id.is_empty() and incoming_id != _recovery_id:
			return
		_recovery_id = incoming_id
	var remote := payload.duplicate(true)
	if remote.get("recovery_id", "") == _recovery_id:
		_recovery_state.remote_sync = remote
		if local_slot == "p2" and not _recovery_sync_reply_sent:
			_send_recovery_sync(_process_now_ms)
	if local_slot == "p1":
		_propose_recovery_comparison()


func _receive_recovery_compare_request(payload: Dictionary) -> void:
	if _is_completed_recovery_id(str(payload.get("recovery_id", ""))):
		return
	var frame_value: Variant = payload.get("frame")
	var host_hash := str(payload.get("hash", ""))
	if local_slot != "p2" or payload.get("epoch") != epoch or payload.get("recovery_id") != _recovery_id \
		or not _integral_number(frame_value) or not _is_digest(host_hash):
		_abort_local("invalid_recovery_compare_request", payload)
		return
	var frame := int(frame_value)
	var snapshot: Dictionary = rollback.state_at(frame)
	if snapshot.is_empty() or rollback.confirmed < frame:
		_abort_local("recovery_compare_state_unavailable", {"frame": frame})
		return
	var digest := State.fingerprint(snapshot)
	if digest != host_hash:
		_abort_local("recovery_state_mismatch", {"frame": frame, "local_hash": digest, "remote_hash": host_hash})
		return
	_recovery_state.requested_frame = frame
	_recovery_state.local_hash = digest
	_send_peer("recovery_compare", {"epoch": epoch, "recovery_id": _recovery_id, "frame": frame, "hash": digest})


func _receive_recovery_compare(payload: Dictionary) -> void:
	if _is_completed_recovery_id(str(payload.get("recovery_id", ""))):
		return
	var frame_value: Variant = payload.get("frame")
	var digest := str(payload.get("hash", ""))
	if local_slot != "p1" or payload.get("epoch") != epoch or payload.get("recovery_id") != _recovery_id \
		or not _integral_number(frame_value) or not _is_digest(digest):
		_abort_local("invalid_recovery_compare", payload)
		return
	var frame := int(frame_value)
	if frame != int(_recovery_state.get("requested_frame", -1)) or digest != str(_recovery_state.get("local_hash", "")):
		_abort_local("recovery_state_mismatch", {"frame": frame, "local_hash": _recovery_state.get("local_hash", ""), "remote_hash": digest})
		return
	var commit := {"epoch": epoch, "recovery_id": _recovery_id, "frame": frame, "hash": digest}
	if _send_peer("recovery_commit", commit):
		_complete_recovery("reconciled")


func _receive_recovery_commit(payload: Dictionary) -> void:
	if _is_completed_recovery_id(str(payload.get("recovery_id", ""))):
		return
	var frame_value: Variant = payload.get("frame")
	if local_slot != "p2" or payload.get("epoch") != epoch or payload.get("recovery_id") != _recovery_id or not _integral_number(frame_value):
		_abort_local("invalid_recovery_commit", payload)
		return
	var frame := int(frame_value)
	var snapshot: Dictionary = rollback.state_at(frame)
	if snapshot.is_empty() or State.fingerprint(snapshot) != str(payload.get("hash", "")):
		_abort_local("recovery_commit_mismatch", {"frame": frame})
		return
	_complete_recovery("reconciled")


func _complete_recovery(reason: String) -> void:
	if _recovery_id.is_empty():
		return
	_last_completed_recovery_id = _recovery_id
	_last_completed_recovery_counter = int(_recovery_id.substr((epoch + ":").length()))
	if local_slot == clock_authority_slot and _recovery_started_ms >= 0:
		_clock_paused_total_ms += maxi(0, _process_now_ms - _recovery_started_ms)
	recovering = false
	_disconnect_started_ms = -1
	_recovery_started_ms = -1
	_recovery_id = ""
	_recovery_sync_reply_sent = false
	_recovery_state.clear()
	_recovery_sync_sent_ms = -1
	_last_heartbeat_received_ms = _process_now_ms
	recovery_changed.emit(reason)
	_poll_control_barriers(_process_now_ms)


func _attempt_signaling_reconnect(generation: int) -> void:
	if _signaling_reconnect_active or room_client == null or not room_client.has_method("connect_signaling"):
		return
	_signaling_reconnect_active = true
	while generation == _generation and room_client != null:
		if room_client.has_method("is_signaling_connected") and room_client.is_signaling_connected():
			_room_service_available = true
			break
		var reply: Dictionary = await room_client.connect_signaling()
		if generation != _generation:
			break
		if not reply.has("error"):
			_room_service_available = true
			break
		_room_service_available = false
		await room_client.get_tree().create_timer(1.0).timeout
	_signaling_reconnect_active = false


func _control_frame_pending() -> bool:
	return _pause_state.has("proposal_frame") or _resume_state.has("proposal_frame")


func _pending_control_frame() -> int:
	var state: Dictionary = _pause_state if _pause_state.has("proposal_frame") else _resume_state
	return int(state.get("proposal_frame", -1))


func _input_frame_is_confirmed(frame: int) -> bool:
	return rollback.frontier >= frame and rollback.confirmed >= frame


func _report_control_ready() -> void:
	for action in ["pause", "resume"]:
		var state: Dictionary = _pause_state if action == "pause" else _resume_state
		if not state.has("proposal_frame") or state.get("ready_sent", false):
			continue
		var frame := int(state.proposal_frame)
		if not _input_frame_is_confirmed(frame):
			continue
		var snapshot: Dictionary = rollback.state_at(frame)
		if snapshot.is_empty():
			_abort_local("control_state_pruned", {"frame": frame})
			return
		var digest := State.fingerprint(snapshot)
		state.ready_sent = true
		state.local_ready_hash = digest
		if local_slot == "p1":
			_maybe_commit_control(action)
		else:
			_send_peer("control", {"action": action + "_ready", "id": state.id, "frame": frame, "hash": digest})


func _integral_number(value: Variant) -> bool:
	if value is int:
		return true
	return value is float and is_finite(value) and value == floor(value) and absf(value) <= 9_007_199_254_740_991.0


func _is_digest(value: String) -> bool:
	if value.length() != 64 or value != value.to_lower():
		return false
	for index in range(value.length()):
		var codepoint := value.unicode_at(index)
		if not ((codepoint >= 48 and codepoint <= 57) or (codepoint >= 97 and codepoint <= 102)):
			return false
	return true


func _schedule_intro_skip(frame: int) -> String:
	if local_slot != "p1" or frame <= rollback.frontier or frame > rollback.frontier + 120:
		return "Intro skip target is outside the host scheduling window"
	if not _intro_skip_frames.is_empty():
		return ""
	_intro_skip_frames[frame] = true
	if not _send_peer("control", {"action": "intro_skip_commit", "frame": frame}):
		return _abort_local("intro_skip_send", {"frame": frame})
	return ""


func _open_peer_transport(startup_generation: int) -> String:
	var client := room_client
	var transport := peer_transport
	if _startup_cancelled(startup_generation): return "Online match closed during startup"
	if client == null or transport == null:
		return "Room or peer transport is unavailable"
	if int(client.get_slot()) != (0 if local_slot == "p1" else 1):
		return "Room slot and battle input slot disagree"
	var state: Dictionary = await _refresh_room_state()
	if _startup_cancelled(startup_generation): return "Online match closed during startup"
	if state.has("error"):
		return str(state.error)
	if not client.is_signaling_connected():
		var signaling: Dictionary = await client.connect_signaling()
		if _startup_cancelled(startup_generation): return "Online match closed during startup"
		if not signaling.has("state"):
			return "Room signaling failed: " + str(signaling.get("error", "unknown"))
	var negotiation_id := ""
	if local_slot == "p1":
		var negotiation: Dictionary = await _room_command({"type": "negotiate", "epoch": epoch})
		if _startup_cancelled(startup_generation): return "Online match closed during startup"
		if not _command_accepted(negotiation): return "Room negotiation failed: " + str(negotiation.get("error", "unknown"))
		_room_state = negotiation.get("state", {})
	else:
		var deadline := Time.get_ticks_msec() + 30_000
		while Time.get_ticks_msec() < deadline:
			var refreshed := await _refresh_room_state()
			if _startup_cancelled(startup_generation): return "Online match closed during startup"
			if refreshed.has("error"): return str(refreshed.error)
			var current: Dictionary = refreshed.get("negotiation", {}) if refreshed.get("negotiation") is Dictionary else {}
			if current.get("epoch") == epoch:
				negotiation_id = str(current.get("id", ""))
				break
			await client.get_tree().create_timer(0.25).timeout
			if _startup_cancelled(startup_generation): return "Online match closed during startup"
		if negotiation_id.is_empty(): return "Peer negotiation was not created"
	if negotiation_id.is_empty():
		var negotiation_state: Variant = _room_state.get("negotiation")
		if negotiation_state is Dictionary:
			negotiation_id = str(negotiation_state.get("id", ""))
	if negotiation_id.is_empty(): return "Room negotiation id is missing"
	var ice_servers: Array = []
	if not str(profile.get("id", "")).ends_with("-lan"):
		var ice: Dictionary = await client.get_ice_servers()
		if _startup_cancelled(startup_generation): return "Online match closed during startup"
		if ice.has("error"): return "ICE lookup failed: " + str(ice.error)
		ice_servers = ice.get("iceServers", [])
	var local_index := 0 if local_slot == "p1" else 1
	var remote_index := 1 - local_index
	if _startup_cancelled(startup_generation): return "Online match closed during startup"
	if not transport.configure(client.get_room_id(), epoch, local_index, remote_index, negotiation_id): return "Peer transport configuration failed"
	if not transport.create_peer(ice_servers): return "Peer creation failed"
	_peer_configured = true
	for early_signal in _early_signals:
		if not transport.handle_signal(early_signal): return "Queued peer signal was rejected"
	_early_signals.clear()
	if local_slot == "p1":
		if not transport.begin_offer(): return "Peer offer creation failed"
	var channel_deadline := Time.get_ticks_msec() + 30_000
	while Time.get_ticks_msec() < channel_deadline:
		if _startup_cancelled(startup_generation): return "Online match closed during startup"
		_flush_pending_signals(Time.get_ticks_msec())
		if not _signal_error.is_empty(): return "Signaling failed: " + _signal_error
		if _peer_link_connected():
			_peer_channel_open = true
			return ""
		await client.get_tree().create_timer(0.05).timeout
		if _startup_cancelled(startup_generation): return "Online match closed during startup"
	return "Data channels did not open before timeout"
	return ""


func _receive_input(payload: Dictionary) -> void:
	var frame_value: Variant = payload.get("frame")
	if not running or not _integral_number(frame_value) or not payload.get("held") is Dictionary:
		_abort_local("invalid_peer_input", payload)
		return
	var frame := int(frame_value)
	var problem: String = rollback.receive(epoch, remote_slot, frame, payload.held)
	if not problem.is_empty():
		_abort_local("peer_input", {"frame": frame, "error": problem})
		return
	_maybe_hash_confirmed()
	_maybe_finish_result()


func _receive_clock_sample(payload: Dictionary) -> void:
	var frame_value: Variant = payload.get("frame")
	var elapsed_value: Variant = payload.get("elapsed_ms")
	if local_slot == clock_authority_slot or not _integral_number(frame_value) or not _integral_number(elapsed_value):
		_abort_local("clock_authority", {"slot": local_slot})
		return
	var frame := int(frame_value)
	var elapsed := int(elapsed_value)
	if frame <= 0 or elapsed < 0:
		_abort_local("invalid_clock_sample", payload)
		return
	if _clock_samples.has(frame):
		if int(_clock_samples[frame]) != elapsed:
			_abort_local("conflicting_clock_sample", {"frame": frame})
		return
	if rollback == null or not rollback.can_receive_frame(frame):
		_abort_local("clock_sample_outside_receive_window", {"frame": frame,
			"oldest": rollback.oldest_frame() + 1 if rollback != null else -1})
		return
	for existing in _clock_samples.keys():
		if existing < frame and int(_clock_samples[existing]) > elapsed:
			_abort_local("clock_regression", {"frame": frame, "elapsed_ms": elapsed})
			return
	_clock_samples[frame] = elapsed

func _maybe_hash_confirmed() -> void:
	if rollback == null: return
	while _next_hash_frame <= mini(rollback.confirmed, rollback.frontier):
		var snapshot: Dictionary = rollback.state_at(_next_hash_frame)
		if snapshot.is_empty():
			_abort_local("missing_hash_state", {"frame": _next_hash_frame})
			return
		var digest := State.fingerprint(snapshot)
		_local_hashes[_next_hash_frame] = digest
		_send_peer("state_hash", {"frame": _next_hash_frame, "hash": digest})
		_compare_hash(_next_hash_frame)
		_next_hash_frame += HASH_INTERVAL
		if _local_hashes.size() + _remote_hashes.size() > MAX_HASH_HISTORY:
			_abort_local("hash_confirmation_stalled", {"pending_local": _local_hashes.size(), "pending_remote": _remote_hashes.size()})
			return


func _receive_state_hash(payload: Dictionary) -> void:
	var frame: Variant = payload.get("frame")
	var digest: Variant = payload.get("hash")
	if not _integral_number(frame) or int(frame) <= 0 or not digest is String or not _is_digest(digest):
		_abort_local("invalid_state_hash", payload)
		return
	_remote_hashes[int(frame)] = digest
	_compare_hash(int(frame))
	if _local_hashes.size() + _remote_hashes.size() > MAX_HASH_HISTORY:
		_abort_local("hash_confirmation_stalled", {"pending_local": _local_hashes.size(), "pending_remote": _remote_hashes.size()})


func _compare_hash(frame: int) -> void:
	if not _local_hashes.has(frame) or not _remote_hashes.has(frame): return
	if _local_hashes[frame] != _remote_hashes[frame]:
		_abort_local("state_mismatch", {"frame": frame, "local_hash": _local_hashes[frame], "remote_hash": _remote_hashes[frame], "local_state": rollback.state_at(frame)})
		return
	_local_hashes.erase(frame)
	_remote_hashes.erase(frame)


func _maybe_finish_result() -> void:
	if game == null or not game.ko_terminal_pending or rollback.confirmed < game.physics_tick:
		return
	var frame: int = game.physics_tick
	if _local_results.has(frame): return
	var winner: Variant = _winner_slot()
	var snapshot: Dictionary = rollback.state_at(frame)
	if snapshot.is_empty():
		_abort_local("missing_result_state", {"frame": frame})
		return
	var result := {"epoch": epoch, "frame": frame, "winner": winner, "hash": State.fingerprint(snapshot)}
	_local_results[frame] = result
	_send_peer("result", result)
	if not _remote_result.is_empty(): _compare_result(result, _remote_result)


func _winner_slot() -> Variant:
	var p1_wins := int(game.ko_state.get("_root.p1ws", 1))
	var p2_wins := int(game.ko_state.get("_root.p2ws", 1))
	if p1_wins == p2_wins: return null
	return 0 if p1_wins > p2_wins else 1


func _receive_result(payload: Dictionary) -> void:
	if payload.get("epoch") != epoch or not _integral_number(payload.get("frame")) or int(payload.get("frame")) <= 0 or not payload.has("winner"):
		_abort_local("invalid_peer_result", payload)
		return
	var normalized_winner := _normalize_winner(payload.get("winner"))
	if not bool(normalized_winner.get("ok", false)) or not _is_digest(str(payload.get("hash", ""))):
		_abort_local("invalid_peer_result", payload)
		return
	_remote_result = {"epoch": epoch, "frame": int(payload.frame), "winner": normalized_winner.winner, "hash": str(payload.hash)}
	for local in _local_results.values():
		_compare_result(local, _remote_result)


func _normalize_winner(value: Variant) -> Dictionary:
	if value == null:
		return {"ok": true, "winner": null}
	if value is bool or not _integral_number(value):
		return {"ok": false}
	var slot := int(value)
	if slot not in [0, 1]:
		return {"ok": false}
	return {"ok": true, "winner": slot}


func _compare_result(local: Dictionary, remote: Dictionary) -> void:
	if local != remote:
		_abort_local("result_mismatch", {"local": local, "remote": remote})
		return
	var problem: String = battle.commit_result()
	if not problem.is_empty():
		_abort_local("result_commit", {"error": problem})
		return
	if not _result_submission_started:
		_result_submission_started = true
		_submit_confirmed_result.call_deferred(local.duplicate(true), _generation)
	running = false
	result_confirmed.emit(local.duplicate(true))


func _submit_confirmed_result(local: Dictionary, generation: int) -> void:
	var operation := {"type": "result", "epoch": local.epoch, "frame": int(local.frame), "hash": local.hash, "winner": local.winner}
	var accepted := false
	while generation == _generation and not _result_submission_complete:
		if not accepted:
			var reply: Dictionary = await _room_command(operation)
			if generation != _generation:
				return
			accepted = _command_accepted(reply)
			if not accepted:
				_room_service_available = false
				var rejected_state: Dictionary = await _refresh_room_state()
				if generation != _generation:
					return
				if _settle_result_service_state(local, rejected_state):
					return
				await room_client.get_tree().create_timer(1.0).timeout
				continue
		var state := await _refresh_room_state()
		if generation != _generation:
			return
		if _settle_result_service_state(local, state):
			return
		if state.has("error"):
			_room_service_available = false
		await room_client.get_tree().create_timer(1.0).timeout


func _settle_result_service_state(local: Dictionary, state: Dictionary) -> bool:
	var terminal := _service_terminal_outcome(state)
	if terminal.is_empty():
		return false
	if terminal.get("kind") == "agreed":
		if terminal.get("winner") == local.get("winner"):
			_result_submission_complete = true
			room_result_committed.emit(local.duplicate(true))
			return true
		var mismatch_report := {"kind": "service_result_mismatch", "epoch": epoch, "frame": local.get("frame"),
			"details": {"service_result": terminal.get("last_result", {}), "local_result": local.duplicate(true)}}
		_settle_service_abort(mismatch_report, {"kind": "no_winner", "reason": "service_result_mismatch"})
		return true
	if terminal.get("kind") in ["no_winner", "room_unavailable"]:
		var report := {"kind": "service_result_unavailable", "epoch": epoch, "frame": local.get("frame"),
			"details": {"local_result": local.duplicate(true)}}
		_settle_service_abort(report, terminal)
		return true
	return false


func _request_control(action: String) -> String:
	if not running or action not in ["pause", "resume"] or (action == "pause" and paused) or (action == "resume" and not paused):
		return "Control request is not valid now"
	var active: Dictionary = _pause_state if action == "pause" else _resume_state
	if not active.is_empty():
		return "A control request is already pending"
	_control_counter += 1
	var request_id := "%s-%d" % [local_slot, _control_counter]
	var state := {"id": request_id, "action": action, "requester": local_slot, "votes": {local_slot: true}}
	_set_control_state(action, state)
	if not _send_peer("control", {"action": action + "_request", "id": request_id, "frame": rollback.frontier}):
		return "Could not send control request"
	return ""


func _respond_control(action: String, request_id: String, accepted: bool) -> String:
	var state: Dictionary = _get_control_state(action)
	if state.is_empty() or state.get("id") != request_id or state.get("requester") == local_slot:
		return "Unknown control request"
	state.votes[local_slot] = accepted
	if not accepted:
		_send_peer("control", {"action": action + "_reject", "id": request_id})
		_set_control_state(action, {})
		return ""
	_send_peer("control", {"action": action + "_accept", "id": request_id, "frame": rollback.frontier})
	_maybe_propose_control(action)
	return ""


func _receive_control(payload: Dictionary) -> void:
	var action := str(payload.get("action", ""))
	var request_id := str(payload.get("id", ""))
	match action:
		"pause_request", "resume_request":
			var control_action := action.trim_suffix("_request")
			var current := _get_control_state(control_action)
			if request_id.is_empty() or not _integral_number(payload.get("frame")):
				_abort_local("invalid_control_request", payload)
				return
			if not current.is_empty():
				if current.get("id") == request_id:
					return
				# P1 is the only sequencer. On crossing requests it keeps its own
				# request and rejects the P2 request deterministically.
				if local_slot == "p1":
					_send_peer("control", {"action": control_action + "_reject", "id": request_id})
				else:
					_set_control_state(control_action, {})
					current = {"id": request_id, "action": control_action, "requester": remote_slot,
						"votes": {remote_slot: true}, "remote_frame": int(payload.frame)}
					_set_control_state(control_action, current)
			else:
				current = {"id": request_id, "action": control_action, "requester": remote_slot,
					"votes": {remote_slot: true}, "remote_frame": int(payload.frame)}
				_set_control_state(control_action, current)
			if local_slot == "p1" and current.get("id") == request_id:
				if control_action == "pause": pause_requested.emit(payload.duplicate(true))
				else: resume_requested.emit(payload.duplicate(true))
			elif local_slot == "p2" and current.get("id") == request_id:
				if control_action == "pause": pause_requested.emit(payload.duplicate(true))
				else: resume_requested.emit(payload.duplicate(true))
		"pause_accept", "resume_accept":
			var control_action := "pause" if action.begins_with("pause") else "resume"
			var state := _get_control_state(control_action)
			if local_slot != "p1" or state.get("id") != request_id or state.is_empty(): return
			if not _integral_number(payload.get("frame")):
				_abort_local("invalid_control_accept", payload)
				return
			state.votes[remote_slot] = true
			state["remote_frame"] = int(payload.get("frame", 0))
			_maybe_propose_control(control_action)
		"pause_reject", "resume_reject":
			var control_action := "pause" if action.begins_with("pause") else "resume"
			var state := _get_control_state(control_action)
			if state.get("id") == request_id:
				_set_control_state(control_action, {})
		"pause_proposal", "resume_proposal":
			var control_action := "pause" if action.begins_with("pause") else "resume"
			var state := _get_control_state(control_action)
			var frame: Variant = payload.get("frame")
			if local_slot != "p2" or state.get("id") != request_id or not _integral_number(frame):
				_abort_local("invalid_control_proposal", payload)
				return
			if int(frame) < rollback.frontier or int(frame) > rollback.frontier + 120:
				_abort_local("stale_control_proposal", payload)
				return
			state.proposal_frame = int(frame)
			_report_control_ready()
		"pause_ready", "resume_ready":
			var control_action := "pause" if action.begins_with("pause") else "resume"
			var state := _get_control_state(control_action)
			var frame: Variant = payload.get("frame")
			if local_slot != "p1" or state.get("id") != request_id or not _integral_number(frame) or not _is_digest(str(payload.get("hash", ""))):
				_abort_local("invalid_control_ready", payload)
				return
			if int(frame) != int(state.get("proposal_frame", -1)):
				_abort_local("control_ready_frame_mismatch", payload)
				return
			state.remote_ready_hash = str(payload.hash)
			_maybe_commit_control(control_action)
		"pause_commit", "resume_commit":
			var control_action := "pause" if action.begins_with("pause") else "resume"
			var state := _get_control_state(control_action)
			if local_slot != "p2" or state.get("id") != request_id:
				return
			_apply_control_commit(control_action, state, payload)
		"intro_skip_request":
			if local_slot != "p1" or not _integral_number(payload.get("frame")):
				_abort_local("invalid_intro_skip_request", payload)
				return
			if game.battle_intro.active and game.battle_intro.polling:
				_schedule_intro_skip(maxi(rollback.frontier + CONTROL_FRAME_LEAD, int(payload.frame) + CONTROL_FRAME_LEAD))
		"intro_skip_commit":
			var frame: Variant = payload.get("frame")
			if local_slot != "p2" or not _integral_number(frame) or int(frame) <= rollback.frontier or int(frame) > rollback.frontier + 120:
				_abort_local("invalid_intro_skip_commit", payload)
				return
			_intro_skip_frames[int(frame)] = true
		_: _abort_local("invalid_control_action", payload)


func _maybe_propose_control(action: String) -> void:
	if local_slot != "p1":
		return
	var state := _get_control_state(action)
	if state.is_empty() or not state.votes.get("p1", false) or not state.votes.get("p2", false) or state.has("proposal_frame"):
		return
	var frame: int
	if action == "resume":
		frame = rollback.frontier
	else:
		frame = maxi(maxi(rollback.frontier, rollback.confirmed), int(state.get("remote_frame", 0))) + CONTROL_FRAME_LEAD
	state.proposal_frame = frame
	_send_peer("control", {"action": action + "_proposal", "id": state.id, "frame": frame})
	_report_control_ready()


func _poll_control_barriers(now_ms: int) -> void:
	_report_control_ready()
	for action in ["pause", "resume"]:
		var state := _get_control_state(action)
		if state.has("commit_payload"):
			_apply_control_commit(action, state, state.commit_payload)


func _get_control_state(action: String) -> Dictionary:
	return _pause_state if action == "pause" else _resume_state


func _set_control_state(action: String, state: Dictionary) -> void:
	if action == "pause":
		_pause_state = state
	else:
		_resume_state = state


func _maybe_commit_control(action: String) -> void:
	if local_slot != "p1": return
	var state := _get_control_state(action)
	if state.is_empty() or not state.get("ready_sent", false) or not state.has("remote_ready_hash"):
		return
	if state.local_ready_hash != state.remote_ready_hash:
		_abort_local("control_state_mismatch", {"frame": state.proposal_frame, "local_hash": state.local_ready_hash, "remote_hash": state.remote_ready_hash})
		return
	var paused_duration := maxi(0, _process_now_ms - _pause_started_ms) if action == "resume" and _pause_started_ms >= 0 else 0
	var commit := {"action": action + "_commit", "id": state.id, "frame": state.proposal_frame,
		"hash": state.local_ready_hash, "paused_ms": paused_duration}
	if not _send_peer("control", commit): return
	_apply_control_commit(action, state, commit)


func _apply_control_commit(action: String, state: Dictionary, payload: Dictionary) -> void:
	if state.is_empty() or state.get("id") != payload.get("id"):
		return
	var frame: Variant = payload.get("frame")
	if not _integral_number(frame) or int(frame) != int(state.get("proposal_frame", -1)):
		_abort_local("invalid_control_commit", payload)
		return
	if not _input_frame_is_confirmed(int(frame)):
		state.commit_payload = payload.duplicate(true)
		return
	var snapshot: Dictionary = rollback.state_at(int(frame))
	var digest := State.fingerprint(snapshot) if not snapshot.is_empty() else ""
	if digest.is_empty() or digest != str(payload.get("hash", "")) or digest != str(state.get("local_ready_hash", digest)):
		_abort_local("control_commit_hash_mismatch", {"frame": frame, "hash": digest})
		return
	if action == "pause":
		paused = true
		_pause_started_ms = _process_now_ms
		pause_changed.emit(true)
	else:
		_clock_paused_total_ms += maxi(0, int(payload.get("paused_ms", 0)))
		_pause_started_ms = -1
		paused = false
		pause_changed.emit(false)
	_set_control_state(action, {})


func _send_peer(type: String, payload: Dictionary) -> bool:
	if peer_transport == null or not peer_transport.has_method("send_peer_message"):
		return false
	var message := {"type": type, "payload": payload.duplicate(true)}
	if type == "match_abort":
		return peer_transport.send_peer_message("reliable", type, message.payload)
	if _pending_peer_messages.size() >= 4096:
		if running:
			_abort_local("peer_send_queue_overflow", {"type": type})
		return false
	if not _pending_peer_messages.is_empty():
		_pending_peer_messages.append(message)
		if running:
			_begin_recovery("peer_send_queue_wait", Time.get_ticks_msec())
		return true
	if _peer_link_connected() and peer_transport.send_peer_message("reliable", type, message.payload):
		return true
	if running:
		_pending_peer_messages.append(message)
		_begin_recovery("peer_channel_unavailable", Time.get_ticks_msec())
		return true
	return false


func _flush_pending_peer_messages(now_ms: int) -> void:
	if _pending_peer_messages.is_empty() or not _peer_link_connected():
		return
	while not _pending_peer_messages.is_empty():
		var message: Dictionary = _pending_peer_messages[0]
		if not peer_transport.send_peer_message("reliable", str(message.type), message.payload):
			_begin_recovery("peer_channel_unavailable", now_ms)
			return
		_pending_peer_messages.pop_front()


func _send_local_abort(kind: String, details: Dictionary) -> void:
	var frame: int = rollback.frontier if rollback != null else 0
	var digest := str(details.get("local_hash", details.get("hash", "")))
	if not _is_digest(digest) and rollback != null:
		var confirmed_frame := mini(rollback.confirmed, rollback.frontier)
		var snapshot: Dictionary = rollback.state_at(confirmed_frame)
		if not snapshot.is_empty():
			digest = State.fingerprint(snapshot)
	_send_local_abort_record(kind, frame, digest)


func _send_local_abort_record(kind: String, frame: int, digest: String) -> void:
	_send_peer("match_abort", {"epoch": epoch, "kind": kind.substr(0, 80), "frame": frame,
		"hash": digest if _is_digest(digest) else ""})


func _startup_cancelled(generation: int) -> bool:
	return generation != _generation or (_startup_active and _startup_cancel_requested)


func _abort_start_for_generation(generation: int, stage: String, details: Dictionary) -> String:
	if _startup_cancelled(generation):
		return "Online match closed during startup"
	var latest_state := await _refresh_room_state()
	if _startup_cancelled(generation):
		return "Online match closed during startup"
	var result := await _abort_start(stage, details, latest_state, generation)
	if _startup_cancelled(generation):
		return "Online match closed during startup"
	return result


func _abort_start(stage: String, details: Dictionary, latest_state: Dictionary, generation: int) -> String:
	if not latest_state.has("error") and _startup_state_is_live(latest_state) and not _startup_cancelled(generation):
		await _room_command({"type": "abort", "epoch": epoch})
	return "Online start failed at %s: %s" % [stage, str(details.get("error", "unknown"))]


func _startup_state_is_live(state: Dictionary) -> bool:
	if state.get("phase") not in ["preparing", "active"]:
		return false
	var match_state: Dictionary = state.get("match", {}) if state.get("match") is Dictionary else {}
	return match_state.get("epoch") == epoch


func _abort_local(kind: String, details: Dictionary, notify_peer: bool = true) -> String:
	if error.is_empty():
		error = kind
		var report := {"kind": kind, "epoch": epoch, "frame": rollback.frontier if rollback != null else 0, "details": details.duplicate(true)}
		if notify_peer:
			_send_local_abort(kind, details)
		if not _abort_submission_started and _valid_epoch(epoch):
			_abort_submission_started = true
			_submit_confirmed_abort.call_deferred(report.duplicate(true), _generation)
		diagnostic_abort.emit(report)
		running = false
	return error


func _check_recovery_deadline(now_ms: int) -> void:
	if recovering and _disconnect_started_ms >= 0 and now_ms - _disconnect_started_ms >= RECOVERY_MS:
		_abort_local("peer_disconnect_timeout", {"timeout_ms": RECOVERY_MS, "winner": null})


func _abort_room_match(generation: int) -> void:
	if room_client == null or generation != _generation:
		return
	await _room_command({"type": "abort", "epoch": epoch})


func _submit_confirmed_abort(report: Dictionary, generation: int) -> void:
	var operation := {"type": "abort", "epoch": epoch}
	var command_accepted := false
	while generation == _generation:
		if not command_accepted:
			var reply: Dictionary = await _room_command(operation)
			if generation != _generation:
				return
			command_accepted = _command_accepted(reply)
			if not command_accepted:
				var rejected_state: Dictionary = await _refresh_room_state()
				if generation != _generation:
					return
				var rejected_terminal := _service_terminal_outcome(rejected_state)
				if not rejected_terminal.is_empty():
					_settle_abort_terminal(report, rejected_terminal)
					return
		var state := await _refresh_room_state()
		if generation != _generation:
			return
		var terminal := _service_terminal_outcome(state)
		if not terminal.is_empty():
			_settle_abort_terminal(report, terminal)
			return
		if state.has("error") or not command_accepted:
			_room_service_available = false
		await room_client.get_tree().create_timer(1.0).timeout


func _service_terminal_outcome(state: Dictionary) -> Dictionary:
	if state.get("phase") == "closed":
		return {"kind": "room_unavailable", "reason": "room_closed", "last_result": state.get("lastResult", {})}
	if state.has("error"):
		var code := str(state.get("error", ""))
		var status := int(state.get("httpStatus", 0))
		if code in PERMANENT_ROOM_ERRORS or status in [401, 403, 404, 410]:
			return {"kind": "room_unavailable", "reason": code if not code.is_empty() else "room_unavailable", "http_status": status}
		return {}
	if state.get("phase") != "lobby":
		return {}
	var result: Dictionary = state.get("lastResult", {}) if state.get("lastResult") is Dictionary else {}
	if result.get("epoch") != epoch or not result.has("winner"):
		return {}
	if result.get("reason") == "agreed":
		var winner := _normalize_winner(result.get("winner"))
		if bool(winner.get("ok", false)):
			return {"kind": "agreed", "winner": winner.winner, "last_result": result.duplicate(true)}
		return {}
	if result.get("reason") in NO_WINNER_TERMINAL_REASONS and result.get("winner") == null:
		return {"kind": "no_winner", "reason": str(result.reason), "last_result": result.duplicate(true)}
	return {}


func _settle_service_abort(report: Dictionary, terminal: Dictionary) -> void:
	var settled := report.duplicate(true)
	var is_room_unavailable: bool = terminal.get("kind") == "room_unavailable"
	var already_finished: bool = terminal.get("kind") == "already_finished"
	settled["service_terminal"] = "room_unavailable" if is_room_unavailable else "match_already_finished" if already_finished else "match_aborted"
	settled["reason"] = str(terminal.get("reason", settled.get("kind", "service_terminal")))
	settled["service_error"] = str(terminal.get("reason", ""))
	if terminal.get("last_result") is Dictionary:
		settled["last_result"] = terminal.last_result.duplicate(true)
	if not error.is_empty():
		settled["kind"] = error
	elif not str(terminal.get("reason", "")).is_empty():
		error = str(terminal.reason)
	_result_submission_complete = true
	_abort_submission_started = true
	_room_service_available = not is_room_unavailable
	room_match_aborted.emit(settled)


func _settle_abort_terminal(report: Dictionary, terminal: Dictionary) -> void:
	if terminal.get("kind") != "agreed":
		_settle_service_abort(report, terminal)
		return
	var matched := _confirmed_local_result(int(terminal.get("winner", -1)))
	if not matched.is_empty():
		_result_submission_complete = true
		room_result_committed.emit(matched)
		return
	var already_finished := terminal.duplicate(true)
	already_finished["kind"] = "already_finished"
	_settle_service_abort(report, already_finished)


func _confirmed_local_result(service_winner: int) -> Dictionary:
	if not _result_submission_started or _remote_result.is_empty():
		return {}
	for value in _local_results.values():
		var local: Dictionary = value
		if local == _remote_result and local.get("winner") == service_winner:
			return local.duplicate(true)
	return {}


func _receive_match_ready(payload: Dictionary) -> void:
	if payload.get("epoch") != epoch or payload.get("initialHash") != _start_hash(save_state()):
		_abort_local("peer_start_hash", payload)
		return
	_peer_ready = true


func _on_room_state(state: Dictionary) -> void:
	_room_state = state.duplicate(true)


func _on_signaling_state(_connected: bool) -> void:
	# Signaling may disappear while the direct WebRTC data channel stays healthy.
	_room_service_available = _connected
	if _connected:
		_signaling_reconnect_active = false
	elif running:
		_attempt_signaling_reconnect.call_deferred(_generation)


func _on_signaling_message(message: Dictionary) -> void:
	if message.get("type") == "socket_closed":
		_room_service_available = false
		return
	if message.get("type") == "signal_ack":
		var sequence: Variant = message.get("seq")
		if not _integral_number(sequence):
			_signal_error = "invalid_signal_ack"
			return
		var item: Variant = _pending_signals.get(int(sequence))
		if item is Dictionary:
			_pending_signals.erase(int(sequence))
			if not bool(message.get("delivered", false)):
				item.retry_after_ms = Time.get_ticks_msec() + 250
				_signal_retry_queue.append(item)
		return
	if message.get("type") == "error":
		_signal_error = str(message.get("error", "signaling_error"))
		return
	if not _peer_configured:
		if _early_signals.size() >= 256:
			_signal_error = "too_many_early_signals"
		else:
			_early_signals.append(message.duplicate(true))
		return
	if peer_transport != null and peer_transport.has_method("handle_signal") and not peer_transport.handle_signal(message):
		_signal_error = "peer_signal_rejected"


func _on_outgoing_signal(kind: String, message_epoch: Variant, negotiation_id: String, payload: String) -> void:
	_signal_retry_queue.append({"kind": kind, "epoch": message_epoch, "negotiation_id": negotiation_id,
		"payload": payload, "retry_after_ms": 0})
	_flush_pending_signals(Time.get_ticks_msec())


func _flush_pending_signals(now_ms: int) -> void:
	if room_client == null or not room_client.has_method("send_signal"):
		return
	var remaining: Array[Dictionary] = []
	for item in _signal_retry_queue:
		if int(item.get("retry_after_ms", 0)) > now_ms:
			remaining.append(item)
			continue
		if room_client.send_signal(str(item.kind), item.epoch, str(item.negotiation_id), str(item.payload)):
			var sequence := int(room_client.get_last_signal_sequence())
			if sequence < 0:
				_signal_error = "signaling_sequence_unavailable"
			else:
				_pending_signals[sequence] = item.duplicate(true)
		else:
			item.retry_after_ms = now_ms + 250
			remaining.append(item)
	_signal_retry_queue = remaining


func _on_peer_state(state: Variant) -> void:
	var state_name := str(state)
	if state_name == "connected":
		_peer_channel_open = _peer_link_connected()
		if running and recovering and _peer_channel_open:
			_send_recovery_sync(Time.get_ticks_msec())
		return
	if running and state_name in ["disconnected", "failed", "closed"]:
		_peer_channel_open = false
		_begin_recovery("peer_" + state_name, Time.get_ticks_msec())


func _on_peer_error(code: String) -> void:
	if running:
		_begin_recovery("peer_transport_" + code, Time.get_ticks_msec())


func _on_room_error(_code: String) -> void:
	_room_service_available = false


func _peer_link_connected() -> bool:
	return peer_transport != null and peer_transport.has_method("peer_is_connected") and peer_transport.peer_is_connected() \
		and peer_transport.get_channel_state("reliable") == "open" and peer_transport.get_channel_state("input") == "open"
