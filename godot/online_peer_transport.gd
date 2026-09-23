extends Node
class_name OnlinePeerTransport

signal outgoing_signal(kind: String, epoch: Variant, negotiation_id: String, payload: String)
signal peer_state_changed(state: String)
signal peer_message(channel: String, type: String, payload: Variant, sequence: int)
signal transport_error(code: String)

const PROTOCOL_VERSION := 1
const MAX_MESSAGE_BYTES := 16_384
const MAX_CANDIDATES_BEFORE_SDP := 256
const MAX_RECENT_UNORDERED_SEQUENCES := 4096
const CHANNEL_RELIABLE := "reliable"
const CHANNEL_INPUT := "input"
const CHANNELS := [CHANNEL_RELIABLE, CHANNEL_INPUT]
const TYPE_PATTERN := "^[A-Za-z0-9_.-]{1,64}$"

var _room_id := ""
var _epoch: Variant
var _local_slot := -1
var _remote_slot := -1
var _negotiation_id := ""

var _peer: WebRTCPeerConnection
var _channels: Dictionary = {}
var _connection_state := "new"
var _remote_description_set := false
var _pending_remote_candidates: Array[Dictionary] = []
var _outgoing_sequences := {CHANNEL_RELIABLE: 0, CHANNEL_INPUT: 0}
var _last_reliable_sequence := 0
var _recent_unordered_sequences: Dictionary = {}
var _recent_unordered_order: Array[int] = []

var _message_type_regex: RegEx


func _ready() -> void:
	_message_type_regex = RegEx.new()
	_message_type_regex.compile(TYPE_PATTERN)


func configure(
	room_id: String,
	epoch: Variant,
	local_slot: int,
	remote_slot: int,
	negotiation_id: String
) -> bool:
	if not _valid_room_id(room_id) or local_slot not in [0, 1] or remote_slot not in [0, 1] or local_slot == remote_slot:
		return _fail("invalid_peer_identity")
	if epoch != null and not _valid_uuid(epoch):
		return _fail("invalid_peer_epoch")
	if not _valid_uuid(negotiation_id):
		return _fail("invalid_negotiation_id")
	if _peer != null:
		if _peer.get_connection_state() == WebRTCPeerConnection.STATE_CONNECTED:
			return _fail("healthy_peer_preserved")
		return _fail("peer_reset_required")
	_room_id = room_id
	_epoch = epoch
	_local_slot = local_slot
	_remote_slot = remote_slot
	_negotiation_id = negotiation_id
	_reset_sequences()
	_remote_description_set = false
	_pending_remote_candidates.clear()
	return true


func create_peer(ice_servers: Array) -> bool:
	if not _is_configured():
		return _fail("peer_not_configured")
	if _peer != null:
		return _fail("peer_already_created")
	if not _validate_ice_servers(ice_servers):
		return _fail("invalid_ice_configuration")
	_peer = WebRTCPeerConnection.new()
	var init_error := _peer.initialize({"iceServers": ice_servers.duplicate(true)})
	if init_error != OK:
		_peer = null
		return _fail("peer_initialize_failed_%d" % init_error)
	_peer.session_description_created.connect(_on_session_description_created)
	_peer.ice_candidate_created.connect(_on_ice_candidate_created)
	_peer.data_channel_received.connect(_on_data_channel_received)
	if _local_slot == 0:
		var reliable := _peer.create_data_channel(CHANNEL_RELIABLE, {"ordered": true})
		var input := _peer.create_data_channel(CHANNEL_INPUT, {"ordered": false, "maxRetransmits": 0})
		if reliable == null or input == null:
			close_peer()
			return _fail("data_channel_create_failed")
		_channels[CHANNEL_RELIABLE] = reliable
		_channels[CHANNEL_INPUT] = input
	return true


func begin_offer() -> bool:
	if _peer == null:
		return _fail("peer_not_created")
	if _local_slot != 0:
		return _fail("offer_owner_required")
	if _peer.get_connection_state() != WebRTCPeerConnection.STATE_NEW:
		return _fail("offer_requires_new_peer")
	var offer_error := _peer.create_offer()
	if offer_error != OK:
		return _fail("offer_create_failed_%d" % offer_error)
	return true


func handle_signal(message: Dictionary) -> bool:
	if _peer == null:
		return _fail("peer_not_created")
	if not _validate_signal(message):
		return _fail("invalid_peer_signal")
	var kind: String = message["kind"]
	var payload: String = message["payload"]
	if kind == "candidate":
		return _handle_remote_candidate(payload)
	if kind == "offer" and (_local_slot != 1 or _remote_slot != 0):
		return _fail("unexpected_offer_role")
	if kind == "answer" and (_local_slot != 0 or _remote_slot != 1):
		return _fail("unexpected_answer_role")
	var result := _peer.set_remote_description(kind, payload)
	if result != OK:
		return _fail("remote_description_failed_%d" % result)
	_remote_description_set = true
	return _flush_remote_candidates()


func send_peer_message(channel: String, type: String, payload: Variant) -> bool:
	if not CHANNELS.has(channel):
		return _fail("unknown_data_channel")
	if _peer == null:
		return _fail("peer_not_created")
	if not _valid_message_type(type):
		return _fail("invalid_peer_message_type")
	var data_channel: WebRTCDataChannel = _channels.get(channel)
	if data_channel == null or data_channel.get_ready_state() != WebRTCDataChannel.STATE_OPEN:
		return false
	var sequence := int(_outgoing_sequences[channel]) + 1
	var envelope := {
		"version": PROTOCOL_VERSION,
		"roomId": _room_id,
		"epoch": _epoch,
		"from": _local_slot,
		"seq": sequence,
		"type": type,
		"payload": payload,
	}
	var encoded := JSON.stringify(envelope)
	var packet := encoded.to_utf8_buffer()
	if encoded.is_empty() or packet.size() > MAX_MESSAGE_BYTES:
		return _fail("peer_message_too_large")
	var send_error := data_channel.put_packet(packet)
	if send_error != OK:
		return _fail("peer_send_failed_%d" % send_error)
	_outgoing_sequences[channel] = sequence
	return true


func close_peer() -> void:
	for data_channel in _channels.values():
		if data_channel is WebRTCDataChannel:
			data_channel.close()
	_channels.clear()
	if _peer != null:
		_peer.close()
	_peer = null
	_remote_description_set = false
	_pending_remote_candidates.clear()
	_set_connection_state("closed")
	_reset_sequences()


func peer_is_connected() -> bool:
	return _peer != null and _peer.get_connection_state() == WebRTCPeerConnection.STATE_CONNECTED


func get_connection_state() -> String:
	return _connection_state


func get_channel_state(channel: String) -> String:
	if not CHANNELS.has(channel):
		return "unknown"
	var data_channel: WebRTCDataChannel = _channels.get(channel)
	if data_channel == null:
		return "missing"
	return _channel_state_name(data_channel.get_ready_state())


func _process(_delta: float) -> void:
	if _peer == null:
		return
	_peer.poll()
	_set_connection_state(_connection_state_name(_peer.get_connection_state()))
	for channel_name in CHANNELS:
		var data_channel: WebRTCDataChannel = _channels.get(channel_name)
		if data_channel == null or data_channel.get_ready_state() != WebRTCDataChannel.STATE_OPEN:
			continue
		while data_channel.get_available_packet_count() > 0:
			var packet: PackedByteArray = data_channel.get_packet()
			_receive_packet(channel_name, packet)


func _on_session_description_created(kind: String, sdp: String) -> void:
	if _peer == null:
		return
	if not ["offer", "answer"].has(kind) or sdp.is_empty() or sdp.length() > 12_000:
		_fail("invalid_local_description")
		return
	var result := _peer.set_local_description(kind, sdp)
	if result != OK:
		_fail("local_description_failed_%d" % result)
		return
	outgoing_signal.emit(kind, _epoch, _negotiation_id, sdp)


func _on_ice_candidate_created(media: String, index: int, candidate: String) -> void:
	if _peer == null or media.is_empty() or index < 0:
		return
	var payload := JSON.stringify({"media": media, "index": index, "name": candidate})
	if payload.to_utf8_buffer().size() > 12_000:
		_fail("ice_candidate_too_large")
		return
	outgoing_signal.emit("candidate", _epoch, _negotiation_id, payload)


func _on_data_channel_received(data_channel: WebRTCDataChannel) -> void:
	var label := data_channel.get_label()
	if not CHANNELS.has(label):
		data_channel.close()
		_fail("unknown_data_channel_label")
		return
	var existing: WebRTCDataChannel = _channels.get(label)
	if existing != null and existing != data_channel:
		data_channel.close()
		_fail("duplicate_data_channel")
		return
	_channels[label] = data_channel


func _handle_remote_candidate(payload: String) -> bool:
	var decoded: Variant = JSON.parse_string(payload)
	if not decoded is Dictionary or not decoded.has_all(["media", "index", "name"]):
		return _fail("invalid_ice_candidate")
	if not decoded["media"] is String or decoded["media"].is_empty() or decoded["media"].length() > 64:
		return _fail("invalid_ice_candidate")
	if not _is_integer(decoded["index"]) or int(decoded["index"]) < 0:
		return _fail("invalid_ice_candidate")
	if not decoded["name"] is String or decoded["name"].length() > 4096:
		return _fail("invalid_ice_candidate")
	var candidate := {
		"media": decoded["media"],
		"index": int(decoded["index"]),
		"name": decoded["name"],
	}
	if not _remote_description_set:
		if _pending_remote_candidates.size() >= MAX_CANDIDATES_BEFORE_SDP:
			return _fail("too_many_early_ice_candidates")
		_pending_remote_candidates.append(candidate)
		return true
	return _add_remote_candidate(candidate)


func _flush_remote_candidates() -> bool:
	while not _pending_remote_candidates.is_empty():
		var candidate: Dictionary = _pending_remote_candidates.pop_front()
		if not _add_remote_candidate(candidate):
			return false
	return true


func _add_remote_candidate(candidate: Dictionary) -> bool:
	if _peer == null:
		return _fail("peer_not_created")
	var result := _peer.add_ice_candidate(
		str(candidate["media"]),
		int(candidate["index"]),
		str(candidate["name"])
	)
	if result != OK:
		return _fail("ice_candidate_rejected_%d" % result)
	return true


func _receive_packet(channel: String, packet: PackedByteArray) -> void:
	if packet.size() > MAX_MESSAGE_BYTES:
		_fail("peer_message_too_large")
		return
	var decoded: Variant = JSON.parse_string(packet.get_string_from_utf8())
	if not decoded is Dictionary or not _validate_envelope(decoded, channel):
		_fail("invalid_peer_envelope")
		return
	var sequence := int(decoded["seq"])
	if channel == CHANNEL_RELIABLE:
		if sequence != _last_reliable_sequence + 1:
			_fail("reliable_sequence_gap")
			return
		_last_reliable_sequence = sequence
	else:
		if _recent_unordered_sequences.has(sequence):
			return
		_recent_unordered_sequences[sequence] = true
		_recent_unordered_order.append(sequence)
		if _recent_unordered_order.size() > MAX_RECENT_UNORDERED_SEQUENCES:
			var expired: int = _recent_unordered_order.pop_front()
			_recent_unordered_sequences.erase(expired)
	peer_message.emit(channel, decoded["type"], decoded["payload"], sequence)


func _validate_envelope(value: Dictionary, _channel: String) -> bool:
	if not value.has_all(["version", "roomId", "epoch", "from", "seq", "type", "payload"]):
		return false
	if not _is_integer(value["version"]) or int(value["version"]) != PROTOCOL_VERSION:
		return false
	if not value["roomId"] is String or value["roomId"] != _room_id:
		return false
	if value["epoch"] != _epoch:
		return false
	if not _is_integer(value["from"]) or int(value["from"]) != _remote_slot:
		return false
	if not _is_integer(value["seq"]) or int(value["seq"]) <= 0:
		return false
	return value["type"] is String and _valid_message_type(value["type"])


func _validate_signal(value: Dictionary) -> bool:
	if not _is_configured() or not value.has_all(["version", "type", "seq", "epoch", "negotiationId", "kind", "payload", "from"]):
		return false
	if not _is_integer(value["version"]) or int(value["version"]) != PROTOCOL_VERSION:
		return false
	if value["type"] != "signal" or not _is_integer(value["seq"]) or int(value["seq"]) < 0:
		return false
	if value["epoch"] != _epoch or value["negotiationId"] != _negotiation_id:
		return false
	if not _is_integer(value["from"]) or int(value["from"]) != _remote_slot:
		return false
	if not ["offer", "answer", "candidate"].has(value["kind"]):
		return false
	return value["payload"] is String and not value["payload"].is_empty() and value["payload"].length() <= 12_000


func _validate_ice_servers(value: Array) -> bool:
	if value.size() > 4:
		return false
	for server in value:
		if not server is Dictionary:
			return false
		var urls: Variant = server.get("urls")
		if not urls is Array or urls.is_empty():
			return false
		for url in urls:
			if not url is String or url.is_empty() or url.length() > 512:
				return false
		if server.has("username") and not server["username"] is String:
			return false
		if server.has("credential") and not server["credential"] is String:
			return false
	return true


func _valid_message_type(value: String) -> bool:
	return _message_type_regex != null and _message_type_regex.search(value) != null


func _is_configured() -> bool:
	return _valid_room_id(_room_id) and _local_slot in [0, 1] and _remote_slot in [0, 1] and _local_slot != _remote_slot and _valid_uuid(_negotiation_id)


func _reset_sequences() -> void:
	_outgoing_sequences[CHANNEL_RELIABLE] = 0
	_outgoing_sequences[CHANNEL_INPUT] = 0
	_last_reliable_sequence = 0
	_recent_unordered_sequences.clear()
	_recent_unordered_order.clear()


func _set_connection_state(state: String) -> void:
	if _connection_state == state:
		return
	_connection_state = state
	peer_state_changed.emit(state)


func _connection_state_name(state: int) -> String:
	match state:
		WebRTCPeerConnection.STATE_NEW:
			return "new"
		WebRTCPeerConnection.STATE_CONNECTING:
			return "connecting"
		WebRTCPeerConnection.STATE_CONNECTED:
			return "connected"
		WebRTCPeerConnection.STATE_DISCONNECTED:
			return "disconnected"
		WebRTCPeerConnection.STATE_FAILED:
			return "failed"
		WebRTCPeerConnection.STATE_CLOSED:
			return "closed"
	return "unknown"


func _channel_state_name(state: int) -> String:
	match state:
		WebRTCDataChannel.STATE_CONNECTING:
			return "connecting"
		WebRTCDataChannel.STATE_OPEN:
			return "open"
		WebRTCDataChannel.STATE_CLOSING:
			return "closing"
		WebRTCDataChannel.STATE_CLOSED:
			return "closed"
	return "unknown"


func _valid_room_id(value: String) -> bool:
	if value.length() != 64 or value != value.to_lower():
		return false
	for index in range(value.length()):
		if not _is_hex_codepoint(value.unicode_at(index)):
			return false
	return true


func _valid_uuid(value: Variant) -> bool:
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


func _is_integer(value: Variant) -> bool:
	if value is int:
		return true
	return value is float and is_finite(value) and floor(value) == value


func _is_hex_codepoint(codepoint: int) -> bool:
	return codepoint >= 48 and codepoint <= 57 or codepoint >= 65 and codepoint <= 70 or codepoint >= 97 and codepoint <= 102


func _fail(code: String) -> bool:
	transport_error.emit(code)
	return false
