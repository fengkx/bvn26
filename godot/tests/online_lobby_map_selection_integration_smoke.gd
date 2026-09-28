extends SceneTree

const Lobby := preload("res://online_lobby.gd")
const RoomClient := preload("res://online_room_client.gd")


class FakeGame extends Control:
	class FakeSession extends RefCounted:
		func menu_held() -> Dictionary:
			return {}

	var session := FakeSession.new()
	var title_menu: TitleMenu


class FakeRoomConnection extends Node:
	var remote_lobby: Node
	var sent_messages: Array[Dictionary] = []
	var next_sequence := 0
	var connection_state := "connected"

	func send_peer_message(message_type: String, payload: Variant) -> bool:
		if connection_state != "connected" or remote_lobby == null:
			return false
		next_sequence += 1
		var copied: Variant = payload.duplicate(true) if payload is Dictionary else payload
		sent_messages.append({"type": message_type, "payload": copied})
		remote_lobby.call_deferred("_on_room_connection_message", message_type, copied, next_sequence)
		return true

	func close() -> void:
		connection_state = "closed"

	func get_connection_state() -> String:
		return connection_state


class FakeMapServer extends RefCounted:
	signal network_configure_pushed(slot: int, state: Dictionary)
	signal network_configure_response_released
	var state: Dictionary = {}
	var clients: Array = []
	var command_types: Array[String] = []
	var operations: Array[Dictionary] = []
	var configure_requests: Array[Dictionary] = []
	var configure_network_requests: Array[Dictionary] = []
	var refresh_failures: Dictionary = {}
	var prepare_count := 0
	var reject_prepare := true
	var push_before_command_reply := true
	var hold_next_network_response := false
	var network_response_held := false

	func wire_copy(value: Variant) -> Variant:
		var encoded := JSON.stringify(value)
		var decoded: Variant = JSON.parse_string(encoded)
		assert(decoded != null or value == null, "Fake service JSON round-trip failed")
		return decoded

	func wire_state() -> Dictionary:
		return wire_copy(state)

	func publish_state() -> void:
		var projected_state := wire_state()
		for client_value in clients:
			var client := client_value as FakeMapRoomClient
			client._room_state = projected_state.duplicate(true)
			client.state_changed.emit(projected_state.duplicate(true))

	func refresh_state(slot: int) -> Dictionary:
		var failures := int(refresh_failures.get(slot, 0))
		if failures > 0:
			refresh_failures[slot] = failures - 1
			return {"error": "fixture_refresh_failed"}
		return {"state": wire_state()}

	func command(slot: int, operation: Dictionary) -> Dictionary:
		var operation_type := str(operation.get("type", ""))
		command_types.append(operation_type)
		operations.append(operation.duplicate(true))
		match operation_type:
			"configure_network":
				configure_network_requests.append(operation.duplicate(true))
				if slot != 0:
					return {"error": "owner_only"}
				if int(operation.get("revision", -1)) != int(state.get("setupRevision", -2)):
					return {"error": "stale_setup_revision"}
				var requested_profile: Dictionary = operation.get("profile", {})
				if not _valid_network_profile(requested_profile):
					return {"error": "network_profile_invalid"}
				var canonical_profile := wire_copy(requested_profile) as Dictionary
				var hold_response := hold_next_network_response
				hold_next_network_response = false
				if hold_response:
					network_response_held = true
				if not _same_network_profile(canonical_profile, state.get("networkProfile", {})):
					state["networkProfile"] = canonical_profile
					state["setupRevision"] = int(state.get("setupRevision", 0)) + 1
					state["revision"] = int(state.get("revision", 0)) + 1
					_clear_ready_profiles_and_negotiation()
					if push_before_command_reply:
						publish_state()
						network_configure_pushed.emit(slot, wire_state())
				if hold_response:
					await network_configure_response_released
					network_response_held = false
				return {"state": wire_state(), "acceptedSeq": command_types.size()}
			"configure":
				configure_requests.append(operation.duplicate(true))
				state["stage"] = str(operation.get("stage", ""))
				var requested_rules: Dictionary = operation.get("rules", {})
				state["rules"] = {
					"time": float(requested_rules.get("time", 0)),
					"life": float(requested_rules.get("life", 0)),
				}
				state["setupRevision"] = int(state.get("setupRevision", 0)) + 1
				state["revision"] = int(state.get("revision", 0)) + 1
				var members: Array = state.get("members", []).duplicate(true)
				for index in members.size():
					var member: Dictionary = members[index].duplicate(true)
					member["ready"] = false
					member["profile"] = null
					members[index] = member
				state["members"] = members
				publish_state()
				return {"state": wire_state(), "acceptedSeq": command_types.size()}
			"ready":
				var ready_profile: Dictionary = operation.get("profile", {})
				if bool(operation.get("ready", false)) \
					and not _same_network_profile(ready_profile, state.get("networkProfile", {})):
					return {"error": "network_profile_mismatch"}
				var members: Array = state.get("members", []).duplicate(true)
				var member: Dictionary = members[slot].duplicate(true)
				var ready := bool(operation.get("ready", false))
				member["ready"] = ready
				member["profile"] = ready_profile.duplicate(true) if ready else null
				members[slot] = member
				state["members"] = members
				state["revision"] = int(state.get("revision", 0)) + 1
				publish_state()
				return {"state": wire_state(), "acceptedSeq": command_types.size()}
			"prepare":
				prepare_count += 1
				if reject_prepare:
					return {"error": "fixture_prepare_rejected"}
				state["phase"] = "preparing"
				state["match"] = {"epoch": "fixture-map-epoch"}
				state["revision"] = int(state.get("revision", 0)) + 1
				publish_state()
				return {"state": wire_state(), "acceptedSeq": command_types.size()}
			_:
				return {"error": "unexpected_operation"}

	func _valid_network_profile(profile: Dictionary) -> bool:
		if profile.size() != 3:
			return false
		var delay_value: Variant = profile.get("inputDelay")
		var prediction_value: Variant = profile.get("predictionWindow")
		if typeof(delay_value) not in [TYPE_INT, TYPE_FLOAT] \
			or typeof(prediction_value) not in [TYPE_INT, TYPE_FLOAT]:
			return false
		var delay := int(delay_value)
		var prediction := int(prediction_value)
		if float(delay_value) != float(delay) or float(prediction_value) != float(prediction) \
			or delay < 0 or delay > 8 or prediction < 0 or prediction > 15:
			return false
		var suffix := "-lan" if str(profile.get("id", "")).ends_with("-lan") else ""
		return str(profile.get("id", "")) == "chrome-exp-d%d-p%d%s" % [delay, prediction, suffix]

	func _same_network_profile(left: Variant, right: Variant) -> bool:
		var left_canonical := _canonical_network_profile(left)
		var right_canonical := _canonical_network_profile(right)
		return not left_canonical.is_empty() and left_canonical == right_canonical

	func _canonical_network_profile(value: Variant) -> Dictionary:
		if not value is Dictionary or not _valid_network_profile(value):
			return {}
		var profile: Dictionary = value
		return {
			"id": str(profile.get("id", "")),
			"inputDelay": int(profile.get("inputDelay", -1)),
			"predictionWindow": int(profile.get("predictionWindow", -1)),
		}

	func _clear_ready_profiles_and_negotiation() -> void:
		var members: Array = state.get("members", []).duplicate(true)
		for index in members.size():
			if not members[index] is Dictionary:
				continue
			var member: Dictionary = members[index].duplicate(true)
			member["ready"] = false
			member["profile"] = null
			members[index] = member
		state["members"] = members
		state["negotiation"] = null


class FakeMapRoomClient extends RoomClient:
	var server: FakeMapServer
	var slot := -1
	var request_log: Array[Dictionary] = []
	var next_sequence := 0
	var pending_sequence := -1
	var pending_body: Dictionary = {}
	var uncertain_configure_network_once := false
	var command_in_flight := false

	func refresh_state() -> Dictionary:
		var result: Dictionary = server.refresh_state(slot)
		if result.get("state") is Dictionary:
			result["state"] = server.wire_state()
		return result

	func command(operation: Dictionary) -> Dictionary:
		if pending_sequence >= 0:
			return {"error": "command_outcome_uncertain", "uncertain": true}
		next_sequence += 1
		var request := {"seq": next_sequence, "body": operation.duplicate(true)}
		request_log.append(request.duplicate(true))
		if str(operation.get("type", "")) == "configure_network" and uncertain_configure_network_once:
			uncertain_configure_network_once = false
			pending_sequence = next_sequence
			pending_body = operation.duplicate(true)
			return {"error": "fixture_response_lost", "uncertain": true}
		command_in_flight = true
		var result: Dictionary = await server.command(slot, operation)
		command_in_flight = false
		return result

	func retry_pending_command() -> Dictionary:
		if pending_sequence < 0:
			return {"error": "no_pending_command"}
		var request := {"seq": pending_sequence, "body": pending_body.duplicate(true)}
		request_log.append(request.duplicate(true))
		command_in_flight = true
		var result: Dictionary = await server.command(slot, pending_body.duplicate(true))
		command_in_flight = false
		if not result.has("error"):
			pending_sequence = -1
			pending_body.clear()
		return result

	func get_room_state() -> Dictionary:
		return server.wire_state()

	func has_uncertain_command() -> bool:
		return pending_sequence >= 0

	func is_command_in_flight() -> bool:
		return command_in_flight


func _initialize() -> void:
	create_timer(20.0).timeout.connect(func() -> void: quit(1))
	call_deferred("_run")


func _run() -> void:
	var host_game := _new_game()
	var guest_game := _new_game()
	var host := await _new_lobby(host_game, 0)
	var guest := await _new_lobby(guest_game, 1)
	var host_choice := {"fighter": host._fighter_ids[0], "helper": host._helper_ids[0]}
	var guest_choice := {"fighter": guest._fighter_ids[0], "helper": guest._helper_ids[0]}
	var server := FakeMapServer.new()
	server.state = _room_state(host_choice, guest_choice, host._stage_ids[0])
	var default_network_profile := {
		"id": "chrome-exp-d2-p6", "inputDelay": 2, "predictionWindow": 6,
	}
	server.state.negotiation = {"id": "old-profile-negotiation"}
	for member_value in server.state.members:
		member_value.ready = true
		member_value.profile = default_network_profile.duplicate(true)
	var host_client := _install_client(host, server, 0)
	var guest_client := _install_client(guest, server, 1)
	var host_connection := FakeRoomConnection.new()
	var guest_connection := FakeRoomConnection.new()
	root.add_child(host_connection)
	root.add_child(guest_connection)
	host_connection.remote_lobby = guest
	guest_connection.remote_lobby = host
	for pair in [[host, host_connection], [guest, guest_connection]]:
		pair[0]._room_connection = pair[1]
		pair[0]._room_connection_ready = true
		pair[0]._select_number(pair[0]._delay_choice, 2)
		pair[0]._select_number(pair[0]._prediction_choice, 6)
		pair[0]._local_connection_profile_id = "chrome-exp-d2-p6"
		pair[0]._remote_connection_profile_id = "chrome-exp-d2-p6"
		pair[0]._room_id = "fixture-room"
		pair[0]._slot = 0 if pair[0] == host else 1
		pair[0]._accept_state(server.state.duplicate(true))
		pair[0]._show_room()
		assert(str(pair[0]._current_connection_profile_id()) == pair[0]._local_connection_profile_id,
			"The lobby's current network selection differs from its room authority")
		assert(pair[0]._selected_number(pair[0]._delay_choice) == 2
			and pair[0]._selected_number(pair[0]._prediction_choice) == 6,
			"The original d2/p6 network defaults changed")
	server.clients = [host_client, guest_client]

	# Owner changes are committed immediately. The fake service pushes its
	# canonical state before the matching HTTP response is allowed to return.
	host._select_number(host._time_choice, 60)
	host._select_number(host._life_choice, 2)
	host._on_setup_picker_changed(0)
	assert(host._dirty and host._rules_draft == {"time": 60, "life": 2},
		"The host rules draft was not established before changing network settings")
	server.hold_next_network_response = true
	host._select_number(host._delay_choice, 0)
	host.call_deferred("_on_profile_picker_changed", 0)
	var pushed: Array = await server.network_configure_pushed
	assert(server.network_response_held, "configure_network reply was not held after the room push")
	assert(pushed[0] == 0 and server._same_network_profile(pushed[1].networkProfile, {
		"id": "chrome-exp-d0-p6", "inputDelay": 0, "predictionWindow": 6,
	}), "Host profile change did not commit the selected d0/p6 value")
	assert(server._same_network_profile(
		{"id": "chrome-exp-d2-p6", "inputDelay": 2.0, "predictionWindow": 6.0},
		{"id": "chrome-exp-d2-p6", "inputDelay": 2, "predictionWindow": 6}
	), "Integral JSON profile numbers were not compared by their room values")
	assert(not server._same_network_profile(
		{"id": "chrome-exp-d2-p6", "inputDelay": 2.5, "predictionWindow": 6.0},
		{"id": "chrome-exp-d2-p6", "inputDelay": 2, "predictionWindow": 6}
	), "Fractional JSON profile values were accepted as canonical")
	for _frame in 2:
		await process_frame
	assert(server._same_network_profile(guest._room_state.networkProfile, pushed[1].networkProfile),
		"Guest did not adopt the authoritative profile before the host HTTP response")
	assert(guest._selected_number(guest._delay_choice) == 0
		and guest._selected_number(guest._prediction_choice) == 6,
		"Guest controls did not immediately mirror the room's d0/p6 profile")
	assert(not guest._owner_settings.visible,
		"Guest can edit or see the owner's advanced settings")
	assert(host._busy and host._delay_choice.disabled,
		"Owner controls stayed editable while configure_network was in flight")
	assert(not host._room_connection_ready and not guest._room_connection_ready
		and host._room_connection == null and guest._room_connection == null,
		"Changing network settings kept a connection negotiated for the old profile")
	assert(server.state.members[0].profile == null and server.state.members[1].profile == null
		and not server.state.members[0].ready and not server.state.members[1].ready
		and server.state.negotiation == null,
		"Network change did not clear both ready/profile fields and negotiation")
	server.network_configure_response_released.emit()
	for _frame in 30:
		if not host._busy:
			break
		await process_frame
	assert(not host._busy, "Owner did not settle profile update after the HTTP response")
	assert(server._same_network_profile(host._room_state.networkProfile, pushed[1].networkProfile),
		"An older HTTP reply replaced the authoritative state push")
	assert(host._dirty and host._rules_draft == {"time": 60, "life": 2}
		and host._selected_number(host._time_choice) == 60
		and host._selected_number(host._life_choice) == 2,
		"Host network-profile response erased the pending time/life draft")

	# Guest handlers are read-only. A lost owner response retains one exact
	# configure_network request and cannot enable the connection on draft state.
	var guest_request_count := server.configure_network_requests.size()
	guest._select_number(guest._delay_choice, 2)
	await guest._on_profile_picker_changed(2)
	guest._lan_candidate_opt_in.set_pressed_no_signal(true)
	await guest._on_profile_option_toggled(true)
	assert(server.configure_network_requests.size() == guest_request_count
		and server._same_network_profile(guest._room_state.networkProfile, pushed[1].networkProfile)
		and guest._selected_number(guest._delay_choice) == 0
		and not guest._lan_candidate_opt_in.button_pressed,
		"Guest settings handler changed the authoritative room network profile")
	host._lan_candidate_opt_in.set_pressed_no_signal(true)
	host_client.uncertain_configure_network_once = true
	await host._on_profile_option_toggled(true)
	assert(host_client.has_uncertain_command() and host._retry_button.visible,
		"Uncertain configure_network response was not retained for retry")
	assert(host._connect_selection_button.disabled,
		"Connection was enabled before an uncertain network profile update settled")
	var original_configure_request: Dictionary = host_client.request_log.back().duplicate(true)
	await host._on_retry_signaling_pressed()
	assert(not host_client.has_uncertain_command(), "Exact retry did not settle configure_network")
	assert(host_client.request_log.size() >= 3
		and host_client.request_log.back() == original_configure_request,
		"configure_network retry changed its sequence or operation body")
	var committed_network_profile: Dictionary = {
		"id": "chrome-exp-d0-p6-lan", "inputDelay": 0, "predictionWindow": 6,
	}
	assert(server._same_network_profile(server.state.networkProfile, committed_network_profile),
		"LAN choice did not become the room's canonical network profile")
	assert(server._same_network_profile(guest._room_state.networkProfile, committed_network_profile),
		"Guest did not adopt the retried LAN profile")
	assert(host._dirty and host._rules_draft == {"time": 60, "life": 2}
		and host._selected_number(host._time_choice) == 60
		and host._selected_number(host._life_choice) == 2,
		"Exact network-profile retry erased the pending time/life draft")
	assert(server.configure_network_requests.size() == 2,
		"The lost response was applied twice or its retry never reached the service")
	for lobby in [host, guest]:
		lobby._select_number(lobby._delay_choice, 0)
		lobby._select_number(lobby._prediction_choice, 6)
		lobby._local_connection_profile_id = "chrome-exp-d0-p6-lan"
		lobby._remote_connection_profile_id = "chrome-exp-d0-p6-lan"
		lobby._room_connection_ready = true
	var host_connection_after_change := FakeRoomConnection.new()
	var guest_connection_after_change := FakeRoomConnection.new()
	root.add_child(host_connection_after_change)
	root.add_child(guest_connection_after_change)
	host_connection_after_change.remote_lobby = guest
	guest_connection_after_change.remote_lobby = host
	host._room_connection = host_connection_after_change
	guest._room_connection = guest_connection_after_change
	var map_baseline_network_profile: Dictionary = server.state.networkProfile.duplicate(true)

	# Host-only map controls retain the current draft and mirror it to the guest.
	host._select_number(host._time_choice, 60)
	host._select_number(host._life_choice, 2)
	host._on_setup_picker_changed(0)
	host._start_host_map_selection()
	for _frame in 4:
		await process_frame
	assert(host._map_active and guest._map_active, "Host map_open did not create both map views")
	var initial_stage := str(server.state.stage)
	host._map_adapter.call("tick_local", {"down": true})
	await process_frame
	assert(str(host._map_adapter.call("selected_stage")) != initial_stage,
		"Host's source map picker did not move to a different map")
	assert(guest._map_adapter.call("selected_stage") == host._map_adapter.call("selected_stage"),
		"Guest did not mirror the host's map snapshot")
	var host_stage := str(host._map_adapter.call("selected_stage"))
	guest._map_adapter.call("tick_local", {"up": true, "down": true, "confirm": true})
	await process_frame
	assert(guest._map_adapter.call("selected_stage") == host_stage,
		"Guest local directions or confirmation changed the map")
	assert(not host._can_ready_current_room() and not guest._can_ready_current_room(),
		"Ready became available before the map service handshake")
	var operations_before_cancel := server.command_types.size()
	host._on_ready_pressed()
	await process_frame
	assert(server.command_types.size() == operations_before_cancel,
		"A ready or prepare operation escaped while map selection was active")
	var cancelled_map_session := host._map_session_id
	guest._map_adapter.call("tick_local", {"back": true})
	for _frame in 12:
		if not host._map_active and not guest._map_active:
			break
		await process_frame
	assert(not host._map_active and not guest._map_active,
		"Guest map-cancel request did not return both players to the room")
	assert(host._dialog.visible and guest._dialog.visible and host._veil.visible and guest._veil.visible,
		"Map cancellation did not restore both room views")
	assert(host._dirty and host._rules_draft == {"time": 60, "life": 2},
		"Cancelling map selection discarded the host's unapplied rules draft")
	host._on_commit_setup_pressed()
	for _frame in 4:
		await process_frame
	assert(host._map_active and guest._map_active and host._map_session_id != cancelled_map_session,
		"Host could not start a fresh map-selection session after cancellation")
	assert(guest._map_pending_snapshot.sessionId == host._map_session_id,
		"Guest did not retain the initial revision-zero map snapshot for commit validation")
	initial_stage = str(server.state.stage)
	host._map_adapter.call("tick_local", {"down": true})
	await process_frame
	assert(str(host._map_adapter.call("selected_stage")) != initial_stage,
		"Host's source map picker did not move on the re-entered session")
	host_stage = str(host._map_adapter.call("selected_stage"))
	assert(guest._map_adapter.call("selected_stage") == host_stage,
		"Guest did not mirror the re-entered map session")
	server.refresh_failures[0] = 1
	for _frame in 5:
		host._map_adapter.call("tick_local", {"confirm": true})
	await create_timer(0.58).timeout
	for _frame in 180:
		if not host._map_active and not guest._map_active:
			break
		await process_frame
	assert(not host._map_active and not guest._map_active,
		"A failed host refresh left either player stuck in the map picker")
	assert(host._dialog.visible and guest._dialog.visible and host._veil.visible and guest._veil.visible,
		"A failed host refresh did not return both clients to the room")
	assert(server.configure_requests.is_empty(),
		"Configure was submitted despite a failed host preflight refresh")
	assert(host._dirty and host._rules_draft == {"time": 60, "life": 2},
		"A failed host refresh discarded the unapplied owner rules")
	assert(host._setup_button.visible and not host._setup_button.disabled,
		"The host could not retry map selection after a refresh failure")

	# Re-enter after the failed refresh. The guest's first commit refresh fails,
	# leaving an explicit retry path; the same commit then completes without a
	# second configure mutation.
	host._on_commit_setup_pressed()
	for _frame in 4:
		await process_frame
	assert(host._map_active and guest._map_active)
	initial_stage = str(server.state.stage)
	host._map_adapter.call("tick_local", {"down": true})
	await process_frame
	host_stage = str(host._map_adapter.call("selected_stage"))
	assert(host_stage != initial_stage and guest._map_adapter.call("selected_stage") == host_stage)
	server.refresh_failures[1] = 1
	for _frame in 5:
		host._map_adapter.call("tick_local", {"confirm": true})
	await create_timer(0.58).timeout
	for _frame in 180:
		if guest._map_ack_pending:
			break
		await process_frame
	assert(guest._map_ack_pending and guest._retry_button.visible,
		"A failed guest verification refresh did not retain its retry action")
	assert(guest._map_active and guest._dialog.visible,
		"Guest lost its pending map commit during a verification refresh failure")
	await guest._on_retry_signaling_pressed()
	for _frame in 180:
		if not host._map_active and not guest._map_active:
			break
		await process_frame
	assert(not host._map_active and not guest._map_active,
		"The configure / map_ack / map_done handshake did not return both players to the room")
	assert(server.state.stage == host_stage, "The selected map was not committed to service state")
	assert(server._same_network_profile(server.state.networkProfile, map_baseline_network_profile),
		"Map configuration overwrote the room's network profile")
	assert(typeof(server.state.rules.time) == TYPE_FLOAT and typeof(server.state.rules.life) == TYPE_FLOAT,
		"The fake service did not preserve the JSON number representation for room rules")
	assert(host._same_rules(server.state.rules, {"time": 60, "life": 2}),
		"The room applied stale map rules instead of the host's current draft")
	assert(host._same_rules({"time": 90.0, "life": 2.0}, {"time": 90, "life": 2}),
		"Integral JSON float rules were not compared by their room values")
	assert(not host._same_rules({"time": 90.5, "life": 2.0}, {"time": 90, "life": 2}),
		"Fractional JSON rule values were accepted as valid room rules")
	assert(server.configure_requests.size() == 1,
		"Guest retry unexpectedly submitted configure again")
	assert(host._map_handshake_complete and guest._map_handshake_complete,
		"The two clients did not record the same completed map handshake")
	assert(host._map_handshake_setup_revision == guest._map_handshake_setup_revision
		and host._map_handshake_stage_id == guest._map_handshake_stage_id,
		"Map completion disagreed across clients")
	for member in server.state.members:
		assert(not member.ready and member.profile == null,
			"Configure did not clear previous ready/profile fields as the service does")
	assert(host._can_ready_current_room() and guest._can_ready_current_room(),
		"Null profiles left both players unable to ready after map configuration")
	assert(not host._connect_selection_button.disabled and not guest._connect_selection_button.disabled,
		"Ready UI remained disabled after a confirmed map selection")

	# One ready player must not start. The second matching ready profile enables exactly one host prepare.
	await host._on_ready_pressed()
	for _frame in 4:
		await process_frame
	assert(server.prepare_count == 0, "Host started before the guest was ready")
	await guest._on_ready_pressed()
	for _frame in 120:
		if server.prepare_count > 0:
			break
		await process_frame
	assert(server.prepare_count == 1, "Both ready matching profiles did not trigger a single host auto-prepare")
	assert(server.command_types.count("prepare") == 1)
	assert(server.state.phase == "lobby", "The rejecting fake prepare unexpectedly changed room phase")
	assert(host._prepare_retry_available, "A rejected auto-prepare did not expose its retry state")
	for _push in 3:
		host._accept_state(server.state.duplicate(true))
	for _frame in 6:
		await process_frame
	assert(server.prepare_count == 1,
		"Repeated qualifying room-state pushes retried an already-rejected prepare automatically")
	await host._retry_auto_prepare()
	for _frame in 120:
		if server.prepare_count == 2:
			break
		await process_frame
	assert(server.prepare_count == 2 and host._prepare_retry_available,
		"Explicit prepare retry did not issue exactly one additional request")

	print("ONLINE_LOBBY_MAP_SELECTION_INTEGRATION_SMOKE_OK network_authority=true guest_read_only=true push_before_http=true profile_change_clears_ready=true uncertain_exact_retry=true map_preserves_profile=true host_authority=true guest_mirror=true map_commit_handshake=true rules_draft=true null_profiles_ready=true auto_prepare_gated=true auto_prepare_deduplicated=true explicit_retry=true cancel_and_reentry=true guest_pending_snapshot=true host_refresh_failure_returns=true guest_refresh_retry=true")
	for lobby in [host, guest]:
		lobby.queue_free()
	for node in [host_game, guest_game, host_connection, guest_connection, host_connection_after_change, guest_connection_after_change]:
		if is_instance_valid(node):
			node.queue_free()
	await process_frame
	quit(0)


func _new_game() -> FakeGame:
	var game := FakeGame.new()
	game.title_menu = TitleMenu.new()
	game.add_child(game.title_menu)
	root.add_child(game)
	game.set_physics_process(true)
	return game


func _new_lobby(game: FakeGame, slot: int) -> Lobby:
	var lobby: OnlineLobby = Lobby.new()
	root.add_child(lobby)
	await process_frame
	lobby.configure(null, game)
	lobby._slot = slot
	lobby._room_id = "fixture-room-%d" % slot
	return lobby


func _install_client(lobby: OnlineLobby, server: FakeMapServer, slot: int) -> FakeMapRoomClient:
	var previous: RoomClient = lobby.room_client
	if previous != null:
		if previous.state_changed.is_connected(lobby._on_room_state_changed):
			previous.state_changed.disconnect(lobby._on_room_state_changed)
		previous.queue_free()
	var client := FakeMapRoomClient.new()
	client.server = server
	client.slot = slot
	client._room_id = "fixture-room-%d" % slot
	client.state_changed.connect(lobby._on_room_state_changed)
	lobby.add_child(client)
	lobby.room_client = client
	server.clients.append(client)
	return client


func _room_state(host_choice: Dictionary, guest_choice: Dictionary, stage_id: String) -> Dictionary:
	return {
		"id": "fixture-room",
		"phase": "lobby",
		"revision": 1,
		"setupRevision": 1,
		"members": [
			{"nickname": "房主", "choice": host_choice, "ready": false, "profile": null},
			{"nickname": "客人", "choice": guest_choice, "ready": false, "profile": null},
		],
		"stage": stage_id,
		"rules": {"time": 90, "life": 1},
		"networkProfile": {"id": "chrome-exp-d2-p6", "inputDelay": 2, "predictionWindow": 6},
		"match": null,
		"lastResult": null,
		"negotiation": null,
	}
