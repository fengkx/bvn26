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
	var connect_calls := 0
	var fail_connect_error := ""
	var refresh_state_after_first: Dictionary
	var stale_offer_on_connect := false
	var current_offer_on_refresh := false
	var uncertain_command := false
	var in_flight := false
	var hold_connect := false
	var close_signaling_count := 0
	var invalidate_first_offer := false
	var disconnect_on_first_signal := false
	var negotiate_count := 0
	var buffered_signals: Array = []

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
		connect_calls += 1
		if hold_connect:
			await connect_release
		if not fail_connect_error.is_empty():
			signaling_connected = false
			return {"error": fail_connect_error}
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
		negotiate_count += 1
		state["negotiation"] = _negotiation(HOST_NEGOTIATION if negotiate_count == 1 else CURRENT_NEGOTIATION)
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
		if disconnect_on_first_signal and signal_send_count == 0:
			signal_send_count += 1
			signaling_connected = false
			return false
		signal_send_count += 1
		last_signal_sequence += 1
		if invalidate_first_offer and signal_send_count == 1:
			state["negotiation"] = null
			signaling_message.emit.call_deferred({"type": "error", "error": "stale_negotiation"})
			return true
		var delivered := signal_send_count >= 2
		if delivered and connection != null:
			var peer: Variant = connection.get("_peer_transport")
			if peer != null:
				peer.open_channels()
		signaling_message.emit.call_deferred({"type": "signal_ack", "seq": last_signal_sequence, "delivered": delivered})
		return true

	func get_last_signal_sequence() -> int:
		return last_signal_sequence

	func consume_recent_signals() -> Array:
		var pending: Array = buffered_signals.duplicate(true)
		buffered_signals.clear()
		return pending

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
	await _test_owner_reoffers_after_guest_socket_replacement()
	await _test_guest_uses_fresh_negotiation_and_buffers_early_offer()
	await _test_guest_reconnect_receives_offer_after_listener_rebind()
	await _test_close_cancels_start_without_leaving()
	await _test_guest_waits_through_short_ice_budget()
	await _test_host_waits_for_guest_signaling()
	await _test_signaling_reconnect_during_handshake()
	await _test_double_start_is_rejected()
	await _test_guest_accepts_offer_buffered_before_subscribe()
	await _test_wait_does_not_poll_while_signaling_is_up()
	await _test_signaling_reconnect_backs_off()
	await _test_close_during_wait_peer_stops()
	if failures.is_empty():
		print("ONLINE_LOBBY_CONNECTION_SMOKE_OK host_retry=true guest_fresh_negotiation=true idle_guest_signal_buffer=true early_signal_filter=true first_data_message_preserved=true reliable_send=true guest_reconnect_rebinds_before_offer=true close_cancels_start=true close_does_not_leave=true guest_late_host=true host_waits_for_guest_signaling=true signaling_reconnect=true double_start_rejected=true pre_subscribe_offer=true poll_idle_while_socket_up=true reconnect_backoff=true close_stops_wait_peer=true")
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


func _test_owner_reoffers_after_guest_socket_replacement() -> void:
	var client := FakeRoomClient.new(0)
	client.invalidate_first_offer = true
	root.add_child(client)
	var connection = ConnectionScript.new()
	connection._peer_transport_factory = func() -> Node: return FakePeerTransport.new()
	client.connection = connection
	root.add_child(connection)
	_expect(connection.configure(client, 0, []), "reconnecting host configuration failed")
	var issue: String = await connection.start()
	_expect(issue.is_empty(), "guest socket replacement failed: " + issue)
	_expect(client.negotiate_count == 2, "host did not renew the invalidated negotiation")
	_expect(connection._negotiation_id == CURRENT_NEGOTIATION, "host reused stale negotiation")
	connection.close()
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


func _test_guest_waits_through_short_ice_budget() -> void:
	var client := FakeRoomClient.new(1)
	client.signaling_connected = true
	root.add_child(client)
	var connection = ConnectionScript.new()
	connection._peer_transport_factory = func() -> Node: return FakePeerTransport.new()
	connection._data_channel_timeout_ms = 200
	connection._peer_wait_timeout_ms = 5_000
	client.connection = connection
	root.add_child(connection)
	_expect(connection.configure(client, 1, []), "late guest configuration was rejected")
	var outcome := {"done": false, "error": ""}
	Callable(self, "_capture_start").call_deferred(connection, outcome)
	await create_timer(0.45).timeout
	_expect(not outcome.done, "guest spent the ICE budget while still waiting for the host")
	_expect(connection.get_startup_phase() == "wait_negotiation", "guest left the idle wait: " + connection.get_startup_phase())
	client.state = client._room_state(client._negotiation(CURRENT_NEGOTIATION))
	client.signaling_message.emit(client._signal_message(CURRENT_NEGOTIATION, 0))
	var spins := 0
	while not outcome.done and spins < 120:
		await process_frame
		spins += 1
	_expect(outcome.done and str(outcome.error).is_empty(), "guest did not finish after the late host offer: " + str(outcome.error))
	connection.close()
	client.queue_free()
	connection.queue_free()
	await process_frame


func _test_host_waits_for_guest_signaling() -> void:
	var client := FakeRoomClient.new(0)
	client.signaling_connected = true
	client.state = client._room_state(null)
	client.state["members"][1]["signaling"] = false
	root.add_child(client)
	var connection = ConnectionScript.new()
	connection._peer_transport_factory = func() -> Node: return FakePeerTransport.new()
	client.connection = connection
	root.add_child(connection)
	_expect(connection.configure(client, 0, []), "waiting host configuration was rejected")
	var outcome := {"done": false, "error": ""}
	Callable(self, "_capture_start").call_deferred(connection, outcome)
	await create_timer(0.2).timeout
	_expect(client.negotiate_count == 0, "host negotiated before the guest signaling socket was up")
	_expect(connection.get_startup_phase() == "wait_peer", "host was not waiting for the guest: " + connection.get_startup_phase())
	client.state["members"][1]["signaling"] = true
	var spins := 0
	while not outcome.done and spins < 40:
		await create_timer(0.05).timeout
		spins += 1
	_expect(outcome.done and str(outcome.error).is_empty(), "host did not connect after the guest signaling socket appeared: " + str(outcome.error))
	_expect(client.negotiate_count == 1, "host negotiate ran more than once: %d" % client.negotiate_count)
	connection.close()
	client.queue_free()
	connection.queue_free()
	await process_frame


func _test_signaling_reconnect_during_handshake() -> void:
	var client := FakeRoomClient.new(0)
	client.signaling_connected = true
	client.disconnect_on_first_signal = true
	root.add_child(client)
	var connection = ConnectionScript.new()
	connection._peer_transport_factory = func() -> Node: return FakePeerTransport.new()
	client.connection = connection
	root.add_child(connection)
	_expect(connection.configure(client, 0, []), "reconnect handshake configuration was rejected")
	var issue: String = await connection.start()
	_expect(issue.is_empty(), "signaling drop during handshake failed: " + issue)
	_expect(client.negotiate_count == 1, "a signaling reconnect started a second negotiation")
	_expect(connection.get_connection_state() == "connected", "handshake did not recover after the signaling reconnect")
	connection.close()
	client.queue_free()
	connection.queue_free()
	await process_frame


func _test_double_start_is_rejected() -> void:
	var client := FakeRoomClient.new(0)
	client.hold_connect = true
	root.add_child(client)
	var connection = ConnectionScript.new()
	connection._peer_transport_factory = func() -> Node: return FakePeerTransport.new()
	client.connection = connection
	root.add_child(connection)
	_expect(connection.configure(client, 0, []), "double-start configuration was rejected")
	var outcome := {"done": false, "error": ""}
	Callable(self, "_capture_start").call_deferred(connection, outcome)
	var ready_spins := 0
	while connection.get_startup_phase() == "idle" and ready_spins < 30:
		await process_frame
		ready_spins += 1
	var second: String = await connection.start()
	_expect(second == "connection_starting", "a second start was not rejected: " + second)
	_expect(client.negotiate_count == 0, "the duplicate start negotiated before the first attempt")
	client.hold_connect = false
	client.connect_release.emit()
	var spins := 0
	while not outcome.done and spins < 40:
		await create_timer(0.05).timeout
		spins += 1
	_expect(outcome.done and str(outcome.error).is_empty(), "the first start did not finish after the duplicate was rejected: " + str(outcome.error))
	_expect(client.negotiate_count == 1, "double start created %d negotiations" % client.negotiate_count)
	connection.close()
	client.queue_free()
	connection.queue_free()
	await process_frame


func _test_guest_accepts_offer_buffered_before_subscribe() -> void:
	var client := FakeRoomClient.new(1, FakeRoomClient._negotiation(CURRENT_NEGOTIATION))
	client.signaling_connected = true
	client.buffered_signals.append(client._signal_message(CURRENT_NEGOTIATION, 0))
	root.add_child(client)
	var connection = ConnectionScript.new()
	connection._peer_transport_factory = func() -> Node: return FakePeerTransport.new()
	connection._peer_wait_timeout_ms = 800
	client.connection = connection
	root.add_child(connection)
	_expect(connection.configure(client, 1, []), "pre-subscribe guest configuration was rejected")
	_expect(client.buffered_signals.is_empty(), "configure left the pre-subscribe offer in the room buffer")
	var issue: String = await connection.start()
	_expect(issue.is_empty(), "guest missed an offer that arrived before it subscribed: " + issue)
	var peer: Variant = connection.get("_peer_transport")
	_expect(peer.handled_negotiations == [CURRENT_NEGOTIATION], "pre-subscribe offer was not applied")
	connection.close()
	client.queue_free()
	connection.queue_free()
	await process_frame


func _test_wait_does_not_poll_while_signaling_is_up() -> void:
	var client := FakeRoomClient.new(1)
	client.signaling_connected = true
	root.add_child(client)
	var connection = ConnectionScript.new()
	connection._peer_transport_factory = func() -> Node: return FakePeerTransport.new()
	connection._peer_wait_timeout_ms = 5_000
	root.add_child(connection)
	_expect(connection.configure(client, 1, []), "idle-poll guest configuration was rejected")
	var outcome := {"done": false, "error": ""}
	Callable(self, "_capture_start").call_deferred(connection, outcome)
	await create_timer(0.6).timeout
	_expect(not outcome.done, "guest finished while the host had not negotiated")
	_expect(connection.get_startup_phase() == "wait_negotiation", "guest left the idle wait: " + connection.get_startup_phase())
	_expect(client.refresh_count == 0, "wait polled /state while the signaling socket was up: %d" % client.refresh_count)
	_expect(client.connect_calls == 0, "wait reconnected a socket that was already up")
	connection.close()
	var spins := 0
	while not outcome.done and spins < 20:
		await process_frame
		spins += 1
	_expect(outcome.done and str(outcome.error) == "start_cancelled", "closing during wait_negotiation did not stop: " + str(outcome.error))
	_expect(client.refresh_count == 0 and client.connect_calls == 0, "close during wait kept polling")
	client.queue_free()
	connection.queue_free()
	await process_frame


func _test_signaling_reconnect_backs_off() -> void:
	var client := FakeRoomClient.new(0)
	client.fail_connect_error = "socket_timeout"
	client.state["members"][1]["signaling"] = false
	root.add_child(client)
	var connection = ConnectionScript.new()
	connection._peer_transport_factory = func() -> Node: return FakePeerTransport.new()
	connection._peer_wait_timeout_ms = 8_000
	root.add_child(connection)
	_expect(connection.configure(client, 0, []), "backoff host configuration was rejected")
	var outcome := {"done": false, "error": ""}
	Callable(self, "_capture_start").call_deferred(connection, outcome)
	await create_timer(2.6).timeout
	_expect(not outcome.done, "host gave up before the reconnect backoff could be measured")
	_expect(client.connect_calls >= 2 and client.connect_calls <= 3, "reconnect was not bounded to about one then two seconds: %d" % client.connect_calls)
	var calls := client.connect_calls
	var refreshes := client.refresh_count
	connection.close()
	var spins := 0
	while not outcome.done and spins < 20:
		await process_frame
		spins += 1
	_expect(outcome.done and str(outcome.error) == "start_cancelled", "close during reconnect backoff did not stop: " + str(outcome.error))
	_expect(client.connect_calls == calls and client.refresh_count == refreshes, "close during reconnect kept dialing")
	client.queue_free()
	connection.queue_free()
	await process_frame


func _test_close_during_wait_peer_stops() -> void:
	var client := FakeRoomClient.new(0)
	client.signaling_connected = true
	client.state["members"][1]["signaling"] = false
	root.add_child(client)
	var connection = ConnectionScript.new()
	connection._peer_transport_factory = func() -> Node: return FakePeerTransport.new()
	connection._peer_wait_timeout_ms = 60_000
	root.add_child(connection)
	_expect(connection.configure(client, 0, []), "wait-peer close configuration was rejected")
	var outcome := {"done": false, "error": ""}
	Callable(self, "_capture_start").call_deferred(connection, outcome)
	await create_timer(0.2).timeout
	_expect(connection.get_startup_phase() == "wait_peer", "host was not waiting for the guest: " + connection.get_startup_phase())
	_expect(client.refresh_count == 0, "wait_peer polled /state while signaling was up")
	var calls := client.connect_calls
	var refreshes := client.refresh_count
	connection.close()
	var spins := 0
	while not outcome.done and spins < 20:
		await process_frame
		spins += 1
	_expect(spins < 15, "close during wait_peer waited out a timer")
	_expect(outcome.done and str(outcome.error) == "start_cancelled", "close during wait_peer did not stop: " + str(outcome.error))
	_expect(client.connect_calls == calls and client.refresh_count == refreshes, "close during wait_peer kept polling or reconnecting")
	client.queue_free()
	connection.queue_free()
	await process_frame


func _capture_start(connection: Object, outcome: Dictionary) -> void:
	outcome["error"] = await connection.start()
	outcome["done"] = true


func _expect(condition: bool, description: String) -> void:
	if not condition:
		failures.append(description)
