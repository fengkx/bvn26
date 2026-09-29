extends RefCounted

class Dependency extends Node:
	signal state_changed(state: Dictionary)
	signal socket_state_changed(connected: bool)
	signal signaling_message(message: Dictionary)
	signal error(code: String)
	signal peer_message(channel: String, type: String, payload: Dictionary, sequence: int)
	signal peer_state_changed(state: String)
	signal outgoing_signal(kind: String, epoch: String, negotiation_id: String, payload: String)
	signal transport_error(code: String)
	signal message_drain_started()
	signal message_drain_completed(messages_delivered: int)


class FakeHub extends RefCounted:
	const EPOCH := "f47ac10b-58cc-4372-a567-0e02b2c3d479"
	const NEGOTIATION := "550e8400-e29b-41d4-a716-446655440000"
	var epoch := EPOCH
	var negotiation_id := NEGOTIATION
	var state: Dictionary
	var peers: Dictionary = {}
	var pending: Array[Dictionary] = []
	var held_from_p2: Array[Dictionary] = []
	var held_results_from_p2: Array[Dictionary] = []
	var hold_p2_to_p1 := false
	var hold_p2_result_to_p1 := false
	var next_peer_sequence := [0, 0]
	var next_channel_sequence := [
		{"reliable": 0, "input": 0},
		{"reliable": 0, "input": 0},
	]
	var next_command_sequence := [0, 0]
	var state_hash_frames := {0: [], 1: []}
	var peer_router: Callable

	func _init(setup: Dictionary) -> void:
		state = {
			"roomId": "PAIR01",
			"revision": 1,
			"setupRevision": 1,
			"compatibility": {"build": "test-build", "content": "test-content"},
			"members": [
				{"choice": setup.members[0].choice, "profile": setup.profile},
				{"choice": setup.members[1].choice, "profile": setup.profile},
			],
			"stage": setup.stage,
			"rules": setup.rules.duplicate(true),
			"phase": "preparing",
			"lastResult": null,
			"match": {
				"epoch": epoch,
				"seed": setup.seed,
				"clockBaseline": 0,
				"profile": setup.profile.duplicate(true),
				"deadline": 9_999_999_999,
				"loaded": [null, null],
				"acknowledged": [false, false],
				"results": [null, null],
			},
			"negotiation": null,
		}

	func command(slot: int, operation: Dictionary) -> Dictionary:
		next_command_sequence[slot] += 1
		var sequence: int = next_command_sequence[slot]
		var members: Array = state.members
		members[slot].seq = sequence
		state.members = members
		match str(operation.get("type", "")):
			"loaded":
				var loaded: Array = state.match.loaded
				loaded[slot] = operation.get("initialHash")
				state.match.loaded = loaded
			"start_ack":
				var acknowledgements: Array = state.match.acknowledged
				acknowledgements[slot] = true
				state.match.acknowledged = acknowledgements
				if acknowledgements[0] and acknowledgements[1]:
					state.phase = "active"
			"negotiate":
				state.negotiation = {"id": negotiation_id, "epoch": operation.get("epoch"), "expires": 9_999_999_999}
			"result":
				var match_state: Dictionary = state.match
				var results: Array = match_state.results
				results[slot] = {"frame": operation.get("frame"), "hash": operation.get("hash"), "winner": operation.get("winner")}
				match_state.results = results
				state.match = match_state
				if results[0] != null and results[1] != null:
					var agreed: bool = results[0] == results[1]
					state.phase = "lobby"
					state.lastResult = {"epoch": epoch, "reason": "agreed" if agreed else "result_mismatch",
						"winner": operation.get("winner") if agreed else null}
					state.match = null
					state.setupRevision = int(state.setupRevision) + 1
			"abort":
				state.phase = "lobby"
		state.revision = int(state.revision) + 1
		return {"acceptedSeq": sequence, "state": state.duplicate(true)}

	func register_peer(slot: int, peer: Object) -> void:
		peers[slot] = peer
		var remaining: Array[Dictionary] = []
		for message in pending:
			if int(message.to) == slot:
				_deliver(message)
			else:
				remaining.append(message)
		pending = remaining

	func unregister_peer(slot: int) -> void:
		peers.erase(slot)

	func send_peer(slot: int, channel: String, type: String, payload: Dictionary) -> void:
		next_peer_sequence[slot] += 1
		next_channel_sequence[slot][channel] += 1
		if type == "state_hash":
			state_hash_frames[slot].append(int(payload.get("frame", -1)))
		var envelope := {
			"version": 1,
			"roomId": state.roomId,
			"epoch": state.match.epoch,
			"from": slot,
			"seq": next_peer_sequence[slot],
			"type": type,
			"payload": payload,
		}
		var decoded: Dictionary = JSON.parse_string(JSON.stringify(envelope))
		decoded.payload = _json_numbers_as_floats(decoded.payload)
		# Keep the envelope's global sequence contract; the simulator checks channel ordering separately.
		var message := {
			"to": 1 - slot,
			"channel": channel,
			"channel_sequence": next_channel_sequence[slot][channel],
			"envelope": decoded,
		}
		if hold_p2_result_to_p1 and slot == 1 and type == "result":
			held_results_from_p2.append(message)
		elif hold_p2_to_p1 and slot == 1:
			held_from_p2.append(message)
		elif peer_router.is_valid():
			peer_router.call(slot, message)
		elif peers.has(1 - slot):
			_deliver(message)
		else:
			pending.append(message)

	func release_p2_messages() -> void:
		hold_p2_to_p1 = false
		for message in held_from_p2:
			_deliver(message)
		held_from_p2.clear()

	func release_p2_result() -> void:
		hold_p2_result_to_p1 = false
		for message in held_results_from_p2:
			_deliver(message)
		held_results_from_p2.clear()

	func prepare_next_epoch(setup: Dictionary, new_epoch: String, new_seed: int) -> void:
		epoch = new_epoch
		negotiation_id = "6ba7b810-9dad-41d1-80b4-00c04fd430c8"
		state = {
			"roomId": "PAIR01",
			"revision": int(state.get("revision", 0)) + 1,
			"setupRevision": int(state.get("setupRevision", 0)) + 1,
			"compatibility": {"build": "test-build", "content": "test-content"},
			"members": [
				{"choice": setup.members[0].choice, "profile": setup.profile},
				{"choice": setup.members[1].choice, "profile": setup.profile},
			],
			"stage": setup.stage,
			"rules": setup.rules.duplicate(true),
			"phase": "preparing",
			"lastResult": null,
			"match": {
				"epoch": epoch,
				"seed": new_seed,
				"clockBaseline": 0,
				"profile": setup.profile.duplicate(true),
				"deadline": 9_999_999_999,
				"loaded": [null, null],
				"acknowledged": [false, false],
				"results": [null, null],
			},
			"negotiation": null,
		}

	func deliver_peer_message(message: Dictionary) -> void:
		if peers.has(int(message.to)):
			_deliver(message)
		else:
			pending.append(message)

	func _deliver(message: Dictionary) -> void:
		var envelope: Dictionary = message.envelope
		var peer: Object = peers[int(message.to)]
		peer.peer_message.emit(str(message.channel), str(envelope.type), envelope.payload, int(envelope.seq))

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


class FakeRoom extends Dependency:
	var hub: FakeHub
	var slot := -1

	func configure(fake_hub: FakeHub, room_slot: int) -> void:
		hub = fake_hub
		slot = room_slot

	func get_slot() -> int:
		return slot

	func get_room_id() -> String:
		return str(hub.state.roomId)

	func get_room_state() -> Dictionary:
		return hub.state.duplicate(true)

	func refresh_state() -> Dictionary:
		return {"state": get_room_state()}

	func command(operation: Dictionary) -> Dictionary:
		return hub.command(slot, operation)

	func is_signaling_connected() -> bool:
		return true

	func connect_signaling() -> Dictionary:
		return {"state": get_room_state()}

	func get_ice_servers() -> Dictionary:
		return {"iceServers": []}

	func send_signal(_kind: String, _epoch: Variant, _negotiation_id: String, _payload: String) -> bool:
		return true


class FakeTransport extends Dependency:
	var hub: FakeHub
	var game: Node
	var slot := -1
	var peer_created := false
	var link_connected := true
	var result_sent_from_source_terminal := false

	func configure(_room_id: String, _epoch: Variant, local_slot: int, remote_slot: int, _negotiation_id: String) -> bool:
		if local_slot not in [0, 1] or remote_slot != 1 - local_slot:
			return false
		slot = local_slot
		return true

	func create_peer(_ice_servers: Array) -> bool:
		peer_created = true
		hub.register_peer(slot, self)
		return true

	func begin_offer() -> bool:
		return slot == 0 and peer_created

	func handle_signal(_message: Dictionary) -> bool:
		return peer_created

	func get_channel_state(channel: String) -> String:
		return "open" if peer_created and link_connected and channel in ["reliable", "input"] else "missing"

	func peer_is_connected() -> bool:
		return peer_created and link_connected

	func set_link_connected(connected: bool) -> void:
		link_connected = connected
		peer_state_changed.emit("connected" if connected else "disconnected")

	func begin_virtual_drain() -> void:
		message_drain_started.emit()

	func end_virtual_drain(messages_delivered: int) -> void:
		message_drain_completed.emit(messages_delivered)

	func send_peer_message(channel: String, type: String, payload: Dictionary) -> bool:
		if not peer_created or not link_connected or channel not in ["reliable", "input"]:
			return false
		if type == "result" and game != null:
			result_sent_from_source_terminal = bool(game.ko_terminal_pending)
		hub.send_peer(slot, channel, type, payload)
		return true

	func close_peer() -> void:
		if peer_created:
			hub.unregister_peer(slot)
		peer_created = false
