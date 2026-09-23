extends SceneTree

const ROOM_CLIENT_SCRIPT := preload("res://online_room_client.gd")
const COMPATIBILITY := {
	"protocol": 1,
	"build": "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb",
	"content": "cccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc",
}

var failures: Array[String] = []


func _initialize() -> void:
	call_deferred("_run")


func _run() -> void:
	var base_url := OS.get_environment("BVN_MATCHMAKING_URL")
	if base_url.is_empty():
		base_url = "http://127.0.0.1:8787"
	var host = ROOM_CLIENT_SCRIPT.new()
	var guest = ROOM_CLIENT_SCRIPT.new()
	root.add_child(host)
	root.add_child(guest)
	_expect(host.configure_service(base_url), "host rejected the local service URL")
	_expect(guest.configure_service(base_url), "guest rejected the local service URL")
	var diagnostic_probe: Dictionary = await host._request_json(HTTPClient.METHOD_POST, "/v1/rooms", "{}", false)
	var http_diagnostic: Dictionary = host.get_last_http_diagnostic()
	_expect(not diagnostic_probe.get("ok", true), "empty room creation probe unexpectedly succeeded")
	var probe_status: Variant = diagnostic_probe.get("httpStatus")
	var probe_transport: Variant = diagnostic_probe.get("transportResult")
	if not probe_status is int or not probe_transport is int:
		_expect(false, "service probe did not return HTTP status (transport=%s, error=%s)" % [str(probe_transport), str(diagnostic_probe.get("error", "unknown"))])
		_finish(host, guest)
		return
	_expect(probe_status == 400, "service rejection did not preserve its HTTP status")
	_expect(probe_transport == HTTPRequest.RESULT_SUCCESS,
		"service rejection did not distinguish transport success from its HTTP status")
	_expect(http_diagnostic.get("httpStatus") == 400 and http_diagnostic.get("phase") == "request_completed",
		"room client did not retain bounded HTTP diagnostic metadata")
	_expect(not diagnostic_probe.has("headers") and not diagnostic_probe.has("body") and not diagnostic_probe.has("url"),
		"request diagnostic contains a private transport detail")

	var created: Dictionary = await host.create_room("Transport Host", COMPATIBILITY)
	_expect(created.has("room_id") and created.has("invite_code"), "room creation did not return a short invitation code")
	if not created.has("room_id") or not created.has("invite_code"):
		_finish(host, guest)
		return
	_expect(created.get("slot") == 0, "room creator did not receive slot 0")
	_expect(host._is_invite_code(created["invite_code"]), "service returned an invalid short invitation code")
	var room_id: String = created["room_id"]
	var old_code: String = created["invite_code"]

	var joined: Dictionary = await guest.join_by_code(old_code.to_upper(), "Transport Guest", COMPATIBILITY)
	_expect(joined.get("slot") == 1, "joined player did not receive slot 1")
	if joined.get("slot") != 1:
		_finish(host, guest)
		return
	var host_read: Dictionary = await host.refresh_state()
	var guest_read: Dictionary = await guest.refresh_state()
	_expect(host_read.get("state", {}).get("members", [null, null])[1] is Dictionary, "host did not see the admitted guest")
	_expect(guest_read.get("slot") == 1, "authenticated state read returned the wrong slot")

	var host_revision := int(host_read.get("state", {}).get("setupRevision", -1))
	var host_select: Dictionary = await host.command({
		"type": "select",
		"revision": host_revision,
		"choice": {"fighter": "rifagu", "helper": "you"},
	})
	_expect(host_select.get("acceptedSeq") == 1, "host selection command was not accepted at seq 1")
	var guest_refresh: Dictionary = await guest.refresh_state()
	var guest_revision := int(guest_refresh.get("state", {}).get("setupRevision", -1))
	var guest_select: Dictionary = await guest.command({
		"type": "select",
		"revision": guest_revision,
		"choice": {"fighter": "yihu", "helper": "kon"},
	})
	_expect(guest_select.get("acceptedSeq") == 1, "guest selection command was not accepted at seq 1")
	var host_after_setup: Dictionary = await host.refresh_state()
	var members: Array = host_after_setup.get("state", {}).get("members", [null, null])
	_expect(members[0].get("choice", {}).get("fighter") == "rifagu", "owner selection did not persist")
	_expect(members[1].get("choice", {}).get("fighter") == "yihu", "guest selection did not persist")

	var host_packets: Array[Dictionary] = []
	var guest_packets: Array[Dictionary] = []
	host.signaling_message.connect(func(message: Dictionary): host_packets.append(message))
	guest.signaling_message.connect(func(message: Dictionary): guest_packets.append(message))
	var host_socket: Dictionary = await host.connect_signaling()
	var guest_socket: Dictionary = await guest.connect_signaling()
	_expect(host_socket.has("state") and guest_socket.has("state"), "ticket websocket did not open with initial room state")
	var negotiation: Dictionary = await host.command({"type": "negotiate", "epoch": null})
	var negotiation_id := str(negotiation.get("state", {}).get("negotiation", {}).get("id", ""))
	_expect(negotiation_id.length() == 36, "owner could not establish an SDP negotiation")
	_expect(host.send_signal("offer", null, negotiation_id, "local-test-offer"), "owner offer did not enter the signaling websocket")
	var deadline := Time.get_ticks_msec() + 5_000
	while guest_packets.is_empty() and Time.get_ticks_msec() < deadline:
		await process_frame
	var received_offer := false
	var guest_signal_errors: Array[String] = []
	for packet in guest_packets:
		if packet.get("type") == "signal" and packet.get("kind") == "offer" and packet.get("from") == 0 and packet.get("payload") == "local-test-offer":
			received_offer = true
		if packet.get("type") == "error":
			guest_signal_errors.append(str(packet.get("error", "unknown")))
	_expect(received_offer, "guest did not receive the owner's signal packet; service_errors=" + ",".join(guest_signal_errors))
	_expect(guest.send_signal("answer", null, negotiation_id, "local-test-answer"), "guest answer did not enter the signaling websocket")
	deadline = Time.get_ticks_msec() + 5_000
	var received_answer := false
	while not received_answer and Time.get_ticks_msec() < deadline:
		for packet in host_packets:
			if packet.get("type") == "signal" and packet.get("kind") == "answer" and packet.get("from") == 1 and packet.get("payload") == "local-test-answer":
				received_answer = true
		if not received_answer:
			await process_frame
	_expect(received_answer, "owner did not receive the guest's answer signal")

	var guest_leave: Dictionary = await guest.command({"type": "leave"})
	_expect(guest_leave.get("acceptedSeq") == 2, "guest departure command sequence was not accepted")
	_expect(guest_leave.get("state", {}).get("members", [null, null])[1] == null, "leave acknowledgement did not accept a null local seat")
	var host_after_leave: Dictionary = await host.refresh_state()
	_expect(host_after_leave.get("state", {}).get("members", [null, null])[1] == null, "host did not observe the guest leaving")
	guest.clear_credentials()
	var reinvited: Dictionary = await host.rotate_invitation()
	_expect(reinvited.get("invite_code") is String and host._is_invite_code(reinvited.get("invite_code")),
		"owner reinvite did not return a valid short code")
	var new_code := str(reinvited.get("invite_code", ""))
	_expect(not new_code.is_empty() and new_code != old_code, "owner reinvite did not rotate the short code")
	var rejected_old_code: Dictionary = await guest.join_by_code(old_code, "Old Code Guest", COMPATIBILITY)
	_expect(rejected_old_code.get("error") == "invalid_invite" and not rejected_old_code.get("uncertain", false),
		"rotated invitation code still admitted a guest")
	var rejoined: Dictionary = await guest.join_by_code(new_code, "New Code Guest", COMPATIBILITY)
	_expect(rejoined.get("slot") == 1, "new invitation code did not admit the guest")
	var final_guest_leave: Dictionary = await guest.command({"type": "leave"})
	_expect(final_guest_leave.get("state", {}).get("members", [null, null])[1] == null,
		"guest could not leave after joining through the rotated code")
	guest.clear_credentials()

	var host_leave: Dictionary = await host.command({"type": "leave"})
	_expect(host_leave.get("state", {}).get("phase") == "closed", "owner departure did not close the room")
	if failures.is_empty():
		print("ONLINE_ROOM_CLIENT_SERVICE_SMOKE_OK diagnostics=true create_code=true join_by_code=true read=true commands=true ticket_ws=true signal_forward=true reinvite=true old_code_revoked=true leave=true")
	else:
		push_error("ONLINE_ROOM_CLIENT_SERVICE_SMOKE_FAILED " + "; ".join(failures))
	_finish(host, guest)


func _expect(condition: bool, description: String) -> void:
	if not condition:
		failures.append(description)


func _finish(host, guest) -> void:
	host.clear_credentials()
	guest.clear_credentials()
	host.queue_free()
	guest.queue_free()
	quit(0 if failures.is_empty() else 1)
