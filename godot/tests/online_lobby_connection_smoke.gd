extends SceneTree

const ROOM_ID := "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"
const HOST_NEGOTIATION := "11111111-1111-4111-8111-111111111111"
const OLD_NEGOTIATION := "22222222-2222-4222-8222-222222222222"
const CURRENT_NEGOTIATION := "33333333-3333-4333-8333-333333333333"
const ConnectionScript := preload("res://online_lobby_connection.gd")

var failures: Array[String] = []
var received_messages: Array[Dictionary] = []


class FakePeerTransport extends Node:
	signal outgoing_signal(kind: String, epoch: Variant, negotiation_id: String, payload: String)
	signal peer_state_changed(state: String)
	signal peer_message(channel: String, type: String, payload: Variant, sequence: int)
	signal transport_error(code: String)

	var local_slot := -1
	var negotiation_id := ""
	var open := false
	var closed := false
	var handled_negotiations: Array[String] = []
	var sent_messages: Array[Dictionary] = []

	func configure(_room_id: String, epoch: Variant, slot: int, _remote_slot: int, id: String) -> bool:
		local_slot = slot
		negotiation_id = id
		return epoch == null

	func create_peer(_ice_servers: Array) -> bool:
		return true

	func begin_offer() -> bool:
		outgoing_signal.emit("offer", null, negotiation_id, "fixture-sdp")
		return true

	func handle_signal(message: Dictionary) -> bool:
		handled_negotiations.append(str(message.get("negotiationId", "")))
		if message.get("kind") == "offer":
			_open_channels()
		return true

	func get_connection_state() -> String:
		return "connected" if open else "connecting"

	func get_channel_state(_channel: String) -> String:
		return "open" if open else "connecting"

	func send_peer_message(channel: String, message_type: String, payload: Variant) -> bool:
		if channel != "reliable" or not open:
			return false
		sent_messages.append({"channel": channel, "type": message_type, "payload": payload})
		return true

	func close_peer() -> void:
		closed = true
		open = false

	func open_channels() -> void:
		_open_channels()

	func _open_channels() -> void:
		open = true
		peer_state_changed.emit("connected")
		peer_message.emit("reliable", "selection_open", {"version": 1}, 1)


class FakeRoomClient extends Node:
	signal signaling_message(message: Dictionary)
	signal connect_release

	var slot := 0
	var signaling_connected := false
	var state: Dictionary
	var connection: Object
	var signal_send_count := 0
	var last_signal_sequence := -1
	var leave_count := 0
	var refresh_count := 0
	var refresh_state_after_first: Dictionary
	var stale_offer_on_connect := false
	var current_offer_on_refresh := false
	var uncertain_command := false
	var in_flight := false
	var hold_connect := false
	var close_signaling_count := 0

	func _init(local_slot: int, negotiation: Variant = null) -> void:
		slot = local_slot
		state = _room_state(negotiation)

	func get_room_id() -> String:
		return ROOM_ID

	func get_slot() -> int:
		return slot

	func get_room_state() -> Dictionary:
		return state.duplicate(true)

	func is_signaling_connected() -> bool:
		return signaling_connected

	func connect_signaling() -> Dictionary:
		if hold_connect:
			await connect_release
		signaling_connected = true
		if stale_offer_on_connect:
			signaling_message.emit(_signal_message(OLD_NEGOTIATION, 0))
		elif slot == 1 and state.get("negotiation") is Dictionary:
			signaling_message.emit(_signal_message(str(state.negotiation.id), 0))
		return {"state": get_room_state()}

	func close_signaling() -> void:
		close_signaling_count += 1
		signaling_connected = false

	func refresh_state() -> Dictionary:
		refresh_count += 1
		if refresh_count == 1 and not refresh_state_after_first.is_empty():
			state = refresh_state_after_first.duplicate(true)
			if current_offer_on_refresh:
				signaling_message.emit(_signal_message(CURRENT_NEGOTIATION, 0))
		return {"state": get_room_state()}

	func command(operation: Dictionary) -> Dictionary:
		if operation.get("type") == "leave":
			leave_count += 1
			return {"acceptedSeq": 2, "state": get_room_state()}
		if operation.get("type") != "negotiate" or operation.get("epoch") != null:
			return {"error": "invalid_fixture_command"}
		state["negotiation"] = _negotiation(HOST_NEGOTIATION)
		state["revision"] = int(state.revision) + 1
		return {"acceptedSeq": 1, "state": get_room_state()}

	func retry_pending_command() -> Dictionary:
		return {"error": "no_pending_command"}

	func has_uncertain_command() -> bool:
		return uncertain_command

	func is_command_in_flight() -> bool:
		return in_flight

	func send_signal(kind: String, epoch: Variant, negotiation_id: String, payload: String) -> bool:
		if not signaling_connected or epoch != null or negotiation_id.is_empty() or payload.is_empty():
			return false
		signal_send_count += 1
		last_signal_sequence += 1
		var delivered := signal_send_count >= 2
		if delivered and connection != null:
			var peer: Variant = connection.get("_peer_transport")
			if peer != null:
				peer.open_channels()
		signaling_message.emit.call_deferred({"type": "signal_ack", "seq": last_signal_sequence, "delivered": delivered})
		return true

	func get_last_signal_sequence() -> int:
		return last_signal_sequence

	func signal_leave() -> void:
		leave_count += 1

	func _signal_message(negotiation_id: String, from_slot: int) -> Dictionary:
		return {
			"type": "signal",
			"version": 1,
			"seq": 0,
			"epoch": null,
			"negotiationId": negotiation_id,
			"kind": "offer",
			"payload": "fixture-sdp",
			"from": from_slot,
		}

	func _room_state(negotiation: Variant) -> Dictionary:
		return {
			"id": ROOM_ID,
			"phase": "lobby",
			"revision": 1,
			"setupRevision": 0,
			"members": [{"choice": null}, {"choice": null}],
			"networkProfile": {"id": "chrome-exp-d2-p6", "inputDelay": 2, "predictionWindow": 6},
			"negotiation": negotiation,
		}

	static func _negotiation(id: String) -> Dictionary:
		return {"id": id, "epoch": null, "expires": int(Time.get_unix_time_from_system() * 1000.0) + 60_000}


func _initialize() -> void:
	call_deferred("_run")


func _run() -> void:
	await _test_owner_retries_undelivered_offer()
	await _test_guest_uses_fresh_negotiation_and_buffers_early_offer()
	await _test_guest_reconnect_receives_offer_after_listener_rebind()
	await _test_close_cancels_start_without_leaving()
	if failures.is_empty():
		print("ONLINE_LOBBY_CONNECTION_SMOKE_OK host_retry=true guest_fresh_negotiation=true idle_guest_signal_buffer=true early_signal_filter=true first_data_message_preserved=true reliable_send=true guest_reconnect_rebinds_before_offer=true close_cancels_start=true close_does_not_leave=true")
	else:
		push_error("ONLINE_LOBBY_CONNECTION_SMOKE_FAILED " + "; ".join(failures))
	quit(0 if failures.is_empty() else 1)


func _test_owner_retries_undelivered_offer() -> void:
	received_messages.clear()
	var client := FakeRoomClient.new(0)
	root.add_child(client)
	var connection = ConnectionScript.new()
	connection._peer_transport_factory = func() -> Node: return FakePeerTransport.new()
	client.connection = connection
	connection.peer_message.connect(_on_peer_message)
	root.add_child(connection)
	_expect(connection.configure(client, 0, []), "host configuration was rejected")
	var error: String = await connection.start()
	_expect(error.is_empty(), "host start failed: " + error)
	_expect(client.signal_send_count == 2, "host did not retry offer after delivered=false")
	_expect(connection.get_connection_state() == "connected", "host did not enter connected state")
	_expect(received_messages.size() == 1 and received_messages[0].get("type") == "selection_open", "first startup data-channel message was dropped")
	_expect(connection.send_peer_message("selection_snapshot", {"fighter": "mingren", "helper": "woailuo"}), "reliable message send failed")
	var host_peer: Variant = connection.get("_peer_transport")
	_expect(host_peer.sent_messages.size() == 1 and host_peer.sent_messages[0].channel == "reliable", "application message did not use ordered reliable channel")
	connection.close()
	_expect(connection.get_connection_state() == "closed", "close did not mark connection closed")
	_expect(client.leave_count == 0, "closing the pre-match transport left the room")
	client.queue_free()
	connection.queue_free()
	await process_frame


func _test_guest_uses_fresh_negotiation_and_buffers_early_offer() -> void:
	received_messages.clear()
	var client := FakeRoomClient.new(1, FakeRoomClient._negotiation(OLD_NEGOTIATION))
	client.signaling_connected = true
	root.add_child(client)
	var connection = ConnectionScript.new()
	connection._peer_transport_factory = func() -> Node: return FakePeerTransport.new()
	client.connection = connection
	connection.peer_message.connect(_on_peer_message)
	root.add_child(connection)
	_expect(connection.configure(client, 1, []), "guest configuration was rejected")
	client.signaling_message.emit(client._signal_message(OLD_NEGOTIATION, 0))
	client.state = client._room_state(client._negotiation(CURRENT_NEGOTIATION))
	client.signaling_message.emit(client._signal_message(CURRENT_NEGOTIATION, 0))
	var error: String = await connection.start()
	_expect(error.is_empty(), "guest start failed: " + error)
	var guest_peer: Variant = connection.get("_peer_transport")
	_expect(guest_peer.handled_negotiations == [CURRENT_NEGOTIATION], "guest accepted stale offer or missed current negotiation")
	_expect(received_messages.size() == 1 and received_messages[0].get("type") == "selection_open", "buffered first guest message was not delivered after connected")
	connection.close()
	_expect(client.leave_count == 0, "guest transport close left the room")
	client.queue_free()
	connection.queue_free()
	await process_frame

	var delayed_client := FakeRoomClient.new(1, FakeRoomClient._negotiation(CURRENT_NEGOTIATION))
	delayed_client.signaling_connected = true
	root.add_child(delayed_client)
	var delayed_connection = ConnectionScript.new()
	delayed_connection._peer_transport_factory = func() -> Node: return FakePeerTransport.new()
	delayed_client.connection = delayed_connection
	delayed_connection.peer_message.connect(_on_peer_message)
	root.add_child(delayed_connection)
	_expect(delayed_connection.configure(delayed_client, 1, []), "already-negotiated guest configuration was rejected")
	delayed_client.signaling_message.emit(delayed_client._signal_message(CURRENT_NEGOTIATION, 0))
	var delayed_error: String = await delayed_connection.start()
	_expect(delayed_error.is_empty(), "guest delayed after host offer failed: " + delayed_error)
	var delayed_peer: Variant = delayed_connection.get("_peer_transport")
	_expect(delayed_peer.handled_negotiations == [CURRENT_NEGOTIATION], "guest delayed start did not accept its buffered current offer")
	delayed_connection.close()
	delayed_client.queue_free()
	delayed_connection.queue_free()
	await process_frame


func _on_peer_message(message_type: String, payload: Variant, sequence: int) -> void:
	received_messages.append({"type": message_type, "payload": payload, "sequence": sequence})


func _test_close_cancels_start_without_leaving() -> void:
	var client := FakeRoomClient.new(1)
	client.hold_connect = true
	root.add_child(client)
	var connection = ConnectionScript.new()
	connection._peer_transport_factory = func() -> Node: return FakePeerTransport.new()
	root.add_child(connection)
	_expect(connection.configure(client, 1, []), "cancellation fixture configuration failed")
	var outcome := {"done": false, "error": ""}
	Callable(self, "_capture_start").call_deferred(connection, outcome)
	await process_frame
	connection.close()
	client.connect_release.emit()
	for _frame in 4:
		await process_frame
	_expect(bool(outcome.done) and str(outcome.error) == "start_cancelled", "close did not cancel pending startup")
	_expect(client.leave_count == 0, "canceling startup left the room")
	client.queue_free()
	connection.queue_free()
	await process_frame


func _test_guest_reconnect_receives_offer_after_listener_rebind() -> void:
	var client := FakeRoomClient.new(1, FakeRoomClient._negotiation(OLD_NEGOTIATION))
	client.signaling_connected = true
	root.add_child(client)
	var old_connection = ConnectionScript.new()
	old_connection._peer_transport_factory = func() -> Node: return FakePeerTransport.new()
	root.add_child(old_connection)
	_expect(old_connection.configure(client, 1, []), "initial guest reconnect configuration was rejected")
	client.signaling_message.emit(client._signal_message(OLD_NEGOTIATION, 0))
	var initial_error: String = await old_connection.start()
	_expect(initial_error.is_empty(), "initial guest connection failed: " + initial_error)
	old_connection.close()
	client.close_signaling()
	_expect(client.close_signaling_count == 1 and not client.signaling_connected,
		"lobby teardown did not close the stale signaling socket")

	client.state = client._room_state(client._negotiation(CURRENT_NEGOTIATION))
	var new_connection = ConnectionScript.new()
	new_connection._peer_transport_factory = func() -> Node: return FakePeerTransport.new()
	root.add_child(new_connection)
	_expect(new_connection.configure(client, 1, []), "reconnected guest failed to bind listener before start")
	var reconnect_error: String = await new_connection.start()
	_expect(reconnect_error.is_empty(), "reconnected guest missed host's fresh offer: " + reconnect_error)
	var reconnected_peer: Variant = new_connection.get("_peer_transport")
	_expect(reconnected_peer.handled_negotiations == [CURRENT_NEGOTIATION],
		"reconnected guest accepted stale signaling or missed the fresh offer")
	new_connection.close()
	client.queue_free()
	old_connection.queue_free()
	new_connection.queue_free()
	await process_frame


func _capture_start(connection: Object, outcome: Dictionary) -> void:
	outcome["error"] = await connection.start()
	outcome["done"] = true


func _expect(condition: bool, description: String) -> void:
	if not condition:
		failures.append(description)
