extends SceneTree


const ROOM_ID := "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"
const EPOCH := "11111111-1111-4111-8111-111111111111"
const NEGOTIATION := "22222222-2222-4222-8222-222222222222"
const TRANSPORT_SCRIPT := preload("res://online_peer_transport.gd")
var failures: Array[String] = []
var received: Array[Dictionary] = []
var errors: Array[String] = []


func _initialize() -> void:
	call_deferred("_run")


func _run() -> void:
	var transport = TRANSPORT_SCRIPT.new()
	root.add_child(transport)
	await process_frame
	_expect(transport.configure(ROOM_ID, EPOCH, 0, 1, NEGOTIATION), "valid peer identity was rejected")
	transport.peer_message.connect(_on_peer_message)
	transport.transport_error.connect(_on_transport_error)

	var input_two := _envelope(2)
	var input_one := _envelope(1)
	transport._receive_packet("input", JSON.stringify(input_two).to_utf8_buffer())
	transport._receive_packet("input", JSON.stringify(input_one).to_utf8_buffer())
	transport._receive_packet("input", JSON.stringify(input_two).to_utf8_buffer())
	_expect(received.size() == 2, "reordered input or duplicate handling was incorrect")
	_expect(received.size() >= 2 and received[0].sequence == 2 and received[1].sequence == 1, "reordered input did not reach the coordinator in arrival order")

	var reliable_one := _envelope(1)
	reliable_one["type"] = "match_start_ack"
	transport._receive_packet("reliable", JSON.stringify(reliable_one).to_utf8_buffer())
	var reliable_gap := _envelope(3)
	reliable_gap["type"] = "match_start_ack"
	transport._receive_packet("reliable", JSON.stringify(reliable_gap).to_utf8_buffer())
	_expect(errors.has("reliable_sequence_gap"), "reliable sequence gap was not rejected")
	_expect(received.size() == 3, "reliable gap packet should not reach the coordinator")

	var valid_signal := {
		"version": 1.0,
		"type": "signal",
		"seq": 4.0,
		"epoch": EPOCH,
		"negotiationId": NEGOTIATION,
		"kind": "candidate",
		"payload": JSON.stringify({"media": "0", "index": 0.0, "name": "candidate:1"}),
		"from": 1.0,
	}
	_expect(transport._validate_signal(valid_signal), "server signal with integral JSON floats was rejected")
	valid_signal["negotiationId"] = "33333333-3333-4333-8333-333333333333"
	_expect(not transport._validate_signal(valid_signal), "signal for a different negotiation was accepted")

	var candidate_payload := JSON.stringify({"media": "0", "index": 0, "name": "candidate:1"})
	_expect(transport._handle_remote_candidate(candidate_payload), "candidate arriving before SDP was rejected")
	_expect(transport._pending_remote_candidates.size() == 1, "early candidate was not queued until remote SDP")
	var invalid := _envelope(4)
	invalid["from"] = 0
	_expect(not transport._validate_envelope(invalid, "input"), "packet from the local slot was accepted as remote")
	invalid = _envelope(4)
	invalid["roomId"] = "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb"
	_expect(not transport._validate_envelope(invalid, "input"), "packet from another room was accepted")
	invalid = _envelope(4)
	invalid["version"] = 2
	_expect(not transport._validate_envelope(invalid, "input"), "unsupported peer protocol version was accepted")

	if failures.is_empty():
		print("ONLINE_PEER_TRANSPORT_SMOKE_OK reordered_input=true reliable_order=true envelope_validation=true early_ice_queue=true")
	else:
		push_error("ONLINE_PEER_TRANSPORT_SMOKE_FAILED " + "; ".join(failures))
	transport.queue_free()
	quit(0 if failures.is_empty() else 1)


func _envelope(sequence: int) -> Dictionary:
	return {
		"version": 1,
		"roomId": ROOM_ID,
		"epoch": EPOCH,
		"from": 1,
		"seq": sequence,
		"type": "input_frame",
		"payload": {"frame": sequence, "held": {}},
	}


func _on_peer_message(channel: String, message_type: String, payload: Variant, sequence: int) -> void:
	received.append({"channel": channel, "type": message_type, "payload": payload, "sequence": sequence})


func _on_transport_error(code: String) -> void:
	errors.append(code)


func _expect(condition: bool, description: String) -> void:
	if not condition:
		failures.append(description)
