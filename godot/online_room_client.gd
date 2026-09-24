extends Node
class_name OnlineRoomClient

signal state_changed(state: Dictionary)
signal signaling_message(message: Dictionary)
signal socket_state_changed(connected: bool)
signal error(code: String)

const PROTOCOL_VERSION := 1
const MAX_HTTP_BODY_BYTES := 16_384
const MAX_SIGNAL_BYTES := 16_384
const REQUEST_TIMEOUT_SECONDS := 15.0
const SOCKET_TIMEOUT_MS := 15_000
const SIGNAL_KINDS := ["offer", "answer", "candidate"]

var _base_url := ""
var _lifecycle_generation := 0
var _session_token := ""
var _invite_token := ""
var _invite_code := ""
var _room_id := ""
var _slot := -1
var _room_state: Dictionary = {}
var _last_room_revision := -1
var _last_accepted_seq := 0
var _pending_command: Dictionary = {}
var _pending_admission: Dictionary = {}
var _command_in_flight := false
var _admission_in_flight := false

var _socket: WebSocketPeer
var _socket_connecting := false
var _socket_waiting_for_state := false
var _socket_initial_state_received := false
var _socket_last_error := ""
var _socket_last_ping_ms := 0
var _signal_sequence := -1
var _socket_attempt_id := 0
var _last_http_diagnostic: Dictionary = {}


func get_last_http_diagnostic() -> Dictionary:
	return _last_http_diagnostic.duplicate(true)


func configure_service(base_url: String) -> bool:
	var normalized := base_url.strip_edges().trim_suffix("/")
	if not normalized.begins_with("https://") and not normalized.begins_with("http://"):
		emit_signal("error", "invalid_service_url")
		return false
	if not _room_id.is_empty() and normalized != _base_url:
		emit_signal("error", "service_change_requires_reset")
		return false
	_base_url = normalized
	return true


func create_room(nickname: String, compatibility: Dictionary) -> Dictionary:
	if not _can_admit():
		return _failure("client_busy")
	if not _validate_nickname(nickname) or not _validate_compatibility(compatibility):
		return _failure("invalid_client_input")
	var create_token := _new_token()
	var session_token := _new_token()
	var invite_token := _new_token()
	var attempts := 0
	while attempts < 4 and (create_token == session_token or create_token == invite_token or session_token == invite_token):
		invite_token = _new_token()
		attempts += 1
	if create_token.is_empty() or session_token.is_empty() or invite_token.is_empty() \
		or create_token == session_token or create_token == invite_token or session_token == invite_token:
		return _failure("secure_random_unavailable")
	var body := {
		"createToken": create_token,
		"sessionToken": session_token,
		"inviteToken": invite_token,
		"nickname": nickname.strip_edges(),
		"compatibility": compatibility.duplicate(true),
	}
	_pending_admission = {
		"kind": "create",
		"body": JSON.stringify(body),
		"sessionToken": session_token,
		"inviteToken": invite_token,
	}
	return await _send_pending_admission()


func join_room(room_id: String, invite_token: String, nickname: String, compatibility: Dictionary) -> Dictionary:
	if not _can_admit():
		return _failure("client_busy")
	if not _is_room_id(room_id) or not _is_token(invite_token):
		return _failure("invalid_invitation")
	if not _validate_nickname(nickname) or not _validate_compatibility(compatibility):
		return _failure("invalid_client_input")
	var session_token := _new_token()
	if session_token.is_empty() or session_token == invite_token:
		return _failure("secure_random_unavailable")
	var body := {
		"sessionToken": session_token,
		"inviteToken": invite_token,
		"nickname": nickname.strip_edges(),
		"compatibility": compatibility.duplicate(true),
	}
	_pending_admission = {
		"kind": "join",
		"roomId": room_id,
		"body": JSON.stringify(body),
		"sessionToken": session_token,
		"inviteToken": invite_token,
	}
	return await _send_pending_admission()


func join_by_code(code: String, nickname: String, compatibility: Dictionary) -> Dictionary:
	if not _can_admit():
		return _failure("client_busy")
	var normalized_code := code.strip_edges().to_lower()
	if not _is_invite_code(normalized_code):
		return _failure("invalid_invitation")
	if not _validate_nickname(nickname) or not _validate_compatibility(compatibility):
		return _failure("invalid_client_input")
	var session_token := _new_token()
	if session_token.is_empty():
		return _failure("secure_random_unavailable")
	var body := {
		"code": normalized_code,
		"sessionToken": session_token,
		"nickname": nickname.strip_edges(),
		"compatibility": compatibility.duplicate(true),
	}
	_pending_admission = {
		"kind": "join_by_code",
		"body": JSON.stringify(body),
		"sessionToken": session_token,
	}
	return await _send_pending_admission()


func rotate_invitation() -> Dictionary:
	if not _has_membership() or _slot != 0:
		return _failure("not_room_owner")
	if has_uncertain_command():
		return _failure("command_outcome_uncertain", true)
	var new_token := _new_token()
	if new_token.is_empty() or new_token == _invite_token:
		return _failure("secure_random_unavailable")
	return await command({"type": "reinvite", "inviteToken": new_token})


func retry_pending_admission() -> Dictionary:
	if _pending_admission.is_empty():
		return _failure("no_pending_admission")
	if _admission_in_flight:
		return _failure("request_in_flight")
	return await _send_pending_admission()


func refresh_state() -> Dictionary:
	if not _has_membership():
		return _failure("not_in_room")
	var generation := _lifecycle_generation
	var response: Dictionary = await _request_json(
		HTTPClient.METHOD_GET,
		"/v1/rooms/%s/state" % _room_id,
		"",
		true
	)
	if generation != _lifecycle_generation:
		return {"error": "session_changed", "uncertain": false}
	if not response.get("ok", false):
		return _report_request_failure(response)
	var value: Variant = response.get("value")
	if _room_state_reply_missing_network_profile(value):
		return _failure("server_upgrade_required")
	if not _validate_state_reply(value):
		return _failure("invalid_service_response")
	_accept_state(value["state"])
	return {"slot": _slot, "state": _room_state.duplicate(true)}


func command(operation: Dictionary) -> Dictionary:
	if not _has_membership():
		return _failure("not_in_room")
	if not _pending_command.is_empty():
		return _failure("command_outcome_uncertain", true)
	if _command_in_flight:
		return _failure("request_in_flight")
	if operation.is_empty() or not operation.has("type") or not operation["type"] is String:
		return _failure("invalid_operation")
	var seq := _last_accepted_seq + 1
	var request_body := {
		"version": PROTOCOL_VERSION,
		"seq": seq,
		"operation": operation.duplicate(true),
	}
	_pending_command = {"seq": seq, "body": JSON.stringify(request_body)}
	return await _send_pending_command()


func retry_pending_command() -> Dictionary:
	if _pending_command.is_empty():
		return _failure("no_pending_command")
	if _command_in_flight:
		return _failure("request_in_flight")
	return await _send_pending_command()


func get_ice_servers() -> Dictionary:
	if not _has_membership():
		return _failure("not_in_room")
	var generation := _lifecycle_generation
	var response: Dictionary = await _request_json(
		HTTPClient.METHOD_POST,
		"/v1/rooms/%s/ice" % _room_id,
		"{}",
		true
	)
	if generation != _lifecycle_generation:
		return {"error": "session_changed", "uncertain": false}
	if not response.get("ok", false):
		return _report_request_failure(response)
	var value: Variant = response.get("value")
	var normalized := _normalize_ice_response(value)
	if normalized.is_empty():
		return _failure("invalid_service_response")
	return normalized


func connect_signaling() -> Dictionary:
	if not _has_membership():
		return _failure("not_in_room")
	if _socket != null and _socket.get_ready_state() == WebSocketPeer.STATE_OPEN and _socket_initial_state_received:
		return {"state": _room_state.duplicate(true)}
	if _socket_connecting:
		return _failure("socket_connecting")
	_close_socket(false)
	_socket_attempt_id += 1
	var socket_attempt := _socket_attempt_id
	var generation := _lifecycle_generation
	_signal_sequence = -1
	_socket_connecting = true
	_socket_waiting_for_state = false
	_socket_initial_state_received = false
	_socket_last_error = ""

	var ticket_reply: Dictionary = await _request_json(
		HTTPClient.METHOD_POST,
		"/v1/rooms/%s/ticket" % _room_id,
		"{}",
		true
	)
	if generation != _lifecycle_generation or socket_attempt != _socket_attempt_id:
		return {"error": "session_changed", "uncertain": false}
	if not ticket_reply.get("ok", false):
		_socket_connecting = false
		return _report_request_failure(ticket_reply)
	var ticket_value: Variant = ticket_reply.get("value")
	if not ticket_value is Dictionary or not _is_token(str(ticket_value.get("ticket", ""))):
		_socket_connecting = false
		return _failure("invalid_service_response")

	_socket = WebSocketPeer.new()
	_socket.supported_protocols = PackedStringArray(["bvn.v1", str(ticket_value["ticket"])])
	_socket.max_queued_packets = 256
	_socket_last_ping_ms = Time.get_ticks_msec()
	var websocket_url := _websocket_url("/v1/rooms/%s/socket" % _room_id)
	var connect_error := _socket.connect_to_url(websocket_url)
	if connect_error != OK:
		_close_socket(false)
		return _failure("socket_connect_failed")
	_socket_waiting_for_state = true
	set_process(true)
	var deadline := Time.get_ticks_msec() + SOCKET_TIMEOUT_MS
	while Time.get_ticks_msec() < deadline:
		if generation != _lifecycle_generation or socket_attempt != _socket_attempt_id:
			return {"error": "socket_cancelled", "uncertain": false}
		if _socket_last_error != "":
			var failure_code := _socket_last_error
			_close_socket(false)
			return _failure(failure_code)
		if _socket != null and _socket.get_ready_state() == WebSocketPeer.STATE_OPEN:
			if _socket.get_selected_protocol() != "bvn.v1":
				_close_socket(false)
				return _failure("socket_protocol_rejected")
			if _socket_initial_state_received:
				_socket_connecting = false
				_socket_last_ping_ms = Time.get_ticks_msec()
				socket_state_changed.emit(true)
				return {"state": _room_state.duplicate(true)}
		if _socket.get_ready_state() == WebSocketPeer.STATE_CLOSED:
			var close_code := _socket.get_close_code()
			_close_socket(false)
			return _failure("socket_closed_%d" % close_code)
		await get_tree().process_frame
	_socket_connecting = false
	_close_socket(false)
	return _failure("socket_timeout")


func send_signal(kind: String, epoch: Variant, negotiation_id: String, payload: String) -> bool:
	if _socket == null or _socket.get_ready_state() != WebSocketPeer.STATE_OPEN:
		return false
	if not SIGNAL_KINDS.has(kind) or not _is_uuid(negotiation_id):
		return false
	if epoch != null and (not epoch is String or not _is_uuid(epoch)):
		return false
	if payload.is_empty() or payload.length() > 12_000:
		return false
	var message := {
		"version": PROTOCOL_VERSION,
		"type": "signal",
		"seq": _signal_sequence + 1,
		"epoch": epoch,
		"negotiationId": negotiation_id,
		"kind": kind,
		"payload": payload,
	}
	var encoded := JSON.stringify(message)
	if encoded.to_utf8_buffer().size() > MAX_SIGNAL_BYTES:
		return false
	if _socket.send_text(encoded) != OK:
		return false
	_signal_sequence += 1
	return true


func close_signaling() -> void:
	_close_socket(true)


func clear_credentials() -> void:
	_lifecycle_generation += 1
	close_signaling()
	_session_token = ""
	_invite_token = ""
	_invite_code = ""
	_room_id = ""
	_slot = -1
	_room_state.clear()
	_last_room_revision = -1
	_last_accepted_seq = 0
	_pending_command.clear()
	_pending_admission.clear()
	_signal_sequence = -1


func get_room_id() -> String:
	return _room_id


func get_invite_code() -> String:
	return _invite_code


func get_slot() -> int:
	return _slot


func get_room_state() -> Dictionary:
	return _room_state.duplicate(true)


func is_signaling_connected() -> bool:
	return _socket != null \
		and _socket.get_ready_state() == WebSocketPeer.STATE_OPEN \
		and _socket_initial_state_received


func get_last_signal_sequence() -> int:
	return _signal_sequence


func has_uncertain_command() -> bool:
	return not _pending_command.is_empty()


func is_command_in_flight() -> bool:
	return _command_in_flight


func is_valid_network_profile(value: Variant) -> bool:
	return _validate_network_profile(value)


func _process(_delta: float) -> void:
	if _socket == null:
		return
	_socket.poll()
	if _socket.get_ready_state() == WebSocketPeer.STATE_OPEN:
		while _socket.get_available_packet_count() > 0:
			var packet: PackedByteArray = _socket.get_packet()
			_handle_socket_packet(packet)
			if _socket_last_error != "":
				_socket.close(1002, "invalid_service_message")
				break
		if Time.get_ticks_msec() - _socket_last_ping_ms >= 60_000:
			_socket.send_text("ping")
			_socket_last_ping_ms = Time.get_ticks_msec()
	elif _socket.get_ready_state() == WebSocketPeer.STATE_CLOSED and not _socket_connecting:
		var close_code := _socket.get_close_code()
		var close_reason := _socket.get_close_reason()
		_socket = null
		socket_state_changed.emit(false)
		if close_code != 1000:
			error.emit("socket_closed_%d" % close_code)
		if not close_reason.is_empty():
			signaling_message.emit({"type": "socket_closed", "code": close_code})


func _send_pending_admission() -> Dictionary:
	if _admission_in_flight:
		return _failure("request_in_flight")
	_admission_in_flight = true
	var generation := _lifecycle_generation
	var pending := _pending_admission.duplicate(true)
	var path := "/v1/rooms"
	if pending["kind"] == "join":
		path = "/v1/rooms/%s/join" % pending["roomId"]
	elif pending["kind"] == "join_by_code":
		path = "/v1/rooms/join-by-code"
	var response: Dictionary = await _request_json(
		HTTPClient.METHOD_POST, path, str(pending["body"]), false
	)
	_admission_in_flight = false
	if generation != _lifecycle_generation:
		return {"error": "session_changed", "uncertain": false}
	if not response.get("ok", false):
		if response.get("uncertain", false):
			return _report_request_failure(response, true)
		_pending_admission.clear()
		return _report_request_failure(response)
	var value: Variant = response.get("value")
	var is_create: bool = pending["kind"] == "create"
	if _room_state_reply_missing_network_profile(value):
		return _failure("server_upgrade_required", true)
	if not value is Dictionary or not _validate_admission_reply(value, is_create):
		return _failure("invalid_service_response", true)
	var expected_room_id := str(value["roomId"])
	if pending["kind"] == "join" and expected_room_id != pending["roomId"]:
		return _failure("invalid_service_response", true)
	_session_token = str(pending["sessionToken"])
	_invite_token = str(pending.get("inviteToken", "")) if is_create else ""
	_invite_code = str(value.get("inviteCode", "")) if is_create else ""
	_room_id = expected_room_id
	_slot = int(value["slot"])
	_pending_admission.clear()
	_accept_state(value["state"])
	var result := {"room_id": _room_id, "slot": _slot, "state": _room_state.duplicate(true)}
	if is_create:
		result["invite_token"] = _invite_token
		result["invite_code"] = _invite_code
	return result


func _send_pending_command() -> Dictionary:
	if _command_in_flight:
		return _failure("request_in_flight")
	_command_in_flight = true
	var generation := _lifecycle_generation
	var pending := _pending_command.duplicate(true)
	var response: Dictionary = await _request_json(
		HTTPClient.METHOD_POST,
		"/v1/rooms/%s/commands" % _room_id,
		str(pending["body"]),
		true
	)
	_command_in_flight = false
	if generation != _lifecycle_generation:
		return {"error": "session_changed", "uncertain": false}
	if not response.get("ok", false):
		if response.get("uncertain", false):
			return _report_request_failure(response, true)
		_pending_command.clear()
		return _report_request_failure(response)
	var value: Variant = response.get("value")
	var expected_seq := int(pending["seq"])
	if not value is Dictionary or not _is_integer(value.get("acceptedSeq")) or int(value["acceptedSeq"]) != expected_seq:
		return _failure("invalid_command_ack", true)
	if _room_state_reply_missing_network_profile(value):
		return _failure("server_upgrade_required", true)
	if not value.has("state") or not _validate_room_state(value["state"], _room_id, _slot, true):
		return _failure("invalid_command_ack", true)
	var request_body: Variant = JSON.parse_string(str(pending.get("body", "")))
	var operation: Dictionary = request_body.get("operation", {}) if request_body is Dictionary else {}
	if operation.get("type") == "reinvite" and not _is_invite_code(value.get("inviteCode")):
		return _failure("invalid_command_ack", true)
	_last_accepted_seq = expected_seq
	_pending_command.clear()
	_accept_state(value["state"])
	var result := {"acceptedSeq": expected_seq, "state": _room_state.duplicate(true)}
	if operation.get("type") == "reinvite":
		_invite_token = str(operation.get("inviteToken", ""))
		_invite_code = str(value.get("inviteCode", ""))
		result["invite_code"] = _invite_code
	return result


func _request_json(method: int, path: String, body_text: String, authenticated: bool) -> Dictionary:
	_last_http_diagnostic = {"phase": "not_started", "transportResult": "not_started", "httpStatus": 0}
	if _base_url.is_empty():
		return {"ok": false, "error": "service_not_configured", "uncertain": false}
	if body_text.to_utf8_buffer().size() > MAX_HTTP_BODY_BYTES:
		return {"ok": false, "error": "request_too_large", "uncertain": false}
	var request_node := HTTPRequest.new()
	request_node.timeout = REQUEST_TIMEOUT_SECONDS
	request_node.body_size_limit = MAX_HTTP_BODY_BYTES
	add_child(request_node)
	var headers := PackedStringArray(["Accept: application/json"])
	if not body_text.is_empty():
		headers.append("Content-Type: application/json")
	if authenticated:
		if _session_token.is_empty():
			request_node.queue_free()
			return {"ok": false, "error": "not_authenticated", "uncertain": false}
		headers.append("Authorization: Bearer " + _session_token)
	var request_error := request_node.request(_base_url + path, headers, method, body_text)
	if request_error != OK:
		request_node.queue_free()
		_last_http_diagnostic = {
			"phase": "request_start",
			"transportResult": "request_start_failed",
			"requestErrorCode": request_error,
			"httpStatus": 0,
		}
		var start_failure := {"ok": false, "error": "http_request_start_failed", "uncertain": true}
		start_failure.merge(_last_http_diagnostic, true)
		return start_failure
	var completed: Array = await request_node.request_completed
	request_node.queue_free()
	var result_code := int(completed[0])
	var response_code := int(completed[1])
	var response_body: PackedByteArray = completed[3]
	_last_http_diagnostic = {
		"phase": "request_completed",
		"transportResult": result_code,
		"httpStatus": response_code,
	}
	if result_code != HTTPRequest.RESULT_SUCCESS:
		var transport_failure := {"ok": false, "error": "http_transport_failed", "uncertain": true}
		transport_failure.merge(_last_http_diagnostic, true)
		return transport_failure
	if response_body.size() > MAX_HTTP_BODY_BYTES:
		var large_failure := {"ok": false, "error": "response_too_large", "uncertain": response_code >= 500}
		large_failure.merge(_last_http_diagnostic, true)
		return large_failure
	var parsed: Variant = JSON.parse_string(response_body.get_string_from_utf8())
	if not parsed is Dictionary:
		var invalid_failure := {"ok": false, "error": "invalid_service_response", "uncertain": response_code >= 500 or response_code >= 200 and response_code < 300}
		invalid_failure.merge(_last_http_diagnostic, true)
		return invalid_failure
	if response_code < 200 or response_code >= 300:
		var code := "service_http_%d" % response_code
		if parsed.get("error") is String:
			code = parsed["error"]
		var status_failure := {"ok": false, "error": code, "uncertain": response_code >= 500}
		status_failure.merge(_last_http_diagnostic, true)
		return status_failure
	return {"ok": true, "value": parsed}


func _handle_socket_packet(packet: PackedByteArray) -> void:
	if packet.size() > MAX_SIGNAL_BYTES:
		_socket_protocol_error("socket_message_too_large")
		return
	var packet_text := packet.get_string_from_utf8()
	if packet_text == "pong":
		return
	var decoded: Variant = JSON.parse_string(packet_text)
	if not decoded is Dictionary:
		_socket_protocol_error("invalid_socket_message")
		return
	var message: Dictionary = decoded
	var kind: Variant = message.get("type")
	if not kind is String:
		_socket_protocol_error("invalid_socket_message")
		return
	match kind:
		"state":
			if _room_state_missing_network_profile(message.get("state")):
				_socket_protocol_error("server_upgrade_required")
				return
			if not message.get("state") is Dictionary or not _validate_room_state(message["state"]):
				_socket_protocol_error("invalid_room_state")
				return
			_accept_state(message["state"])
			_socket_initial_state_received = true
			_socket_waiting_for_state = false
		"signal":
			if not _validate_signaling_message(message):
				_socket_protocol_error("invalid_signal_message")
				return
			signaling_message.emit(message.duplicate(true))
		"signal_ack":
			if not _is_integer(message.get("seq")) or not message.get("delivered") is bool:
				_socket_protocol_error("invalid_signal_ack")
				return
			signaling_message.emit(message.duplicate(true))
		"error":
			if not message.get("error") is String:
				_socket_protocol_error("invalid_socket_error")
				return
			signaling_message.emit(message.duplicate(true))
			if ["unauthorized", "room_expired", "membership_ended"].has(message["error"]):
				_socket_protocol_error(message["error"])
		_:
			_socket_protocol_error("unknown_socket_message")


func _accept_state(state: Dictionary) -> void:
	if not _validate_room_state(state, _room_id, _slot, true):
		return
	var revision := int(state["revision"])
	if revision < _last_room_revision:
		return
	_last_room_revision = revision
	_room_state = state.duplicate(true)
	if _pending_command.is_empty():
		var members: Array = state["members"]
		if members[_slot] is Dictionary:
			_last_accepted_seq = int(members[_slot].get("seq", _last_accepted_seq))
	state_changed.emit(_room_state.duplicate(true))


func _validate_admission_reply(value: Dictionary, require_invite_code: bool = false) -> bool:
	if not value.get("roomId") is String or not _is_room_id(value["roomId"]):
		return false
	if not _is_integer(value.get("slot")) or int(value["slot"]) not in [0, 1]:
		return false
	if not value.has("state") or not _validate_room_state(value["state"], value["roomId"], int(value["slot"]), false):
		return false
	var members: Array = value["state"]["members"]
	if not members[int(value["slot"])] is Dictionary:
		return false
	if require_invite_code and not _is_invite_code(value.get("inviteCode")):
		return false
	return true


func _validate_state_reply(value: Variant) -> bool:
	return value is Dictionary \
		and _is_integer(value.get("slot")) \
		and int(value["slot"]) == _slot \
		and value.has("state") \
		and _validate_room_state(value["state"], _room_id, _slot, false)


func _validate_room_state(
	value: Variant,
	expected_room_id: String = "",
	expected_slot: int = -1,
	allow_departed: bool = true
) -> bool:
	if not value is Dictionary:
		return false
	if not value.has_all([
		"schema", "id", "compatibility", "revision", "setupRevision", "members",
		"stage", "rules", "networkProfile", "phase", "match", "lastResult", "negotiation",
		"lastActivity", "leaseUntil"
	]):
		return false
	if not _is_integer(value.get("schema")) or int(value["schema"]) != 1:
		return false
	if not _is_room_id(value.get("id")) or not _is_integer(value.get("revision")) or int(value["revision"]) < 0:
		return false
	if not _is_integer(value.get("setupRevision")) or int(value["setupRevision"]) < 0:
		return false
	if not _validate_compatibility(value.get("compatibility")):
		return false
	if not _validate_network_profile(value.get("networkProfile")):
		return false
	var members: Variant = value.get("members")
	var validation_slot := expected_slot if expected_slot in [0, 1] else _slot
	if not members is Array or members.size() != 2 or validation_slot not in [0, 1]:
		return false
	var validation_room_id := expected_room_id if not expected_room_id.is_empty() else _room_id
	if not validation_room_id.is_empty() and value["id"] != validation_room_id:
		return false
	var member: Variant = members[validation_slot]
	if member == null:
		if not allow_departed:
			return false
	elif not _validate_member(member):
		return false
	var other_slot := 1 - validation_slot
	if members[other_slot] != null and not _validate_member(members[other_slot]):
		return false
	if not _is_identifier(value.get("stage")) or not _validate_rules(value.get("rules")):
		return false
	if not value.get("phase") is String or not ["lobby", "preparing", "active", "closed"].has(value["phase"]):
		return false
	if not _validate_match(value.get("match")) or not _validate_last_result(value.get("lastResult")):
		return false
	if ["preparing", "active"].has(value["phase"]) != (value["match"] != null):
		return false
	if not _validate_negotiation(value.get("negotiation")):
		return false
	if not _is_integer(value.get("lastActivity")) or int(value["lastActivity"]) < 0:
		return false
	if not _is_integer(value.get("leaseUntil")) or int(value["leaseUntil"]) < 0:
		return false
	return true


func _validate_ice_response(value: Dictionary) -> bool:
	var servers: Variant = value.get("iceServers")
	if not servers is Array or servers.size() > 4:
		return false
	if not _is_integer(value.get("expiresIn")) or int(value["expiresIn"]) <= 0:
		return false
	var has_authenticated_turn := false
	for server_value in servers:
		if not server_value is Dictionary:
			return false
		var urls: Variant = server_value.get("urls")
		if urls is String:
			urls = [urls]
		if not urls is Array or urls.is_empty():
			return false
		var has_turn_url := false
		for url_value in urls:
			if not url_value is String:
				return false
			if url_value.begins_with("turn:") or url_value.begins_with("turns:"):
				has_turn_url = true
			elif not url_value.begins_with("stun:") and not url_value.begins_with("stuns:"):
				return false
		var has_username: bool = server_value.has("username")
		var has_credential: bool = server_value.has("credential")
		if has_username != has_credential:
			return false
		if has_turn_url:
			if not has_username or not server_value["username"] is String or server_value["username"].is_empty():
				return false
			if not server_value["credential"] is String or server_value["credential"].is_empty():
				return false
			has_authenticated_turn = true
		elif has_username and (not server_value["username"] is String or not server_value["credential"] is String):
			return false
	return has_authenticated_turn


func _normalize_ice_response(value: Variant) -> Dictionary:
	if not value is Dictionary or not _validate_ice_response(value):
		return {}
	var normalized: Dictionary = value.duplicate(true)
	var servers: Array = normalized.get("iceServers", [])
	for index in servers.size():
		var server: Dictionary = servers[index]
		if server.get("urls") is String:
			server["urls"] = [server["urls"]]
		servers[index] = server
	normalized["iceServers"] = servers
	return normalized


func _validate_signaling_message(message: Dictionary) -> bool:
	return message.has_all(["version", "type", "seq", "epoch", "negotiationId", "kind", "payload", "from"]) \
		and message.get("type") == "signal" \
		and _is_integer(message.get("version")) and int(message["version"]) == PROTOCOL_VERSION \
		and _is_integer(message.get("seq")) \
		and int(message["seq"]) >= 0 \
		and (message.get("epoch") == null or _is_uuid(message.get("epoch"))) \
		and _is_uuid(message.get("negotiationId")) \
		and message.get("kind") in SIGNAL_KINDS \
		and message.get("payload") is String \
		and str(message["payload"]).length() <= 12_000 \
		and _is_integer(message.get("from")) \
		and int(message["from"]) in [0, 1] \
		and int(message["from"]) != _slot


func _validate_compatibility(value: Variant) -> bool:
	return value is Dictionary \
		and _is_integer(value.get("protocol")) and int(value["protocol"]) == PROTOCOL_VERSION \
		and _is_sha256(value.get("build", "")) \
		and _is_sha256(value.get("content", ""))


func _validate_nickname(value: String) -> bool:
	var nickname := value.strip_edges()
	return not nickname.is_empty() and nickname.length() <= 32 and not nickname.contains("<") and not nickname.contains(">")


func _validate_member(value: Variant) -> bool:
	if not value is Dictionary:
		return false
	if not value.has_all(["nickname", "choice", "ready", "profile", "seq"]):
		return false
	if not value.get("nickname") is String or value["nickname"].is_empty() or value["nickname"].length() > 32:
		return false
	if not value.get("ready") is bool or not _is_integer(value.get("seq")) or int(value["seq"]) < 0:
		return false
	var choice: Variant = value.get("choice")
	if choice != null and (not choice is Dictionary or not _is_identifier(choice.get("fighter")) or not _is_identifier(choice.get("helper"))):
		return false
	var profile: Variant = value.get("profile")
	if profile != null and not _validate_profile(profile):
		return false
	if value["ready"] != (profile != null):
		return false
	return true


func _validate_profile(value: Variant) -> bool:
	return value is Dictionary \
		and _is_identifier(value.get("id")) \
		and _is_integer(value.get("inputDelay")) \
		and int(value["inputDelay"]) >= 0 and int(value["inputDelay"]) <= 8 \
		and _is_integer(value.get("predictionWindow")) \
		and int(value["predictionWindow"]) >= 0 and int(value["predictionWindow"]) <= 15


func _validate_network_profile(value: Variant) -> bool:
	if not _validate_profile(value):
		return false
	var base_id := "chrome-exp-d%d-p%d" % [int(value["inputDelay"]), int(value["predictionWindow"])]
	return value["id"] == base_id or value["id"] == base_id + "-lan"


func _room_state_reply_missing_network_profile(value: Variant) -> bool:
	return value is Dictionary and _room_state_missing_network_profile(value.get("state"))


func _room_state_missing_network_profile(value: Variant) -> bool:
	return value is Dictionary and not value.has("networkProfile")


func _validate_rules(value: Variant) -> bool:
	return value is Dictionary \
		and _is_integer(value.get("time")) and [30, 60, 90, 100].has(int(value["time"])) \
		and _is_integer(value.get("life")) and int(value["life"]) >= 1 and int(value["life"]) <= 5


func _validate_match(value: Variant) -> bool:
	if value == null:
		return true
	if not value is Dictionary or not _is_uuid(value.get("epoch")):
		return false
	if not value.has_all(["epoch", "seed", "clockBaseline", "profile", "deadline", "loaded", "acknowledged", "results"]):
		return false
	if not _is_integer(value.get("seed")) or int(value["seed"]) < 0 or int(value["seed"]) > 4_294_967_295:
		return false
	if not _is_integer(value.get("clockBaseline")) or int(value["clockBaseline"]) < 0:
		return false
	if not _validate_profile(value.get("profile")) or not _is_integer(value.get("deadline")):
		return false
	if not _validate_pair(value.get("loaded"), "digest", true) or not _validate_pair(value.get("acknowledged"), "bool", false):
		return false
	var results: Variant = value.get("results")
	if not results is Array or results.size() != 2:
		return false
	for result in results:
		if result == null:
			continue
		if not result is Dictionary or not _is_integer(result.get("frame")) or int(result["frame"]) < 0:
			return false
		if not _is_sha256(result.get("hash")) or not _valid_winner(result.get("winner")):
			return false
	return true


func _validate_pair(value: Variant, element_kind: String, allow_null: bool) -> bool:
	if not value is Array or value.size() != 2:
		return false
	for item in value:
		if item == null:
			if allow_null:
				continue
			return false
		if element_kind == "digest" and not _is_sha256(item):
			return false
		if element_kind == "bool" and not item is bool:
			return false
	return true


func _validate_last_result(value: Variant) -> bool:
	if value == null:
		return true
	if not value is Dictionary or not value.has_all(["epoch", "winner", "reason"]):
		return false
	return value is Dictionary \
		and _is_uuid(value.get("epoch")) \
		and _valid_winner(value.get("winner")) \
		and value.get("reason") is String


func _validate_negotiation(value: Variant) -> bool:
	if value == null:
		return true
	if not value is Dictionary or not value.has_all(["id", "epoch", "expires"]):
		return false
	return value is Dictionary \
		and _is_uuid(value.get("id")) \
		and (value.get("epoch") == null or _is_uuid(value.get("epoch"))) \
		and _is_integer(value.get("expires")) and int(value["expires"]) >= 0


func _valid_winner(value: Variant) -> bool:
	return value == null or (_is_integer(value) and int(value) in [0, 1])


func _is_identifier(value: Variant) -> bool:
	return value is String and not value.is_empty() and value.length() <= 80


func _is_room_id(value: Variant) -> bool:
	if not value is String or value.length() != 64 or value != value.to_lower():
		return false
	for index in range(value.length()):
		if not _is_hex_codepoint(value.unicode_at(index)):
			return false
	return true


func _is_token(value: Variant) -> bool:
	if not value is String or value.length() != 43:
		return false
	for index in range(value.length()):
		var codepoint: int = value.unicode_at(index)
		if not (codepoint >= 48 and codepoint <= 57 or codepoint >= 65 and codepoint <= 90 or codepoint >= 97 and codepoint <= 122 or codepoint == 45 or codepoint == 95):
			return false
	return true


func _is_invite_code(value: Variant) -> bool:
	if not value is String:
		return false
	var parts: PackedStringArray = (value as String).split("-", false)
	if parts.size() != 3 or parts[0].is_empty() or parts[1].is_empty() or parts[2].length() != 8:
		return false
	for word_index in 2:
		for index in parts[word_index].length():
			var codepoint: int = parts[word_index].unicode_at(index)
			if codepoint < 97 or codepoint > 122:
				return false
	for index in parts[2].length():
		var codepoint: int = parts[2].unicode_at(index)
		var is_letter := codepoint >= 97 and codepoint <= 122
		var is_base32_digit := codepoint >= 50 and codepoint <= 55
		if not is_letter and not is_base32_digit:
			return false
	return true


func _is_sha256(value: Variant) -> bool:
	if not value is String or value.length() != 64 or value != value.to_lower():
		return false
	for index in range(value.length()):
		if not _is_hex_codepoint(value.unicode_at(index)):
			return false
	return true


func _is_uuid(value: Variant) -> bool:
	if not value is String or value.length() != 36:
		return false
	for index in range(36):
		var codepoint: int = value.unicode_at(index)
		if index in [8, 13, 18, 23]:
			if codepoint != 45:
				return false
		elif not _is_hex_codepoint(codepoint):
			return false
	return true


func _is_hex_codepoint(codepoint: int) -> bool:
	return codepoint >= 48 and codepoint <= 57 or codepoint >= 65 and codepoint <= 70 or codepoint >= 97 and codepoint <= 102


func _socket_protocol_error(code: String) -> void:
	if _socket_last_error.is_empty():
		_socket_last_error = code
		error.emit(code)


func _is_integer(value: Variant) -> bool:
	if value is int:
		return true
	return value is float and is_finite(value) and floor(value) == value


func _new_token() -> String:
	var bytes := Crypto.new().generate_random_bytes(32)
	if bytes.size() != 32:
		return ""
	return Marshalls.raw_to_base64(bytes).replace("+", "-").replace("/", "_").trim_suffix("=")


func _can_admit() -> bool:
	return not _base_url.is_empty() and _room_id.is_empty() and _pending_admission.is_empty() and not _admission_in_flight


func _has_membership() -> bool:
	return not _room_id.is_empty() and _slot in [0, 1] and not _session_token.is_empty()


func _websocket_url(path: String) -> String:
	if _base_url.begins_with("https://"):
		return "wss://" + _base_url.trim_prefix("https://") + path
	return "ws://" + _base_url.trim_prefix("http://") + path


func _close_socket(notify: bool) -> void:
	_socket_attempt_id += 1
	var was_open := _socket != null and _socket.get_ready_state() == WebSocketPeer.STATE_OPEN
	if _socket != null:
		_socket.close(1000, "client_closed")
	_socket = null
	_socket_connecting = false
	_socket_waiting_for_state = false
	_socket_initial_state_received = false
	_signal_sequence = -1
	if notify and was_open:
		socket_state_changed.emit(false)


func _report_request_failure(response: Dictionary, uncertain_override: bool = false) -> Dictionary:
	var code := str(response.get("error", "request_failed"))
	var uncertain := uncertain_override or bool(response.get("uncertain", false))
	error.emit(code)
	var result := {"error": code, "uncertain": uncertain}
	for field in ["phase", "transportResult", "requestErrorCode", "httpStatus"]:
		if response.has(field):
			result[field] = response[field]
	return result


func _failure(code: String, uncertain: bool = false) -> Dictionary:
	error.emit(code)
	return {"error": code, "uncertain": uncertain}
