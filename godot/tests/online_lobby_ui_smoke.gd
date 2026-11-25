extends SceneTree

const Lobby := preload("res://online_lobby.gd")
const Surface := preload("res://render_surface.gd")

class FakeSession:
	extends RefCounted
	var root_label := "MENU"

class FakeGame:
	extends Control
	var session := FakeSession.new()
	var title_menu: TitleMenu

class DelayedPrepareRoomClient:
	extends OnlineRoomClient
	signal prepare_started
	signal prepare_response(response: Dictionary)
	var room_state: Dictionary = {}
	var operations: Array[Dictionary] = []
	var credentials_cleared := false

	func command(operation: Dictionary) -> Dictionary:
		operations.append(operation.duplicate(true))
		if str(operation.get("type", "")) != "prepare":
			return {"error": "unexpected_operation"}
		prepare_started.emit()
		var response: Dictionary = await prepare_response
		return response

	func get_room_state() -> Dictionary:
		return room_state.duplicate(true)

	func has_uncertain_command() -> bool:
		return false

	func clear_credentials() -> void:
		credentials_cleared = true

class DelayedCoordinator:
	extends RefCounted
	signal cancel_started
	signal cancel_response(issue: String)
	var close_reason := ""

	func cancel_startup() -> String:
		cancel_started.emit()
		var issue: String = await cancel_response
		return issue

	func close(reason: String = "") -> void:
		close_reason = reason


func _initialize() -> void:
	call_deferred("_run")


func _run() -> void:
	var lobby: OnlineLobby = Lobby.new()
	lobby.preferences_path = OS.get_temp_dir().path_join("online-menu-test-%d.cfg" % Time.get_ticks_usec())
	lobby.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	root.add_child(lobby)
	await process_frame
	lobby.configure(null, null)
	assert(
		lobby._endpoint.text.trim_suffix("/") == "https://bvn26-pvp.fengkx.top",
		"Lobby should default to the production matchmaking endpoint"
	)
	assert(lobby._configure_service(), "Production service URL should configure without making a request")
	lobby._endpoint.text = "http://127.0.0.1:8787"
	assert(lobby._configure_service(), "Local service endpoint override should remain available")
	assert(lobby.room_client._base_url == "http://127.0.0.1:8787")
	lobby._endpoint.text = "   "
	assert(lobby._configure_service() and lobby.room_client._base_url == OnlineLobby.DEFAULT_SERVICE_URL)
	lobby._endpoint.text = OnlineLobby.DEFAULT_SERVICE_URL
	assert(lobby._selected_number(lobby._delay_choice) == 2
		and lobby._selected_number(lobby._prediction_choice) == 6,
		"A new online lobby should default to the 2-frame delay / 6-frame prediction profile")
	assert(not ResourceLoader.has_cached(OnlineUserTextFont.CJK_FALLBACK_PATH))
	lobby._dialog.show()
	await process_frame
	var nickname_font: Font = lobby._nickname.get_theme_font("font")
	assert(nickname_font.has_char(0x9F98), "Nickname LineEdit is missing the supported CJK fallback glyph 龘")
	lobby._dialog.hide()
	assert(lobby._endpoint.placeholder_text == OnlineLobby.DEFAULT_SERVICE_URL)
	assert(not lobby._endpoint.get_parent().visible)
	lobby._home_advanced_toggle.button_pressed = true
	assert(lobby._endpoint.get_parent().visible)
	lobby._home_advanced_toggle.button_pressed = false
	assert(not lobby._endpoint.get_parent().visible)
	var custom_url := "https://pvp.example.org"
	lobby._endpoint.text = custom_url
	lobby._endpoint.text_changed.emit(custom_url)
	lobby._save_profile_value("nickname", "Tester")
	var reopened: OnlineLobby = Lobby.new()
	reopened.preferences_path = lobby.preferences_path
	root.add_child(reopened)
	reopened._dialog.show()
	assert(reopened._endpoint.text == custom_url and reopened._home_advanced_toggle.button_pressed)
	assert(reopened._nickname.text == "Tester")
	reopened._endpoint.text = ""
	reopened._endpoint.text_changed.emit("")
	reopened._dialog.hide()
	reopened._dialog.show()
	assert(reopened._endpoint.text == OnlineLobby.DEFAULT_SERVICE_URL and not reopened._home_advanced_toggle.button_pressed)
	var saved := ConfigFile.new()
	assert(saved.load(lobby.preferences_path) == OK and saved.get_value("profile", "service_url") == OnlineLobby.DEFAULT_SERVICE_URL)
	reopened.free()
	DirAccess.remove_absolute(lobby.preferences_path)
	assert(lobby._lan_candidate_opt_in.text == "本机 / 同一局域网对战（无需中转）")
	assert(lobby._room_visibility_hint.text.contains("两个窗口并排") and lobby._room_visibility_hint.text.contains("保持可见"))
	lobby._startup_busy = true
	lobby._on_page_visibility_changed(false)
	assert(lobby._status.text.contains("本页已在后台") and lobby._status.text.contains("保持可见"))
	lobby._on_page_visibility_changed(true)
	assert(lobby._status.text.contains("正在建立点对点连接"))
	lobby._startup_busy = false
	var parsed_code: Dictionary = lobby._parse_invitation("Calm-Otter-ABCDEFGH")
	assert(parsed_code.get("kind") == "code" and parsed_code.get("code") == "calm-otter-abcdefgh",
		"Short invitation codes should be normalized for the service")
	var parsed_legacy: Dictionary = lobby._parse_invitation("%s.%s" % ["a".repeat(64), "b".repeat(43)])
	assert(parsed_legacy.get("kind") == "legacy", "Legacy roomId.token invitation input stopped working")
	lobby._show_error("ICE lookup failed: turn_not_configured")
	assert(lobby._status.text == "服务未配置互联网中转。若使用本机或同一局域网，请由房主开启对应模式并重新连接；跨网络对战需先配置 TURN 服务。")
	lobby._slot = 0
	lobby._room_id = "a".repeat(64)
	lobby._invite_token = "b".repeat(43)
	lobby._invite_code = "calm-otter-abcdefgh"
	var initial_fighter := lobby._fighter_ids[0]
	var initial_helper := lobby._helper_ids[0]
	var initial_stage := lobby._stage_ids[0]
	var state := {
		"id": lobby._room_id,
		"phase": "lobby",
		"revision": 1,
		"setupRevision": 1,
		"members": [{
			"nickname": "房主",
			"choice": {"fighter": initial_fighter, "helper": initial_helper},
			"ready": false,
			"profile": null,
		}, null],
		"stage": initial_stage,
		"rules": {"time": 90, "life": 1},
		"networkProfile": {"id": "chrome-exp-d2-p6", "inputDelay": 2, "predictionWindow": 6},
		"match": null,
		"lastResult": null,
		"negotiation": null,
	}
	lobby._room_state = state.duplicate(true)
	lobby._show_room()
	assert(lobby._room_code_output.text == "calm-otter-abcdefgh", "Room view exposed long credentials instead of the short code")
	assert(lobby._rotate_invite_button.visible, "Room owner could not rotate an invitation code")

	lobby._select_number(lobby._time_choice, 60)
	lobby._select_number(lobby._life_choice, 2)
	lobby._on_setup_picker_changed(0)
	lobby._accept_state(state.duplicate(true))
	assert(lobby._dirty)
	assert(lobby._selected_number(lobby._time_choice) == 60)
	assert(lobby._selected_number(lobby._life_choice) == 2)
	var visible_stage_label := str(lobby._stage_labels.get(initial_stage, ""))
	assert(not visible_stage_label.is_empty() and not lobby._stage_summary.text.contains(visible_stage_label))
	assert(lobby._stage_summary.text.contains("地图待选择"))
	lobby._map_handshake_complete = true
	lobby._map_handshake_setup_revision = int(state.setupRevision)
	lobby._map_handshake_stage_id = initial_stage
	lobby._show_room()
	assert(lobby._stage_summary.text.contains(visible_stage_label))
	lobby._map_handshake_setup_revision -= 1
	lobby._show_room()
	assert(lobby._stage_summary.text.contains("地图待选择"))
	lobby._map_handshake_complete = false
	var room_options := 0
	for node in lobby._room_view.find_children("*", "OptionButton", true, false):
		room_options += 1
	assert(room_options == 5,
		"Room includes the online mode switch, time/life/network options; map selection uses the original picker")
	assert(lobby._mode_choice.item_count == 2 and lobby._mode_choice.get_item_text(0) == "回滚联机")
	assert(lobby._member_status.text.contains("房主"))
	var dialog := lobby.find_child("OnlineDialog", true, false) as Control
	assert(dialog != null)
	var dialog_rect := dialog.get_global_rect()
	assert(dialog_rect.position.x >= 0 and dialog_rect.position.y >= 0)
	var viewport_size := root.get_visible_rect().size
	if dialog_rect.end.x > viewport_size.x or dialog_rect.end.y > viewport_size.y:
		push_error("Online dialog exceeds viewport: %s > %s" % [dialog_rect, viewport_size])
		quit(1)
		return
	print("ONLINE_LOBBY_UI_SMOKE_OK owner_setup_draft_preserved=true map_picker_not_dropdown=true role_dropdowns_absent=true dialog_fits=true")
	lobby._room_id = ""
	var game := FakeGame.new()
	game.title_menu = TitleMenu.new()
	game.add_child(game.title_menu)
	root.add_child(game)
	await process_frame
	lobby.configure(null, game)
	_open_online_menu(game.title_menu)
	for _frame in 14:
		game.title_menu.apply_held({})
	assert(lobby._dialog.visible and game.has_meta("online_modal_open"))
	var close_button_pressed := [false]
	lobby._home_close_button.pressed.connect(func() -> void: close_button_pressed[0] = true)
	_push_mouse_button(lobby._home_close_button, true)
	await process_frame
	_push_mouse_button(lobby._home_close_button, false)
	await process_frame
	assert(close_button_pressed[0], "Mouse input did not reach the visible close button")
	assert(not lobby._dialog.visible and game.title_menu.controller.anj == 0)
	_open_online_menu(game.title_menu)
	for _frame in 14:
		game.title_menu.apply_held({})
	assert(lobby._dialog.visible, "Online entry could not open the lobby a second time")
	var nickname := lobby._nickname
	nickname.text = "focus test"
	nickname.grab_focus()
	await process_frame
	assert(lobby._focused_online_line_edit() == nickname, "Focused lobby LineEdit was not recognized")
	lobby._on_web_edit_shortcut(["a"])
	assert(nickname.has_selection(), "Command/Control+A bridge did not select the focused lobby text")
	assert(nickname.text == "focus test", "Select-all shortcut inserted a character into the nickname")
	lobby._on_web_paste([])
	var unrelated_edit := LineEdit.new()
	root.add_child(unrelated_edit)
	unrelated_edit.grab_focus()
	await process_frame
	assert(lobby._focused_online_line_edit() == null, "A LineEdit outside the lobby was treated as the online target")
	lobby._on_web_edit_shortcut(["a"])
	assert(not nickname.has_selection(), "Shortcut bridge acted after focus left the lobby")
	assert(nickname.text == "focus test", "Deferred paste followed focus into another control")
	unrelated_edit.queue_free()
	print("ONLINE_LOBBY_SHORTCUT_SMOKE_OK focused_select_all=true focus_isolated=true deferred_paste_focus_bound=true")
	_push_escape(true)
	await process_frame
	assert(not lobby._dialog.visible, "Escape did not close the safe lobby home")
	_push_escape(false)
	await process_frame
	assert(game.title_menu.controller.anj == 0 and game.title_menu.pending_item.is_empty())
	assert(root.gui_get_focus_owner() == null, "Lobby close left a hidden input control focused")
	print("ONLINE_LOBBY_REENTRY_SMOKE_OK open_mouse_close_reopen_escape=true")
	await _test_cancel_startup_during_delayed_prepare(lobby, state, false)
	await _test_cancel_startup_during_delayed_prepare(lobby, state, true)
	lobby.queue_free()
	game.queue_free()
	await process_frame
	await _test_render_surface_input_tree()
	quit(0)


func _test_cancel_startup_during_delayed_prepare(
	lobby: OnlineLobby, lobby_state: Dictionary, abandon_after_failure: bool
) -> void:
	var client := DelayedPrepareRoomClient.new()
	var original_client := lobby.room_client
	var settled_state := lobby_state.duplicate(true)
	settled_state["phase"] = "lobby"
	var map_stage := str(lobby._stage_ids[0])
	settled_state["stage"] = map_stage
	settled_state["setupRevision"] = 1
	var shared_profile := {"id": "chrome-exp-d2-p6", "inputDelay": 2, "predictionWindow": 6}
	var members: Array = settled_state.get("members", []).duplicate(true)
	var owner_member: Dictionary = members[0].duplicate(true)
	owner_member["ready"] = true
	owner_member["profile"] = shared_profile.duplicate(true)
	members[0] = owner_member
	members[1] = {
		"nickname": "客人",
		"choice": {"fighter": lobby._fighter_ids[1], "helper": lobby._helper_ids[1]},
		"ready": true,
		"profile": shared_profile.duplicate(true),
	}
	settled_state["members"] = members
	client.room_state = settled_state.duplicate(true)
	lobby.room_client = client
	lobby._select_number(lobby._delay_choice, int(shared_profile.inputDelay))
	lobby._select_number(lobby._prediction_choice, int(shared_profile.predictionWindow))
	lobby._lan_candidate_opt_in.set_pressed_no_signal(false)
	lobby._room_id = "a".repeat(64)
	lobby._slot = 0
	lobby._room_state = settled_state.duplicate(true)
	lobby._room_connection_ready = true
	lobby._local_connection_profile_id = str(shared_profile.id)
	lobby._remote_connection_profile_id = str(shared_profile.id)
	lobby._dirty = false
	lobby._selection_active = false
	lobby._selection_commit_busy = false
	lobby._map_active = false
	lobby._map_handshake_complete = true
	lobby._map_handshake_setup_revision = 1
	lobby._map_handshake_stage_id = map_stage
	assert(str(lobby._current_connection_profile_id()) == str(shared_profile.id),
		"Delayed-prepare fixture controls must match the already-negotiated room profile")
	lobby._starting_epoch = "delayed-prepare-epoch"
	lobby._startup_busy = true
	lobby._startup_cancel_in_progress = false
	lobby._startup_cancel_requested = false
	lobby._match_started = false
	var fake_coordinator := DelayedCoordinator.new()
	lobby.coordinator = fake_coordinator
	lobby._show_room()
	lobby._process(0.0)
	assert(lobby._startup_cancel_button.visible and not lobby._startup_cancel_button.disabled,
		"A cancellable startup did not expose its dedicated cancel action")
	var prepare_started := [false]
	var cancel_calls := [0]
	var prepare_finished := [false]
	client.prepare_started.connect(func() -> void: prepare_started[0] = true)
	fake_coordinator.cancel_started.connect(func() -> void: cancel_calls[0] += 1)
	call_deferred("_await_delayed_prepare_operation", lobby, prepare_finished)
	for _frame in 10:
		if prepare_started[0]:
			break
		await process_frame
	assert(prepare_started[0], "The delayed prepare request did not start")
	_click_button(lobby._startup_cancel_button)
	for _frame in 10:
		if cancel_calls[0] >= 1:
			break
		await process_frame
	assert(cancel_calls[0] == 1, "Mouse click did not begin safe startup cancellation")
	var preparing_state := settled_state.duplicate(true)
	preparing_state["phase"] = "preparing"
	preparing_state["match"] = {"epoch": "delayed-prepare-epoch"}
	client.prepare_response.emit({"state": preparing_state})
	for _frame in 10:
		if prepare_finished[0]:
			break
		await process_frame
	assert(prepare_finished[0], "Delayed prepare coroutine did not settle")
	assert(str(lobby._room_state.get("phase", "")) == "lobby",
		"A stale prepare response changed the lobby after cancellation began")
	lobby._room_state = preparing_state.duplicate(true)
	client.room_state = preparing_state.duplicate(true)
	fake_coordinator.cancel_response.emit("cancel_outcome_unconfirmed")
	for _frame in 10:
		if not lobby._startup_cancel_in_progress and not lobby._busy:
			break
		await process_frame
	lobby._process(0.0)
	assert(lobby._startup_busy and lobby._starting_epoch == "delayed-prepare-epoch",
		"An unconfirmed cancellation discarded the active startup")
	assert((not lobby._setup_button.visible or lobby._setup_button.disabled)
		and (not lobby._connect_selection_button.visible or lobby._connect_selection_button.disabled)
		and lobby._leave_button.disabled,
		"Room actions unlocked while service startup cancellation was unconfirmed")
	assert(lobby._connect_selection_button.disabled and lobby._startup_cancel_button.visible
		and not lobby._startup_cancel_button.disabled,
		"Unconfirmed startup should keep the explicit cancel retry available")
	if abandon_after_failure:
		assert(lobby._startup_abandon_button.visible and not lobby._startup_abandon_button.disabled,
			"Unconfirmed cancellation did not expose the local abandon action")
		assert(lobby._startup_abandon_button.text == "放弃等待并返回主菜单")
		await _click_button(lobby._startup_abandon_button)
		assert(client.credentials_cleared, "Local abandon did not clear RoomClient credentials")
		assert(fake_coordinator.close_reason == "user_abandoned_unconfirmed_startup",
			"Local abandon did not close the coordinator without claiming service settlement")
		assert(lobby._room_id.is_empty() and lobby._invite_token.is_empty() and lobby._invite_code.is_empty())
		assert(lobby._slot == -1 and not lobby._startup_busy and lobby._starting_epoch.is_empty())
		assert(not lobby._dialog.visible and not lobby._veil.visible,
			"Local abandon did not return to the title menu")
		assert(lobby._status.text.contains("服务端清理未确认") and lobby._status.text.contains("空闲房间在 30 分钟后关闭"),
			"Local abandon status overpromised remote cleanup or idle expiry")
	else:
		assert(lobby._startup_abandon_button.visible and not lobby._startup_abandon_button.disabled,
			"Unconfirmed cancellation did not expose the separate abandon path")
		await _click_button(lobby._startup_cancel_button)
		for _frame in 10:
			if cancel_calls[0] >= 2:
				break
			await process_frame
		assert(cancel_calls[0] == 2, "Cancellation could not be retried after an uncertain result")
		client.room_state = settled_state.duplicate(true)
		fake_coordinator.cancel_response.emit("")
		for _frame in 10:
			if not lobby._startup_busy and lobby._starting_epoch.is_empty():
				break
			await process_frame
		assert(fake_coordinator.close_reason == "startup_cancelled")
		assert(str(lobby._room_state.get("phase", "")) == "lobby")
		assert(not lobby._startup_busy and not lobby._startup_cancel_in_progress and lobby._starting_epoch.is_empty(),
			"Confirmed cancellation did not release startup state")
		assert(lobby._dialog.visible and lobby._room_view.visible and lobby._status.text.contains("开局已取消"),
			"Confirmed cancellation did not return to the room")
		assert(not client.credentials_cleared, "Retry success should preserve room credentials")
	assert(client.operations.size() == 1 and client.operations[0].get("type") == "prepare",
		"Cancellation path sent an unexpected service command from the UI")
	lobby.room_client = original_client
	client.free()
	if abandon_after_failure:
		print("ONLINE_LOBBY_CANCEL_SMOKE_OK mouse_cancel=true delayed_prepare_ignored=true generation_guard=true phase_locked=true retry_success=true local_abandon=true no_remote_leave=true")


func _await_delayed_prepare_operation(lobby: OnlineLobby, finished: Array) -> void:
	await lobby._submit_operation({"type": "prepare", "revision": 1})
	finished[0] = true


func _option_index(option: OptionButton, metadata: String) -> int:
	for index in option.item_count:
		if str(option.get_item_metadata(index)) == metadata:
			return index
	return -1


func _push_mouse_button(control: Control, pressed: bool) -> void:
	var event := InputEventMouseButton.new()
	event.button_index = MOUSE_BUTTON_LEFT
	event.pressed = pressed
	event.position = control.get_global_rect().get_center()
	event.global_position = event.position
	root.push_input(event, true)


func _click_button(control: Control) -> void:
	_push_mouse_button(control, true)
	await process_frame
	_push_mouse_button(control, false)
	await process_frame


func _push_escape(pressed: bool) -> void:
	var event := InputEventKey.new()
	event.keycode = KEY_ESCAPE
	event.physical_keycode = KEY_ESCAPE
	event.pressed = pressed
	root.push_input(event, true)


func _open_online_menu(menu: TitleMenu) -> void:
	_prepare_online_menu(menu)
	menu._online_entry.pressed.emit()


func _prepare_online_menu(menu: TitleMenu) -> void:
	menu.source_frame = 63
	menu._wheel_born = true
	menu.controller.reset()
	menu.controller.select = 6
	menu.controller.positions[6] = 0.0
	menu._refresh()


func _test_render_surface_input_tree() -> void:
	var surface: RenderSurface = Surface.new()
	surface.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	root.add_child(surface)
	await process_frame
	await process_frame
	var game := surface.game
	var lobby := surface.online_lobby
	assert(game != null and lobby != null)
	game.set_physics_process(false)
	_prepare_online_menu(game.title_menu)
	await process_frame
	var entry_rect: Rect2 = game.title_menu._online_entry.get_global_rect()
	assert(entry_rect.size.x > 0 and entry_rect.size.y > 0)
	_push_mouse_button(game.title_menu._online_entry, true)
	await process_frame
	_push_mouse_button(game.title_menu._online_entry, false)
	await process_frame
	assert(game.title_menu.pending_item.get("id") == "online", "Title entry did not receive a real RenderSurface mouse click")
	for _frame in 14:
		game.title_menu.apply_held({})
	assert(lobby._dialog.visible, "Main menu entry did not open OnlineLobby through RenderSurface")
	assert(not game.is_physics_processing(), "Opening the lobby did not pause the source menu")
	await process_frame
	await process_frame
	var close_rect := lobby._home_close_button.get_global_rect()
	assert(close_rect.size.x > 0 and close_rect.size.y > 0 and close_rect.has_point(close_rect.get_center()))
	var pressed := [false]
	lobby._home_close_button.pressed.connect(func() -> void: pressed[0] = true)
	_push_mouse_button(lobby._home_close_button, true)
	await process_frame
	_push_mouse_button(lobby._home_close_button, false)
	await process_frame
	assert(pressed[0] and not lobby._dialog.visible, "SubViewport mouse routing prevented closing through RenderSurface")
	assert(game.is_physics_processing(), "Closing the lobby did not resume the MENU scene")
	assert(game.title_menu.controller.anj == 0 and game.title_menu.pending_item.is_empty())
	assert(not game.has_meta("online_modal_open"))
	await process_frame
	assert(not lobby._dialog.visible and game.title_menu.pending_item.is_empty(),
		"A delayed menu confirmation reopened the lobby after closing")
	game.set_physics_process(false)
	_prepare_online_menu(game.title_menu)
	await process_frame
	_push_mouse_button(game.title_menu._online_entry, true)
	await process_frame
	_push_mouse_button(game.title_menu._online_entry, false)
	await process_frame
	assert(game.title_menu.pending_item.get("id") == "online", "Title entry did not reopen after close")
	for _frame in 14:
		game.title_menu.apply_held({})
	assert(lobby._dialog.visible, "Main menu could not reopen the online home")
	assert(lobby._home_footer.visible, "Home actions must stay outside the scrollable form")
	lobby._set_admission_uncertain(true)
	await process_frame
	assert(lobby._home_close_button.disabled, "Uncertain admission must retain its explicit retry/abandon flow")
	assert(lobby._admission_retry_button.visible and lobby._admission_abandon_button.visible)
	assert(lobby._admission_uncertain_warning.text == "暂时无法确认请求结果。返回将放弃此次请求，已创建的空闲房间最多 30 分钟后关闭。")
	var fixed_footer_rect := lobby._home_footer.get_global_rect()
	var active_dialog_rect := lobby._dialog.get_global_rect()
	assert(fixed_footer_rect.position.y >= active_dialog_rect.position.y)
	assert(fixed_footer_rect.end.y <= active_dialog_rect.end.y, "Uncertain-request actions must remain inside the dialog without scrolling")
	assert(fixed_footer_rect.intersects(lobby._admission_abandon_button.get_global_rect()))
	_push_escape(true)
	await process_frame
	assert(lobby._dialog.visible, "Escape discarded an uncertain room admission")
	_push_escape(false)
	await process_frame
	_push_mouse_button(lobby._admission_abandon_button, true)
	await process_frame
	_push_mouse_button(lobby._admission_abandon_button, false)
	await process_frame
	assert(not lobby._dialog.visible, "Fixed-footer abandon action did not return to the title menu")
	assert(not lobby._admission_uncertain)
	game.set_physics_process(false)
	_prepare_online_menu(game.title_menu)
	await process_frame
	_push_mouse_button(game.title_menu._online_entry, true)
	await process_frame
	_push_mouse_button(game.title_menu._online_entry, false)
	await process_frame
	for _frame in 14:
		game.title_menu.apply_held({})
	assert(lobby._dialog.visible and lobby._home_footer.visible, "Online home could not reopen after abandoning uncertain admission")
	lobby._set_admission_uncertain(false)
	_push_escape(true)
	await process_frame
	assert(not lobby._dialog.visible, "Escape did not close OnlineLobby in the RenderSurface tree")
	_push_escape(false)
	await process_frame
	assert(game.is_physics_processing() and root.gui_get_focus_owner() == null)
	print("ONLINE_LOBBY_RENDER_SURFACE_SMOKE_OK mouse_close=true escape_close=true reentry=true fixed_footer=true abandon=true")
	surface.queue_free()
	await process_frame
