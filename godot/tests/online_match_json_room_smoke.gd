extends SceneTree

const Coordinator := preload("res://online_match.gd")
const Lobby := preload("res://online_lobby.gd")
const RoomClient := preload("res://online_room_client.gd")

const ROOM_ID := "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"
const EPOCH := "3fa85f64-5717-4562-b3fc-2c963f66afa6"
const NEGOTIATION_ID := "550e8400-e29b-41d4-a716-446655440000"


class FakeRoom extends Node:
	var state: Dictionary = {}
	var slot := 0
	var command_sequence := 0

	func get_slot() -> int:
		return slot

	func get_room_id() -> String:
		return str(state.get("id", ""))

	func get_room_state() -> Dictionary:
		return state.duplicate(true)

	func refresh_state() -> Dictionary:
		return {"state": get_room_state()}

	func command(operation: Dictionary) -> Dictionary:
		command_sequence += 1
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
			_:
				return {"error": "unsupported_test_command", "uncertain": false}
		return {"acceptedSeq": command_sequence, "state": get_room_state()}

	func is_signaling_connected() -> bool:
		return true

	func connect_signaling() -> Dictionary:
		return {"state": get_room_state()}

	func get_ice_servers() -> Dictionary:
		return {"iceServers": []}

	func send_signal(_kind: String, _signal_epoch: Variant, _negotiation_id: String, _payload: String) -> bool:
		return true

	func get_last_signal_sequence() -> int:
		return 0


class FakeTransport extends Node:
	signal peer_message(channel: String, type: String, payload: Dictionary, sequence: int)
	signal peer_state_changed(state: String)
	signal outgoing_signal(kind: String, epoch: String, negotiation_id: String, payload: String)
	signal transport_error(code: String)

	var configured := false
	var peer_created := false
	var sequence := 0

	func configure(_room_id: String, _epoch: Variant, local_slot: int, remote_slot: int, _negotiation_id: String) -> bool:
		configured = local_slot == 0 and remote_slot == 1
		return configured

	func create_peer(_ice_servers: Array) -> bool:
		peer_created = configured
		return peer_created

	func begin_offer() -> bool:
		return peer_created

	func handle_signal(_message: Dictionary) -> bool:
		return peer_created

	func get_channel_state(channel: String) -> String:
		return "open" if peer_created and channel in ["reliable", "input"] else "closed"

	func peer_is_connected() -> bool:
		return peer_created

	func send_peer_message(channel: String, type: String, payload: Dictionary) -> bool:
		if not peer_created or channel != "reliable":
			return false
		sequence += 1
		if type == "match_ready":
			peer_message.emit("reliable", "match_ready", payload.duplicate(true), sequence)
		return true

	func close_peer() -> void:
		peer_created = false


func _initialize() -> void:
	call_deferred("_run")


func _run() -> void:
	var lobby: OnlineLobby = Lobby.new()
	root.add_child(lobby)
	await process_frame
	lobby._room_id = ROOM_ID
	lobby._slot = 0
	lobby._starting_epoch = EPOCH

	var client: OnlineRoomClient = lobby.room_client
	client._room_id = ROOM_ID
	client._slot = 0
	var wire_state := _json_state()
	if not client._validate_room_state(wire_state, ROOM_ID, 0, true):
		_fail("RoomClient rejected the JSON round-trip projection")
		return
	client._accept_state(wire_state)
	if client.get_room_state().is_empty() or not client.get_room_state().rules.time is float \
		or not client.get_room_state().match.profile.inputDelay is float:
		_fail("RoomClient did not retain the integral-float service metadata")
		return
	lobby._accept_state(client.get_room_state())
	var room_state: Dictionary = lobby._room_state.duplicate(true)

	var game: Node = load("res://main.tscn").instantiate()
	root.add_child(game)
	game.set_process(false)
	game.set_physics_process(false)
	await process_frame
	lobby.configure(null, game)
	var apply_error: String = lobby._configure_live_game(room_state)
	if not apply_error.is_empty():
		_fail("Lobby could not configure Main from the room projection: " + apply_error)
		return
	if game.session.root_label != "游戏场景" or game.physics_tick != 0 or game.is_physics_processing():
		_fail("Invalid-number cases require a configured, stopped battle at tick zero")
		return
	var session_before := {
		"root_label": str(game.session.root_label),
		"modo": int(game.session.modo),
		"maxhp": float(game.session.maxhp),
		"physics_tick": int(game.physics_tick),
	}
	var room := FakeRoom.new()
	room.state = room_state.duplicate(true)
	root.add_child(room)
	var transport := FakeTransport.new()
	root.add_child(transport)
	for invalid in _invalid_setups(room_state):
		var rejected := Coordinator.new()
		var rejected_error: String = rejected.configure(game, invalid, "p1", room, transport)
		if rejected_error != "Online room setup is incomplete" or rejected._configured or not rejected.setup.is_empty():
			_fail("Malformed numeric setup was accepted or partially installed")
			return
		if str(game.session.root_label) != session_before.root_label or int(game.session.modo) != session_before.modo \
			or float(game.session.maxhp) != session_before.maxhp or int(game.physics_tick) != session_before.physics_tick:
			_fail("Rejected numeric setup mutated the live Main")
			return

	var setup := {
		"members": room_state.members.duplicate(true),
		"stage": room_state.stage,
		"rules": room_state.rules.duplicate(true),
		"profile": room_state.match.profile.duplicate(true),
		"seed": room_state.match.seed,
		"clockBaseline": room_state.match.clockBaseline,
		"setupRevision": room_state.setupRevision,
	}
	var coordinator: OnlineMatchCoordinator = Coordinator.new()
	var configure_error := coordinator.configure(game, setup, "p1", room, transport)
	if not configure_error.is_empty():
		_fail("Coordinator rejected valid JSON numeric metadata: " + configure_error)
		return
	if not coordinator.setup.rules.time is int or not coordinator.setup.profile.inputDelay is int \
		or not coordinator.setup.seed is int:
		_fail("Coordinator setup was not normalized to native integers")
		return
	var start_profile: Dictionary = room_state.match.profile.duplicate(true)
	var start_error: String = await coordinator.start(EPOCH, start_profile, "p1")
	if not start_error.is_empty() or not coordinator.running:
		_fail("Coordinator did not complete the loaded/active/channel/peer-ready barriers: " + start_error)
		return
	if not coordinator.profile.inputDelay is int or not coordinator.profile.predictionWindow is int:
		_fail("Coordinator did not normalize the agreed and service profile before comparison")
		return
	print("ONLINE_MATCH_JSON_ROOM_OK room_projection=true lobby_main=true setup_normalized=true start_barriers=true strict_rejection=true")
	coordinator.close()
	lobby.room_client.clear_credentials()
	for audio_node in game.find_children("*", "AudioStreamPlayer", true, false):
		var player := audio_node as AudioStreamPlayer
		player.stop()
		player.stream = null
	lobby.queue_free()
	game.queue_free()
	room.queue_free()
	transport.queue_free()
	await process_frame
	quit(0)


func _json_state() -> Dictionary:
	var profile := {"id": "chrome-exp-d2-p5", "inputDelay": 2, "predictionWindow": 5}
	var state := {
		"schema": 1,
		"id": ROOM_ID,
		"compatibility": {"protocol": 1, "build": "b".repeat(64), "content": "c".repeat(64)},
		"revision": 1,
		"setupRevision": 2,
		"members": [
			{"nickname": "Host", "choice": {"fighter": "minren", "helper": "woailuo"}, "ready": true, "profile": profile, "seq": 4},
			{"nickname": "Guest", "choice": {"fighter": "yihu", "helper": "kon"}, "ready": true, "profile": profile.duplicate(true), "seq": 3},
		],
		"stage": "现世",
		"rules": {"time": 90, "life": 1},
		"networkProfile": {"id": "chrome-exp-d2-p5", "inputDelay": 2, "predictionWindow": 5},
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
	var decoded: Variant = JSON.parse_string(JSON.stringify(state))
	return _json_numbers_as_floats(decoded)


func _invalid_setups(state: Dictionary) -> Array[Dictionary]:
	var base := {
		"members": state.members.duplicate(true),
		"stage": state.stage,
		"rules": state.rules.duplicate(true),
		"profile": state.match.profile.duplicate(true),
		"seed": state.match.seed,
	}
	var cases: Array[Dictionary] = []
	var fractional_rule := base.duplicate(true)
	fractional_rule.rules.time = 90.5
	cases.append(fractional_rule)
	var boolean_profile := base.duplicate(true)
	boolean_profile.profile.inputDelay = true
	cases.append(boolean_profile)
	var excessive_profile := base.duplicate(true)
	excessive_profile.profile.predictionWindow = 16.0
	cases.append(excessive_profile)
	var excessive_seed := base.duplicate(true)
	excessive_seed.seed = 4_294_967_296.0
	cases.append(excessive_seed)
	return cases


func _json_numbers_as_floats(value: Variant) -> Variant:
	if value is int:
		return float(value)
	if value is Array:
		var converted: Array = []
		for item in value:
			converted.append(_json_numbers_as_floats(item))
		return converted
	if value is Dictionary:
		var converted: Dictionary = {}
		for key in value:
			converted[key] = _json_numbers_as_floats(value[key])
		return converted
	return value


func _fail(message: String) -> void:
	push_error("ONLINE_MATCH_JSON_ROOM_FAILED " + message)
	quit(1)
