extends SceneTree

const Lobby := preload("res://online_lobby.gd")


class PresenceRoomClient:
	extends OnlineRoomClient
	var connect_calls := 0
	var commands: Array[Dictionary] = []
	var connected := false
	var terminal_code := ""
	var published_state: Dictionary = {}

	func connect_signaling() -> Dictionary:
		connect_calls += 1
		if terminal_code != "":
			var code := terminal_code
			terminal_code = ""
			connected = false
			return {"error": code, "uncertain": false}
		connected = true
		return {"state": published_state.duplicate(true)}

	func is_signaling_connected() -> bool:
		return connected

	func command(operation: Dictionary) -> Dictionary:
		commands.append(operation.duplicate(true))
		var state := published_state.duplicate(true)
		state["revision"] = int(state.get("revision", 1)) + commands.size()
		published_state = state
		return {"acceptedSeq": commands.size(), "state": state}

	func has_uncertain_command() -> bool:
		return false

	func is_command_in_flight() -> bool:
		return false

	func get_room_state() -> Dictionary:
		return published_state.duplicate(true)

	func close_signaling() -> void:
		connected = false


func _initialize() -> void:
	call_deferred("_run")


func _run() -> void:
	var lobby: OnlineLobby = Lobby.new()
	root.add_child(lobby)
	await process_frame
	var client := PresenceRoomClient.new()
	lobby.add_child(client)
	lobby.room_client = client
	var room_id := "a".repeat(64)
	var now_ms := int(Time.get_unix_time_from_system() * 1000.0)
	var state := {
		"id": room_id,
		"phase": "lobby",
		"revision": 1,
		"setupRevision": 1,
		"members": [{
			"nickname": "房主",
			"choice": null,
			"ready": false,
			"profile": null,
		}, null],
		"stage": lobby._stage_ids[0],
		"rules": {"time": 90, "life": 1},
		"networkProfile": {"id": "chrome-exp-d2-p6", "inputDelay": 2, "predictionWindow": 6},
		"match": null,
		"lastResult": null,
		"negotiation": null,
		"lastActivity": now_ms,
		"leaseUntil": now_ms + 30 * 60 * 1000,
	}
	client.published_state = state.duplicate(true)
	lobby._room_id = room_id
	lobby._slot = 0
	lobby._invite_code = "calm-otter-abcdefgh"
	lobby._room_state = state.duplicate(true)
	lobby._network_profile_authority = state["networkProfile"].duplicate(true)
	lobby._status.text = "正在创建房间…"
	lobby._show_room()
	lobby._arm_lobby_presence()
	assert(client.connect_calls == 1, "Creating a room did not open signaling")
	assert(client.connected, "Lobby signaling did not stay open after create")
	assert(not lobby._status.text.begins_with("正在创建房间"),
		"Create status stayed on the in-progress text: " + lobby._status.text)
	assert(lobby._status.text.contains("邀请口令已显示") and lobby._status.text.contains("信令已连接")
		and lobby._status.text.contains("正在等待对手") and lobby._status.text.contains("最长约 2 小时"),
		"Host lobby status did not show the invite and a live socket: " + lobby._status.text)
	lobby._slot = 1
	var guest_status := lobby._lobby_presence_status_text()
	assert(guest_status.begins_with("已加入房间，信令已连接"),
		"Guest lobby status did not report a connected socket: " + guest_status)
	lobby._slot = 0

	client.connected = false
	lobby._on_socket_state_changed(false)
	assert(lobby._status.text.begins_with("信令已断开"),
		"A dropped lobby socket did not schedule a visible reconnect: " + lobby._status.text)
	lobby._process(0.4)
	assert(client.connect_calls == 1, "Lobby reconnect did not wait out its backoff")
	lobby._process(1.0)
	assert(client.connect_calls == 2 and client.connected,
		"Lobby reconnect did not run after the backoff elapsed")
	assert(lobby._status.text.contains("信令已连接") and lobby._status.text.contains("正在等待对手"),
		"Reconnect did not restore the waiting status: " + lobby._status.text)

	lobby._room_connection_ready = true
	client.connected = false
	lobby._on_socket_state_changed(false)
	lobby._process(40.0)
	assert(client.connect_calls == 2,
		"Lobby reconnect replaced a socket owned by character-select")
	lobby._room_connection_ready = false
	client.connected = true

	lobby._process(899.0)
	assert(client.commands.is_empty(), "Keepalive fired before the 15 minute interval")
	lobby._process(2.0)
	assert(client.commands.size() == 1 and str(client.commands[0].get("type", "")) == "keepalive",
		"An open lobby socket did not send keepalive: " + JSON.stringify(client.commands))

	lobby._lobby_reconnect_attempt = 8
	lobby._schedule_lobby_reconnect()
	assert(lobby._lobby_reconnect_wait <= 30.0, "Lobby reconnect backoff exceeded 30 seconds")
	lobby._lobby_reconnect_wait = 0.0
	lobby._lobby_reconnect_attempt = 0

	var calls_before_terminal := client.connect_calls
	client.terminal_code = "invite_expired"
	client.connected = false
	lobby._process(0.0)
	assert(client.connect_calls == calls_before_terminal + 1,
		"A terminal lobby error did not attempt the in-flight reconnect once")
	assert(not lobby._lobby_signaling_desired, "invite_expired kept scheduling lobby reconnects")
	assert(lobby._status.text.contains("已过期"),
		"invite_expired did not explain that the code is gone: " + lobby._status.text)
	lobby._process(120.0)
	assert(client.connect_calls == calls_before_terminal + 1,
		"Lobby reconnect continued after invite_expired")
	for code in ["unauthorized", "not_authenticated", "not_in_room", "membership_ended", "service_http_401"]:
		client.terminal_code = code
		client.connected = false
		var calls_before_auth_failure := client.connect_calls
		lobby._arm_lobby_presence()
		assert(not lobby._lobby_signaling_desired, code + " kept lobby presence active")
		lobby._process(120.0)
		assert(client.connect_calls == calls_before_auth_failure + 1,
			code + " kept requesting signaling tickets")
	assert(not lobby._lobby_presence_error_is_terminal("invalid_ticket"),
		"An expired single-use ticket should allow fetching a fresh ticket")
	client.terminal_code = "http_transport_failed"
	client.connected = false
	lobby._arm_lobby_presence()
	assert(lobby._lobby_signaling_desired and lobby._lobby_reconnect_wait > 0.0,
		"Transient transport failure stopped lobby presence")
	var calls_before_retry := client.connect_calls
	lobby._process(31.0)
	assert(client.connect_calls == calls_before_retry + 1 and client.connected,
		"Transient transport failure did not reconnect")
	assert(await _check_ticket_cancellation(lobby, state), "Ticket cancellation checks failed")
	print("ONLINE_LOBBY_PRESENCE_SMOKE_OK create_connects=true invite_status=true reconnect_backoff=true selection_socket_held=true keepalive=15m terminal_stop=true auth_stop=true ticket_cancel_restart=true")
	quit(0)


func _check_ticket_cancellation(lobby: OnlineLobby, state: Dictionary) -> bool:
	# Keep real HTTPRequests pending without relying on an external service.
	var server := TCPServer.new()
	assert(server.listen(0, "127.0.0.1") == OK)
	var client := OnlineRoomClient.new()
	lobby.add_child(client)
	lobby.room_client = client
	client._base_url = "http://127.0.0.1:%d" % server.get_local_port()
	var errors: Array[String] = []
	client.error.connect(func(code: String) -> void: errors.append(code))
	for attempt in 2:
		client._room_id = str(state["id"])
		client._slot = 0
		client._session_token = "A".repeat(43)
		lobby._arm_lobby_presence()
		var request_node := client._signaling_request
		assert(request_node != null and lobby._lobby_signaling_in_flight,
			"A fresh lobby could not start a signaling ticket request")
		if attempt == 1:
			client.cancel_signaling()
		await lobby._cancel_lobby_signaling()
		client.cancel_signaling()
		assert(not lobby._lobby_signaling_in_flight and not client._socket_connecting,
			"Cancelling a ticket left signaling in flight")
		assert(client._signaling_request == null, "Cancelled request remained attached")
		assert(not lobby._lobby_signaling_desired and lobby._lobby_reconnect_wait == 0.0,
			"Cancelled request scheduled a reconnect")
		await process_frame
		assert(not is_instance_valid(request_node), "Cancelled HTTPRequest was not freed")
		client.clear_credentials()
	assert(errors.is_empty(), "Cancellation reported a stale transport error: " + str(errors))
	server.stop()
	return true
