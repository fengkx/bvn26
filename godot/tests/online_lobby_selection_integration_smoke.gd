extends SceneTree

const Lobby := preload("res://online_lobby.gd")


class FakeGame extends Control:
	class FakeSession extends RefCounted:
		func menu_held() -> Dictionary:
			return {}

	var session := FakeSession.new()
	var title_menu: TitleMenu

	func _physics_process(_delta: float) -> void:
		pass


class FakeRoomConnection extends Node:
	var remote_lobby: Node
	var next_sequence := 0
	var sent_messages: Array[Dictionary] = []
	var connection_state := "connected"

	func send_peer_message(message_type: String, payload: Variant) -> bool:
		if remote_lobby == null or connection_state != "connected":
			return false
		next_sequence += 1
		var message := {
			"type": message_type,
			"payload": payload.duplicate(true) if payload is Dictionary else payload,
			"sequence": next_sequence,
		}
		sent_messages.append(message)
		remote_lobby.call_deferred(
			"_on_room_connection_message",
			message_type,
			message.payload,
			next_sequence
		)
		return true

	func start() -> String:
		connection_state = "connected"
		return ""

	func close() -> void:
		connection_state = "closed"

	func get_connection_state() -> String:
		return connection_state


class FakeSelectionRoomServer extends RefCounted:
	var state: Dictionary = {}
	var clients: Array = []
	var command_order: Array[int] = []
	var state_push_before_reply: Array[int] = []
	var waiting_slots: Array[int] = []
	var refresh_waiting_slots: Array[int] = []
	var hold_http_replies := false
	var hold_owner_refresh := false
	signal owner_http_reply_released
	signal guest_http_reply_released
	signal owner_refresh_released

	func publish_state_before_reply(slot: int) -> void:
		state_push_before_reply.append(slot)
		for client in clients:
			client.emit_signal("state_changed", state.duplicate(true))

	func release_http_reply(slot: int) -> void:
		if slot == 0:
			owner_http_reply_released.emit()
		else:
			guest_http_reply_released.emit()


class FakeSelectionRoomClient extends OnlineRoomClient:
	var server: FakeSelectionRoomServer
	var slot := -1
	var next_sequence := 0
	var select_commands: Array[Dictionary] = []
	var operations: Array[Dictionary] = []

	func refresh_state() -> Dictionary:
		if slot == 0 and server.hold_owner_refresh:
			server.refresh_waiting_slots.append(slot)
			await server.owner_refresh_released
			server.refresh_waiting_slots.erase(slot)
		return {"slot": slot, "state": server.state.duplicate(true)}

	func has_uncertain_command() -> bool:
		return false

	func command(operation: Dictionary) -> Dictionary:
		operations.append(operation.duplicate(true))
		next_sequence += 1
		var operation_type := str(operation.get("type", ""))
		if operation_type == "configure_network":
			if slot != 0 or int(operation.get("revision", -1)) != int(server.state.get("setupRevision", -2)):
				return {"error": "stale_revision"}
			var next_state: Dictionary = server.state.duplicate(true)
			next_state["networkProfile"] = operation.get("profile", {}).duplicate(true)
			next_state["revision"] = int(next_state.get("revision", 0)) + 1
			next_state["setupRevision"] = int(next_state.get("setupRevision", 0)) + 1
			var members: Array = next_state.get("members", []).duplicate(true)
			for member_index in members.size():
				if members[member_index] is Dictionary:
					var member: Dictionary = members[member_index].duplicate(true)
					member["ready"] = false
					member["profile"] = null
					members[member_index] = member
			next_state["members"] = members
			next_state["negotiation"] = null
			server.state = next_state
			server.command_order.append(slot)
			server.publish_state_before_reply(slot)
			return {"state": server.state.duplicate(true), "acceptedSeq": next_sequence}
		if operation_type != "select":
			return {"error": "unexpected_operation"}
		select_commands.append(operation.duplicate(true))
		server.command_order.append(slot)
		var next_state: Dictionary = server.state.duplicate(true)
		var members: Array = next_state.get("members", []).duplicate(true)
		var member: Dictionary = members[slot].duplicate(true)
		member["choice"] = operation.get("choice", {}).duplicate(true)
		members[slot] = member
		next_state["members"] = members
		next_state["revision"] = int(next_state.get("revision", 0)) + 1
		next_state["setupRevision"] = int(next_state.get("setupRevision", 0)) + 1
		server.state = next_state
		# Model the service push winning the race against the HTTP response.
		server.publish_state_before_reply(slot)
		if server.hold_http_replies:
			server.waiting_slots.append(slot)
			if slot == 0:
				await server.owner_http_reply_released
			else:
				await server.guest_http_reply_released
			server.waiting_slots.erase(slot)
		return {"state": server.state.duplicate(true), "acceptedSeq": next_sequence}


func _initialize() -> void:
	call_deferred("_run")


func _run() -> void:
	var host_game := FakeGame.new()
	var guest_game := FakeGame.new()
	for game in [host_game, guest_game]:
		game.title_menu = TitleMenu.new()
		game.add_child(game.title_menu)
		root.add_child(game)
		game.set_physics_process(true)

	var host := Lobby.new()
	var guest := Lobby.new()
	for lobby in [host, guest]:
		lobby.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
		root.add_child(lobby)
	await process_frame
	for pair in [[host, host_game], [guest, guest_game]]:
		pair[0].configure(null, pair[1])
		pair[0].call("_end_selection_session", false)
		assert(pair[1].is_physics_processing(),
			"Ending an inactive selector changed Main's existing physics state")

	var host_connection := FakeRoomConnection.new()
	var guest_connection := FakeRoomConnection.new()
	root.add_child(host_connection)
	root.add_child(guest_connection)
	host_connection.remote_lobby = guest
	guest_connection.remote_lobby = host
	host._room_connection = host_connection
	guest._room_connection = guest_connection
	host._room_connection_ready = true
	guest._room_connection_ready = true
	host._slot = 0
	guest._slot = 1
	host._room_id = "fake-selection-room"
	guest._room_id = "fake-selection-room"

	var host_choice := {
		"fighter": host._fighter_ids[0],
		"helper": host._helper_ids[0],
	}
	var guest_choice := {
		"fighter": guest._fighter_ids[0],
		"helper": guest._helper_ids[0],
	}
	var state := _room_state(host_choice, guest_choice, host._stage_ids[0])
	for lobby in [host, guest]:
		lobby.call("_accept_state", state)
		lobby._show_room()
		assert(not (host_game if lobby == host else guest_game).is_physics_processing(),
			"Room view should pause the title menu before opening selector")
		lobby.call("_on_room_connection_changed", "connected")
		lobby._local_connection_profile_id = "chrome-exp-d1-p2-lan"

	var room_options := 0
	for node in host._room_view.find_children("*", "OptionButton", true, false):
		room_options += 1
	assert(room_options == 4,
		"Room should expose only time/life/network dropdowns; choices and map use the original visual pickers")
	var connection_profile := {"version": 1, "id": "chrome-exp-d1-p2-lan"}
	host.call("_on_room_connection_message", "selection_connection_profile", connection_profile, 1)
	guest.call("_on_room_connection_message", "selection_connection_profile", connection_profile, 1)
	for _frame in 4:
		await process_frame
	var host_view: OnlineCharacterSelectionAdapter = host._selection_adapter
	var guest_view: OnlineCharacterSelectionAdapter = guest._selection_adapter
	assert(host_view != null and guest_view != null)
	assert(host._selection_active and guest._selection_active,
		"Host selection_open did not start the guest selector")
	var first_selection_session := host._selection_session_id
	assert(host_connection.sent_messages.any(func(message: Dictionary) -> bool:
		return str(message.get("type", "")) == "selection_open"
	), "Host did not open the selection session over the fake room connection")
	assert(host_view.get_parent() == host_game and guest_view.get_parent() == guest_game,
		"Online choices must use the actual VS Human selector inside each game viewport")
	assert(host_view.visible and guest_view.visible)
	assert(host_view is CharacterSelection and guest_view is CharacterSelection)
	assert(not host._dialog.visible and not guest._dialog.visible and not host._veil.visible and not guest._veil.visible,
		"The room dialog remained visible over the full-screen character selector")

	var host_local_before := host_view._local_choice_resource_ids()
	var host_remote_before := str(host_view.fighters[1])
	host_view.repeats[0] = int(host_view.spec.repeat_frames) - 1
	host_view.tick_local({"right": true})
	await process_frame
	assert(host_view._local_choice_resource_ids() != host_local_before,
		"Host's P1 key did not move the host's own character")
	assert(str(host_view.fighters[1]) == host_remote_before,
		"Host's input moved the guest's character")
	assert(str(guest_view.fighters[0]) == str(host_view.fighters[0]),
		"The room connection did not mirror the host selection snapshot")

	var guest_local_before := guest_view._local_choice_resource_ids()
	var guest_remote_before := str(guest_view.fighters[0])
	guest_view.repeats[1] = int(guest_view.spec.repeat_frames) - 1
	guest_view.tick_local({"right": true})
	await process_frame
	assert(guest_view._local_choice_resource_ids() != guest_local_before,
		"Guest's local P1 key did not map to the guest's own seat")
	assert(str(guest_view.fighters[0]) == guest_remote_before,
		"Guest's input moved the host's character")
	assert(str(host_view.fighters[1]) == str(guest_view.fighters[1]),
		"The room connection did not mirror the guest selection snapshot")

	# A stale service projection may update room labels but must not overwrite the
	# in-progress local visual-selection draft.
	var draft_before_refresh := host_view._local_choice_resource_ids()
	host._accept_state(state.duplicate(true))
	assert(host._selection_active and host_view.visible)
	assert(host_view._local_choice_resource_ids() == draft_before_refresh,
		"A room-state refresh overwrote the host's uncommitted visual selection")

	var selection_server := FakeSelectionRoomServer.new()
	selection_server.state = state.duplicate(true)
	selection_server.hold_http_replies = true
	var host_room_client := _install_fake_room_client(host, selection_server, 0)
	var guest_room_client := _install_fake_room_client(guest, selection_server, 1)
	_confirm_local_selection(guest_view)
	await _wait_selection_delay(guest_view)
	assert(selection_server.command_order.is_empty(),
		"Guest submitted its choice before the host completed the shared selection")
	_confirm_local_selection(host_view)
	await _wait_selection_delay(host_view)
	assert(host_view.phase == 1 and guest_view.phase == 1,
		"Both confirmed fighter choices did not enter the helper phase")
	_confirm_local_selection(guest_view)
	await _wait_selection_delay(guest_view)
	assert(selection_server.command_order.is_empty(),
		"A faster guest submitted before the host confirmed the helper phase")
	_confirm_local_selection(host_view)
	await _wait_for_waiting_slot(selection_server, 0)
	assert(selection_server.command_order == [0] and selection_server.state_push_before_reply == [0],
		"Host select did not publish room state before its HTTP reply")
	assert(host._busy and host._selection_commit_busy,
		"Host room-state push unlocked controls before select HTTP completion")
	assert(_member_choice(selection_server.state, 0) == host._selection_completed_choice,
		"Synchronous room state did not contain the host choice before its HTTP reply")
	selection_server.release_http_reply(0)
	await _wait_for_waiting_slot(selection_server, 1)
	assert(selection_server.command_order == [0, 1] and selection_server.state_push_before_reply == [0, 1],
		"Guest did not commit after the host; room state push did not beat guest HTTP reply")
	assert(guest._busy and guest._selection_commit_busy,
		"Guest room-state push unlocked controls before select HTTP completion")
	assert(_member_choice(selection_server.state, 1) == guest._selection_completed_choice,
		"Synchronous room state did not contain the guest choice before its HTTP reply")
	selection_server.release_http_reply(1)
	for _frame in 120:
		if not host._selection_active and not guest._selection_active:
			break
		await process_frame
	assert(not host._selection_active and not guest._selection_active,
		"Both selection commits were not acknowledged back to the room")
	assert(host_room_client.select_commands.size() == 1 and guest_room_client.select_commands.size() == 1)
	for _frame in 120:
		if host._map_active and guest._map_active:
			break
		await process_frame
	assert(host._map_active and guest._map_active,
		"Committed character choices did not advance to the original map picker")
	assert(not host._dialog.visible and not guest._dialog.visible and host._map_adapter.visible and guest._map_adapter.visible,
		"The original map picker did not replace the room dialog after character confirmation")
	assert(not host._can_ready_current_room() and not guest._can_ready_current_room(),
		"Ready became available before map configuration and its peer handshake")
	guest._map_adapter.call("tick_local", {"back": true})
	for _frame in 12:
		if not host._map_active and not guest._map_active:
			break
		await process_frame
	assert(not host._map_active and not guest._map_active
		and host._dialog.visible and guest._dialog.visible,
		"Guest cancellation of the automatic map picker did not return both players to the room")
	var reselect_state: Dictionary = selection_server.state.duplicate(true)
	var reselect_members: Array = reselect_state.members
	for member in reselect_members:
		member["ready"] = true
	selection_server.state = reselect_state
	selection_server.publish_state_before_reply(0)
	host.call("_start_host_selection_session")
	for _frame in 4:
		await process_frame
	assert(host._selection_active and guest._selection_active,
		"Ready players could not reopen the selector")
	selection_server.hold_owner_refresh = true
	_confirm_local_selection(guest._selection_adapter)
	await _wait_selection_delay(guest._selection_adapter)
	_confirm_local_selection(host._selection_adapter)
	await _wait_selection_delay(host._selection_adapter)
	_confirm_local_selection(guest._selection_adapter)
	await _wait_selection_delay(guest._selection_adapter)
	_confirm_local_selection(host._selection_adapter)
	await _wait_for_refresh_slot(selection_server, 0)
	assert(host._busy and host._selection_commit_busy,
		"Same-choice reselect did not hold the commit busy state while refreshing")
	assert(bool(_member_at(selection_server.state, 0).get("ready", false))
		and bool(_member_at(selection_server.state, 1).get("ready", false)),
		"The reselect fixture no longer represents two previously ready players")
	var host_operation_count := host_room_client.operations.size()
	host._on_ready_pressed()
	host._on_start_pressed()
	host._on_commit_setup_pressed()
	host._submit_operation({"type": "prepare", "revision": int(selection_server.state.setupRevision)})
	await process_frame
	assert(host_room_client.operations.size() == host_operation_count,
		"A ready/start/configure request escaped during same-role reselect commit")
	selection_server.release_http_reply(0)
	selection_server.owner_refresh_released.emit()
	for _frame in 120:
		if not host._selection_active and not guest._selection_active \
			and host._map_active and guest._map_active:
			break
		await process_frame
	assert(not host._selection_active and not guest._selection_active,
		"Previously ready same-role reselection did not return both players to room")
	assert(host._map_active and guest._map_active,
		"Same-choice reselect did not return to the map picker after role confirmation")
	assert(selection_server.command_order == [0, 1],
		"Same-role reselection unexpectedly sent a select mutation")
	assert(bool(_member_at(selection_server.state, 0).get("ready", false))
		and bool(_member_at(selection_server.state, 1).get("ready", false)),
		"Same-role reselection unexpectedly cleared both ready states")
	guest._map_adapter.call("tick_local", {"back": true})
	for _frame in 12:
		if not host._map_active and not guest._map_active:
			break
		await process_frame
	assert(not host._map_active and not guest._map_active
		and host._dialog.visible and guest._dialog.visible,
		"Guest cancellation after reselect did not restore the room")

	assert(not host_game.is_physics_processing() and not guest_game.is_physics_processing(),
		"Selection start did not pause Main physics")
	assert(not host._selection_previous_root_physics and not guest._selection_previous_root_physics,
		"Selection start did not preserve the paused room-view physics state")
	guest_view.repeats[guest_view.local_slot] = int(guest_view.spec.repeat_frames) - 1
	guest_view.tick_local({"back": true})
	for _frame in 4:
		await process_frame
	assert(not host._selection_active and not guest._selection_active,
		"A local cancel did not end the selection for both seats")
	assert(not host_game.is_physics_processing(), "Selection cancel changed host Main physics under the room modal")
	assert(not guest_game.is_physics_processing(), "Selection cancel changed guest Main physics under the room modal")
	assert(host._dialog.visible and guest._dialog.visible and host._veil.visible and guest._veil.visible,
		"Selection cancel did not restore the room UI for both seats")
	assert(not host_view.visible and not guest_view.visible,
		"Cancelled selectors remained visible over the room")

	host.call("_start_host_selection_session")
	for _frame in 4:
		await process_frame
	assert(host._selection_active and guest._selection_active,
		"Host could not reopen selection after both sides cancelled")
	assert(host._selection_session_id != first_selection_session,
		"Re-entry reused the previous selection session ID")
	assert(not host_game.is_physics_processing() and not guest_game.is_physics_processing(),
		"Selector reentry did not pause Main physics again")
	host.call("_end_selection_session", false)
	assert(not host_game.is_physics_processing(), "First selection end changed the paused room Main state")
	host.call("_end_selection_session", false)
	assert(not host_game.is_physics_processing(), "Repeated selection end changed the paused room Main state")
	guest.call("_end_selection_session", false)
	assert(not host_game.is_physics_processing() and not guest_game.is_physics_processing(),
		"Final selection teardown changed the paused room-view physics state")
	assert(not host_view.visible and not guest_view.visible)
	host_game.set_physics_process(true)
	assert(bool(host.call("_begin_selection_session", "selection-restore-enabled-main", [host_choice, guest_choice])),
		"Selector could not begin from an explicitly running Main state")
	assert(not host_game.is_physics_processing() and host._selection_previous_root_physics,
		"Selector did not capture a running Main state")
	host.call("_end_selection_session", false)
	assert(host_game.is_physics_processing(), "Selector teardown failed to restore an initially running Main")
	host.call("_end_selection_session", false)
	assert(host_game.is_physics_processing(), "Repeated inactive teardown changed the restored Main state")
	host._show_room()
	assert(not host_game.is_physics_processing(), "Room view failed to pause Main after selector teardown")
	assert(bool(host.call("_begin_selection_session", "selection-busy-restore", [host_choice, guest_choice])))
	host.call("_begin_selection_commit")
	assert(host._busy and host._selection_commit_busy, "Selection commit did not lock Lobby operations")
	host.call("_end_selection_session", false)
	assert(not host._busy and not host._selection_commit_busy,
		"Selection teardown did not restore the Lobby's prior busy state")
	host._delay_choice.select(0)
	host._on_profile_picker_changed(0)
	assert(host._room_connection == null and not host._room_connection_ready,
		"A connection-profile change retained the stale peer connection")
	assert(host._connect_selection_button.visible,
		"A profile change did not expose the reconnect path")
	print("ONLINE_LOBBY_SELECTION_INTEGRATION_SMOKE_OK two_lobbies=true original_view=true one_local_slot=true peer_snapshot=true refresh_preserves_draft=true dropdowns_absent=true select_order=true push_before_http_reply=true commits_acknowledged=true map_follows_roles=true ready_gated_until_map=true same_choice_reselect=true ready_start_gated=true busy_restored=true profile_change_disconnect=true room_hidden=true cancel_both=true inactive_end_idempotent=true physics_end_idempotent=true reentry=true")
	for lobby in [host, guest]:
		lobby.queue_free()
	for node in [host_game, guest_game, host_connection, guest_connection]:
		node.queue_free()
	await process_frame
	quit(0)


func _room_state(host_choice: Dictionary, guest_choice: Dictionary, stage_id: String) -> Dictionary:
	return {
		"id": "fake-selection-room",
		"phase": "lobby",
		"revision": 1,
		"setupRevision": 1,
		"members": [
			{"nickname": "房主", "choice": host_choice, "ready": false, "profile": null},
			{"nickname": "客人", "choice": guest_choice, "ready": false, "profile": null},
		],
		"stage": stage_id,
		"rules": {"time": 90, "life": 1},
		"networkProfile": {"id": "chrome-exp-d1-p2-lan", "inputDelay": 1, "predictionWindow": 2},
		"match": null,
		"lastResult": null,
		"negotiation": null,
	}


func _install_fake_room_client(
	lobby: OnlineLobby, server: FakeSelectionRoomServer, slot: int
) -> FakeSelectionRoomClient:
	var previous: OnlineRoomClient = lobby.room_client
	if previous != null and previous.state_changed.is_connected(lobby._on_room_state_changed):
		previous.state_changed.disconnect(lobby._on_room_state_changed)
	if previous != null:
		previous.queue_free()
	var client := FakeSelectionRoomClient.new()
	client.server = server
	client.slot = slot
	client.state_changed.connect(lobby._on_room_state_changed)
	lobby.add_child(client)
	lobby.room_client = client
	server.clients.append(client)
	return client


func _confirm_local_selection(view: OnlineCharacterSelectionAdapter) -> void:
	view.repeats[view.local_slot] = int(view.spec.repeat_frames) - 1
	view.tick_local({"confirm": true})


func _wait_selection_delay(view: OnlineCharacterSelectionAdapter) -> void:
	await create_timer(float(view.spec.confirm_delay_ms) / 1000.0 + 0.08).timeout
	await process_frame


func _wait_for_waiting_slot(server: FakeSelectionRoomServer, slot: int) -> void:
	for _frame in 120:
		if server.waiting_slots.has(slot):
			return
		await process_frame
	assert(server.waiting_slots.has(slot), "Select HTTP response did not reach the controllable wait point")


func _wait_for_refresh_slot(server: FakeSelectionRoomServer, slot: int) -> void:
	for _frame in 120:
		if server.refresh_waiting_slots.has(slot):
			return
		await process_frame
	assert(server.refresh_waiting_slots.has(slot), "Room refresh did not reach the controllable wait point")


func _member_at(state: Dictionary, slot: int) -> Dictionary:
	var members: Array = state.get("members", [])
	if slot < 0 or slot >= members.size() or not members[slot] is Dictionary:
		return {}
	return members[slot]


func _member_choice(state: Dictionary, slot: int) -> Dictionary:
	var members: Array = state.get("members", [])
	if slot < 0 or slot >= members.size() or not members[slot] is Dictionary:
		return {}
	var member: Dictionary = members[slot]
	return member.get("choice", {}) if member.get("choice") is Dictionary else {}
