extends Node

const RoomClient = preload("res://online_room_client.gd")
const PeerTransport = preload("res://online_peer_transport.gd")
const BASE_URL := "http://127.0.0.1:8787"
const BUS_NAME := "bvn-online-webrtc-transport-test"
const BUS_TAG := "webrtc-transport-v1"
const COMPATIBILITY := {
	"protocol": 1,
	"build": "506b8cb4ad0e2afb39a7ac32cb7dcd575935dbf95f1b1839b0a60888801ecd53",
	"content": "428ae4387ca6ab245f86d62a3b51b1c8c01cd93507a7add8a21042e046608e14",
}
const ICE_SERVERS: Array = []
const WAIT_MS := 45_000

var _role := ""
var _run_id := ""
var _room: Node
var _peer: Node
var _invite: Dictionary = {}
var _early_signals: Array[Dictionary] = []
var _received: Dictionary = {}
var _sent_signals := {"offer": 0, "answer": 0, "candidate": 0}
var _received_signals := {"offer": 0, "answer": 0, "candidate": 0}
var _delivered_acks := 0
var _failure := ""
var _failure_diagnostic: Dictionary = {}
var _channels_opened := false


func _ready() -> void:
	_role = str(JavaScriptBridge.eval("new URLSearchParams(window.location.search).get('role') || ''"))
	_run_id = str(JavaScriptBridge.eval("new URLSearchParams(window.location.search).get('run') || ''"))
	if not ["owner", "guest"].has(_role) or _run_id.is_empty():
		_finish(false, "invalid_test_parameters")
		return
	_init_bus()
	_room = RoomClient.new()
	_room.name = "OnlineRoomClient"
	add_child(_room)
	_room.signaling_message.connect(_on_room_signaling_message)
	_room.error.connect(_on_room_error)
	if not _room.configure_service(BASE_URL):
		_finish(false, "service_configuration_failed")
		return
	_run.call_deferred()


func _init_bus() -> void:
	var script := """
	(() => {
		const key = %s;
		window.__bvnOnlineBusQueue = [];
		window.__bvnOnlineBus = new BroadcastChannel(key);
		window.__bvnOnlineBus.onmessage = event => {
			const value = event.data;
			if (value && value.tag === %s && value.run === %s) window.__bvnOnlineBusQueue.push(value);
		};
		window.__bvnOnlineBusSend = text => window.__bvnOnlineBus.postMessage(JSON.parse(text));
		window.__bvnOnlineBusPop = () => {
			const value = window.__bvnOnlineBusQueue.shift();
			return value ? JSON.stringify(value) : "";
		};
		window.__bvnTransportResult = { role: %s, run: %s, phase: "starting", ok: false };
	})()
	""" % [JSON.stringify(BUS_NAME), JSON.stringify(BUS_TAG), JSON.stringify(_run_id), JSON.stringify(_role), JSON.stringify(_run_id)]
	JavaScriptBridge.eval(script)


func _run() -> void:
	_mark("admission")
	if _role == "owner":
		await _run_owner()
	else:
		await _run_guest()


func _run_owner() -> void:
	var created: Dictionary = await _room.create_room("webrtc-owner", COMPATIBILITY)
	if created.has("error"):
		_fail("owner_create_%s" % str(created.get("error", "unknown")))
		return
	_invite = {
			"tag": BUS_TAG,
			"run": _run_id,
			"kind": "invite",
			"roomId": str(created.get("room_id", "")),
			"inviteToken": str(created.get("invite_token", "")),
	}
	if str(_invite.roomId).is_empty() or str(_invite.inviteToken).is_empty():
		_fail("owner_invite_missing")
		return
	var guest_event: Dictionary = await _wait_bus("guest_joined", WAIT_MS, _invite)
	if guest_event.is_empty():
		_fail("guest_join_timeout")
		return
	await _establish_peer()


func _run_guest() -> void:
	var invitation: Dictionary = await _wait_bus("invite", WAIT_MS)
	if invitation.is_empty():
		_fail("invite_timeout")
		return
	var joined: Dictionary = await _room.join_room(
		str(invitation.get("roomId", "")),
		str(invitation.get("inviteToken", "")),
		"webrtc-guest",
		COMPATIBILITY
	)
	if joined.has("error"):
		_fail("guest_join_%s" % str(joined.get("error", "unknown")))
		return
	_bus_send({"kind": "guest_joined"})
	await _establish_peer()


func _establish_peer() -> void:
	_mark("signaling_socket")
	var socket_reply: Dictionary = await _room.connect_signaling()
	if socket_reply.has("error") or not _room.is_signaling_connected():
		_fail("socket_%s" % str(socket_reply.get("error", "not_connected")))
		return
	var socket_event: Dictionary = await _wait_bus(
		"socket_ready",
		WAIT_MS,
		{"kind": "socket_ready", "role": _role}
	)
	if socket_event.is_empty():
		_fail("peer_socket_ready_timeout")
		return

	if _role == "owner":
		_mark("negotiate")
		var result: Dictionary = await _room.command({"type": "negotiate", "epoch": null})
		if result.has("error"):
			_fail("negotiate_%s" % str(result.get("error", "unknown")))
			return

	var negotiation: Dictionary = await _wait_for_negotiation()
	if negotiation.is_empty():
		_fail("negotiation_state_timeout")
		return
	var room_state: Dictionary = _room.get_room_state()
	var members: Array = room_state.get("members", [])
	var local_slot := int(_room.get_slot())
	var remote_slot := 1 - local_slot
	var room_id := str(_room.get_room_id())
	var epoch: Variant = negotiation.get("epoch")
	if epoch != null or local_slot not in [0, 1] or members.size() != 2 or members[remote_slot] == null:
		_fail("lobby_negotiation_identity_invalid")
		return

	_peer = PeerTransport.new()
	_peer.name = "OnlinePeerTransport"
	add_child(_peer)
	_peer.outgoing_signal.connect(_on_outgoing_signal)
	_peer.peer_message.connect(_on_peer_message)
	_peer.transport_error.connect(_on_transport_error)
	if not _peer.configure(room_id, null, local_slot, remote_slot, str(negotiation.get("id", ""))):
		_fail("peer_configuration_failed")
		return
	if not _peer.create_peer(ICE_SERVERS):
		_fail("peer_creation_failed")
		return
	for message in _early_signals:
		if not _peer.handle_signal(message):
			_fail("early_signal_rejected")
			return
	_early_signals.clear()

	if local_slot == 0:
		_mark("offer")
		if not _peer.begin_offer():
			_fail("offer_start_failed")
			return

	_mark("data_channels")
	var channels_deadline := Time.get_ticks_msec() + WAIT_MS
	while Time.get_ticks_msec() < channels_deadline:
		if not _failure.is_empty():
			return
		if _peer.get_channel_state("reliable") == "open" and _peer.get_channel_state("input") == "open":
			break
		await get_tree().create_timer(0.05).timeout
	if _peer.get_channel_state("reliable") != "open" or _peer.get_channel_state("input") != "open":
		_fail("data_channel_open_timeout")
		return
	_channels_opened = true

	_mark("channel_exchange")
	if local_slot == 0:
		if not _send_test_pair("owner_to_guest"):
			_fail("owner_channel_send_failed")
			return
	else:
		var owner_messages: Dictionary = await _wait_for_channel_pair("owner_to_guest")
		if owner_messages.size() != 2:
			_fail("owner_messages_timeout")
			return
		if not _send_test_pair("guest_to_owner"):
			_fail("guest_channel_send_failed")
			return
		_bus_send({"kind": "guest_messages_sent"})

	if local_slot == 0:
		var guest_sent: Dictionary = await _wait_bus("guest_messages_sent", WAIT_MS)
		if guest_sent.is_empty():
			_fail("guest_send_ack_timeout")
			return
		var reverse_messages: Dictionary = await _wait_for_channel_pair("guest_to_owner")
		if reverse_messages.size() != 2:
			_fail("guest_messages_timeout")
			return
		_bus_send({"kind": "owner_exchange_passed"})
	else:
		var owner_passed: Dictionary = await _wait_bus("owner_exchange_passed", WAIT_MS)
		if owner_passed.is_empty():
			_fail("owner_exchange_ack_timeout")
			return

	_mark("leave")
	if local_slot == 1:
		var guest_leave: Dictionary = await _room.command({"type": "leave"})
		if guest_leave.has("error"):
			_fail("guest_leave_%s" % str(guest_leave.get("error", "unknown")))
			return
		_peer.close_peer()
		_room.clear_credentials()
		_bus_send({"kind": "guest_left"})
		_finish(true, "webrtc_lan_transport_passed", true)
		return

	var left_event: Dictionary = await _wait_bus("guest_left", WAIT_MS)
	if left_event.is_empty():
		_fail("guest_leave_ack_timeout")
		return
	var owner_leave: Dictionary = await _room.command({"type": "leave"})
	if owner_leave.has("error"):
		_fail("owner_leave_%s" % str(owner_leave.get("error", "unknown")))
		return
	_peer.close_peer()
	_room.clear_credentials()
	_finish(true, "webrtc_lan_transport_passed", true)


func _wait_for_negotiation() -> Dictionary:
	var deadline := Time.get_ticks_msec() + WAIT_MS
	while Time.get_ticks_msec() < deadline:
		if not _failure.is_empty():
			return {}
		var state: Dictionary = _room.get_room_state()
		var value: Variant = state.get("negotiation")
		if value is Dictionary and value.get("epoch") == null and not str(value.get("id", "")).is_empty():
			return value
		await get_tree().create_timer(0.05).timeout
	return {}


func _wait_bus(kind: String, timeout_ms: int, repeat_message: Dictionary = {}) -> Dictionary:
	var deadline := Time.get_ticks_msec() + timeout_ms
	var next_repeat := 0
	while Time.get_ticks_msec() < deadline:
		if not _failure.is_empty():
			return {}
		var now := Time.get_ticks_msec()
		if not repeat_message.is_empty() and now >= next_repeat:
			_bus_send(repeat_message)
			next_repeat = now + 500
		var value := _bus_pop()
		if not value.is_empty() and value.get("kind") == kind:
			if kind != "socket_ready" or value.get("role") != _role:
				return value
		await get_tree().process_frame
	return {}


func _wait_for_channel_pair(direction: String) -> Dictionary:
	var deadline := Time.get_ticks_msec() + WAIT_MS
	while Time.get_ticks_msec() < deadline:
		if not _failure.is_empty():
			return {}
		var pair := {}
		for channel in ["reliable", "input"]:
			var key := "%s:%s" % [direction, channel]
			if _received.has(key):
				pair[channel] = true
		if pair.size() == 2:
			return pair
		await get_tree().create_timer(0.05).timeout
	return {}


func _send_test_pair(direction: String) -> bool:
	for channel in ["reliable", "input"]:
		if not _peer.send_peer_message(channel, "transport_smoke", {
			"run": _run_id,
			"direction": direction,
			"channel": channel,
		}):
			return false
	return true


func _on_peer_message(channel: String, type: String, payload: Variant, _sequence: int) -> void:
	if type != "transport_smoke" or not payload is Dictionary:
		_fail("unexpected_peer_message")
		return
	if payload.get("run") != _run_id or payload.get("channel") != channel:
		_fail("peer_message_envelope_mismatch")
		return
	var direction := str(payload.get("direction", ""))
	if direction not in ["owner_to_guest", "guest_to_owner"]:
		_fail("peer_message_direction_invalid")
		return
	_received["%s:%s" % [direction, channel]] = true
	

func _on_room_signaling_message(message: Dictionary) -> void:
	match str(message.get("type", "")):
		"signal":
			var kind := str(message.get("kind", ""))
			if _received_signals.has(kind):
				_received_signals[kind] = int(_received_signals[kind]) + 1
			if _peer == null:
				_early_signals.append(message.duplicate(true))
			elif not _peer.handle_signal(message):
				_fail("peer_rejected_%s" % kind)
		"signal_ack":
			if bool(message.get("delivered", false)):
				_delivered_acks += 1
		"error":
			_fail("signaling_%s" % str(message.get("error", "unknown")))


func _on_outgoing_signal(kind: String, epoch: Variant, negotiation_id: String, payload: String) -> void:
	if not _sent_signals.has(kind):
		_fail("unexpected_outgoing_signal_kind")
		return
	if not _room.send_signal(kind, epoch, negotiation_id, payload):
		_fail("service_signal_send_failed_%s" % kind)
		return
	_sent_signals[kind] = int(_sent_signals[kind]) + 1


func _on_room_error(code: String) -> void:
	if _failure_diagnostic.is_empty() and _room != null:
		var diagnostic: Dictionary = _room.get_last_http_diagnostic()
		if not diagnostic.is_empty():
			_failure_diagnostic = {
				"phase": str(diagnostic.get("phase", "unknown")),
				"transportResult": diagnostic.get("transportResult", "unknown"),
				"httpStatus": int(diagnostic.get("httpStatus", 0)),
				"requestErrorCode": int(diagnostic.get("requestErrorCode", -1)),
			}
	_fail("room_%s" % code)


func _on_transport_error(code: String) -> void:
	_fail("peer_%s" % code)


func _bus_send(value: Dictionary) -> void:
	var message := value.duplicate(true)
	message["tag"] = BUS_TAG
	message["run"] = _run_id
	var message_json := JSON.stringify(message)
	var js_literal := JSON.stringify(message_json)
	JavaScriptBridge.eval("window.__bvnOnlineBusSend(" + js_literal + ")")


func _bus_pop() -> Dictionary:
	var value: Variant = JavaScriptBridge.eval("window.__bvnOnlineBusPop()")
	if not value is String or value.is_empty():
		return {}
	var decoded: Variant = JSON.parse_string(value)
	return decoded if decoded is Dictionary else {}


func _mark(phase: String) -> void:
	JavaScriptBridge.eval("window.__bvnTransportResult.phase = " + JSON.stringify(phase))
	print("ONLINE_WEBRTC_TRANSPORT_PHASE role=%s phase=%s" % [_role, phase])


func _fail(code: String) -> void:
	if not _failure.is_empty():
		return
	_failure = code
	push_error("ONLINE_WEBRTC_TRANSPORT_FAIL role=%s code=%s" % [_role, code])
	_cleanup_failed_test.call_deferred(code)


func _cleanup_failed_test(code: String) -> void:
	var cleanup_complete := _room == null
	if _room != null and _room.get_room_id().is_empty():
		cleanup_complete = false
		for attempt in range(3):
			var admission: Dictionary = await _room.retry_pending_admission()
			if not admission.has("error"):
				break
			if admission.get("error") == "no_pending_admission":
				cleanup_complete = true
				break
			if not admission.get("uncertain", false) and admission.get("error") != "request_in_flight":
				cleanup_complete = true
				break
			await get_tree().create_timer(0.25).timeout
		if not _room.get_room_id().is_empty():
			cleanup_complete = false
	if _room != null and not _room.get_room_id().is_empty():
		if _room.has_uncertain_command():
			var pending_result: Dictionary = {}
			for attempt in range(3):
				pending_result = await _room.retry_pending_command()
				if not pending_result.has("error"):
					break
				if not _room.has_uncertain_command():
					break
				await get_tree().create_timer(0.25).timeout
			if pending_result.has("error") and _room.has_uncertain_command():
				cleanup_complete = false
			else:
				var leave_result: Dictionary = await _room.command({"type": "leave"})
				for attempt in range(3):
					if not leave_result.has("error"):
						cleanup_complete = true
						break
					if not _room.has_uncertain_command():
						break
					leave_result = await _room.retry_pending_command()
					await get_tree().create_timer(0.25).timeout
				if leave_result.has("error"):
					cleanup_complete = false
	if _peer != null:
		_peer.close_peer()
	if _room != null:
		_room.clear_credentials()
	_finish(false, code, cleanup_complete)


func _finish(ok: bool, result: String, cleanup_complete: bool = false) -> void:
	var report := {
		"role": _role,
		"run": _run_id,
		"phase": "done",
		"ok": ok,
		"result": result,
		"sentSignalCounts": _sent_signals.duplicate(true),
		"receivedSignalCounts": _received_signals.duplicate(true),
		"deliveredSignalAcks": _delivered_acks,
		"channels": {
			"reliable": _channels_opened,
			"input": _channels_opened,
		},
		"receivedMessagesByChannel": _received_message_counts(),
		"receivedDataMessages": _received.size(),
		"iceServers": 0,
		"failureDiagnostic": _failure_diagnostic.duplicate(true),
		"cleanupComplete": cleanup_complete,
	}
	JavaScriptBridge.eval("window.__bvnTransportResult = " + JSON.stringify(report))
	print("ONLINE_WEBRTC_TRANSPORT_RESULT " + JSON.stringify(report))
	if _peer != null:
		_peer.close_peer()
	if _room != null:
		_room.clear_credentials()


func _received_message_counts() -> Dictionary:
	var counts := {"reliable": 0, "input": 0}
	for received_key in _received.keys():
		var parts := str(received_key).split(":")
		if parts.size() == 2 and counts.has(parts[1]):
			counts[parts[1]] = int(counts[parts[1]]) + 1
	return counts
