extends SceneTree


const ROOM_ID := "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"
const ROOM_CLIENT_SCRIPT := preload("res://online_room_client.gd")
const PEER_TRANSPORT_SCRIPT := preload("res://online_peer_transport.gd")
const FAULT_CLIENT_SCRIPT := preload("res://tests/online_room_client_fault_fixture.gd")
const EPOCH := "11111111-1111-4111-8111-111111111111"
const NEGOTIATION := "22222222-2222-4222-8222-222222222222"
const BUILD_HASH := "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb"
const CONTENT_HASH := "cccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc"
var failures: Array[String] = []


func _initialize() -> void:
	call_deferred("_run")


func _run() -> void:
	var client = ROOM_CLIENT_SCRIPT.new()
	root.add_child(client)
	client._room_id = ROOM_ID
	client._slot = 1
	client._session_token = "A".repeat(43)
	client._last_accepted_seq = 7

	var local_member := _member("host", 3)
	var remote_member := _member("local", 7)
	var state := _state(ROOM_ID, 7, [local_member, remote_member])
	_expect(client._validate_room_state(state, ROOM_ID, 1, false), "valid room projection was rejected")
	_expect(client._validate_state_reply({"slot": 1, "state": state}), "GET state response shape was rejected")
	var legacy_state := state.duplicate(true)
	legacy_state.erase("networkProfile")
	_expect(client._room_state_reply_missing_network_profile({"slot": 1, "state": legacy_state}),
		"room state without networkProfile did not require a server upgrade")
	_expect(not client._validate_state_reply({"slot": 1, "state": legacy_state}),
		"legacy room projection without authoritative networkProfile was accepted")
	var legacy_client = FAULT_CLIENT_SCRIPT.new()
	root.add_child(legacy_client)
	legacy_client._base_url = "http://127.0.0.1:8787"
	legacy_client._room_id = ROOM_ID
	legacy_client._session_token = "L".repeat(43)
	legacy_client._slot = 1
	legacy_client.fixture_state = legacy_state
	legacy_client.omit_network_profile = true
	var upgrade_required: Dictionary = await legacy_client.refresh_state()
	_expect(upgrade_required.get("error") == "server_upgrade_required",
		"legacy service state did not produce the explicit server_upgrade_required error")
	var malformed_network_profile := state.duplicate(true)
	malformed_network_profile["networkProfile"] = {"id": "chrome-exp-d2-p6", "inputDelay": 2.5, "predictionWindow": 6}
	_expect(not client._validate_room_state(malformed_network_profile, ROOM_ID, 1, false),
		"fractional authoritative network profile was accepted")
	var fresh_client = ROOM_CLIENT_SCRIPT.new()
	fresh_client._slot = -1
	_expect(fresh_client._validate_admission_reply({"roomId": ROOM_ID, "slot": 1, "state": state}), "join response was rejected before installing slot")
	_expect(fresh_client._is_invite_code("calm-otter-abcdefgh"), "service short-code format was rejected")
	_expect(not fresh_client._is_invite_code("calm-otter-abcdefg0"), "short code outside the service suffix alphabet was accepted")
	_expect(not fresh_client._is_invite_code("calm-otter-bad"), "short code with the wrong suffix length was accepted")
	_expect(not client._validate_state_reply({"slot": 0, "state": state}), "foreign slot state was accepted")
	_expect(not client._validate_room_state(5, ROOM_ID, 1), "non-object state should fail closed")
	var cloudflare_ice := {
		"expiresIn": 14400,
		"iceServers": [
			{"urls": ["stun:stun.cloudflare.com:3478"]},
			{
				"urls": [
					"turn:turn.cloudflare.com:3478?transport=udp",
					"turn:turn.cloudflare.com:3478?transport=tcp",
					"turns:turn.cloudflare.com:5349?transport=tcp",
				],
				"username": "temporary-user",
				"credential": "temporary-password",
			},
		],
	}
	_expect(client._validate_ice_response(cloudflare_ice), "Cloudflare STUN and TURN response was rejected")
	var peer_transport = PEER_TRANSPORT_SCRIPT.new()
	root.add_child(peer_transport)
	var normalized_cloudflare_ice := client._normalize_ice_response(cloudflare_ice)
	_expect(not normalized_cloudflare_ice.is_empty(), "Cloudflare ICE response did not normalize")
	_expect(peer_transport._validate_ice_servers(normalized_cloudflare_ice.get("iceServers", [])),
		"Normalized Cloudflare ICE response failed the peer transport validator")
	var standard_string_urls := {
		"expiresIn": 14400,
		"iceServers": [
			{"urls": "stun:stun.cloudflare.com:3478"},
			{
				"urls": "turn:turn.cloudflare.com:3478?transport=udp",
				"username": "temporary-user",
				"credential": "temporary-password",
			},
		],
	}
	var normalized_string_urls := client._normalize_ice_response(standard_string_urls)
	_expect(not normalized_string_urls.is_empty(), "RTC-standard string ICE URLs were rejected")
	_expect(normalized_string_urls.iceServers[0].urls is Array
		and normalized_string_urls.iceServers[0].urls == ["stun:stun.cloudflare.com:3478"],
		"ICE URLs were not normalized to the peer transport's array contract")
	_expect(peer_transport._validate_ice_servers(normalized_string_urls.get("iceServers", [])),
		"Normalized RTC-standard ICE response failed the peer transport validator")
	var no_turn_credentials := cloudflare_ice.duplicate(true)
	no_turn_credentials["iceServers"][1].erase("credential")
	_expect(not client._validate_ice_response(no_turn_credentials), "TURN server without credentials was accepted")
	var stun_only := {"expiresIn": 14400, "iceServers": [{"urls": ["stun:stun.cloudflare.com:3478"]}]}
	_expect(not client._validate_ice_response(stun_only), "STUN-only response was accepted without a TURN relay")

	var malformed := state.duplicate(true)
	malformed["compatibility"] = 5
	_expect(not client._validate_room_state(malformed, ROOM_ID, 1), "malformed compatibility should fail closed")
	malformed = state.duplicate(true)
	malformed["members"][1]["nickname"] = 9
	_expect(not client._validate_room_state(malformed, ROOM_ID, 1), "malformed member should fail closed")
	malformed = state.duplicate(true)
	malformed["setupRevision"] = "1"
	_expect(not client._validate_room_state(malformed, ROOM_ID, 1), "malformed revision should fail closed")
	malformed = state.duplicate(true)
	malformed["match"] = _match()
	malformed["match"]["acknowledged"] = [true, null]
	malformed["phase"] = "active"
	_expect(not client._validate_room_state(malformed, ROOM_ID, 1), "null start acknowledgement should fail closed")

	client._last_room_revision = 7
	client._room_state = state.duplicate(true)
	var stale := state.duplicate(true)
	stale["revision"] = 6
	client._accept_state(stale)
	_expect(client.get_room_state()["revision"] == 7, "stale room projection replaced the current state")
	client._accept_state(state)
	_expect(client.get_room_state()["revision"] == 7, "current room projection was not installed")
	var departed := _state(ROOM_ID, 8, [local_member, null])
	client._accept_state(departed)
	_expect(client.get_room_state()["members"][1] == null, "guest departure projection was rejected")
	_expect(client._last_accepted_seq == 7, "departed seat incorrectly reset the local command sequence")

	client._handle_socket_packet("pong".to_utf8_buffer())
	_expect(client._socket_last_error.is_empty(), "raw server pong should be ignored")
	var signal_message := {
		"version": 1.0,
		"type": "signal",
		"seq": 0.0,
		"epoch": null,
		"negotiationId": NEGOTIATION,
		"kind": "candidate",
		"payload": JSON.stringify({"media": "0", "index": 0, "name": "candidate:1"}),
		"from": 0.0,
	}
	_expect(client._validate_signaling_message(signal_message), "integral JSON floats should satisfy integer fields")
	signal_message["epoch"] = {"unexpected": true}
	_expect(not client._validate_signaling_message(signal_message), "non-string epoch was accepted")

	var fault_client = FAULT_CLIENT_SCRIPT.new()
	root.add_child(fault_client)
	fault_client._base_url = "http://127.0.0.1:8787"
	fault_client._room_id = ROOM_ID
	fault_client._session_token = "D".repeat(43)
	fault_client._slot = 1
	fault_client._last_accepted_seq = 7
	fault_client.fixture_state = _state(ROOM_ID, 7, [_member("host", 3), _member("guest", 7)])
	var first := await fault_client.command({"type": "ready", "revision": 4})
	_expect(first.get("uncertain", false), "lost command response did not stay uncertain")
	_expect(fault_client.has_uncertain_command(), "uncertain command body was discarded")
	var blocked := await fault_client.command({"type": "leave"})
	_expect(blocked.get("error") == "command_outcome_uncertain", "next command was allowed before retry")
	_expect(fault_client.command_requests.size() == 1, "blocked command reached the service")
	var retry := await fault_client.retry_pending_command()
	_expect(retry.get("acceptedSeq") == 8, "same-sequence command retry was not accepted")
	_expect(fault_client.command_requests.size() == 2, "retry did not issue one identical request")
	_expect(fault_client.command_requests[0] == fault_client.command_requests[1], "retry changed the exact command body")
	_expect(not fault_client.has_uncertain_command(), "successful retry did not clear uncertainty")
	_expect(fault_client._last_accepted_seq == 8, "accepted sequence did not advance")

	var code_client = FAULT_CLIENT_SCRIPT.new()
	root.add_child(code_client)
	code_client._base_url = "http://127.0.0.1:8787"
	code_client.fixture_state = _state(ROOM_ID, 1, [_member("host", 0), _member("guest", 1)])
	var uncertain_code_join: Dictionary = await code_client.join_by_code(
		"Calm-Otter-ABCDEFGH", "Code Guest", {"protocol": 1, "build": BUILD_HASH, "content": CONTENT_HASH}
	)
	_expect(uncertain_code_join.get("uncertain", false), "uncertain short-code join did not retain its admission request")
	_expect(code_client.admission_requests.size() == 1, "short-code join was not sent through the body-based route")
	var code_request: Dictionary = JSON.parse_string(code_client.admission_requests[0])
	_expect(code_request.get("code") == "calm-otter-abcdefgh", "short code was not normalized before admission")
	var code_join_retry: Dictionary = await code_client.retry_pending_admission()
	_expect(code_join_retry.get("slot") == 1, "short-code retry did not restore the guest seat")
	_expect(code_client.admission_requests.size() == 2
		and code_client.admission_requests[0] == code_client.admission_requests[1],
		"short-code retry changed its code, session token, or exact admission body")

	var owner_client = FAULT_CLIENT_SCRIPT.new()
	root.add_child(owner_client)
	owner_client._base_url = "http://127.0.0.1:8787"
	owner_client.fixture_state = _state(ROOM_ID, 1, [_member("host", 0), null])
	var uncertain_create: Dictionary = await owner_client.create_room(
		"Code Host", {"protocol": 1, "build": BUILD_HASH, "content": CONTENT_HASH}
	)
	_expect(uncertain_create.get("uncertain", false), "uncertain create did not retain its admission request")
	var create_retry: Dictionary = await owner_client.retry_pending_admission()
	_expect(create_retry.get("invite_code") == "calm-otter-abcdefgh", "create did not return the service-issued short code")
	_expect(owner_client.admission_requests.size() == 2
		and owner_client.admission_requests[0] == owner_client.admission_requests[1],
		"create retry changed its original token or request body")
	var uncertain_rotation: Dictionary = await owner_client.rotate_invitation()
	_expect(uncertain_rotation.get("uncertain", false), "uncertain reinvite did not retain its command")
	var rotation_body: String = owner_client.command_requests[0]
	var rotation_retry: Dictionary = await owner_client.retry_pending_command()
	var rotation_request: Dictionary = JSON.parse_string(rotation_body)
	_expect(rotation_retry.get("invite_code") == "bright-wolf-234567ab", "reinvite did not expose the new service-issued code")
	_expect(owner_client.command_requests.size() == 2
		and owner_client.command_requests[0] == owner_client.command_requests[1],
		"reinvite retry changed the accepted sequence or invite token")
	_expect(owner_client._invite_token == rotation_request.get("operation", {}).get("inviteToken"),
		"successful reinvite did not replace the old internal invitation token")

	if failures.is_empty():
		print("ONLINE_ROOM_CLIENT_SMOKE_OK state_validation=true network_profile_validation=true server_upgrade_required=true cloudflare_ice=true ice_transport_chain=true string_urls_normalized=true turn_credentials_required=true monotonic_revision=true leave_projection=true exact_retry=true short_code_join=true create_code=true reinvite_retry=true")
	else:
		push_error("ONLINE_ROOM_CLIENT_SMOKE_FAILED " + "; ".join(failures))
	client.queue_free()
	fault_client.queue_free()
	code_client.queue_free()
	owner_client.queue_free()
	legacy_client.queue_free()
	fresh_client.queue_free()
	peer_transport.queue_free()
	quit(0 if failures.is_empty() else 1)


func _member(nickname: String, sequence: int) -> Dictionary:
	return {
		"nickname": nickname,
		"choice": null,
		"ready": false,
		"profile": null,
		"seq": sequence,
	}


func _state(room_id: String, revision: int, members: Array) -> Dictionary:
	return {
		"schema": 1,
		"id": room_id,
		"compatibility": {"protocol": 1, "build": BUILD_HASH, "content": CONTENT_HASH},
		"revision": revision,
		"setupRevision": 1,
		"members": members,
		"stage": "现世",
		"rules": {"time": 90, "life": 1},
		"networkProfile": {"id": "chrome-exp-d2-p6", "inputDelay": 2, "predictionWindow": 6},
		"phase": "lobby",
		"match": null,
		"lastResult": null,
		"negotiation": null,
		"lastActivity": 1000,
		"leaseUntil": 20_000,
	}


func _match() -> Dictionary:
	return {
		"epoch": EPOCH,
		"seed": 1234,
		"clockBaseline": 0,
		"profile": {"id": "rollback-v1", "inputDelay": 2, "predictionWindow": 8},
		"deadline": 20_000,
		"loaded": [null, null],
		"acknowledged": [false, false],
		"results": [null, null],
	}


func _expect(condition: bool, description: String) -> void:
	if not condition:
		failures.append(description)
