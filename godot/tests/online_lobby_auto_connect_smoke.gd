extends SceneTree

class GuestLobby extends OnlineLobby:
	var starts := 0

	func _start_room_connection() -> void:
		starts += 1


class DiagnosticGame extends Control:
	var diagnostics := DiagnosticRuntime.new()
	var title_menu: TitleMenu

	func _diagnostic_snapshot() -> Dictionary:
		return {"fightTick": 0}


func _initialize() -> void:
	call_deferred("_run")


func _run() -> void:
	var lobby := GuestLobby.new()
	root.add_child(lobby)
	lobby._room_id = "a".repeat(64)
	lobby._slot = 1
	var state := {
		"id": lobby._room_id, "phase": "lobby", "revision": 1,
		"setupRevision": 0, "members": [{}, {}],
		"networkProfile": {"id": "chrome-exp-d2-p6", "inputDelay": 2, "predictionWindow": 6},
		"negotiation": null,
	}
	lobby._accept_state(state)
	await process_frame
	assert(lobby.starts == 0, "Joining alone must not start an unsolicited negotiation")
	state.negotiation = {
		"id": "11111111-1111-4111-8111-111111111111", "epoch": null,
		"expires": int(Time.get_unix_time_from_system() * 1000) + 60000,
	}
	lobby._busy = true
	lobby._accept_state(state)
	await process_frame
	assert(lobby.starts == 0, "An in-flight room operation must finish first")
	lobby._busy = false
	lobby._accept_state(state)
	await process_frame
	assert(lobby.starts == 1, "A polled host request must connect a guest without a button press or socket")
	lobby._accept_state(state)
	await process_frame
	assert(lobby.starts == 1, "Repeated polling must not retry a failed request forever")
	state.negotiation.expires += 10000
	lobby._accept_state(state)
	await process_frame
	assert(lobby.starts == 1, "Extending the same handshake must not restart the guest")
	# The completed selection channel has disconnected, but its request key remains.
	lobby._room_connection_ready = true
	lobby._close_room_connection()
	assert(lobby._auto_connection_request.ends_with(str(state.negotiation.id)))
	state.negotiation.id = "22222222-2222-4222-8222-222222222222"
	lobby._room_connection_starting = true
	lobby._accept_state(state)
	await process_frame
	assert(lobby.starts == 1, "Manual connection startup must not race auto-connect")
	lobby._room_connection_starting = false
	lobby._accept_state(state)
	await process_frame
	assert(lobby.starts == 2, "A fresh host retry must wake the guest")
	state.negotiation.id = "33333333-3333-4333-8333-333333333333"
	state.negotiation.expires = 1
	lobby._accept_state(state)
	await process_frame
	assert(lobby.starts == 2, "Expired requests must be ignored")
	state.negotiation.expires = int(Time.get_unix_time_from_system() * 1000) + 60000
	state.negotiation.epoch = "44444444-4444-4444-8444-444444444444"
	lobby._accept_state(state)
	await process_frame
	assert(lobby.starts == 2, "Match negotiations must not start selection connections")
	state.negotiation.epoch = null
	lobby._slot = 0
	lobby._accept_state(state)
	await process_frame
	assert(lobby.starts == 2, "The host must retain control of starting negotiation")
	lobby._slot = 1
	lobby._accept_state(state)
	lobby._room_id = ""
	await process_frame
	assert(lobby.starts == 2, "A deferred request must not connect after leaving")
	var game := DiagnosticGame.new()
	root.add_child(game)
	game.add_child(game.diagnostics)
	lobby.configure(null, game)
	lobby._invite_code = "private-invitation"
	lobby._connection_phase = "ice_servers"
	lobby._show_error("http_transport_failed")
	var snapshot: Dictionary = game.diagnostics.snapshot_provider.call()
	assert(snapshot.fightTick == 0 and snapshot.onlineLobby.lastError.phase == "ice_servers")
	assert(snapshot.onlineLobby.lastError.code == "http_transport_failed")
	assert(not JSON.stringify(snapshot).contains("private-invitation"), "Diagnostics leaked an invitation")
	lobby._show_error("https://example.invalid/private-token")
	assert(lobby.get_connection_diagnostic().lastError.code == "unclassified_error")
	lobby.queue_free()
	await process_frame
	assert(game.diagnostics.snapshot_provider == Callable(game, "_diagnostic_snapshot"))
	game.queue_free()
	await process_frame
	print("ONLINE_LOBBY_AUTO_CONNECT_SMOKE_OK")
	quit()
