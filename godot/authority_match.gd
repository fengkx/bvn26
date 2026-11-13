extends "res://online_match.gd"

# Inherit room command settlement, signaling, cancellation and terminal barriers.
# Simulation, input consumption, presentation and recovery have no rollback path.
const HostSelection = preload("res://authority_host_selection.gd")
const HostProbe = preload("res://authority_probe.gd")
const InputQueue = preload("res://authority_input_queue.gd")
const DisplayProjection = preload("res://authority_projection.gd")
const Wire = preload("res://authority_wire.gd")
const SAFETY_STALL_MS := 1000
const SAFETY_ABORT_MS := 10000
const INITIAL_STATE_RETRY_MS := 1000
# Reserve room for one loss-recovery probe below the 64 KiB receive buffer.
const MAX_UNACKED_STATES := 2
var scene_factory: Callable
var authority_slot := -1
var _probe := HostProbe.new()
var _reports := {}
var _selection_ack := -1
var _projector := DisplayProjection.new()
var _inputs := InputQueue.new()
var _initial := {}
var _initial_hash := ""
var _initial_ack := false
var _display_ready := false
var _pending_display := {}
var _latest_display := {}
var _state_serial := 0
var _received_serial := 0
var _ack_serial := 0
var _ack_progress_ms := 0
var _input_sequence := 0
var _last_state_ms := 0
var _last_send_ms := 0
var _last_heartbeat_ms := 0
var _ping_sequence := 0
var _pending_pings := {}
var _rtt_samples: Array[int] = []
var _peer_visible := true
var _safety_id := 0
var _safety_ack := -1
var _safety_started := -1
var _skip_requested := false
var _terminal_result := {}
var _last_snapshot_hash := ""

func configure(scene: Node, room_setup: Dictionary, player_slot: String, room: Object, transport: Object) -> String:
	if _configured or player_slot not in ["p1", "p2"] or not scene_factory.is_valid(): return "invalid_authority_configuration"
	setup = _normalize_setup(room_setup)
	if not _valid_setup(setup) or setup.get("mode") != "host-authoritative": return "invalid_authority_setup"
	game = scene
	local_slot = player_slot
	remote_slot = "p2" if local_slot == "p1" else "p1"
	room_client = room
	peer_transport = transport
	peer_transport.enable_state_channel = true
	_configured = true
	_connect_dependencies()
	return ""

func _is_host() -> bool:
	return authority_slot == (0 if local_slot == "p1" else 1)

func start(match_epoch: String, agreed_profile: Dictionary, _authority: String = "p1") -> String:
	if not _configured or _startup_active or not _valid_epoch(match_epoch): return "invalid_authority_start"
	epoch = match_epoch
	profile = _normalize_profile(agreed_profile)
	if profile.is_empty() or profile != setup.profile: return "authority_profile_mismatch"
	_startup_active = true
	_startup_context_eligible = true
	var generation := _generation
	var problem := await _start_authority(generation)
	if not problem.is_empty() and not _startup_cancelled(generation):
		problem = await _abort_start_for_generation(generation, "authority_start", {"error": problem})
	_startup_active = false
	_startup_context_eligible = false
	return problem

func _replace_scene(role: String) -> String:
	_disconnect_dependencies()
	var value: Dictionary = scene_factory.call(role)
	if value.has("error"): return str(value.error)
	game = value.game
	_connect_dependencies()
	return ""

func _start_authority(generation: int) -> String:
	var state := await _refresh_room_state()
	if _startup_cancelled(generation): return "match_closed"
	if state.get("mode") != "host-authoritative" or not state.get("match") is Dictionary or state.match.get("epoch") != epoch: return "authority_mode_barrier"
	var problem := await _open_peer_transport(generation)
	if not problem.is_empty(): return problem
	problem = _replace_scene("probe")
	if not problem.is_empty(): return problem
	var report := await _run_probe()
	if _startup_cancelled(generation): return "match_closed"
	_reports[local_slot] = report
	if not _send_peer("authority_probe", {"epoch": epoch, "report": report}): return "authority_probe_send"
	problem = await _wait_until(func() -> bool: return _reports.has(remote_slot), generation)
	if not problem.is_empty(): return problem
	authority_slot = HostSelection.choose(_reports.get("p1"), _reports.get("p2"))
	if authority_slot < 0: return "no_eligible_authority"
	clock_authority_slot = "p1" if authority_slot == 0 else "p2"
	if not _send_peer("authority_selection", {"epoch": epoch, "slot": authority_slot}): return "authority_selection_send"
	problem = await _wait_until(func() -> bool: return _selection_ack >= 0, generation)
	if not problem.is_empty(): return problem
	if _selection_ack != authority_slot: return "authority_selection_disagreed"
	var reply := await _room_command({"type": "authority_ack", "epoch": epoch, "authoritySlot": authority_slot}, _startup_deadline_ms())
	if not _command_accepted(reply): return "authority_room_ack"
	while not _startup_cancelled(generation):
		state = await _refresh_room_state()
		if state.get("match") is Dictionary and state.match.get("authoritySlot") == authority_slot: break
		if Time.get_ticks_msec() >= _startup_deadline_ms(): return "authority_room_barrier_timeout"
		await room_client.get_tree().create_timer(0.05).timeout
	if _startup_cancelled(generation): return "match_closed"
	problem = _replace_scene("host" if _is_host() else "guest")
	if not problem.is_empty(): return problem
	if _is_host():
		battle = Battle.new()
		problem = battle.configure(game, false)
		if not problem.is_empty(): return problem
		timers = TimerAuthority.new()
		problem = timers.configure(game, 0)
		if not problem.is_empty(): return problem
		battle.set_event_supplier(timers.events_for_phase)
		game.combo_hud.set_presentation_enabled(false)
		game.set_meta("authority_projector", _projector)
		game.set_meta("authority_audio", _projector.audio)
		game.stage_sound.start()
		_initial = _projector.capture(game)
		if not _projector.error.is_empty(): return _projector.error
		_initial_hash = _display_hash(_initial)
	else:
		_projector.configure_presenter(game)
		if not _send_peer("authority_display_ready", {"epoch": epoch}): return "authority_display_ready_send"
	problem = await _wait_until(func() -> bool: return _initial_ack, generation, true)
	if not problem.is_empty(): return problem
	reply = await _room_command({"type": "loaded", "epoch": epoch, "initialHash": _initial_hash}, _startup_deadline_ms())
	if not _command_accepted(reply): return "authority_loaded"
	problem = await _wait_for_loaded_barrier(_initial_hash, generation)
	if not problem.is_empty(): return problem
	reply = await _room_command({"type": "start_ack", "epoch": epoch}, _startup_deadline_ms())
	if not _command_accepted(reply): return "authority_start_ack"
	problem = await _wait_for_active_barrier(generation)
	if not problem.is_empty(): return problem
	_send_peer("authority_ready", {"epoch": epoch, "hash": _initial_hash})
	problem = await _wait_until(func() -> bool: return _peer_ready, generation)
	if not problem.is_empty(): return problem
	running = true
	_last_state_ms = Time.get_ticks_msec()
	_last_heartbeat_received_ms = _last_state_ms
	_ack_progress_ms = _last_state_ms
	_inputs.last_received_ms = _last_state_ms
	started.emit()
	return ""

func _wait_until(predicate: Callable, generation: int, initial: bool = false) -> String:
	var deadline := _startup_deadline_ms()
	var client := room_client
	while Time.get_ticks_msec() < deadline:
		if _startup_cancelled(generation): return "match_closed"
		if not error.is_empty(): return error
		# Resource loading can outlast several poll intervals on the other peer.
		# Do not fill its bounded receive buffer with the same initial snapshot.
		if initial and _is_host() and _display_ready and not _initial_ack \
			and (_last_send_ms == 0 or Time.get_ticks_msec() - _last_send_ms >= INITIAL_STATE_RETRY_MS):
			_send_display(_initial, true)
		if predicate.call(): return ""
		await client.get_tree().create_timer(0.05).timeout
	return "authority_startup_timeout"

func _display_hash(snapshot: Dictionary) -> String:
	var choices := []
	for member in setup.members: choices.append(member.choice)
	return Wire.digest(State.canonical({"mode": "host-authoritative", "epoch": epoch, "authoritySlot": authority_slot,
		"schema": Wire.VERSION, "setupRevision": setup.setupRevision, "choices": choices, "rules": setup.rules,
		"stage": setup.stage, "seed": setup.seed, "profile": setup.profile,
		"compatibility": _room_state.get("compatibility", {}), "display": snapshot}))

func _run_probe() -> Dictionary:
	return await _probe.run(game, _visible)

func _visible() -> bool:
	return bool(JavaScriptBridge.eval("document.visibilityState === 'visible'")) if OS.has_feature("web") else page_visible

func _send_display(snapshot: Dictionary, initial: bool = false) -> void:
	# Browser bufferedAmount only measures the sender, not a busy guest receiver.
	# Keep simulating, but replace unsent display states with the freshest one.
	if not initial and _state_serial - _ack_serial >= MAX_UNACKED_STATES:
		var now := Time.get_ticks_msec()
		# Unreliable packets may all be lost. A fresh heartbeat proves the guest
		# is processing again; send one probe per second, never a catch-up burst.
		if now - _last_send_ms < SAFETY_STALL_MS or now - _last_heartbeat_received_ms > 250: return
	_state_serial += 1
	_last_snapshot_hash = _display_hash(snapshot)
	peer_transport.send_peer_message("state", "authority_state", {"epoch": epoch, "authority": authority_slot,
		"serial": _state_serial, "initial": initial, "hash": _last_snapshot_hash,
		"safety": _safety_id, "paused": paused, "inputAck": _inputs.consumed_sequence, "display": snapshot})
	_last_send_ms = Time.get_ticks_msec()

func receive_peer_message(channel: String, type: String, payload: Dictionary, _sequence: int) -> void:
	if not error.is_empty() or payload.get("epoch") != epoch: return
	var now := Time.get_ticks_msec()
	if channel == "state":
		if _is_host() or type != "authority_state":
			_abort_local("authority_state_sender", {})
			return
		if not payload.get("serial") is int or payload.serial <= _received_serial: return
		if payload.get("authority") != authority_slot or not payload.get("display") is Dictionary or not payload.get("initial") is bool or not payload.get("paused") is bool or not payload.get("safety") is int or not payload.get("inputAck") is int or payload.inputAck < 0 or payload.inputAck > _input_sequence or not _is_digest(str(payload.get("hash", ""))):
			_abort_local("authority_state_envelope", {})
			return
		_pending_display = payload
		return
	if channel == "input":
		if not running or not _is_host() or type != "authority_input": return
		var sequence: Variant = _wire_integer(payload.get("sample"), 1, 2147483647)
		if sequence == null or not payload.get("held") is Dictionary:
			_abort_local("authority_input_schema", {})
			return
		var problem := _inputs.receive(sequence, payload.held, now)
		if not problem.is_empty(): _abort_local(problem, {})
		return
	if channel != "reliable": return
	match type:
		"authority_probe":
			var report: Dictionary = payload.get("report", {}) if payload.get("report") is Dictionary else {}
			for key in ["samples", "p95_us", "long_stalls"]:
				if report.has(key): report[key] = _wire_integer(report[key], 0, 2147483647)
			if _reports.has(remote_slot) and _reports[remote_slot] != report: _abort_local("conflicting_authority_probe", {})
			else: _reports[remote_slot] = report
		"authority_selection":
			var slot: Variant = _wire_integer(payload.get("slot"), 0, 1)
			if slot == null or (_selection_ack >= 0 and _selection_ack != slot): _abort_local("invalid_authority_selection", {})
			else: _selection_ack = slot
		"authority_display_ready":
			if not _is_host(): _abort_local("authority_display_ready_sender", {})
			else: _display_ready = true
		"authority_initial_ack":
			if not _is_host() or payload.get("hash") != _initial_hash: _abort_local("authority_initial_hash", {})
			else: _initial_ack = true
		"authority_ready":
			if payload.get("hash") != _initial_hash: _abort_local("authority_ready_hash", {})
			else: _peer_ready = true
		"authority_heartbeat":
			if not payload.get("visible") is bool: return
			var ping: Variant = _wire_integer(payload.get("ping"), 1, 2147483647)
			if ping == null: return
			_send_peer("authority_pong", {"epoch": epoch, "ping": ping})
			_peer_visible = payload.visible
			_last_heartbeat_received_ms = now
			var serial: Variant = _wire_integer(payload.get("serial"), 0, _state_serial if _is_host() else 2147483647)
			if serial != null and serial > _ack_serial:
				_ack_serial = serial
				_ack_progress_ms = now
		"authority_state_ack":
			if not _is_host(): return
			var serial: Variant = _wire_integer(payload.get("serial"), 1, _state_serial)
			if serial != null and serial > _ack_serial:
				_ack_serial = serial
				_ack_progress_ms = now
		"authority_pong":
			var ping: Variant = _wire_integer(payload.get("ping"), 1, 2147483647)
			if ping != null and _pending_pings.has(ping):
				_rtt_samples.append(maxi(0, now - int(_pending_pings[ping])))
				_pending_pings.erase(ping)
				if _rtt_samples.size() > 300: _rtt_samples.pop_front()
		"authority_safety_ack":
			if _is_host() and paused and payload.get("id") == _safety_id and payload.get("hash") == _last_snapshot_hash: _safety_ack = _safety_id
		"authority_resume":
			if not _is_host() and payload.get("id") == _safety_id:
				paused = false
				recovering = false
				_safety_started = -1
				recovery_changed.emit("resumed")
		"authority_skip":
			if _is_host() and running: _skip_requested = true
		"authority_result_receipt":
			if _is_host() and not _terminal_result.is_empty() and payload.get("hash") == _terminal_result.hash and payload.get("frame") == _terminal_result.frame: _finish_authority_result()
		"match_abort": _abort_local("peer_abort", payload, false)
		_: _abort_local("authority_peer_protocol", {"type": type})

func _on_transport_message_drain_started() -> void:
	pass

func _on_transport_message_drain_completed(_count: int) -> void:
	if _pending_display.is_empty() or game == null or not game.presentation_only: return
	var packet := _pending_display
	_pending_display = {}
	if packet.hash != _display_hash(packet.display):
		_abort_local("authority_display_hash", {})
		return
	if not _initial_ack or not packet.initial:
		var problem := _projector.apply(packet.display)
		if not problem.is_empty():
			_abort_local(problem, {})
			return
	_latest_display = packet.display
	_received_serial = packet.serial
	_send_peer("authority_state_ack", {"epoch": epoch, "serial": _received_serial})
	_last_state_ms = Time.get_ticks_msec()
	if packet.initial:
		_initial = packet.display
		_initial_hash = packet.hash
		_initial_ack = true
		_send_peer("authority_initial_ack", {"epoch": epoch, "hash": _initial_hash})
		return
	if packet.paused:
		paused = true
		recovering = true
		_safety_id = packet.safety
		if _safety_started < 0: _safety_started = Time.get_ticks_msec()
		_send_peer("authority_safety_ack", {"epoch": epoch, "id": _safety_id, "hash": packet.hash})
		recovery_changed.emit("paused")
	elif paused:
		# Reliable resume and unordered snapshots can cross. The latest state wins.
		paused = false
		recovering = false
		_safety_started = -1
		recovery_changed.emit("resumed")
	if packet.display.terminal and _terminal_result.is_empty():
		_terminal_result = {"epoch": epoch, "frame": packet.display.frame, "winner": packet.display.winner, "hash": packet.hash}
		_send_peer("authority_result_receipt", _terminal_result)
		_finish_authority_result()

func process_tick(now_ms: int, local_held: Dictionary) -> String:
	if not running: return "match_finished" if not _terminal_result.is_empty() else "waiting_for_start"
	if not error.is_empty(): return error
	page_visible = _visible()
	if now_ms - _last_heartbeat_ms >= 100:
		_ping_sequence += 1
		_pending_pings[_ping_sequence] = now_ms
		for old in _pending_pings.keys():
			if old < _ping_sequence - 64: _pending_pings.erase(old)
		_send_peer("authority_heartbeat", {"epoch": epoch, "visible": page_visible, "serial": _received_serial, "ping": _ping_sequence})
		_last_heartbeat_ms = now_ms
	_flush_pending_signals(now_ms)
	_flush_pending_peer_messages(now_ms)
	if not _is_host():
		_input_sequence += 1
		peer_transport.send_peer_message("input", "authority_input", {"epoch": epoch, "sample": _input_sequence,
			"held": InputQueue.neutral() if not page_visible or paused else local_held})
		if now_ms - _last_state_ms > SAFETY_STALL_MS: _begin_recovery("state_stall", now_ms)
		_check_authority_deadline(now_ms)
		return ""
	var stalled := not page_visible or not _peer_visible or now_ms - _last_heartbeat_received_ms > SAFETY_STALL_MS or now_ms - _inputs.last_received_ms > SAFETY_STALL_MS or now_ms - _ack_progress_ms > SAFETY_STALL_MS
	if stalled: _begin_recovery("authority_stall", now_ms)
	if paused:
		_check_authority_deadline(now_ms)
		if not stalled and _safety_ack == _safety_id:
			_inputs.reset()
			_inputs.last_received_ms = now_ms
			paused = false
			recovering = false
			_safety_started = -1
			_send_peer("authority_resume", {"epoch": epoch, "id": _safety_id})
			recovery_changed.emit("resumed")
		else:
			if now_ms - _last_send_ms >= 100: _send_display(_latest_display)
			return ""
	if not _terminal_result.is_empty():
		if now_ms - _last_send_ms >= 100: _send_display(_latest_display)
		return ""
	var frame: int = game.physics_tick + 1
	var elapsed := frame * 1000 / 30
	timers.set_time(elapsed)
	battle.set_frame_clock(frame, elapsed)
	if _skip_requested:
		battle.set_intro_skip(frame)
		_skip_requested = false
	var players := {local_slot: local_held, remote_slot: _inputs.consume(now_ms)}
	var problem: String = battle.advance(frame, players)
	if not problem.is_empty(): return _abort_local(problem, {})
	timers.finish_frame()
	if not timers.error.is_empty(): return _abort_local(timers.error, {})
	_latest_display = _projector.capture(game)
	if not _projector.error.is_empty(): return _abort_local(_projector.error, {})
	if _latest_display.terminal:
		_terminal_result = {"epoch": epoch, "frame": frame, "winner": _latest_display.winner, "hash": _display_hash(_latest_display)}
	_send_display(_latest_display)
	return ""

func _begin_recovery(_reason: String, now_ms: int) -> void:
	if not running or paused: return
	paused = true
	recovering = true
	_safety_started = now_ms
	_safety_id += 1
	_safety_ack = -1
	_inputs.reset()
	if _is_host():
		if _latest_display.is_empty(): _latest_display = _initial
		_send_display(_latest_display)
	recovery_changed.emit("paused")

func _check_authority_deadline(now_ms: int) -> void:
	if _safety_started >= 0 and now_ms - _safety_started >= SAFETY_ABORT_MS: _abort_local("authority_safety_timeout", {"winner": null})

func _on_peer_error(code: String) -> void:
	if _startup_active: error = code
	elif running: _begin_recovery(code, Time.get_ticks_msec())

func _on_peer_state(state: Variant) -> void:
	_peer_channel_open = str(state) == "connected" and _peer_link_connected()
	if running and not _peer_channel_open: _begin_recovery("connection_stall", Time.get_ticks_msec())

func _peer_link_connected() -> bool:
	return super._peer_link_connected() and peer_transport.get_channel_state("state") == "open"

func request_intro_skip() -> String:
	if not running: return "waiting_for_start"
	if _is_host(): _skip_requested = true
	else: _send_peer("authority_skip", {"epoch": epoch})
	return ""

func intro_skippable() -> bool:
	return bool(game.battle_intro.active and game.battle_intro.polling) if _is_host() else bool(_latest_display.get("intro_active", false) and _latest_display.get("intro_polling", false))

func request_pause() -> String:
	return "authority_voluntary_pause_unavailable"

func request_resume() -> String:
	return "authority_voluntary_pause_unavailable"

func _finish_authority_result() -> void:
	if _result_submission_started: return
	_result_submission_started = true
	running = false
	_submit_confirmed_result.call_deferred(_terminal_result.duplicate(true), _generation)
	result_confirmed.emit(_terminal_result.duplicate(true))

func _service_terminal_outcome(state: Dictionary) -> Dictionary:
	var result: Variant = state.get("lastResult")
	if state.get("phase") == "lobby" and result is Dictionary and result.get("epoch") == epoch and result.get("reason") == "host-declared/guest-received" and result.get("mode") == "host-authoritative" and result.get("authoritySlot") == authority_slot:
		return {"kind": "agreed", "winner": result.winner, "last_result": result}
	return super._service_terminal_outcome(state)

func performance_report() -> Dictionary:
	return {"mode": "host-authoritative", "authoritySlot": authority_slot, "probe": _reports.duplicate(true),
		"sentStates": _state_serial, "receivedStates": _received_serial, "expiredInputs": _inputs.expired,
		"applicationRttMs": _rtt_samples.duplicate(), "unansweredPings": _pending_pings.size(),
		"g0Passed": false, "weakMachineAccepted": false, "twoMachinePerformanceAccepted": false}

func close(reason: String = "") -> void:
	_probe.cancelled = true
	_generation += 1
	running = false
	_disconnect_dependencies()
	if peer_transport != null: peer_transport.close_peer()
	if battle != null: battle.close()
	battle = null
	timers = null
	_configured = false
	_pending_display.clear()
	room_client = null
	peer_transport = null
	game = null
	if not reason.is_empty(): error = reason
