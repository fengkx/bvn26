extends SceneTree

const Coordinator := preload("res://online_match.gd")
const Lobby := preload("res://online_lobby.gd")

const ROOM_ID := "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"
const EPOCH := "3fa85f64-5717-4562-b3fc-2c963f66afa6"
const NEGOTIATION_ID := "550e8400-e29b-41d4-a716-446655440000"
const PROFILE := {"id": "async-close-test", "inputDelay": 0, "predictionWindow": 2}


class FakeRoom extends Node:
	signal first_refresh_started
	signal release_first_refresh
	signal ice_lookup_started
	signal release_ice_lookup
	signal pending_command_wait_started

	var pending_prepare := false
	var prepare_in_flight := false
	var pending_wait_announced := false
	var pending_retry_count := 0
	var uncertain_abort_once := false
	var accept_abort_pending := false
	var pending_abort: Dictionary = {}
	var original_abort_body: Dictionary = {}
	var abort_retry_bodies: Array[Dictionary] = []

	var state: Dictionary = {}
	var block_first_refresh := false
	var block_ice_lookup := false
	var refresh_calls := 0
	var command_calls: Array[Dictionary] = []
	var abort_count := 0
	var abort_attempts := 0
	var fail_next_abort := false

	func get_slot() -> int:
		return 0

	func get_room_id() -> String:
		return ROOM_ID

	func get_room_state() -> Dictionary:
		return state.duplicate(true)

	func refresh_state() -> Dictionary:
		refresh_calls += 1
		if block_first_refresh and refresh_calls == 1:
			first_refresh_started.emit()
			await release_first_refresh
		return {"state": get_room_state()}

	func has_uncertain_command() -> bool:
		return pending_prepare or not pending_abort.is_empty()

	func is_command_in_flight() -> bool:
		if (prepare_in_flight or (not pending_abort.is_empty() and bool(pending_abort.get("in_flight", false)))) and not pending_wait_announced:
			pending_wait_announced = true
			pending_command_wait_started.emit()
		return prepare_in_flight or bool(pending_abort.get("in_flight", false))

	func retry_pending_command() -> Dictionary:
		if not pending_abort.is_empty():
			abort_retry_bodies.append(pending_abort.duplicate(true))
			if not accept_abort_pending:
				return {"error": "command_outcome_uncertain", "uncertain": true}
			var accepted_abort := pending_abort.duplicate(true)
			pending_abort.clear()
			abort_count += 1
			_abort_state()
			return {"acceptedSeq": int(accepted_abort.seq), "state": get_room_state()}
		if prepare_in_flight:
			return {"error": "request_in_flight", "uncertain": false}
		if not pending_prepare:
			return {"error": "no_pending_command", "uncertain": false}
		pending_prepare = false
		pending_retry_count += 1
		return {"acceptedSeq": pending_retry_count, "state": get_room_state()}

	func command(operation: Dictionary) -> Dictionary:
		command_calls.append(operation.duplicate(true))
		var match_state: Dictionary = state.match
		match str(operation.get("type", "")):
			"loaded":
				match_state.loaded = [operation.get("initialHash"), operation.get("initialHash")]
				state.match = match_state
			"start_ack":
				match_state.acknowledged = [true, true]
				state.match = match_state
				state.phase = "active"
			"negotiate":
				state.negotiation = {"id": NEGOTIATION_ID, "epoch": operation.get("epoch"), "expires": 9_999_999_999}
			"abort":
				abort_attempts += 1
				if fail_next_abort:
					fail_next_abort = false
					return {"error": "http_transport_failed", "uncertain": false}
				if uncertain_abort_once:
					uncertain_abort_once = false
					pending_abort = {"seq": 50_000 + abort_attempts, "operation": operation.duplicate(true), "in_flight": false}
					original_abort_body = pending_abort.duplicate(true)
					return {"error": "command_outcome_uncertain", "uncertain": true}
				abort_count += 1
				_abort_state()
			_:
				return {"error": "unsupported_test_command", "uncertain": false}
		return {"acceptedSeq": command_calls.size(), "state": get_room_state()}

	func _abort_state() -> void:
		state.phase = "lobby"
		state.lastResult = {"epoch": EPOCH, "winner": null, "reason": "aborted"}
		state.match = null

	func is_signaling_connected() -> bool:
		return true

	func get_ice_servers() -> Dictionary:
		if block_ice_lookup:
			ice_lookup_started.emit()
			await release_ice_lookup
		return {"iceServers": []}


class FakeTransport extends Node:
	signal peer_message(channel: String, type: String, payload: Dictionary, sequence: int)
	signal peer_state_changed(state: String)
	signal outgoing_signal(kind: String, epoch: Variant, negotiation_id: String, payload: String)
	signal transport_error(code: String)

	var configure_calls := 0
	var create_peer_calls := 0
	var offer_calls := 0
	var ready_messages := 0
	var close_calls := 0

	func configure(_room_id: String, _epoch: Variant, _local_slot: int, _remote_slot: int, _negotiation_id: String) -> bool:
		configure_calls += 1
		return true

	func create_peer(_ice_servers: Array) -> bool:
		create_peer_calls += 1
		return true

	func begin_offer() -> bool:
		offer_calls += 1
		return true

	func get_channel_state(_channel: String) -> String:
		return "open"

	func peer_is_connected() -> bool:
		return true

	func send_peer_message(channel: String, type: String, payload: Dictionary) -> bool:
		if type == "match_ready":
			ready_messages += 1
		return true

	func close_peer() -> void:
		close_calls += 1


var _start_completed := false
var _start_result := ""
var _started_count := 0
var _cancel_completed := false
var _cancel_result := ""
var _cancel_retry_result := ""
var _failures: Array[String] = []


func _initialize() -> void:
	call_deferred("_run")


func _run() -> void:
	for gate in ["initial_refresh", "ice_lookup"]:
		await _run_close_during_start(gate)
	await _run_cancel_while_prior_command_pending()
	await _run_cancel_startup_case(false, true)
	await _run_cancel_startup_case(false, false, true)
	await _run_cancel_startup_case(true, false)
	if _failures.is_empty():
		print("ONLINE_MATCH_START_CANCEL_OK close_during_refresh=true close_during_ice=true pending_command_settled_before_abort=true live_epoch_abort=true retry_after_unconfirmed_abort=true uncertain_abort_same_request=true terminal_epoch_no_abort=true no_peer_ready=true")
		quit(0)
	else:
		quit(1)


func _run_close_during_start(gate: String) -> bool:
	var lobby: OnlineLobby = Lobby.new()
	root.add_child(lobby)
	await process_frame
	var room_state := _room_state()
	lobby._accept_state(room_state)
	var game: Node = load("res://main.tscn").instantiate()
	root.add_child(game)
	game.set_process(false)
	game.set_physics_process(false)
	await process_frame
	lobby.configure(null, game)
	var setup_error: String = lobby._configure_live_game(room_state)
	if not setup_error.is_empty():
		_fail("Could not configure real Main for " + gate + ": " + setup_error)
		return false
	var room := FakeRoom.new()
	room.state = room_state.duplicate(true)
	room.block_first_refresh = gate == "initial_refresh"
	room.block_ice_lookup = gate == "ice_lookup"
	root.add_child(room)
	var transport := FakeTransport.new()
	root.add_child(transport)
	var coordinator: OnlineMatchCoordinator = Coordinator.new()
	var configure_error: String = coordinator.configure(game, _setup(room_state), "p1", room, transport)
	if not configure_error.is_empty():
		_fail("Could not configure coordinator for " + gate + ": " + configure_error)
		return false
	coordinator.started.connect(_on_started)
	_start_completed = false
	_start_result = ""
	_started_count = 0
	_start_coordinator.call_deferred(coordinator)
	if gate == "initial_refresh":
		await room.first_refresh_started
	else:
		await room.ice_lookup_started
	await process_frame
	coordinator.close("test_close")
	if gate == "initial_refresh":
		room.release_first_refresh.emit()
	else:
		room.release_ice_lookup.emit()
	for _frame in 4:
		await process_frame
	var case_ok := true
	if not _start_completed:
		_fail("Startup coroutine did not settle after close during " + gate)
		case_ok = false
	if _start_result != "Online match closed during startup":
		_fail("Closed startup returned an unsafe result during " + gate + ": " + _start_result)
		case_ok = false
	if room.abort_count != 0 or _started_count != 0:
		_fail("Closed startup submitted abort or emitted started during " + gate)
		case_ok = false
	if transport.configure_calls != 0 or transport.create_peer_calls != 0 or transport.offer_calls != 0 or transport.ready_messages != 0:
		_fail("Closed startup recreated peer or sent peer-ready during " + gate)
		case_ok = false
	for operation in room.command_calls:
		if operation.get("type") == "abort":
			_fail("Closed startup issued an abort service command during " + gate)
			case_ok = false
	var audio_nodes := game.find_children("*", "AudioStreamPlayer", true, false)
	for audio_node in audio_nodes:
		var player := audio_node as AudioStreamPlayer
		player.stop()
		player.stream = null
	lobby.room_client.clear_credentials()
	lobby.queue_free()
	game.queue_free()
	room.queue_free()
	transport.queue_free()
	await process_frame
	return case_ok


func _start_coordinator(coordinator: OnlineMatchCoordinator) -> void:
	_start_result = await coordinator.start(EPOCH, PROFILE, "p1")
	_start_completed = true


func _cancel_startup_coordinator(coordinator: OnlineMatchCoordinator) -> void:
	_cancel_result = await coordinator.cancel_startup()
	_cancel_completed = true


func _run_cancel_startup_case(service_already_ended: bool, fail_first_abort: bool, uncertain_abort: bool = false) -> void:
	var label := "terminal" if service_already_ended else "uncertain" if uncertain_abort else "live"
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
		_fail("Could not configure Main for " + label + " startup cancellation: " + setup_error)
		return
	var room := FakeRoom.new()
	room.state = room_state.duplicate(true)
	room.block_ice_lookup = true
	room.fail_next_abort = fail_first_abort
	room.uncertain_abort_once = uncertain_abort
	root.add_child(room)
	var transport := FakeTransport.new()
	root.add_child(transport)
	var coordinator: OnlineMatchCoordinator = Coordinator.new()
	var configure_error: String = coordinator.configure(game, _setup(room_state), "p1", room, transport)
	if not configure_error.is_empty():
		_fail("Could not configure coordinator for " + label + " startup cancellation: " + configure_error)
		return
	_started_count = 0
	_start_completed = false
	_start_result = ""
	_cancel_completed = false
	_cancel_result = ""
	_start_coordinator.call_deferred(coordinator)
	await room.ice_lookup_started
	_cancel_startup_coordinator.call_deferred(coordinator)
	for _frame in 20:
		if coordinator._startup_cancel_requested:
			break
		await process_frame
	if not coordinator._startup_cancel_requested:
		_fail("Cancellation request was not registered during " + label + " startup")
	if service_already_ended:
		room.state.phase = "lobby"
		room.state.lastResult = {"epoch": EPOCH, "winner": null, "reason": "start_timeout"}
		room.state.match = null
	room.release_ice_lookup.emit()
	if uncertain_abort:
		await create_timer(22.0).timeout
	else:
		for _frame in 120:
			if _start_completed and _cancel_completed:
				break
			await process_frame
	if not _start_completed or not _cancel_completed:
		_fail("Startup cancellation did not settle for " + label)
	if _start_result != "Online match closed during startup":
		_fail("Startup did not stop cleanly after cancellation for " + label + ": " + _start_result)
	if _started_count != 0 or transport.configure_calls != 0 or transport.create_peer_calls != 0 or transport.offer_calls != 0 or transport.ready_messages != 0:
		_fail("Cancelled startup established or announced a peer for " + label)
	if service_already_ended:
		if not _cancel_result.is_empty() or room.abort_count != 0 or room.abort_attempts != 0:
			_fail("Terminal epoch was aborted or reported uncertain during cancellation: " + _cancel_result)
	elif uncertain_abort:
		if _cancel_result.find("not be confirmed") < 0 or room.abort_attempts != 1 or room.abort_count != 0:
			_fail("Uncertain abort was incorrectly reported or retried as a new command: %s attempts=%d accepted=%d" % [_cancel_result, room.abort_attempts, room.abort_count])
		if room.pending_abort.is_empty() or room.original_abort_body.is_empty():
			_fail("Uncertain abort did not retain its exact pending request")
		room.accept_abort_pending = true
		_cancel_completed = false
		_cancel_retry_result = ""
		_cancel_retry_task.call_deferred(coordinator)
		for _frame in 120:
			if _cancel_completed:
				break
			await process_frame
		if not _cancel_completed or not _cancel_retry_result.is_empty() or room.abort_attempts != 1 or room.abort_count != 1:
			_fail("Retry did not settle the existing uncertain abort without sending a second command: result=%s attempts=%d accepted=%d" % [_cancel_retry_result, room.abort_attempts, room.abort_count])
		for retry_body in room.abort_retry_bodies:
			if retry_body != room.original_abort_body:
				_fail("Uncertain abort retry changed the original sequence or body")
	elif not service_already_ended:
		if _cancel_result.find("not be confirmed") < 0:
			_fail("Failed abort attempt was incorrectly reported as settled: " + _cancel_result)
		_cancel_completed = false
		_cancel_retry_result = ""
		_cancel_retry_task.call_deferred(coordinator)
		for _frame in 120:
			if _cancel_completed:
				break
			await process_frame
		if not _cancel_completed or not _cancel_retry_result.is_empty() or room.abort_count != 1 or room.abort_attempts != 2:
			_fail("Cancellation retry did not settle the live epoch: result=%s attempts=%d accepted=%d" % [_cancel_retry_result, room.abort_attempts, room.abort_count])
	coordinator.close("test_cleanup")
	for audio_node in game.find_children("*", "AudioStreamPlayer", true, false):
		var player := audio_node as AudioStreamPlayer
		player.stop()
		player.stream = null
	lobby.room_client.clear_credentials()
	lobby.queue_free()
	game.queue_free()
	room.queue_free()
	transport.queue_free()
	await process_frame


func _cancel_retry_task(coordinator: OnlineMatchCoordinator) -> void:
	_cancel_retry_result = await coordinator.cancel_startup()
	_cancel_completed = true


func _run_cancel_while_prior_command_pending() -> void:
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
		_fail("Could not configure Main for pending-command cancellation: " + setup_error)
		return
	var room := FakeRoom.new()
	room.state = room_state.duplicate(true)
	room.pending_prepare = true
	room.prepare_in_flight = true
	root.add_child(room)
	var transport := FakeTransport.new()
	root.add_child(transport)
	var coordinator: OnlineMatchCoordinator = Coordinator.new()
	var configure_error: String = coordinator.configure(game, _setup(room_state), "p1", room, transport)
	if not configure_error.is_empty():
		_fail("Could not configure coordinator for pending-command cancellation: " + configure_error)
		return
	_start_completed = false
	_start_result = ""
	_cancel_completed = false
	_cancel_result = ""
	_start_coordinator.call_deferred(coordinator)
	await room.pending_command_wait_started
	_cancel_startup_coordinator.call_deferred(coordinator)
	for _frame in 20:
		if coordinator._startup_cancel_requested:
			break
		await process_frame
	room.prepare_in_flight = false
	for _frame in 200:
		if _start_completed and _cancel_completed:
			break
		await process_frame
	if not _start_completed or not _cancel_completed:
		_fail("Cancellation did not drain the pending command before its deadline")
	if not _cancel_result.is_empty() or room.pending_retry_count != 1 or room.abort_count != 1:
		_fail("Cancellation did not settle the old command before its epoch abort: result=%s retries=%d aborts=%d" % [_cancel_result, room.pending_retry_count, room.abort_count])
	for operation in room.command_calls:
		if operation.get("type") == "loaded":
			_fail("Startup sent loaded after cancellation while a previous command was pending")
	coordinator.close("test_cleanup")
	for audio_node in game.find_children("*", "AudioStreamPlayer", true, false):
		var player := audio_node as AudioStreamPlayer
		player.stop()
		player.stream = null
	lobby.room_client.clear_credentials()
	lobby.queue_free()
	game.queue_free()
	room.queue_free()
	transport.queue_free()
	await process_frame


func _on_started() -> void:
	_started_count += 1


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
		"revision": 1,
		"setupRevision": 2,
		"members": [
			{"nickname": "Host", "choice": {"fighter": "minren", "helper": "woailuo"}, "ready": true, "profile": profile.duplicate(true), "seq": 4},
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
			"deadline": 9_999_999_999,
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
	push_error("ONLINE_MATCH_START_CANCEL_FAILED " + message)
