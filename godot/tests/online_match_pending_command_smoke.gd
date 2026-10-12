extends SceneTree

const Coordinator := preload("res://online_match.gd")
const Lobby := preload("res://online_lobby.gd")

const ROOM_ID := "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"
const EPOCH := "3fa85f64-5717-4562-b3fc-2c963f66afa6"
const NEGOTIATION_ID := "550e8400-e29b-41d4-a716-446655440000"
const PROFILE := {"id": "chrome-exp-d2-p2-lan", "inputDelay": 2, "predictionWindow": 2}


class DeadlineCoordinator extends Coordinator:
	var deadlines := {}

	func _room_command(operation: Dictionary, deadline_ms: int) -> Dictionary:
		deadlines[str(operation.type)] = deadline_ms
		return await super._room_command(operation, deadline_ms)


class FakeRoom extends Node:
	var state: Dictionary = {}
	var pending_prepare := true
	var prepare_in_flight := false
	var applied_operations: Array[String] = []
	var attempted_operations: Array[String] = []
	var retried_operations: Array[String] = []
	var operation_order: Array[String] = []
	var terminal_after_loaded_reason := ""

	func get_slot() -> int:
		return 0

	func get_room_id() -> String:
		return ROOM_ID

	func get_room_state() -> Dictionary:
		return state.duplicate(true)

	func has_uncertain_command() -> bool:
		return pending_prepare

	func is_command_in_flight() -> bool:
		return prepare_in_flight

	func complete_prepare_http() -> void:
		pending_prepare = false
		prepare_in_flight = false
		applied_operations.append("prepare")
		operation_order.append("prepare_http_response")

	func refresh_state() -> Dictionary:
		return {"state": get_room_state()}

	func command(operation: Dictionary) -> Dictionary:
		var kind := str(operation.get("type", ""))
		attempted_operations.append(kind)
		operation_order.append("command:" + kind)
		if pending_prepare:
			return {"error": "command_outcome_uncertain", "uncertain": true}
		return _apply_operation(operation)

	func retry_pending_command() -> Dictionary:
		if pending_prepare:
			if prepare_in_flight:
				return {"error": "request_in_flight", "uncertain": false}
			retried_operations.append("prepare")
			operation_order.append("retry:prepare")
			pending_prepare = false
			applied_operations.append("prepare")
			return {"acceptedSeq": 5, "state": get_room_state()}
		return {"error": "no_pending_command", "uncertain": false}

	func _apply_operation(operation: Dictionary) -> Dictionary:
		var kind := str(operation.get("type", ""))
		applied_operations.append(kind)
		var match_state: Dictionary = state.match
		match str(kind):
			"loaded":
				if terminal_after_loaded_reason.is_empty():
					match_state.loaded = [str(operation.initialHash), str(operation.initialHash)]
					state.match = match_state
				else:
					state.phase = "lobby"
					state.lastResult = {"epoch": EPOCH, "winner": null, "reason": terminal_after_loaded_reason}
					state.match = null
			"start_ack":
				match_state.acknowledged = [true, true]
				state.match = match_state
				state.phase = "active"
			"negotiate":
				state.negotiation = {"id": NEGOTIATION_ID, "epoch": operation.epoch, "expires": 9_999_999_999}
			_:
				return {"error": "unsupported_test_operation", "uncertain": false}
		return {"acceptedSeq": applied_operations.size() + 5, "state": get_room_state()}

	func is_signaling_connected() -> bool:
		return true

	func connect_signaling() -> Dictionary:
		return {"state": get_room_state()}

	func get_ice_servers() -> Dictionary:
		return {"iceServers": []}


class FakeTransport extends Node:
	signal peer_message(channel: String, type: String, payload: Dictionary, sequence: int)
	signal peer_state_changed(state: String)
	signal outgoing_signal(kind: String, epoch: Variant, negotiation_id: String, payload: String)
	signal transport_error(code: String)

	var sent: Array[String] = []
	var connected := true
	var connection_predicate_checks := 0

	func configure(_room_id: String, _epoch: Variant, _local_slot: int, _remote_slot: int, _negotiation_id: String) -> bool:
		return true

	func create_peer(_ice_servers: Array) -> bool:
		return true

	func begin_offer() -> bool:
		return true

	func get_channel_state(_channel: String) -> String:
		return "open"

	func peer_is_connected() -> bool:
		connection_predicate_checks += 1
		return connected

	func send_peer_message(channel: String, type: String, payload: Dictionary) -> bool:
		sent.append(type)
		if type == "match_ready":
			peer_message.emit(channel, type, payload.duplicate(true), sent.size())
		return true

	func close_peer() -> void:
		pass


var _start_done := false
var _start_error := ""
var _started_count := 0
var _visibility_events: Array[bool] = []
var _failures: Array[String] = []


func _initialize() -> void:
	call_deferred("_run")


func _run() -> void:
	await _run_pending_command_case(false)
	await _run_pending_command_case(true)
	await _run_peer_connection_barrier_case()
	await _run_terminal_barrier_case()
	if _failures.is_empty():
		print("ONLINE_MATCH_STARTUP_BARRIERS_OK prior_prepare_drained=true inflight_prepare_waited=true loaded_sent=true start_ack_sent=true peer_connection_barrier=true terminal_reason=start_timeout abort_not_resubmitted=true")
		quit(0)
	else:
		quit(1)


func _run_pending_command_case(prepare_is_in_flight: bool) -> void:
	var room_state := _room_state()
	var lobby: OnlineLobby = Lobby.new()
	root.add_child(lobby)
	await process_frame
	var game: Node = load("res://main.tscn").instantiate()
	root.add_child(game)
	game.set_process(false)
	game.set_physics_process(false)
	await process_frame
	lobby.configure(null, game)
	var setup_error: String = lobby._configure_live_game(room_state)
	if not setup_error.is_empty():
		_fail("Could not configure production Main: " + setup_error)
		quit(1)
		return

	var room := FakeRoom.new()
	room.state = room_state.duplicate(true)
	room.prepare_in_flight = prepare_is_in_flight
	root.add_child(room)
	var transport := FakeTransport.new()
	root.add_child(transport)
	var coordinator := DeadlineCoordinator.new()
	var configure_error: String = coordinator.configure(game, _setup(room_state), "p1", room, transport)
	if not configure_error.is_empty():
		_fail("Could not configure coordinator: " + configure_error)
		quit(1)
		return
	if not prepare_is_in_flight:
		_visibility_events.clear()
		coordinator.page_visibility_changed.connect(_on_page_visibility_changed)
		coordinator._startup_context_eligible = true
		game.diagnostics.visibility_changed.emit(false)
		if coordinator._startup_timeout_context("Room start acknowledgement timed out").find("本页在开局期间进入过后台") < 0:
			_fail("Hidden-page startup timeout did not include its visibility context")
		if coordinator._startup_timeout_context("Peer initial causal state differs").find("本页在开局期间进入过后台") >= 0:
			_fail("A non-timeout startup failure was incorrectly attributed to page visibility")
		game.diagnostics.visibility_changed.emit(true)
		if _visibility_events != [false, true]:
			_fail("Coordinator did not forward Main visibility changes: " + str(_visibility_events))
	coordinator.started.connect(_on_started)
	_start_done = false
	_start_error = ""
	_started_count = 0
	_start_coordinator.call_deferred(coordinator)
	if prepare_is_in_flight:
		await create_timer(0.1).timeout
		if not room.attempted_operations.is_empty():
			_fail("Coordinator sent a second operation before the in-flight prepare response")
		room.complete_prepare_http()
	await create_timer(0.75).timeout
	if not _start_done:
		_fail("Coordinator startup did not finish after draining the previous command; in_flight=" + str(prepare_is_in_flight))
	if not _start_error.is_empty():
		_fail("Coordinator startup failed after draining the previous command: " + _start_error + "; in_flight=" + str(prepare_is_in_flight))
	var expected_first := "prepare_http_response" if prepare_is_in_flight else "retry:prepare"
	if room.operation_order.size() < 4 or room.operation_order[0] != expected_first or room.operation_order[1] != "command:loaded" or room.operation_order[2] != "command:start_ack":
		_fail("The pending prepare was not drained before the new loaded/start_ack commands: " + str(room.operation_order))
	if room.applied_operations != ["prepare", "loaded", "start_ack", "negotiate"]:
		_fail("Room applied the wrong startup operation sequence: " + str(room.applied_operations) + "; in_flight=" + str(prepare_is_in_flight))
	if _started_count != 1:
		_fail("Coordinator did not emit started after the actual loaded and start_ack commands; in_flight=" + str(prepare_is_in_flight))
	for operation in ["loaded", "start_ack", "negotiate"]:
		if int(coordinator.deadlines.get(operation, 0)) - Time.get_ticks_msec() < 60_000:
			_fail("Startup operation ignored the Worker's extended preparation deadline: " + operation)
	var visibility_count_before_close := _visibility_events.size()
	coordinator.close("test_cleanup")
	if not prepare_is_in_flight:
		game.diagnostics.visibility_changed.emit(false)
		if _visibility_events.size() != visibility_count_before_close:
			_fail("Coordinator retained its Main visibility dependency after close")
		if _failures.is_empty():
			print("ONLINE_MATCH_STARTUP_VISIBILITY_OK signal_forwarded=true timeout_context_only=true disconnect_on_close=true")
	for node in game.find_children("*", "AudioStreamPlayer", true, false):
		var player := node as AudioStreamPlayer
		player.stop()
		player.stream = null
	room.queue_free()
	transport.queue_free()
	lobby.queue_free()
	game.queue_free()
	await process_frame


func _start_coordinator(coordinator: OnlineMatchCoordinator) -> void:
	_start_error = await coordinator.start(EPOCH, PROFILE, "p1")
	_start_done = true


func _on_started() -> void:
	_started_count += 1


func _on_page_visibility_changed(visible: bool) -> void:
	_visibility_events.append(visible)


func _run_terminal_barrier_case() -> void:
	var room_state := _room_state()
	var lobby: OnlineLobby = Lobby.new()
	root.add_child(lobby)
	await process_frame
	var game: Node = load("res://main.tscn").instantiate()
	root.add_child(game)
	game.set_process(false)
	game.set_physics_process(false)
	await process_frame
	lobby.configure(null, game)
	var setup_error: String = lobby._configure_live_game(room_state)
	if not setup_error.is_empty():
		_fail("Could not configure production Main for startup terminal case: " + setup_error)
		return
	var room := FakeRoom.new()
	room.state = room_state.duplicate(true)
	room.pending_prepare = false
	room.terminal_after_loaded_reason = "start_timeout"
	root.add_child(room)
	var transport := FakeTransport.new()
	root.add_child(transport)
	var coordinator := DeadlineCoordinator.new()
	var configure_error: String = coordinator.configure(game, _setup(room_state), "p1", room, transport)
	if not configure_error.is_empty():
		_fail("Could not configure coordinator for startup terminal case: " + configure_error)
		return
	_start_done = false
	_start_error = ""
	_started_count = 0
	var started_at := Time.get_ticks_msec()
	_start_coordinator.call_deferred(coordinator)
	for _frame in 60:
		if _start_done:
			break
		await process_frame
	if not _start_done:
		_fail("Coordinator did not leave the loaded barrier after the service ended the epoch")
	if not _start_error.contains("start_timeout"):
		_fail("Coordinator did not report the service terminal reason: " + _start_error)
	if room.attempted_operations.has("abort"):
		_fail("Coordinator submitted a stale-epoch abort after the service had ended startup")
	if _started_count != 0 or Time.get_ticks_msec() - started_at >= 1_000:
		_fail("Terminal startup did not settle promptly without emitting started")
	coordinator.close("test_cleanup")
	for node in game.find_children("*", "AudioStreamPlayer", true, false):
		var player := node as AudioStreamPlayer
		player.stop()
		player.stream = null
	room.queue_free()
	transport.queue_free()
	lobby.queue_free()
	game.queue_free()
	await process_frame


func _run_peer_connection_barrier_case() -> void:
	var room_state := _room_state()
	var lobby: OnlineLobby = Lobby.new()
	root.add_child(lobby)
	await process_frame
	var game: Node = load("res://main.tscn").instantiate()
	root.add_child(game)
	game.set_process(false)
	game.set_physics_process(false)
	await process_frame
	lobby.configure(null, game)
	var setup_error: String = lobby._configure_live_game(room_state)
	if not setup_error.is_empty():
		_fail("Could not configure production Main for peer connection case: " + setup_error)
		return
	var room := FakeRoom.new()
	room.state = room_state.duplicate(true)
	room.pending_prepare = false
	root.add_child(room)
	var transport := FakeTransport.new()
	transport.connected = false
	root.add_child(transport)
	var coordinator := DeadlineCoordinator.new()
	var configure_error: String = coordinator.configure(game, _setup(room_state), "p1", room, transport)
	if not configure_error.is_empty():
		_fail("Could not configure coordinator for peer connection case: " + configure_error)
		return
	coordinator.started.connect(_on_started)
	_start_done = false
	_start_error = ""
	_started_count = 0
	_start_coordinator.call_deferred(coordinator)
	var deadline := Time.get_ticks_msec() + 2_000
	while transport.connection_predicate_checks == 0 and Time.get_ticks_msec() < deadline:
		await process_frame
	if transport.connection_predicate_checks == 0:
		_fail("Coordinator did not verify the complete peer connection predicate")
	elif transport.sent.has("match_ready") or _start_done:
		_fail("Coordinator sent peer-ready before the peer connection state reached connected")
	transport.connected = true
	await create_timer(0.75).timeout
	if not _start_done or not _start_error.is_empty() or _started_count != 1:
		_fail("Coordinator did not continue after peer connectivity completed: " + str({
			"start_error": _start_error,
			"coordinator_error": coordinator.error,
			"done": _start_done,
			"started": _started_count,
			"peer_ready": coordinator._peer_ready,
			"channel_open": coordinator._peer_channel_open,
			"connected": transport.connected,
			"checks": transport.connection_predicate_checks,
			"sent": transport.sent,
			"operations": room.applied_operations,
		}))
	coordinator.close("test_cleanup")
	for node in game.find_children("*", "AudioStreamPlayer", true, false):
		var player := node as AudioStreamPlayer
		player.stop()
		player.stream = null
	room.queue_free()
	transport.queue_free()
	lobby.queue_free()
	game.queue_free()
	await process_frame


func _setup(state: Dictionary) -> Dictionary:
	return {
		"members": state.members.duplicate(true),
		"stage": state.stage,
		"rules": state.rules.duplicate(true),
		"profile": state.match.profile.duplicate(true),
		"seed": state.match.seed,
		"clockBaseline": state.match.clockBaseline,
		"setupRevision": state.setupRevision,
	}


func _room_state() -> Dictionary:
	var profile := PROFILE.duplicate(true)
	return {
		"schema": 1,
		"id": ROOM_ID,
		"compatibility": {"protocol": 1, "build": "b".repeat(64), "content": "c".repeat(64)},
		"revision": 5,
		"setupRevision": 2,
		"members": [
			{"nickname": "Host", "choice": {"fighter": "minren", "helper": "woailuo"}, "ready": true, "profile": profile.duplicate(true), "seq": 5},
			{"nickname": "Guest", "choice": {"fighter": "yihu", "helper": "kon"}, "ready": true, "profile": profile.duplicate(true), "seq": 3},
		],
		"stage": "现世",
		"rules": {"time": 90, "life": 1},
		"networkProfile": {"id": "chrome-exp-d2-p6", "inputDelay": 2, "predictionWindow": 6},
		"phase": "preparing",
		"match": {
			"epoch": EPOCH,
			"seed": 271828,
			"clockBaseline": 0,
			"profile": profile.duplicate(true),
			"deadline": int(Time.get_unix_time_from_system() * 1000) + 120_000,
			"loaded": [null, null],
			"acknowledged": [false, false],
			"results": [null, null],
		},
		"lastResult": null,
		"negotiation": null,
		"lastActivity": 10,
		"leaseUntil": 9_999_999_999,
	}


func _fail(message: String) -> void:
	_failures.append(message)
	push_error("ONLINE_MATCH_PENDING_COMMAND_FAILED " + message)
