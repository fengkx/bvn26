extends Node
class_name OnlineLobbyConnection

signal connection_changed(state: String)
signal peer_message(type: String, payload: Variant, sequence: int)
signal transport_error(code: String)

const PEER_TRANSPORT_SCRIPT := preload("res://online_peer_transport.gd")
# Waiting for the other player is not part of the ICE budget. 10 minutes covers
# a late click; cancel/close still ends the wait immediately.
const PEER_WAIT_TIMEOUT_MS := 10 * 60_000
# Matches services/matchmaking NEGOTIATION_TTL_MS. Starts only once a negotiation id exists.
const DATA_CHANNEL_TIMEOUT_MS := 45_000
const RECONNECT_BASE_MS := 1_000
const RECONNECT_MAX_MS := 30_000
const STATE_POLL_BASE_MS := 5_000
const STATE_POLL_MAX_MS := 30_000
const MAX_BUFFERED_SIGNALS := 256
const MAX_SIGNAL_DELIVERY_ATTEMPTS := 8
const MAX_NEGOTIATION_RESTARTS := 3

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
var _startup_phase := "idle"
var _negotiation_restarts := 0
var _rejected_negotiation_id := ""
var _delivered_signals: Array[Dictionary] = []
var _remote_signaling_down := false
var _peer_wait_timeout_ms := PEER_WAIT_TIMEOUT_MS
var _data_channel_timeout_ms := DATA_CHANNEL_TIMEOUT_MS


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
	var room_state: Variant = _room_client.get_room_state()
	_initial_negotiation_id = ""
	if room_state is Dictionary and room_state.get("negotiation") is Dictionary:
		_initial_negotiation_id = str(room_state["negotiation"].get("id", ""))
	_early_signals.clear()
	_absorb_recent_signals()
	_configured = true
	if not _room_client.is_connected("signaling_message", _on_signaling_message):
		_room_client.connect("signaling_message", _on_signaling_message)
	return true


func start() -> String:
	if _starting:
		return "connection_starting"
	_negotiation_restarts = 0
	_rejected_negotiation_id = ""
	return await _start_until(Time.get_ticks_msec() + _peer_wait_timeout_ms)


func _start_until(peer_deadline: int) -> String:
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
	_starting = true
	_connected = false
	_signaling_frozen = false
	_negotiation_id = ""
	_startup_peer_messages.clear()
	_signal_retry_queue.clear()
	_pending_signals.clear()
	_delivered_signals.clear()
	_remote_signaling_down = false
	_signal_error = ""
	_set_connection_state("connecting")

	_startup_phase = "signaling"
	var signaling_state: Dictionary = await _maintain_signaling(peer_deadline, generation)
	if _was_cancelled(generation):
		return "start_cancelled"
	if signaling_state.has("error"):
		return _fail_start(str(signaling_state.get("error", "signaling_failed")), generation)

	var negotiation: Dictionary
	if _local_slot == 0:
		_startup_phase = "wait_peer"
		var peer_ready: Dictionary = await _wait_for_peer_signaling(peer_deadline, generation)
		if _was_cancelled(generation):
			return "start_cancelled"
		if peer_ready.has("error"):
			return _fail_start(str(peer_ready.get("error", "peer_wait_timeout")), generation)
		_startup_phase = "create_negotiation"
		negotiation = await _create_negotiation(peer_deadline, generation)
	else:
		_startup_phase = "wait_negotiation"
		negotiation = await _wait_for_negotiation(peer_deadline, generation)
	if _was_cancelled(generation):
		return "start_cancelled"
	if negotiation.has("error"):
		return _fail_start(str(negotiation.get("error", "negotiation_failed")), generation)
	_negotiation_id = str(negotiation.get("id", ""))
	if _negotiation_id.is_empty():
		return _fail_start("negotiation_missing", generation)
	_rejected_negotiation_id = ""

	var current_state: Variant = _room_client.get_room_state()
	if not _valid_lobby_state(current_state):
		return _fail_start("room_not_ready", generation)
	var room_id := str(_room_client.get_room_id())
	var remote_slot := 1 - _local_slot
	var ice_deadline := _ice_deadline(negotiation, peer_deadline)
	_startup_phase = "create_peer"
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

	_startup_phase = "data_channels"
	var signal_attempt := 0
	var next_signal_retry := 0
	while Time.get_ticks_msec() < ice_deadline:
		if _was_cancelled(generation):
			return "start_cancelled"
		var latest_state: Variant = _room_client.get_room_state()
		if _local_slot == 0 and _valid_lobby_state(latest_state) and latest_state.get("negotiation") == null:
			return await _restart_negotiation(peer_deadline, generation, "")
		_note_remote_signaling(latest_state)
		if _signal_error == "stale_negotiation":
			return await _restart_negotiation(peer_deadline, generation, _negotiation_id if _local_slot == 1 else "")
		if not _signal_error.is_empty():
			return _fail_start(_signal_error, generation)
		if not _room_client.is_signaling_connected():
			if Time.get_ticks_msec() < next_signal_retry:
				await _room_client.get_tree().process_frame
				continue
			var restored: Dictionary = await _ensure_signaling(ice_deadline, generation)
			if _was_cancelled(generation):
				return "start_cancelled"
			if restored.has("error"):
				var restored_code := str(restored.get("error", "signaling_disconnected"))
				if _fatal_signaling_error(restored_code) or Time.get_ticks_msec() >= ice_deadline:
					return _fail_start(restored_code, generation)
				signal_attempt += 1
				next_signal_retry = Time.get_ticks_msec() + _reconnect_backoff_ms(signal_attempt)
				await _room_client.get_tree().process_frame
				continue
			signal_attempt = 0
			_requeue_pending_signals()
		_flush_signals(Time.get_ticks_msec())
		if _channels_open():
			_startup_phase = "connected"
			_connected = true
			_starting = false
			_signaling_frozen = true
			_used_negotiation_ids[_negotiation_id] = true
			_signal_retry_queue.clear()
			_pending_signals.clear()
			_set_connection_state("connected")
			var startup_messages := _startup_peer_messages
			_startup_peer_messages = []
			for pending_message in startup_messages:
				peer_message.emit(str(pending_message.get("type", "")), pending_message.get("payload"), int(pending_message.get("sequence", 0)))
			return ""
		await _room_client.get_tree().process_frame

	return _fail_start("data_channels_timeout", generation)


func _restart_negotiation(peer_deadline: int, generation: int, rejected_id: String) -> String:
	if generation != _generation or not _starting:
		return "start_cancelled"
	if _negotiation_restarts >= MAX_NEGOTIATION_RESTARTS:
		return _fail_start("stale_negotiation", generation)
	_negotiation_restarts += 1
	if not rejected_id.is_empty():
		_rejected_negotiation_id = rejected_id
	_signal_error = ""
	_early_signals.clear()
	_signal_retry_queue.clear()
	_pending_signals.clear()
	_delivered_signals.clear()
	_remote_signaling_down = false
	_close_peer_transport()
	# Keep _starting set so close() aborts this pause on the next frame.
	var resume_at := Time.get_ticks_msec() + _reconnect_backoff_ms(_negotiation_restarts)
	while generation == _generation and _starting and Time.get_ticks_msec() < resume_at:
		await _room_client.get_tree().process_frame
	if generation != _generation or not _starting:
		return "start_cancelled"
	_starting = false
	return await _start_until(peer_deadline)


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
	_delivered_signals.clear()
	_remote_signaling_down = false
	_signal_error = ""
	_startup_peer_messages.clear()
	_close_peer_transport()
	_set_connection_state("closed")


func get_connection_state() -> String:
	return _connection_state


func get_startup_phase() -> String:
	return _startup_phase


func _ensure_signaling(deadline: int, generation: int) -> Dictionary:
	if _room_client.is_signaling_connected():
		return {"state": _room_client.get_room_state()}
	var result: Dictionary = await _room_client.connect_signaling()
	if _was_cancelled(generation):
		return {"error": "start_cancelled"}
	if Time.get_ticks_msec() >= deadline:
		return {"error": "peer_wait_timeout"}
	if result.has("error"):
		return {"error": str(result.get("error", "signaling_failed"))}
	if not _room_client.is_signaling_connected():
		return {"error": "signaling_not_ready"}
	return result


func _maintain_signaling(deadline: int, generation: int) -> Dictionary:
	var attempt := 0
	while not _was_cancelled(generation) and Time.get_ticks_msec() < deadline:
		var was_connected: bool = bool(_room_client.is_signaling_connected())
		var result: Dictionary = await _ensure_signaling(deadline, generation)
		if _was_cancelled(generation):
			return {"error": "start_cancelled"}
		if not result.has("error"):
			if not was_connected:
				_requeue_pending_signals()
			return result
		var code := str(result.get("error", ""))
		if _fatal_signaling_error(code):
			return result
		if Time.get_ticks_msec() >= deadline:
			return {"error": "peer_wait_timeout"}
		attempt += 1
		var resume_at := Time.get_ticks_msec() + _reconnect_backoff_ms(attempt)
		while not _was_cancelled(generation) and Time.get_ticks_msec() < resume_at and Time.get_ticks_msec() < deadline:
			await _room_client.get_tree().process_frame
	if _was_cancelled(generation):
		return {"error": "start_cancelled"}
	return {"error": "peer_wait_timeout"}


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
		return {"error": "peer_wait_timeout"}
	if reply.has("error"):
		return {"error": str(reply.get("error", "negotiate_failed"))}
	var state: Variant = reply.get("state")
	if not _valid_lobby_state(state):
		return {"error": "room_not_ready"}
	var negotiation := _null_epoch_negotiation(state)
	if negotiation.is_empty() or _negotiation_expired(negotiation):
		return {"error": "negotiation_missing"}
	return negotiation


func _wait_for_peer_signaling(deadline: int, generation: int) -> Dictionary:
	var pacing := _wait_pacing()
	while not _was_cancelled(generation) and Time.get_ticks_msec() < deadline:
		if bool(_room_client.is_signaling_connected()):
			var live := _acceptable_peer_state(_room_client.get_room_state())
			if not live.is_empty():
				return {"state": live}
		var progress: Dictionary = await _service_disconnected_wait(deadline, generation, pacing)
		if progress.has("error"):
			return progress
		if progress.has("state"):
			var refreshed: Variant = progress.get("state")
			if not _valid_lobby_state(refreshed):
				return {"error": "room_not_ready"}
			var ready := _acceptable_peer_state(refreshed)
			if not ready.is_empty():
				return {"state": ready}
		await _room_client.get_tree().process_frame
	if _was_cancelled(generation):
		return {"error": "start_cancelled"}
	return {"error": "peer_wait_timeout"}


func _wait_for_negotiation(deadline: int, generation: int) -> Dictionary:
	var pacing := _wait_pacing()
	while not _was_cancelled(generation) and Time.get_ticks_msec() < deadline:
		if bool(_room_client.is_signaling_connected()):
			var live := _acceptable_negotiation(_room_client.get_room_state())
			if not live.is_empty():
				return live
		var progress: Dictionary = await _service_disconnected_wait(deadline, generation, pacing)
		if progress.has("error"):
			return progress
		if progress.has("state"):
			var refreshed: Variant = progress.get("state")
			if not _valid_lobby_state(refreshed):
				return {"error": "room_not_ready"}
			var negotiation := _acceptable_negotiation(refreshed)
			if not negotiation.is_empty():
				return negotiation
		await _room_client.get_tree().process_frame
	if _was_cancelled(generation):
		return {"error": "start_cancelled"}
	return {"error": "peer_wait_timeout"}


func _wait_pacing() -> Dictionary:
	return {
		"next_reconnect": 0,
		"next_poll": 0,
		"reconnect_attempt": 0,
		"poll_attempt": 0,
	}


# HTTP refresh and socket reconnect run only while signaling is down. A live
# socket already receives room state, so this returns without a request.
func _service_disconnected_wait(deadline: int, generation: int, pacing: Dictionary) -> Dictionary:
	if bool(_room_client.is_signaling_connected()):
		pacing["reconnect_attempt"] = 0
		return {}
	var now := Time.get_ticks_msec()
	if now >= int(pacing["next_reconnect"]):
		var result: Dictionary = await _ensure_signaling(deadline, generation)
		if _was_cancelled(generation):
			return {"error": "start_cancelled"}
		if not result.has("error"):
			_requeue_pending_signals()
			pacing["reconnect_attempt"] = 0
			return {}
		var code := str(result.get("error", ""))
		if _fatal_signaling_error(code):
			return {"error": code}
		pacing["reconnect_attempt"] = int(pacing["reconnect_attempt"]) + 1
		pacing["next_reconnect"] = Time.get_ticks_msec() + _reconnect_backoff_ms(int(pacing["reconnect_attempt"]))
	now = Time.get_ticks_msec()
	if now >= int(pacing["next_poll"]) and not _page_hidden():
		var refreshed: Dictionary = await _room_client.refresh_state()
		pacing["poll_attempt"] = int(pacing["poll_attempt"]) + 1
		pacing["next_poll"] = Time.get_ticks_msec() + _state_poll_backoff_ms(int(pacing["poll_attempt"]))
		if _was_cancelled(generation):
			return {"error": "start_cancelled"}
		if refreshed.has("error"):
			var refresh_code := str(refreshed.get("error", "room_refresh_failed"))
			if _fatal_signaling_error(refresh_code):
				return {"error": refresh_code}
		else:
			return {"state": refreshed.get("state", _room_client.get_room_state())}
	return {}


func _reconnect_backoff_ms(attempt: int) -> int:
	return mini(RECONNECT_MAX_MS, RECONNECT_BASE_MS * (1 << clampi(attempt - 1, 0, 5)))


func _state_poll_backoff_ms(attempt: int) -> int:
	return mini(STATE_POLL_MAX_MS, STATE_POLL_BASE_MS * (1 << clampi(attempt - 1, 0, 3)))


func _page_hidden() -> bool:
	if not OS.has_feature("web"):
		return false
	var document: Variant = JavaScriptBridge.get_interface("document")
	if document == null:
		return false
	return str(document.visibilityState) == "hidden"


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
			else:
				_remember_delivered_signal(pending)
		"error":
			var code := str(message.get("error", "signaling_error"))
			if code == "stale_negotiation":
				if _connected:
					return
				var stale_id := str(message.get("negotiationId", ""))
				if not stale_id.is_empty() and not _negotiation_id.is_empty() and stale_id != _negotiation_id:
					return
			_signal_error = code
		"socket_closed":
			if _connected:
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


func _ice_deadline(negotiation: Dictionary, peer_deadline: int) -> int:
	var now := Time.get_ticks_msec()
	var expires: Variant = negotiation.get("expires")
	var remaining := _data_channel_timeout_ms
	if _integral_number(expires):
		remaining = int(expires) - int(Time.get_unix_time_from_system() * 1000.0)
		if remaining < 0:
			remaining = 0
		remaining = mini(remaining, _data_channel_timeout_ms)
	return mini(peer_deadline, now + remaining)


func _acceptable_peer_state(state: Variant) -> Dictionary:
	if not _valid_lobby_state(state):
		return {}
	if _local_slot != 0:
		return state
	var members: Array = state.get("members")
	var peer: Variant = members[1]
	if not peer is Dictionary:
		return {}
	# Missing on older servers: do not block the host forever.
	if peer.has("signaling") and not bool(peer.get("signaling")):
		return {}
	return state


func _acceptable_negotiation(state: Variant) -> Dictionary:
	if not state is Dictionary:
		return {}
	var negotiation := _null_epoch_negotiation(state)
	if negotiation.is_empty() or _negotiation_expired(negotiation):
		return {}
	var negotiation_id := str(negotiation.get("id", ""))
	if _used_negotiation_ids.has(negotiation_id):
		return {}
	var needs_offer := negotiation_id == _initial_negotiation_id or negotiation_id == _rejected_negotiation_id
	if needs_offer and not _has_early_signal_for_negotiation(negotiation_id):
		return {}
	return negotiation


func _absorb_recent_signals() -> void:
	if _room_client == null or not _room_client.has_method("consume_recent_signals"):
		return
	var pending: Variant = _room_client.consume_recent_signals()
	if not pending is Array:
		return
	for message in pending:
		if not message is Dictionary:
			continue
		if _early_signals.size() >= MAX_BUFFERED_SIGNALS:
			_signal_error = "too_many_early_signals"
			return
		_early_signals.append((message as Dictionary).duplicate(true))


func _remember_delivered_signal(pending: Dictionary) -> void:
	var copy := pending.duplicate(true)
	copy["peer_resends"] = int(copy.get("peer_resends", 0))
	if _delivered_signals.size() >= MAX_BUFFERED_SIGNALS:
		_delivered_signals.pop_front()
	_delivered_signals.append(copy)


func _note_remote_signaling(state: Variant) -> void:
	var flag := _remote_signaling_flag(state)
	if flag == 0:
		_remote_signaling_down = true
	elif flag == 1 and _remote_signaling_down:
		_remote_signaling_down = false
		_requeue_delivered_signals()


func _remote_signaling_flag(state: Variant) -> int:
	if not state is Dictionary:
		return -1
	var members: Variant = state.get("members")
	if not members is Array:
		return -1
	var remote_slot := 1 - _local_slot
	if remote_slot < 0 or remote_slot >= members.size() or not members[remote_slot] is Dictionary:
		return -1
	var peer: Dictionary = members[remote_slot]
	if not peer.has("signaling"):
		return -1
	return 1 if bool(peer.get("signaling")) else 0


func _requeue_delivered_signals() -> void:
	for delivered in _delivered_signals:
		var resends := int(delivered.get("peer_resends", 0))
		if resends >= MAX_NEGOTIATION_RESTARTS:
			continue
		var payload := str(delivered.get("payload", ""))
		var kind := str(delivered.get("kind", ""))
		var already := false
		for queued in _signal_retry_queue:
			if str(queued.get("kind", "")) == kind and str(queued.get("payload", "")) == payload:
				already = true
				break
		if already:
			continue
		var retry := delivered.duplicate(true)
		retry["peer_resends"] = resends + 1
		retry["attempts"] = 0
		retry["retry_at"] = 0
		delivered["peer_resends"] = resends + 1
		_signal_retry_queue.append(retry)


func _requeue_pending_signals() -> void:
	for sequence in _pending_signals.keys():
		var pending: Variant = _pending_signals[sequence]
		if not pending is Dictionary:
			continue
		var retry: Dictionary = pending.duplicate(true)
		retry["retry_at"] = 0
		_signal_retry_queue.push_front(retry)
	_pending_signals.clear()


func _fatal_signaling_error(code: String) -> bool:
	return code in [
		"not_in_room",
		"room_closed",
		"room_expired",
		"unauthorized",
		"session_changed",
		"not_configured",
		"start_cancelled",
		"room_not_ready",
	]


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
