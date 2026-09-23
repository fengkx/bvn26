extends Node
class_name OnlineLobbyConnection

signal connection_changed(state: String)
signal peer_message(type: String, payload: Variant, sequence: int)
signal transport_error(code: String)

const PEER_TRANSPORT_SCRIPT := preload("res://online_peer_transport.gd")
const START_TIMEOUT_MS := 60_000
const NEGOTIATION_POLL_MS := 250
const MAX_BUFFERED_SIGNALS := 256
const MAX_SIGNAL_DELIVERY_ATTEMPTS := 8

var _room_client: Object
var _local_slot := -1
var _ice_servers: Array = []
var _peer_transport: Node
var _peer_transport_factory := Callable()
var _configured := false
var _starting := false
var _connected := false
var _signaling_frozen := true
var _generation := 0
var _connection_state := "new"
var _negotiation_id := ""
var _configured_room_id := ""
var _initial_negotiation_id := ""
var _used_negotiation_ids: Dictionary = {}
var _early_signals: Array[Dictionary] = []
var _startup_peer_messages: Array[Dictionary] = []
var _signal_retry_queue: Array[Dictionary] = []
var _pending_signals: Dictionary = {}
var _signal_error := ""


func _process(_delta: float) -> void:
	if _connected and not _channels_open():
		_connected = false
		_set_connection_state("disconnected")
		transport_error.emit("data_channel_closed")


func configure(room_client: Object, local_slot: int, ice_servers: Array) -> bool:
	if _starting or _connected or _peer_transport != null:
		return false
	if not is_instance_valid(room_client) or local_slot not in [0, 1]:
		return false
	for method_name in ["get_room_id", "get_slot", "get_room_state", "is_signaling_connected", "connect_signaling", "refresh_state", "command", "send_signal", "get_last_signal_sequence"]:
		if not room_client.has_method(method_name):
			return false
	if not room_client.has_signal("signaling_message"):
		return false
	var room_id := str(room_client.get_room_id())
	if room_id.is_empty() or int(room_client.get_slot()) != local_slot:
		return false
	if _configured and is_instance_valid(_room_client) and _room_client.is_connected("signaling_message", Callable(self, "_on_signaling_message")):
		_room_client.disconnect("signaling_message", _on_signaling_message)
	if _configured_room_id != room_id:
		_used_negotiation_ids.clear()
	_configured_room_id = room_id
	_room_client = room_client
	_local_slot = local_slot
	_ice_servers = ice_servers.duplicate(true)
	_signaling_frozen = false
	if not _room_client.is_connected("signaling_message", _on_signaling_message):
		_room_client.connect("signaling_message", _on_signaling_message)
	var room_state: Variant = _room_client.get_room_state()
	_initial_negotiation_id = ""
	if room_state is Dictionary and room_state.get("negotiation") is Dictionary:
		_initial_negotiation_id = str(room_state["negotiation"].get("id", ""))
	_configured = true
	return true


func start() -> String:
	if not _configured or not is_instance_valid(_room_client):
		return "not_configured"
	if _connected and _channels_open():
		return ""
	if _starting:
		return "connection_starting"
	if _peer_transport != null:
		_close_peer_transport()
	if _room_client_has_pending_command():
		return "room_command_uncertain"
	if _room_client_command_in_flight():
		return "room_command_in_flight"

	_generation += 1
	var generation := _generation
	var deadline := Time.get_ticks_msec() + START_TIMEOUT_MS
	_starting = true
	_connected = false
	_signaling_frozen = false
	_negotiation_id = ""
	_startup_peer_messages.clear()
	_signal_retry_queue.clear()
	_pending_signals.clear()
	_signal_error = ""
	_set_connection_state("connecting")

	var signaling_state: Dictionary = await _ensure_signaling(deadline, generation)
	if _was_cancelled(generation):
		return "start_cancelled"
	if signaling_state.has("error"):
		return _fail_start(str(signaling_state.get("error", "signaling_failed")), generation)
	if Time.get_ticks_msec() >= deadline:
		return _fail_start("start_timeout", generation)

	var negotiation: Dictionary
	if _local_slot == 0:
		negotiation = await _create_negotiation(deadline, generation)
	else:
		negotiation = await _wait_for_negotiation(deadline, generation)
	if _was_cancelled(generation):
		return "start_cancelled"
	if negotiation.has("error"):
		return _fail_start(str(negotiation.get("error", "negotiation_failed")), generation)
	_negotiation_id = str(negotiation.get("id", ""))
	if _negotiation_id.is_empty():
		return _fail_start("negotiation_missing", generation)
	_used_negotiation_ids[_negotiation_id] = true

	var current_state: Variant = _room_client.get_room_state()
	if not _valid_lobby_state(current_state):
		return _fail_start("room_not_ready", generation)
	var room_id := str(_room_client.get_room_id())
	var remote_slot := 1 - _local_slot
	_peer_transport = _new_peer_transport()
	if _peer_transport == null:
		return _fail_start("peer_transport_unavailable", generation)
	add_child(_peer_transport)
	_peer_transport.outgoing_signal.connect(_on_outgoing_signal)
	_peer_transport.peer_state_changed.connect(_on_peer_state_changed)
	_peer_transport.peer_message.connect(_on_peer_data_message)
	_peer_transport.transport_error.connect(_on_peer_transport_error)
	if not _peer_transport.configure(room_id, null, _local_slot, remote_slot, _negotiation_id):
		return _fail_start("peer_configuration_failed", generation)
	if not _peer_transport.create_peer(_ice_servers):
		return _fail_start("peer_creation_failed", generation)
	for early_signal in _early_signals:
		if not _signal_matches_negotiation(early_signal, _negotiation_id, remote_slot):
			continue
		if not _peer_transport.handle_signal(early_signal):
			return _fail_start("queued_signal_rejected", generation)
	_early_signals.clear()
	if _local_slot == 0 and not _peer_transport.begin_offer():
		return _fail_start("offer_creation_failed", generation)

	while Time.get_ticks_msec() < deadline:
		if _was_cancelled(generation):
			return "start_cancelled"
		if not _signal_error.is_empty():
			return _fail_start(_signal_error, generation)
		_flush_signals(Time.get_ticks_msec())
		if _channels_open():
			_connected = true
			_starting = false
			_signaling_frozen = true
			_signal_retry_queue.clear()
			_pending_signals.clear()
			_set_connection_state("connected")
			var startup_messages := _startup_peer_messages
			_startup_peer_messages = []
			for pending_message in startup_messages:
				peer_message.emit(str(pending_message.get("type", "")), pending_message.get("payload"), int(pending_message.get("sequence", 0)))
			return ""
		if not _room_client.is_signaling_connected():
			return _fail_start("signaling_disconnected", generation)
		await _room_client.get_tree().process_frame

	return _fail_start("data_channels_timeout", generation)


func send_peer_message(message_type: String, payload: Variant) -> bool:
	if not _connected or not _channels_open() or _peer_transport == null:
		return false
	return _peer_transport.send_peer_message("reliable", message_type, payload)


func close() -> void:
	_generation += 1
	_starting = false
	_connected = false
	_signaling_frozen = true
	_negotiation_id = ""
	_early_signals.clear()
	_signal_retry_queue.clear()
	_pending_signals.clear()
	_signal_error = ""
	_startup_peer_messages.clear()
	_close_peer_transport()
	_set_connection_state("closed")


func get_connection_state() -> String:
	return _connection_state


func _ensure_signaling(deadline: int, generation: int) -> Dictionary:
	if _room_client.is_signaling_connected():
		return {"state": _room_client.get_room_state()}
	var result: Dictionary = await _room_client.connect_signaling()
	if _was_cancelled(generation):
		return {"error": "start_cancelled"}
	if Time.get_ticks_msec() >= deadline:
		return {"error": "start_timeout"}
	if result.has("error"):
		return {"error": str(result.get("error", "signaling_failed"))}
	if not _room_client.is_signaling_connected():
		return {"error": "signaling_not_ready"}
	return result


func _create_negotiation(deadline: int, generation: int) -> Dictionary:
	var reply: Dictionary = await _room_client.command({"type": "negotiate", "epoch": null})
	while not _was_cancelled(generation) and Time.get_ticks_msec() < deadline:
		if not (reply.get("uncertain", false) or reply.get("error") == "command_outcome_uncertain"):
			break
		await _room_client.get_tree().create_timer(0.5).timeout
		if _was_cancelled(generation):
			return {"error": "start_cancelled"}
		reply = await _room_client.retry_pending_command()
	if _was_cancelled(generation):
		return {"error": "start_cancelled"}
	if Time.get_ticks_msec() >= deadline:
		return {"error": "start_timeout"}
	if reply.has("error"):
		return {"error": str(reply.get("error", "negotiate_failed"))}
	var state: Variant = reply.get("state")
	if not _valid_lobby_state(state):
		return {"error": "room_not_ready"}
	var negotiation := _null_epoch_negotiation(state)
	if negotiation.is_empty() or _negotiation_expired(negotiation):
		return {"error": "negotiation_missing"}
	return negotiation


func _wait_for_negotiation(deadline: int, generation: int) -> Dictionary:
	while not _was_cancelled(generation) and Time.get_ticks_msec() < deadline:
		var result: Dictionary = await _room_client.refresh_state()
		if _was_cancelled(generation):
			return {"error": "start_cancelled"}
		if result.has("error"):
			return {"error": str(result.get("error", "room_refresh_failed"))}
		var state: Variant = result.get("state", _room_client.get_room_state())
		if not _valid_lobby_state(state):
			return {"error": "room_not_ready"}
		var negotiation := _null_epoch_negotiation(state)
		if not negotiation.is_empty() \
			and not _used_negotiation_ids.has(str(negotiation.get("id", ""))) \
			and not _negotiation_expired(negotiation) \
			and (str(negotiation.get("id", "")) != _initial_negotiation_id \
				or _has_early_signal_for_negotiation(str(negotiation.get("id", "")))) \
			and not _used_negotiation_ids.has(str(negotiation.get("id", ""))):
			return negotiation
		await _room_client.get_tree().create_timer(NEGOTIATION_POLL_MS / 1000.0).timeout
	return {"error": "negotiation_timeout"}


func _on_signaling_message(message: Dictionary) -> void:
	if not _configured or _signaling_frozen:
		return
	match message.get("type"):
		"signal":
			if _peer_transport == null or _negotiation_id.is_empty():
				if _early_signals.size() >= MAX_BUFFERED_SIGNALS:
					_signal_error = "too_many_early_signals"
				else:
					_early_signals.append(message.duplicate(true))
			elif not _signal_matches_negotiation(message, _negotiation_id, 1 - _local_slot):
				return
			elif not _peer_transport.handle_signal(message):
				_signal_error = "peer_signal_rejected"
		"signal_ack":
			var sequence_value: Variant = message.get("seq")
			if not _integral_number(sequence_value):
				_signal_error = "invalid_signal_ack"
				return
			var sequence := int(sequence_value)
			var pending: Variant = _pending_signals.get(sequence)
			if not pending is Dictionary:
				return
			_pending_signals.erase(sequence)
			if not bool(message.get("delivered", false)):
				var retry: Dictionary = pending.duplicate(true)
				var attempts := int(retry.get("attempts", 0))
				if attempts >= MAX_SIGNAL_DELIVERY_ATTEMPTS:
					_signal_error = "signal_delivery_failed"
				else:
					retry["retry_at"] = Time.get_ticks_msec() + _signal_retry_delay_ms(attempts)
					_signal_retry_queue.push_front(retry)
		"error":
			var code := str(message.get("error", "signaling_error"))
			if _connected and code == "stale_negotiation":
				return
			_signal_error = code
		"socket_closed":
			_signal_error = "signaling_disconnected"


func _on_outgoing_signal(kind: String, message_epoch: Variant, negotiation_id: String, payload: String) -> void:
	if _signaling_frozen:
		return
	if message_epoch != null or negotiation_id != _negotiation_id:
		_signal_error = "unexpected_lobby_signal_identity"
		return
	if not ["offer", "answer", "candidate"].has(kind):
		_signal_error = "invalid_lobby_signal_kind"
		return
	_signal_retry_queue.append({
		"kind": kind,
		"epoch": null,
		"negotiation_id": negotiation_id,
		"payload": payload,
		"attempts": 0,
		"retry_at": 0,
	})


func _flush_signals(now_ms: int) -> void:
	if _room_client == null or not _room_client.is_signaling_connected():
		return
	if not _pending_signals.is_empty() or _signal_retry_queue.is_empty():
		return
	var item: Dictionary = _signal_retry_queue[0]
	if int(item.get("retry_at", 0)) > now_ms:
		return
	var attempts := int(item.get("attempts", 0)) + 1
	if attempts > MAX_SIGNAL_DELIVERY_ATTEMPTS:
		_signal_retry_queue.pop_front()
		_signal_error = "signal_delivery_failed"
		return
	item["attempts"] = attempts
	if not _room_client.send_signal(str(item.kind), null, str(item.negotiation_id), str(item.payload)):
		if attempts >= MAX_SIGNAL_DELIVERY_ATTEMPTS:
			_signal_retry_queue.pop_front()
			_signal_error = "signal_delivery_failed"
		else:
			item["retry_at"] = now_ms + _signal_retry_delay_ms(attempts)
		return
	_signal_retry_queue.pop_front()
	var sequence_value: Variant = _room_client.get_last_signal_sequence()
	if not _integral_number(sequence_value) or int(sequence_value) < 0:
		_signal_error = "signaling_sequence_unavailable"
		return
	_pending_signals[int(sequence_value)] = item.duplicate(true)


func _on_peer_data_message(channel: String, message_type: String, payload: Variant, sequence: int) -> void:
	if channel != "reliable":
		return
	if _connected:
		peer_message.emit(message_type, payload, sequence)
	elif _starting:
		if _startup_peer_messages.size() >= MAX_BUFFERED_SIGNALS:
			_signal_error = "too_many_startup_peer_messages"
		else:
			_startup_peer_messages.append({"type": message_type, "payload": payload, "sequence": sequence})


func _on_peer_state_changed(state: String) -> void:
	if _starting:
		if state in ["failed", "closed"]:
			_signal_error = "peer_" + state
		else:
			_set_connection_state("connecting")
		return
	if _connected and state in ["disconnected", "failed", "closed"]:
		_connected = false
		_set_connection_state(state)
		transport_error.emit("peer_" + state)


func _on_peer_transport_error(code: String) -> void:
	if _starting:
		_signal_error = code
		return
	if _connected:
		_connected = false
		_set_connection_state("failed")
		transport_error.emit(code)


func _fail_start(code: String, generation: int) -> String:
	if generation == _generation:
		_starting = false
		_connected = false
		_signaling_frozen = true
		_signal_retry_queue.clear()
		_pending_signals.clear()
		_close_peer_transport()
		_set_connection_state("failed")
		transport_error.emit(code)
	return code


func _valid_lobby_state(value: Variant) -> bool:
	if not value is Dictionary or value.get("phase") != "lobby":
		return false
	if str(value.get("id", "")) != str(_room_client.get_room_id()):
		return false
	var members: Variant = value.get("members")
	return members is Array and members.size() == 2 and members[0] is Dictionary and members[1] is Dictionary


func _null_epoch_negotiation(state: Dictionary) -> Dictionary:
	if not _valid_lobby_state(state):
		return {}
	var negotiation: Variant = state.get("negotiation")
	if not negotiation is Dictionary or negotiation.get("epoch") != null:
		return {}
	var negotiation_id: Variant = negotiation.get("id")
	if not negotiation_id is String or negotiation_id.is_empty():
		return {}
	return negotiation.duplicate(true)


func _signal_matches_negotiation(message: Dictionary, negotiation_id: String, remote_slot: int) -> bool:
	return message.get("type") == "signal" \
		and message.get("epoch") == null \
		and message.get("negotiationId") == negotiation_id \
		and _integral_number(message.get("from")) \
		and int(message.get("from")) == remote_slot \
		and _integral_number(message.get("seq")) \
		and ["offer", "answer", "candidate"].has(message.get("kind")) \
		and message.get("payload") is String \
		and not str(message.get("payload", "")).is_empty()


func _has_early_signal_for_negotiation(negotiation_id: String) -> bool:
	for message in _early_signals:
		if _signal_matches_negotiation(message, negotiation_id, 1 - _local_slot):
			return true
	return false


func _negotiation_expired(negotiation: Dictionary) -> bool:
	var expires: Variant = negotiation.get("expires")
	if not _integral_number(expires):
		return true
	return int(expires) <= int(Time.get_unix_time_from_system() * 1000.0)


func _signal_retry_delay_ms(attempt: int) -> int:
	return mini(4_000, 250 * (1 << clampi(attempt - 1, 0, 4)))


func _room_client_has_pending_command() -> bool:
	return _room_client.has_method("has_uncertain_command") and bool(_room_client.has_uncertain_command())


func _room_client_command_in_flight() -> bool:
	return _room_client.has_method("is_command_in_flight") and bool(_room_client.is_command_in_flight())


func _channels_open() -> bool:
	return _peer_transport != null \
		and _peer_transport.get_connection_state() == "connected" \
		and _peer_transport.get_channel_state("reliable") == "open" \
		and _peer_transport.get_channel_state("input") == "open"


func _new_peer_transport() -> Node:
	if _peer_transport_factory.is_valid():
		var injected: Variant = _peer_transport_factory.call()
		return injected if injected is Node else null
	return PEER_TRANSPORT_SCRIPT.new()


func _close_peer_transport() -> void:
	if _peer_transport != null and is_instance_valid(_peer_transport):
		if _peer_transport.has_method("close_peer"):
			_peer_transport.close_peer()
		_peer_transport.queue_free()
	_peer_transport = null


func _was_cancelled(generation: int) -> bool:
	return generation != _generation or not _starting


func _set_connection_state(state: String) -> void:
	if _connection_state == state:
		return
	_connection_state = state
	connection_changed.emit(state)


func _integral_number(value: Variant) -> bool:
	return (value is int or value is float) and is_finite(float(value)) and floor(float(value)) == float(value)
