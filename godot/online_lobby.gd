class_name OnlineLobby
extends Control

const DEFAULT_SERVICE_URL := "https://bvn26-pvp.fengkx.top"
const LOBBY_IDLE_MS := 30 * 60 * 1000
const LOBBY_KEEPALIVE_SECONDS := 900.0
const LOBBY_RECONNECT_BASE_SECONDS := 1.0
const LOBBY_RECONNECT_MAX_SECONDS := 30.0
const LOBBY_STATUS_REFRESH_SECONDS := 30.0
const CLIENT := preload("res://online_room_client.gd")
const ROOM_CONNECTION := preload("res://online_lobby_connection.gd")
const ONLINE_USER_TEXT_FONT := preload("res://online_user_text_font.gd")
const ONLINE_SELECTION := preload("res://online_character_selection.gd")
const CHARACTER_SELECTION := "res://generated/main/character_selection/available.json"
const STAGE_CATALOG := "res://generated/stages/catalog/catalog.json"

var render_surface: RenderSurface
var game_root: Control
var room_client: OnlineRoomClient
var peer_transport: Node
var coordinator: RefCounted

var _manifest: Dictionary = {}
var _room_state: Dictionary = {}
var _room_id := ""
var _invite_token := ""
var _invite_code := ""
var _slot := -1
var _busy := false
var _startup_busy := false
var _startup_cancel_in_progress := false
var _startup_cancel_requested := false
var _startup_cancel_unconfirmed := false
var _starting_epoch := ""
var _match_started := false
var _match_paused := false
var _dirty := false
var _exit_confirmation_deadline := -1
var _last_result_text := ""
var _signal_connected := false
var _lobby_signaling_desired := false
var _lobby_signaling_in_flight := false
var _lobby_presence_generation := 0
var _lobby_keepalive_elapsed := 0.0
var _lobby_reconnect_wait := 0.0
var _lobby_reconnect_attempt := 0
var _lobby_status_refresh_elapsed := 0.0
var _admission_uncertain := false
var _profile_draft_dirty := false
var _pending_network_profile: Dictionary = {}
var _network_profile_authority: Dictionary = {}
var _lifecycle_generation := 0
var _terminal_pending_epoch := ""
var _terminal_finished_epoch := ""
var _terminal_commit_queued_epoch := ""
var _pending_control_action := ""
var _pending_control_request_id := ""
var _web_window: JavaScriptObject
var _web_shortcut_callback: JavaScriptObject
var _web_paste_callback: JavaScriptObject
var _web_match_hud_callback: Variant
var _web_match_hud_token := -1
var _web_match_hud_session := ""
var _web_match_hud_revision := 0
var _web_match_hud_consumed_revision := -1
var _web_match_hud_last_fields: Dictionary = {}
var _web_match_hud_registered := false
# Allows native smoke tests to exercise the same bridge contract without JavaScript.
var _web_match_hud_bridge_override: Object
var _web_focused_line_edit: LineEdit
var _web_paste_target_active := false
var _room_connection: Node
var _room_connection_ready := false
var _room_connection_starting := false
var _room_connection_generation := 0
var _auto_connection_request := ""
var _connection_phase := "idle"
var _last_connection_error: Dictionary = {}
var _room_state_poll_elapsed := 0.0
var _room_state_poll_in_flight := false
var _selection_adapter: OnlineCharacterSelectionAdapter
var _selection_session_id := ""
var _selection_active := false
var _selection_completed_choice: Dictionary = {}
var _selection_owner_commit: Dictionary = {}
var _selection_guest_commit: Dictionary = {}
var _selection_commit_busy := false
var _selection_busy_previous := false
var _pending_selection_snapshot: Dictionary = {}
var _local_connection_profile_id := ""
var _remote_connection_profile_id := ""
var _selection_auto_started := false
var _selection_previous_root_physics := false
var _selection_root_restore_pending := false

var _map_adapter: Node
var _map_session_id := ""
var _map_active := false
var _map_host_authority := false
var _map_initializing := false
var _map_committing := false
var _map_cancel_waiting := false
var _map_handshake_complete := false
var _map_handshake_setup_revision := -1
var _map_pending_snapshot: Dictionary = {}
var _map_pending_open: Dictionary = {}
var _map_pending_configure: Dictionary = {}
var _map_pending_commit: Dictionary = {}
var _map_remote_ack: Dictionary = {}
var _map_commit_verifying := false
var _map_commit_delivery_pending := false
var _map_ack_pending := false
var _map_done_delivery_pending := false
var _map_previous_root_physics := false
var _map_root_restore_pending := false
var _rules_draft: Dictionary = {}
var _map_handshake_stage_id := ""
var _map_initial_selection_started := false
var _prepare_attempt_revision := -1
var _prepare_attempt_room_id := ""
var _prepare_attempt_generation := -1
var _prepare_success_revision := -1
var _prepare_success_room_id := ""
var _prepare_success_generation := -1
var _prepare_in_flight := false
var _prepare_retry_available := false

var _fighter_ids: Array[String] = []
var _helper_ids: Array[String] = []
var _stage_ids: Array[String] = []
var _fighter_labels := {}
var _helper_labels := {}
var _stage_labels := {}

var _veil: ColorRect
var _dialog: Panel
var _home_view: VBoxContainer
var _home_footer: VBoxContainer
var _startup_footer: HBoxContainer
var _room_view: VBoxContainer
var _match_view: VBoxContainer
var _status: Label
var _room_code: LineEdit
var _invite_input: LineEdit
var _room_code_output: LineEdit
var _invitation_row: HBoxContainer
var _copy_invite_button: Button
var _nickname: LineEdit
var _endpoint: LineEdit
var _time_choice: OptionButton
var _life_choice: OptionButton
var _delay_choice: OptionButton
var _prediction_choice: OptionButton
var _lan_candidate_opt_in: CheckBox
var _roster_status: Label
var _member_status: Label
var _profile_status: Label
var _room_visibility_hint: Label
var _result_status: Label
var _stage_summary: Label
var _advanced_toggle: CheckButton
var _advanced_settings: VBoxContainer
var _owner_settings: VBoxContainer
var _room_primary_action := ""
var _setup_button: Button
var _connect_selection_button: Button
var _reselect_button: Button
var _startup_cancel_button: Button
var _startup_abandon_button: Button
var _retry_button: Button
var _rotate_invite_button: Button
var _rematch_button: Button
var _leave_button: Button
var _result_leave_button: Button
var _match_hud: PanelContainer
var _match_status: Label
var _pause_button: Button
var _exit_button: Button
var _admission_retry_button: Button
var _admission_abandon_button: Button
var _admission_uncertain_warning: Label
var _control_reply_actions: HBoxContainer
var _control_accept_button: Button
var _control_refuse_button: Button
var _intro_skip_button: Button
var _diagnostic_button: Button
var _home_close_button: Button
var _diagnostic_report: Dictionary = {}


func _ready() -> void:
	process_mode = Node.PROCESS_MODE_ALWAYS
	if OS.has_feature("web"):
		_web_window = JavaScriptBridge.get_interface("window")
		if _web_window != null:
			_web_shortcut_callback = JavaScriptBridge.create_callback(_on_web_edit_shortcut)
			_web_paste_callback = JavaScriptBridge.create_callback(_on_web_paste)
			_web_window.bvnOnlineShortcutCallback = _web_shortcut_callback
			_web_window.bvnOnlinePasteCallback = _web_paste_callback
			_web_window.bvnOnlinePasteTargetActive = false
	_manifest = _as_dictionary(JSON.parse_string(FileAccess.get_file_as_string("res://generated/online/manifest.json")))
	_load_catalogs()
	_build_ui()
	room_client = CLIENT.new()
	room_client.process_mode = Node.PROCESS_MODE_ALWAYS
	room_client.state_changed.connect(_on_room_state_changed)
	room_client.signaling_message.connect(_on_signaling_message)
	room_client.socket_state_changed.connect(_on_socket_state_changed)
	room_client.error.connect(_on_room_error)
	add_child(room_client)
	set_physics_process(false)


func _exit_tree() -> void:
	if is_instance_valid(game_root) and game_root.has_method("_diagnostic_snapshot"):
		var diagnostics = game_root.get("diagnostics")
		if diagnostics is DiagnosticRuntime and diagnostics.snapshot_provider == Callable(self, "_diagnostic_snapshot"):
			diagnostics.snapshot_provider = Callable(game_root, "_diagnostic_snapshot")
	_close_room_connection()
	_end_selection_session(false)
	_unregister_web_match_hud()
	_web_focused_line_edit = null
	_set_web_paste_target_active(false)
	if _web_window != null:
		_web_window.bvnOnlineShortcutCallback = null
		_web_window.bvnOnlinePasteCallback = null
	_web_shortcut_callback = null
	_web_paste_callback = null


func configure(surface: RenderSurface, game: Control) -> void:
	render_surface = surface
	game_root = game
	if game_root != null:
		if game_root.has_method("_diagnostic_snapshot"):
			var diagnostics = game_root.get("diagnostics")
			if diagnostics is DiagnosticRuntime:
				diagnostics.snapshot_provider = Callable(self, "_diagnostic_snapshot")
		var title_menu := game_root.get("title_menu") as TitleMenu
		if title_menu != null and not title_menu.confirmed.is_connected(_on_game_menu_confirmed):
			title_menu.confirmed.connect(_on_game_menu_confirmed)


func _diagnostic_snapshot() -> Dictionary:
	var snapshot: Dictionary = game_root._diagnostic_snapshot() if is_instance_valid(game_root) else {}
	snapshot["onlineLobby"] = get_connection_diagnostic()
	return snapshot


func get_connection_diagnostic() -> Dictionary:
	var phase := _connection_phase
	if is_instance_valid(_room_connection) and _room_connection.has_method("get_startup_phase"):
		phase = str(_room_connection.get_startup_phase())
	return {
		"slot": _slot, "phase": phase, "inRoom": not _room_id.is_empty(),
		"roomPhase": str(_room_state.get("phase", "")),
		"busy": _busy, "starting": _room_connection_starting, "connected": _room_connection_ready,
		"signalingConnected": room_client != null and room_client.is_signaling_connected(),
		"negotiationPresent": _room_state.get("negotiation") is Dictionary,
		"profileDraftDirty": _profile_draft_dirty,
		"commandUncertain": room_client != null and room_client.has_uncertain_command(),
		"lastError": _last_connection_error.duplicate(true),
	}


func blocks_game_input(event: InputEvent) -> bool:
	return _veil != null and _veil.visible


func _input(event: InputEvent) -> void:
	if not blocks_game_input(event) or not event is InputEventKey:
		return
	var key_event := event as InputEventKey
	if not key_event.pressed or key_event.echo or key_event.keycode != KEY_ESCAPE:
		return
	if _home_view.visible and _can_close_home():
		_close_home()
	get_viewport().set_input_as_handled()


func _focused_online_line_edit() -> LineEdit:
	if _veil == null or not _veil.visible or _dialog == null or not _dialog.visible:
		return null
	var focused := get_viewport().gui_get_focus_owner()
	if not focused is LineEdit or focused != _web_focused_line_edit:
		return null
	var edit := focused as LineEdit
	if not edit.editable or not edit.is_visible_in_tree() or not _dialog.is_ancestor_of(edit):
		return null
	return edit


func _sync_web_paste_target() -> void:
	_set_web_paste_target_active(_focused_online_line_edit() != null)


func _set_web_paste_target_active(active: bool) -> void:
	if _web_paste_target_active == active:
		return
	_web_paste_target_active = active
	if _web_window != null:
		_web_window.bvnOnlinePasteTargetActive = active


func _on_online_edit_focus_entered(edit: LineEdit) -> void:
	_web_focused_line_edit = edit
	_sync_web_paste_target()


func _on_online_edit_focus_exited(edit: LineEdit) -> void:
	if _web_focused_line_edit == edit:
		_web_focused_line_edit = null
		_set_web_paste_target_active(false)


func _on_web_edit_shortcut(args: Array) -> void:
	if args.size() != 1 or typeof(args[0]) != TYPE_STRING:
		return
	var focused_edit := _focused_online_line_edit()
	if focused_edit == null:
		return
	match str(args[0]):
		"a":
			focused_edit.menu_option(LineEdit.MENU_SELECT_ALL)
		"c":
			focused_edit.menu_option(LineEdit.MENU_COPY)
		"x":
			if focused_edit.editable:
				focused_edit.menu_option(LineEdit.MENU_CUT)
		_: return


func _on_web_paste(_args: Array) -> void:
	var focused_edit := _focused_online_line_edit()
	if focused_edit == null:
		return
	# The browser's native paste handler updates Godot's clipboard cache after capture.
	# Deferring the native LineEdit action lets it preserve selection, filtering, length,
	# text_changed, and undo behavior without replacing the user's system clipboard.
	call_deferred("_paste_web_clipboard_into_edit", focused_edit.get_instance_id())


func _paste_web_clipboard_into_edit(instance_id: int) -> void:
	var focused_edit := _focused_online_line_edit()
	if focused_edit == null or focused_edit.get_instance_id() != instance_id:
		return
	focused_edit.menu_option(LineEdit.MENU_PASTE)


func _load_catalogs() -> void:
	var selection := _as_dictionary(JSON.parse_string(FileAccess.get_file_as_string(CHARACTER_SELECTION)))
	var service := _as_dictionary(_manifest.get("roster", {}))
	var stage_catalog := _as_dictionary(JSON.parse_string(FileAccess.get_file_as_string(STAGE_CATALOG)))
	for kind in ["fighters", "helpers"]:
		var available: Dictionary = selection[kind]
		var inverse := {}
		for display_name in available:
			inverse[str(available[display_name])] = str(display_name)
		var ids: Array = _as_array(service.get(kind, []))
		for raw_id in ids:
			var id := str(raw_id)
			if kind == "fighters":
				_fighter_ids.append(id)
				_fighter_labels[id] = str(inverse.get(id, id))
			else:
				_helper_ids.append(id)
				_helper_labels[id] = str(inverse.get(id, id))
	for raw_id in service.stages:
		var id := str(raw_id)
		_stage_ids.append(id)
		for entry_value in _as_array(stage_catalog.get("stages", [])):
			var entry := _as_dictionary(entry_value)
			if str(entry.get("id", "")) == id:
				_stage_labels[id] = str(entry.get("name", id))
				break


func _build_ui() -> void:
	var online_theme := Theme.new()
	var menu_font: Font = load("res://generated/main/title_menu/menu-font.ttf")
	if menu_font != null:
		online_theme.default_font = ONLINE_USER_TEXT_FONT.with_cjk_fallback(menu_font)

	_veil = ColorRect.new()
	_veil.name = "OnlineVeil"
	_veil.color = Color(0.025, 0.035, 0.055, 0.94)
	_veil.mouse_filter = Control.MOUSE_FILTER_STOP
	_veil.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	_veil.visible = false
	_veil.z_index = 1100
	add_child(_veil)

	_dialog = Panel.new()
	_dialog.name = "OnlineDialog"
	_dialog.set_anchors_preset(Control.PRESET_CENTER)
	_dialog.offset_left = -275
	_dialog.offset_top = -184
	_dialog.offset_right = 275
	_dialog.offset_bottom = 184
	_dialog.custom_minimum_size = Vector2(550, 368)
	_dialog.z_index = 1101
	_dialog.visible = false
	add_child(_dialog)
	_dialog.theme = online_theme
	var margin := MarginContainer.new()
	margin.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	margin.add_theme_constant_override("margin_left", 18)
	margin.add_theme_constant_override("margin_right", 18)
	margin.add_theme_constant_override("margin_top", 14)
	margin.add_theme_constant_override("margin_bottom", 14)
	_dialog.add_child(margin)
	var pages := VBoxContainer.new()
	pages.add_theme_constant_override("separation", 8)
	margin.add_child(pages)
	var title := Label.new()
	title.text = "联机对战 · 实验功能"
	title.add_theme_font_size_override("font_size", 20)
	title.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	pages.add_child(title)
	_status = Label.new()
	_status.text = "局域网/本机测试。网络参数仍需实测。"
	_status.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	_status.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	pages.add_child(_status)
	var page_scroll := ScrollContainer.new()
	page_scroll.name = "OnlinePageScroll"
	page_scroll.size_flags_vertical = Control.SIZE_EXPAND_FILL
	page_scroll.horizontal_scroll_mode = ScrollContainer.SCROLL_MODE_DISABLED
	pages.add_child(page_scroll)
	_home_footer = VBoxContainer.new()
	_home_footer.name = "OnlineHomeFooter"
	_home_footer.add_theme_constant_override("separation", 4)
	_home_footer.visible = false
	pages.add_child(_home_footer)
	_startup_footer = HBoxContainer.new()
	_startup_footer.name = "OnlineStartupFooter"
	_startup_footer.alignment = BoxContainer.ALIGNMENT_CENTER
	_startup_footer.visible = false
	pages.add_child(_startup_footer)
	var page_content := VBoxContainer.new()
	page_content.add_theme_constant_override("separation", 7)
	page_scroll.add_child(page_content)

	_home_view = VBoxContainer.new()
	_home_view.add_theme_constant_override("separation", 7)
	page_content.add_child(_home_view)
	_build_home_view()

	_room_view = VBoxContainer.new()
	_room_view.add_theme_constant_override("separation", 5)
	_room_view.visible = false
	page_content.add_child(_room_view)
	_build_room_view()

	_match_view = VBoxContainer.new()
	_match_view.add_theme_constant_override("separation", 8)
	_match_view.visible = false
	page_content.add_child(_match_view)
	_build_result_view()

	_match_hud = PanelContainer.new()
	_match_hud.name = "OnlineMatchHud"
	_match_hud.anchor_left = 1.0
	_match_hud.anchor_right = 1.0
	_match_hud.offset_left = -220
	_match_hud.offset_right = -12
	_match_hud.offset_top = 40
	_match_hud.offset_bottom = 118
	_match_hud.z_index = 1000
	_match_hud.visible = false
	add_child(_match_hud)
	_match_hud.theme = online_theme
	var hud_box := VBoxContainer.new()
	hud_box.add_theme_constant_override("separation", 2)
	_match_hud.add_child(hud_box)
	_match_status = Label.new()
	_match_status.text = "同步中"
	_match_status.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	_match_status.clip_text = false
	_match_status.add_theme_font_size_override("font_size", 12)
	_match_status.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	hud_box.add_child(_match_status)
	_intro_skip_button = _button("请求跳过开场", _on_intro_skip_pressed)
	_intro_skip_button.visible = false
	_intro_skip_button.add_theme_font_size_override("font_size", 12)
	hud_box.add_child(_intro_skip_button)
	var hud_actions := HBoxContainer.new()
	hud_actions.alignment = BoxContainer.ALIGNMENT_CENTER
	hud_box.add_child(hud_actions)
	_pause_button = _button("请求暂停", _on_pause_pressed)
	_pause_button.add_theme_font_size_override("font_size", 12)
	hud_actions.add_child(_pause_button)
	_exit_button = _button("退出本局", _on_exit_match_pressed)
	_exit_button.add_theme_font_size_override("font_size", 12)
	hud_actions.add_child(_exit_button)
	_control_reply_actions = HBoxContainer.new()
	_control_reply_actions.alignment = BoxContainer.ALIGNMENT_CENTER
	_control_reply_actions.visible = false
	hud_box.add_child(_control_reply_actions)
	_control_accept_button = _button("同意", _on_control_reply.bind(true))
	_control_refuse_button = _button("拒绝", _on_control_reply.bind(false))
	_control_accept_button.add_theme_font_size_override("font_size", 12)
	_control_refuse_button.add_theme_font_size_override("font_size", 12)
	_control_reply_actions.add_child(_control_accept_button)
	_control_reply_actions.add_child(_control_refuse_button)


func _build_home_view() -> void:
	_nickname = _line_edit("玩家", "昵称")
	_endpoint = _line_edit(DEFAULT_SERVICE_URL, "服务地址")
	_home_view.add_child(_row("昵称", _nickname))
	_home_view.add_child(_row("服务地址", _endpoint))
	var create := _button("创建好友房间", _on_create_pressed)
	_home_view.add_child(create)
	_room_code = _line_edit("", "好友邀请码或旧版邀请串")
	_room_code.custom_minimum_size.x = 300
	_home_view.add_child(_row("加入码", _room_code))
	var join := _button("加入房间", _on_join_pressed)
	_home_view.add_child(join)
	_admission_retry_button = _button("重试上次房间请求", _on_retry_admission_pressed)
	_admission_retry_button.visible = false
	var admission_actions := HBoxContainer.new()
	admission_actions.alignment = BoxContainer.ALIGNMENT_CENTER
	admission_actions.add_child(_admission_retry_button)
	_admission_uncertain_warning = Label.new()
	_admission_uncertain_warning.text = "暂时无法确认请求结果。返回将放弃此次请求，已创建的空闲房间最多 30 分钟后关闭。"
	_admission_uncertain_warning.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	_admission_uncertain_warning.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	_admission_uncertain_warning.visible = false
	_admission_abandon_button = _button("放弃请求并返回主菜单", _on_abandon_admission_pressed)
	_admission_abandon_button.visible = false
	admission_actions.add_child(_admission_abandon_button)
	_home_footer.add_child(_admission_uncertain_warning)
	_home_footer.add_child(admission_actions)
	var footer := HBoxContainer.new()
	footer.alignment = BoxContainer.ALIGNMENT_CENTER
	_home_footer.add_child(footer)
	_home_close_button = _button("返回主菜单（Esc）", _on_close_pressed)
	footer.add_child(_home_close_button)


func _build_room_view() -> void:
	_member_status = Label.new()
	_member_status.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	_room_view.add_child(_member_status)
	_stage_summary = Label.new()
	_stage_summary.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	_room_view.add_child(_stage_summary)
	_room_code_output = _line_edit("", "房间邀请码")
	_room_code_output.editable = false
	var invitation_actions := HBoxContainer.new()
	invitation_actions.alignment = BoxContainer.ALIGNMENT_CENTER
	_room_code_output.custom_minimum_size.y = 28
	_invitation_row = HBoxContainer.new()
	_invitation_row.alignment = BoxContainer.ALIGNMENT_CENTER
	_invitation_row.add_child(_room_code_output)
	_room_view.add_child(_invitation_row)
	_copy_invite_button = _button("复制加入码", _copy_invitation)
	invitation_actions.add_child(_copy_invite_button)
	_rotate_invite_button = _button("换一个加入码", _on_rotate_invitation_pressed)
	_rotate_invite_button.visible = false
	_room_view.add_child(invitation_actions)
	_retry_button = _button("重试未确认操作", _on_retry_signaling_pressed)
	_retry_button.visible = false
	_room_view.add_child(_retry_button)

	_advanced_toggle = CheckButton.new()
	_advanced_toggle.text = "高级设置"
	_advanced_toggle.toggled.connect(_on_advanced_toggled)
	_room_view.add_child(_advanced_toggle)
	_advanced_settings = VBoxContainer.new()
	_advanced_settings.add_theme_constant_override("separation", 4)
	_advanced_settings.visible = false
	_room_view.add_child(_advanced_settings)
	_advanced_settings.add_child(_rotate_invite_button)
	_room_visibility_hint = Label.new()
	_room_visibility_hint.text = "同机联调时请把两个窗口并排并保持可见。"
	_room_visibility_hint.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	_room_visibility_hint.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	_advanced_settings.add_child(_room_visibility_hint)
	_owner_settings = VBoxContainer.new()
	_owner_settings.add_theme_constant_override("separation", 2)
	_advanced_settings.add_child(_owner_settings)
	var owner_rules_grid := GridContainer.new()
	owner_rules_grid.columns = 2
	_owner_settings.add_child(owner_rules_grid)
	_time_choice = _option()
	_add_number_options(owner_rules_grid, "时间", _time_choice, [30, 60, 90, 100], " 秒")
	_life_choice = _option()
	_add_number_options(owner_rules_grid, "生命倍率", _life_choice, [1, 2, 3, 4, 5], "×")
	var profile_grid := GridContainer.new()
	profile_grid.columns = 2
	profile_grid.add_theme_constant_override("h_separation", 12)
	profile_grid.add_theme_constant_override("v_separation", 4)
	_owner_settings.add_child(profile_grid)
	_delay_choice = _option()
	_add_number_options(profile_grid, "输入延迟", _delay_choice, [0, 1, 2], " 帧")
	_select_number(_delay_choice, 2)
	_prediction_choice = _option()
	_add_number_options(profile_grid, "预测上限", _prediction_choice, [2, 4, 6], " 帧")
	_select_number(_prediction_choice, 6)
	var profile_latency_hint := Label.new()
	profile_latency_hint.text = "默认增加约 67 毫秒操作延迟以减少等待；由房主统一设置。"
	profile_latency_hint.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	profile_latency_hint.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	_owner_settings.add_child(profile_latency_hint)
	for picker in [_time_choice, _life_choice]:
		picker.item_selected.connect(_on_setup_picker_changed)
	for picker in [_delay_choice, _prediction_choice]:
		picker.item_selected.connect(_on_profile_picker_changed)

	_roster_status = Label.new()
	_roster_status.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	_roster_status.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	_advanced_settings.add_child(_roster_status)
	_profile_status = Label.new()
	_profile_status.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	_profile_status.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	_advanced_settings.add_child(_profile_status)
	_lan_candidate_opt_in = CheckBox.new()
	_lan_candidate_opt_in.text = "本机 / 同一局域网对战（无需中转）"
	_lan_candidate_opt_in.tooltip_text = "只用于本机或同一局域网测试；跨网络对战仍需服务端配置 TURN。由房主选择并同步双方。"
	_lan_candidate_opt_in.toggled.connect(_on_profile_option_toggled)
	_owner_settings.add_child(_lan_candidate_opt_in)

	var actions := HBoxContainer.new()
	actions.alignment = BoxContainer.ALIGNMENT_CENTER
	_room_view.add_child(actions)
	_connect_selection_button = _button("连接并选择角色", _on_room_primary_pressed)
	actions.add_child(_connect_selection_button)
	_reselect_button = _button("改选角色与援助", _on_reselect_pressed)
	_reselect_button.visible = false
	actions.add_child(_reselect_button)
	_setup_button = _button("改选地图", _on_commit_setup_pressed)
	_setup_button.visible = false
	actions.add_child(_setup_button)
	_startup_cancel_button = _button("取消开局并返回房间", _on_cancel_start_pressed)
	_startup_cancel_button.visible = false
	_startup_footer.add_child(_startup_cancel_button)
	_startup_abandon_button = _button("放弃等待并返回主菜单", _on_abandon_startup_pressed)
	_startup_abandon_button.visible = false
	_startup_footer.add_child(_startup_abandon_button)
	_leave_button = _button("离开房间", _on_leave_room_pressed)
	_room_view.add_child(_leave_button)


func _build_result_view() -> void:
	_result_status = Label.new()
	_result_status.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	_result_status.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	_match_view.add_child(_result_status)
	_diagnostic_button = _button("下载本局诊断", _on_diagnostic_download_pressed)
	_diagnostic_button.visible = false
	_match_view.add_child(_diagnostic_button)
	_rematch_button = _button("返回房间 · 再战", _on_rematch_pressed)
	_match_view.add_child(_rematch_button)
	_result_leave_button = _button("离开联机模式", _on_leave_room_pressed)
	_match_view.add_child(_result_leave_button)


func _open_home() -> void:
	if not _is_title_menu() or _busy:
		return
	if game_root != null:
		game_root.set_physics_process(false)
		game_root.set_meta("online_modal_open", true)
	_veil.visible = true
	_dialog.visible = true
	_home_view.visible = true
	_home_footer.visible = true
	_room_view.visible = false
	_match_view.visible = false
	_match_hud.visible = false
	_status.text = "局域网/本机测试。网络参数仍需实测。"
	_nickname.grab_focus()


func _on_close_pressed() -> void:
	if not _can_close_home():
		return
	_close_home()


func _can_close_home() -> bool:
	return not _busy and not _admission_uncertain and _room_id.is_empty()


func _close_home() -> void:
	_veil.visible = false
	_dialog.visible = false
	_home_footer.visible = false
	get_viewport().gui_release_focus()
	_sync_web_paste_target()
	if game_root != null:
		game_root.remove_meta("online_modal_open")
		var title_menu := game_root.get("title_menu") as TitleMenu
		if title_menu != null:
			title_menu.reset()
		game_root.set_physics_process(_is_title_menu())


func _on_create_pressed() -> void:
	if _busy or _admission_uncertain:
		return
	if not _configure_service():
		return
	_busy = true
	var request_generation := _lifecycle_generation
	_status.text = "正在创建房间…"
	var response: Dictionary = await room_client.create_room(_nickname.text, _compatibility())
	if request_generation != _lifecycle_generation:
		return
	_busy = false
	if response.has("error"):
		_set_admission_uncertain(bool(response.get("uncertain", false)))
		_show_error(str(response.error))
		return
	_set_admission_uncertain(false)
	_room_id = str(response.room_id)
	_slot = int(response.slot)
	_invite_token = str(response.get("invite_token", ""))
	_invite_code = str(response.get("invite_code", ""))
	_accept_state(response.state)
	_show_room()
	_refresh_room_view()
	_arm_lobby_presence()


func _on_join_pressed() -> void:
	if _busy or _admission_uncertain:
		return
	if not _configure_service():
		return
	var invitation := _parse_invitation(_room_code.text)
	if invitation.is_empty():
		_show_error("invalid_invitation")
		return
	_busy = true
	var request_generation := _lifecycle_generation
	_status.text = "正在加入房间…"
	var response: Dictionary
	if invitation.get("kind") == "legacy":
		response = await room_client.join_room(
			str(invitation.room_id), str(invitation.invite_token), _nickname.text, _compatibility()
		)
	else:
		response = await room_client.join_by_code(
			str(invitation.get("code", "")), _nickname.text, _compatibility()
		)
	if request_generation != _lifecycle_generation:
		return
	_busy = false
	if response.has("error"):
		_set_admission_uncertain(bool(response.get("uncertain", false)))
		_show_error(str(response.error))
		return
	_set_admission_uncertain(false)
	_room_id = str(response.room_id)
	_slot = int(response.slot)
	_invite_code = str(response.get("invite_code", ""))
	_accept_state(response.state)
	_show_room()
	_refresh_room_view()
	_arm_lobby_presence()


func _configure_service() -> bool:
	if _admission_uncertain:
		_show_error("admission_retry_required")
		return false
	if not _manifest.has("compatibility"):
		_show_error("manifest_missing")
		return false
	if not room_client.configure_service(_endpoint.text):
		_show_error("invalid_service_url")
		return false
	if not room_client.get_room_id().is_empty():
		_show_error("already_in_room")
		return false
	return true


func _on_retry_admission_pressed() -> void:
	if _busy or not _admission_uncertain:
		return
	_busy = true
	var request_generation := _lifecycle_generation
	_admission_retry_button.disabled = true
	_status.text = "正在重试完全相同的房间请求…"
	var response: Dictionary = await room_client.retry_pending_admission()
	if request_generation != _lifecycle_generation:
		return
	_busy = false
	_admission_retry_button.disabled = false
	if response.has("error"):
		_set_admission_uncertain(bool(response.get("uncertain", false)))
		_show_error(str(response.get("error", "service_error")))
		return
	_set_admission_uncertain(false)
	_room_id = str(response.get("room_id", ""))
	_slot = int(response.get("slot", -1))
	_invite_token = str(response.get("invite_token", ""))
	_invite_code = str(response.get("invite_code", ""))
	_accept_state(response.get("state"))
	_show_room()
	_refresh_room_view()
	_arm_lobby_presence()


func _set_admission_uncertain(uncertain: bool) -> void:
	_admission_uncertain = uncertain
	_admission_retry_button.visible = uncertain
	_admission_abandon_button.visible = uncertain
	_admission_uncertain_warning.visible = uncertain
	_admission_retry_button.disabled = false
	_admission_abandon_button.disabled = false


func _on_abandon_admission_pressed() -> void:
	if _busy or not _admission_uncertain or not _room_id.is_empty():
		return
	_busy = true
	_lifecycle_generation += 1
	var generation := _lifecycle_generation
	room_client.clear_credentials()
	if generation != _lifecycle_generation:
		return
	_set_admission_uncertain(false)
	_room_state.clear()
	_pending_network_profile.clear()
	_network_profile_authority.clear()
	_profile_draft_dirty = false
	_room_id = ""
	_invite_token = ""
	_invite_code = ""
	_slot = -1
	_signal_connected = false
	_stop_lobby_presence()
	_starting_epoch = ""
	_terminal_pending_epoch = ""
	_terminal_finished_epoch = ""
	_terminal_commit_queued_epoch = ""
	_pending_control_action = ""
	_pending_control_request_id = ""
	_busy = false
	get_tree().paused = false
	_on_close_pressed()


func _compatibility() -> Dictionary:
	return _manifest.compatibility.duplicate(true)


func _connect_signaling() -> void:
	_arm_lobby_presence()


func _arm_lobby_presence(update_status := true) -> void:
	if _room_id.is_empty() or room_client == null or not is_instance_valid(room_client):
		return
	if str(_room_state.get("phase", "")) != "lobby":
		return
	_lobby_signaling_desired = true
	_lobby_keepalive_elapsed = 0.0
	_lobby_reconnect_attempt = 0
	_lobby_reconnect_wait = 0.0
	_lobby_status_refresh_elapsed = 0.0
	if update_status:
		_refresh_lobby_presence_status(true)
	_ensure_lobby_signaling()


func _stop_lobby_presence() -> void:
	_lobby_signaling_desired = false
	_lobby_presence_generation += 1
	_lobby_keepalive_elapsed = 0.0
	_lobby_reconnect_wait = 0.0
	_lobby_reconnect_attempt = 0
	_lobby_status_refresh_elapsed = 0.0


func _cancel_lobby_signaling() -> void:
	_stop_lobby_presence()
	if room_client != null and is_instance_valid(room_client) \
		and room_client.has_method("cancel_signaling"):
		room_client.cancel_signaling()
	# The cancelled ticket request resumes on a deferred signal. Yield until
	# that call drops its in-flight flag so a later connect does not overlap it.
	var spins := 0
	while _lobby_signaling_in_flight and spins < 3:
		await get_tree().process_frame
		spins += 1


func _ensure_lobby_signaling() -> void:
	if _lobby_signaling_in_flight or not _lobby_signaling_desired:
		return
	if room_client == null or not is_instance_valid(room_client) or _room_id.is_empty():
		return
	if room_client.is_signaling_connected():
		_signal_connected = true
		_refresh_lobby_presence_status(false)
		return
	if _room_connection_starting or _room_connection_ready or _startup_busy or _match_started:
		return
	if str(_room_state.get("phase", "")) != "lobby":
		return
	_lobby_signaling_in_flight = true
	var generation := _lobby_presence_generation
	var room_id := _room_id
	var response: Dictionary = await room_client.connect_signaling()
	_lobby_signaling_in_flight = false
	if generation != _lobby_presence_generation or room_id != _room_id or not _lobby_signaling_desired:
		return
	if response.has("error"):
		_signal_connected = false
		var code := str(response.get("error", ""))
		if code == "socket_cancelled" or code == "session_changed":
			return
		if code == "socket_connecting":
			_lobby_reconnect_wait = 0.5
			return
		if _lobby_presence_error_is_terminal(code):
			_abandon_lobby_presence(code)
			return
		_schedule_lobby_reconnect()
		if _can_show_lobby_presence_status():
			_status.text = "信令已断开，约 %d 秒后重新连接。" % int(ceili(_lobby_reconnect_wait))
		return
	_signal_connected = true
	_lobby_reconnect_attempt = 0
	_lobby_reconnect_wait = 0.0
	if response.get("state") is Dictionary:
		_accept_state(response.get("state"))
	_refresh_lobby_presence_status(false)


func _schedule_lobby_reconnect() -> void:
	var exponent := mini(_lobby_reconnect_attempt, 5)
	_lobby_reconnect_wait = minf(
		LOBBY_RECONNECT_MAX_SECONDS,
		LOBBY_RECONNECT_BASE_SECONDS * float(1 << exponent)
	)
	_lobby_reconnect_attempt += 1


func _send_lobby_keepalive() -> void:
	if not _lobby_signaling_desired or room_client == null or not is_instance_valid(room_client):
		return
	if room_client.has_uncertain_command() or room_client.is_command_in_flight():
		return
	if not room_client.is_signaling_connected():
		return
	var generation := _lobby_presence_generation
	var room_id := _room_id
	var result: Dictionary = await room_client.command({"type": "keepalive"})
	if generation != _lobby_presence_generation or room_id != _room_id or not _lobby_signaling_desired:
		return
	if result.has("error"):
		var code := str(result.get("error", ""))
		if _lobby_presence_error_is_terminal(code):
			_abandon_lobby_presence(code)
			return
		if bool(result.get("uncertain", false)) and _retry_button != null:
			_retry_button.visible = true
		return
	_accept_state(result.get("state"))


func _lobby_presence_error_is_terminal(code: String) -> bool:
	return code in [
		"unauthorized",
		"not_authenticated",
		"not_in_room",
		"membership_ended",
		"service_http_401",
		"invalid_invite",
		"invite_expired",
		"room_closed",
		"room_expired",
		"room_not_found",
		"not_found",
		"service_http_404",
	]


func _abandon_lobby_presence(code: String) -> void:
	_stop_lobby_presence()
	_signal_connected = false
	if _can_show_lobby_presence_status():
		_show_error(code)


func _tick_lobby_presence(delta: float) -> void:
	if not _lobby_signaling_desired or _room_id.is_empty() or room_client == null \
		or not is_instance_valid(room_client):
		return
	if str(_room_state.get("phase", "")) != "lobby" or _startup_busy or _match_started:
		return
	if room_client.is_signaling_connected():
		_lobby_keepalive_elapsed += delta
		_lobby_status_refresh_elapsed += delta
		if _lobby_status_refresh_elapsed >= LOBBY_STATUS_REFRESH_SECONDS \
			and _status_is_lobby_presence():
			_lobby_status_refresh_elapsed = 0.0
			_refresh_lobby_presence_status(true)
		if _lobby_keepalive_elapsed >= LOBBY_KEEPALIVE_SECONDS:
			if room_client.has_uncertain_command() or room_client.is_command_in_flight():
				return
			_lobby_keepalive_elapsed = 0.0
			_send_lobby_keepalive()
		return
	if _lobby_signaling_in_flight or _room_connection_starting or _room_connection_ready:
		return
	if _lobby_reconnect_wait > 0.0:
		_lobby_reconnect_wait = maxf(0.0, _lobby_reconnect_wait - delta)
		if _lobby_reconnect_wait > 0.0:
			return
	_ensure_lobby_signaling()


func _can_show_lobby_presence_status() -> bool:
	if _status == null or _room_id.is_empty() or _room_state.is_empty():
		return false
	if _match_started or _startup_busy or _selection_active or _map_active:
		return false
	if _room_connection_starting or _room_connection_ready:
		return false
	if str(_room_state.get("phase", "")) != "lobby":
		return false
	return _dialog != null and _dialog.visible and _room_view != null and _room_view.visible


func _status_is_lobby_presence() -> bool:
	if _status == null:
		return false
	var text := _status.text
	return text.begins_with("房间已创建") \
		or text.begins_with("邀请口令已显示") \
		or text.begins_with("已加入房间") \
		or text.begins_with("双方已在房间") \
		or text.begins_with("信令已断开") \
		or text.begins_with("正在创建房间") \
		or text.begins_with("正在加入房间")


func _refresh_lobby_presence_status(force := false) -> void:
	if not _can_show_lobby_presence_status():
		return
	if not force and not _status_is_lobby_presence():
		return
	_status.text = _lobby_presence_status_text()


func _lobby_presence_status_text() -> String:
	var connected := room_client != null and is_instance_valid(room_client) \
		and room_client.is_signaling_connected()
	var members := _as_array(_room_state.get("members", []))
	var has_guest := members.size() > 1 and members[1] is Dictionary
	var idle_note := _lobby_idle_note(connected)
	if _slot == 0 and not has_guest:
		if connected:
			return "邀请口令已显示，信令已连接，正在等待对手加入。" + idle_note
		return "房间已创建。邀请口令已显示，正在连接信令并等待对手。" + idle_note
	if _slot == 1:
		if connected:
			return "已加入房间，信令已连接。可以连接并选择角色。" + idle_note
		return "已加入房间，正在连接信令。" + idle_note
	if connected:
		return "双方已在房间，信令已连接。可以连接并选择角色。" + idle_note
	return "双方已在房间，正在连接信令。" + idle_note


func _lobby_idle_note(connected: bool) -> String:
	if _slot != 0:
		return ""
	var minutes := _lobby_idle_remaining_minutes()
	if connected:
		return " 信令保持连接时房间最长约 2 小时，断开后约 %d 分钟关闭。" % maxi(minutes, 1)
	if minutes <= 0:
		return " 房间即将因空闲关闭。"
	return " 信令断开后约 %d 分钟关闭。" % minutes


func _lobby_idle_remaining_minutes() -> int:
	var last := int(_room_state.get("lastActivity", 0))
	if last <= 0:
		return 30
	var remaining_ms := float(last + LOBBY_IDLE_MS) - Time.get_unix_time_from_system() * 1000.0
	if remaining_ms <= 0.0:
		return 0
	return int(ceili(remaining_ms / 60000.0))


func _on_connect_selection_pressed() -> void:
	if _busy or _room_connection_starting or _room_id.is_empty() or _selection_active:
		return
	await _start_room_connection()


func _start_room_connection() -> void:
	if _room_connection_ready or _room_connection_starting or _room_id.is_empty() or _slot not in [0, 1]:
		return
	if room_client.has_uncertain_command() or room_client.is_command_in_flight():
		_show_error("command_outcome_uncertain")
		_retry_button.visible = true
		return
	if _profile_draft_dirty or not _pending_network_profile.is_empty():
		_show_error("network_profile_not_committed")
		return
	if _room_connection != null:
		_close_room_connection()
	_room_connection_starting = true
	var generation := _room_connection_generation + 1
	_room_connection_generation = generation
	var lifecycle_generation := _lifecycle_generation
	var expected_room_id := _room_id
	_room_connection_ready = false
	_remote_connection_profile_id = ""
	_local_connection_profile_id = ""
	_connection_phase = "refresh_room"
	_status.text = "正在建立选人连接…"
	_refresh_room_view()
	var room_reply: Dictionary = await room_client.refresh_state()
	if not _room_connection_attempt_current(generation, lifecycle_generation, expected_room_id):
		_abandon_stale_room_connection_attempt(generation, lifecycle_generation, expected_room_id)
		return
	if room_reply.has("error"):
		_room_connection_starting = false
		_show_error(str(room_reply.get("error", "service_error")))
		_refresh_room_view()
		return
	_accept_state(room_reply.get("state"))
	if not _room_connection_attempt_current(generation, lifecycle_generation, expected_room_id):
		_abandon_stale_room_connection_attempt(generation, lifecycle_generation, expected_room_id)
		return
	var profile := _authoritative_network_profile()
	if profile.is_empty():
		_room_connection_starting = false
		_show_error("server_upgrade_required")
		_refresh_room_view()
		return
	if _slot == 0 and not _same_network_profile(_current_network_profile(), profile):
		_room_connection_starting = false
		_profile_draft_dirty = false
		_sync_network_profile_controls_from_state()
		_show_error("network_profile_not_committed")
		_refresh_room_view()
		return
	var expected_setup_revision := int(_room_state.get("setupRevision", -1))
	_local_connection_profile_id = str(profile.get("id", ""))

	var ice_servers: Array = []
	if not _local_connection_profile_id.ends_with("-lan"):
		_connection_phase = "ice_servers"
		var ice_reply: Dictionary = await room_client.get_ice_servers()
		if not _room_connection_attempt_current(
			generation, lifecycle_generation, expected_room_id, profile, expected_setup_revision
		):
			_abandon_stale_room_connection_attempt(generation, lifecycle_generation, expected_room_id)
			return
		if ice_reply.has("error"):
			_room_connection_starting = false
			_show_error(str(ice_reply.get("error", "ice_lookup_failed")))
			_refresh_room_view()
			return
		ice_servers = _as_array(ice_reply.get("iceServers", []))
	if not _room_connection_attempt_current(
		generation, lifecycle_generation, expected_room_id, profile, expected_setup_revision
	):
		_abandon_stale_room_connection_attempt(generation, lifecycle_generation, expected_room_id)
		return

	var connection := ROOM_CONNECTION.new() as Node
	connection.process_mode = Node.PROCESS_MODE_ALWAYS
	_room_connection = connection
	connection.connection_changed.connect(_on_room_connection_changed)
	connection.peer_message.connect(_on_room_connection_message)
	connection.transport_error.connect(_on_room_connection_error)
	add_child(connection)
	if not connection.configure(room_client, _slot, ice_servers):
		_room_connection_starting = false
		_close_room_connection()
		_show_error("peer_configuration_failed")
		_refresh_room_view()
		return
	_connection_phase = "signaling"
	var issue := str(await connection.start())
	if not _room_connection_attempt_current(
		generation, lifecycle_generation, expected_room_id, profile, expected_setup_revision
	) or connection != _room_connection:
		_abandon_stale_room_connection_attempt(generation, lifecycle_generation, expected_room_id)
		return
	_room_connection_starting = false
	if not issue.is_empty():
		_room_connection_ready = false
		_show_error(issue)
		_refresh_room_view()
		return
	_room_connection_ready = true
	_signal_connected = room_client.is_signaling_connected()
	connection.send_peer_message("selection_connection_profile", {"version": 1, "id": _local_connection_profile_id})
	_status.text = "选人连接已建立，正在确认双方网络档位…"
	_refresh_room_view()
	_maybe_begin_initial_selection()


func _room_connection_attempt_current(
	generation: int,
	lifecycle_generation: int,
	expected_room_id: String,
	profile: Dictionary = {},
	setup_revision: int = -1
) -> bool:
	if generation != _room_connection_generation or lifecycle_generation != _lifecycle_generation \
		or _room_id != expected_room_id or room_client == null or room_client.get_room_id() != expected_room_id \
		or room_client.has_uncertain_command() or room_client.is_command_in_flight():
		return false
	if not profile.is_empty() and (
		not _same_network_profile(_authoritative_network_profile(), profile)
		or int(_room_state.get("setupRevision", -1)) != setup_revision
	):
		return false
	return true


func _abandon_stale_room_connection_attempt(generation: int, lifecycle_generation: int, expected_room_id: String) -> void:
	if generation != _room_connection_generation or lifecycle_generation != _lifecycle_generation \
		or _room_id != expected_room_id or room_client == null \
		or room_client.get_room_id() != expected_room_id:
		return
	_close_room_connection()
	_status.text = "房间设置已变化，请重新建立连接。"
	_refresh_room_view()


func _current_connection_profile_id() -> String:
	return str(_current_network_profile().get("id", ""))


func _current_network_profile() -> Dictionary:
	var delay := _selected_number(_delay_choice)
	var prediction := _selected_number(_prediction_choice)
	var profile_id := "chrome-exp-d%d-p%d" % [delay, prediction]
	if _lan_candidate_opt_in.button_pressed:
		profile_id += "-lan"
	return {"id": profile_id, "inputDelay": delay, "predictionWindow": prediction}


func _authoritative_network_profile() -> Dictionary:
	return _network_profile_authority.duplicate(true)


func _network_profile_from_state(state: Dictionary) -> Dictionary:
	var profile := _as_dictionary(state.get("networkProfile"))
	if profile.is_empty() or not _valid_network_profile(profile):
		return {}
	return profile.duplicate(true)


func _valid_network_profile(profile: Dictionary) -> bool:
	if not profile.has_all(["id", "inputDelay", "predictionWindow"]):
		return false
	var id: Variant = profile.get("id")
	var delay: Variant = profile.get("inputDelay")
	var prediction: Variant = profile.get("predictionWindow")
	if not id is String or not _is_integral_profile_number(delay) \
		or not _is_integral_profile_number(prediction):
		return false
	var normalized_delay := int(delay)
	var normalized_prediction := int(prediction)
	if normalized_delay < 0 or normalized_delay > 8 or normalized_prediction < 0 or normalized_prediction > 15:
		return false
	var base_id := "chrome-exp-d%d-p%d" % [normalized_delay, normalized_prediction]
	return id == base_id or id == base_id + "-lan"


func _is_integral_profile_number(value: Variant) -> bool:
	return value is int or (value is float and is_finite(value) and floor(value) == value)


func _same_network_profile(left: Dictionary, right: Dictionary) -> bool:
	return _valid_network_profile(left) and _valid_network_profile(right) \
		and str(left.get("id")) == str(right.get("id")) \
		and int(left.get("inputDelay", -1)) == int(right.get("inputDelay", -2)) \
		and int(left.get("predictionWindow", -1)) == int(right.get("predictionWindow", -2))


func _on_reselect_pressed() -> void:
	if _busy or _selection_active or _selection_commit_busy or not _room_connection_ready:
		return
	if _slot == 0:
		_start_host_selection_session()
	else:
		_room_connection.send_peer_message("selection_open_request", {"version": 1})
		_status.text = "已请求房主重新开放选人。"


func _on_room_connection_changed(state: String) -> void:
	_room_connection_ready = state == "connected"
	if state in ["failed", "closed", "disconnected"]:
		_room_connection_starting = false
		_remote_connection_profile_id = ""
		if _selection_active:
			_end_selection_session(false)
			_status.text = "选人连接已中断；角色尚未提交。"
		if _room_connection != null and is_instance_valid(_room_connection):
			call_deferred(
				"_close_room_connection_if_current",
				_room_connection,
				_room_connection_generation
			)
	_refresh_room_view()
	if _room_connection_ready:
		_maybe_begin_initial_selection()


func _close_room_connection_if_current(connection: Node, generation: int) -> void:
	if generation != _room_connection_generation or not is_instance_valid(connection) \
		or connection != _room_connection:
		return
	_close_room_connection()
	_refresh_room_view()


func _on_room_connection_error(code: String) -> void:
	_room_connection_ready = false
	_room_connection_starting = false
	_show_error(code)
	_refresh_room_view()


func _on_room_connection_message(message_type: String, payload: Variant, _sequence: int) -> void:
	if not payload is Dictionary:
		return
	var message: Dictionary = payload
	match message_type:
		"selection_connection_profile":
			if message.get("version") != 1 or not message.get("id") is String:
				return
			_remote_connection_profile_id = str(message.id)
			_maybe_begin_initial_selection()
			_refresh_room_view()
		"selection_open_request":
			if _slot == 0 and message.get("version") == 1 and _room_connection_ready:
				_start_host_selection_session()
		"selection_open":
			if _slot != 1 or message.get("version") != 1:
				return
			_map_handshake_complete = false
			_map_handshake_setup_revision = -1
			_map_handshake_stage_id = ""
			_map_initial_selection_started = false
			var session_id := str(message.get("sessionId", ""))
			var initial_choices: Variant = message.get("initialChoices", [])
			if initial_choices is Array and _begin_selection_session(session_id, initial_choices):
				_selection_auto_started = true
		"selection_snapshot":
			if _selection_active and str(message.get("sessionId", "")) == _selection_session_id:
				_selection_adapter.apply_remote_snapshot(message)
		"selection_cancel":
			if _selection_active and str(message.get("sessionId", "")) == _selection_session_id:
				_end_selection_session(false)
				_show_room()
				_status.text = "选人已取消；已确认选择保持不变。"
				_refresh_room_view()
		"selection_owner_committed":
			if _slot == 1 and _valid_selection_commit(message):
				_selection_owner_commit[_selection_session_id] = message.duplicate(true)
				_maybe_commit_guest_selection()
		"selection_guest_committed":
			if _slot == 0 and _valid_selection_commit(message):
				_selection_guest_commit[_selection_session_id] = message.duplicate(true)
				_maybe_finish_selection_from_room_state()
		"map_open":
			if _slot == 1:
				_receive_map_open(message)
		"map_snapshot":
			if _slot == 1:
				_receive_map_snapshot(message)
		"map_committed":
			if _slot == 1:
				_verify_guest_map_commit.call_deferred(message.duplicate(true))
		"map_ack":
			if _slot == 0:
				_receive_map_ack(message)
		"map_done":
			if _slot == 1:
				_receive_map_done(message)
		"map_cancel_request":
			if _slot == 0:
				_receive_map_cancel_request(message)
		"map_cancel":
			_receive_map_cancel(message)


func _valid_selection_commit(message: Dictionary) -> bool:
	return str(message.get("sessionId", "")) == _selection_session_id \
		and _selection_active \
		and message.get("version") == 1 \
		and message.get("choice") is Dictionary


func _has_both_committed_choices() -> bool:
	var members := _as_array(_room_state.get("members", []))
	if members.size() != 2 or not members[0] is Dictionary or not members[1] is Dictionary:
		return false
	return _valid_selection_choice(_as_dictionary(_as_dictionary(members[0]).get("choice"))) \
		and _valid_selection_choice(_as_dictionary(_as_dictionary(members[1]).get("choice")))


func _maybe_start_initial_map_selection() -> void:
	if _slot != 0 or _map_initial_selection_started or _map_active or _selection_active \
		or not _room_connection_ready or not _has_both_committed_choices():
		return
	if not _map_handshake_complete:
		_start_host_map_selection()


func _start_host_map_selection() -> void:
	if _slot != 0 or not _room_connection_ready or _map_active or _selection_active \
		or _selection_commit_busy or _busy or not _has_both_committed_choices():
		return
	var stage_id := str(_room_state.get("stage", ""))
	if not _stage_labels.has(stage_id):
		_show_error("unsupported_stage")
		return
	var session_id := Crypto.new().generate_random_bytes(16).hex_encode()
	_map_initial_selection_started = true
	if not _begin_map_selection_session(session_id, true, stage_id):
		return
	var snapshot := _map_pending_snapshot.duplicate(true)
	if not _valid_map_snapshot(snapshot, session_id):
		_end_map_selection_session(session_id, false)
		_show_error("invalid_map_snapshot")
		return
	if not _room_connection.send_peer_message("map_open", {"version": 1, "snapshot": snapshot}):
		_end_map_selection_session(session_id, true)
		_show_error("selection_channel_unavailable")
		return
	_status.text = "房主请选择地图；对手会同步观看。"


func _receive_map_open(message: Dictionary) -> void:
	if message.get("version") != 1 or not message.get("snapshot") is Dictionary:
		return
	var snapshot: Dictionary = message.snapshot
	var session_id := str(snapshot.get("sessionId", ""))
	if not _valid_map_snapshot(snapshot, session_id):
		return
	if _selection_active or not _has_both_committed_choices():
		_map_pending_open = message.duplicate(true)
		return
	if _map_active:
		if session_id == _map_session_id:
			_receive_map_snapshot({"version": 1, "snapshot": snapshot})
		return
	if not _begin_map_selection_session(session_id, false, str(snapshot.get("stageId", "")), snapshot):
		return
	_status.text = "房主正在选择地图。"


func _consume_pending_map_open() -> void:
	if _map_pending_open.is_empty() or _selection_active or _slot != 1 or not _has_both_committed_choices():
		return
	var pending := _map_pending_open.duplicate(true)
	_map_pending_open.clear()
	_receive_map_open(pending)


func _begin_map_selection_session(
	session_id: String, host_authority: bool, initial_stage_id: String,
	initial_snapshot: Dictionary = {}
) -> bool:
	if session_id.is_empty() or not _stage_labels.has(initial_stage_id) \
		or game_root == null or not is_instance_valid(game_root):
		return false
	if _map_adapter == null or not is_instance_valid(_map_adapter):
		var map_script := load("res://online_map_selection.gd") as Script
		if map_script == null:
			_show_error("map_selection_adapter_missing")
			return false
		_map_adapter = map_script.new() as Node
		if _map_adapter == null:
			_show_error("map_selection_adapter_invalid")
			return false
		_map_adapter.name = "OnlineMapSelection"
		var map_control := _map_adapter as Control
		map_control.z_index = 200
		map_control.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
		_map_adapter.connect("snapshot_changed", Callable(self, "_on_map_snapshot_changed"))
		_map_adapter.connect("selection_confirmed", Callable(self, "_on_map_selection_confirmed"))
		_map_adapter.connect("selection_cancelled", Callable(self, "_on_map_selection_cancelled"))
		game_root.add_child(_map_adapter)
	_map_session_id = session_id
	_map_host_authority = host_authority
	_map_active = true
	_map_cancel_waiting = false
	_map_committing = false
	_map_pending_snapshot.clear()
	_map_pending_configure.clear()
	_map_pending_commit.clear()
	_map_remote_ack.clear()
	_map_initializing = true
	_map_previous_root_physics = game_root.is_physics_processing()
	_map_root_restore_pending = _map_previous_root_physics
	game_root.set_physics_process(false)
	game_root.remove_meta("online_modal_open")
	_veil.visible = false
	_dialog.visible = false
	set_physics_process(true)
	var begin_error := str(_map_adapter.call("begin", session_id, host_authority, initial_stage_id))
	_map_initializing = false
	if not begin_error.is_empty():
		_end_map_selection_session(session_id, true)
		_show_error(begin_error)
		return false
	if not host_authority:
		if not _valid_map_snapshot(initial_snapshot, session_id) \
			or not bool(_map_adapter.call("apply_remote_snapshot", initial_snapshot)):
			_end_map_selection_session(session_id, true)
			_show_error("invalid_map_snapshot")
			return false
		_map_pending_snapshot = initial_snapshot.duplicate(true)
	else:
		var snapshot := _map_pending_snapshot.duplicate(true)
		if not _valid_map_snapshot(snapshot, session_id):
			_end_map_selection_session(session_id, true)
			_show_error("invalid_map_snapshot")
			return false
	_refresh_room_view()
	return true


func _on_map_snapshot_changed(snapshot: Dictionary) -> void:
	if not _map_active or not _map_host_authority \
		or str(snapshot.get("sessionId", "")) != _map_session_id \
		or not _valid_map_snapshot(snapshot, _map_session_id):
		return
	_map_pending_snapshot = snapshot.duplicate(true)
	if _map_initializing:
		return
	if _room_connection != null and _room_connection_ready:
		_room_connection.send_peer_message("map_snapshot", {"version": 1, "snapshot": snapshot})


func _receive_map_snapshot(message: Dictionary) -> void:
	if _slot != 1 or not _map_active or _map_host_authority \
		or message.get("version") != 1 or not message.get("snapshot") is Dictionary:
		return
	var snapshot: Dictionary = message.snapshot
	if not _valid_map_snapshot(snapshot, _map_session_id):
		return
	if bool(_map_adapter.call("apply_remote_snapshot", snapshot)):
		_map_pending_snapshot = snapshot.duplicate(true)


func _valid_map_snapshot(snapshot: Dictionary, expected_session_id: String) -> bool:
	var revision: Variant = snapshot.get("revision")
	var stage_id: Variant = snapshot.get("stageId")
	return snapshot.get("version") == 1 \
		and _valid_map_session_id(str(snapshot.get("sessionId", ""))) \
		and str(snapshot.get("sessionId", "")) == expected_session_id \
		and _wire_nonnegative_integer(revision) \
		and stage_id is String and _stage_labels.has(stage_id) \
		and typeof(snapshot.get("confirmed")) == TYPE_BOOL


func _valid_map_session_id(value: String) -> bool:
	if value.length() != 32:
		return false
	for character in value:
		if not (character in "0123456789abcdef"):
			return false
	return true


func _wire_nonnegative_integer(value: Variant) -> bool:
	if typeof(value) == TYPE_INT:
		return int(value) >= 0
	if typeof(value) == TYPE_FLOAT:
		var number := float(value)
		return is_finite(number) and number >= 0.0 and floor(number) == number
	return false


func _on_map_selection_confirmed(stage_id: String, session_id: String, revision: int) -> void:
	if not _map_active or not _map_host_authority or _map_committing \
		or session_id != _map_session_id or not _stage_labels.has(stage_id) or revision < 0:
		return
	var snapshot := _map_pending_snapshot
	if not bool(snapshot.get("confirmed", false)) \
		or int(snapshot.get("revision", -1)) != revision \
		or str(snapshot.get("stageId", "")) != stage_id:
		return
	_map_committing = true
	_map_pending_configure = {"sessionId": session_id, "stageId": stage_id, "revision": revision}
	_commit_host_map_selection.call_deferred(session_id, stage_id, revision)


func _commit_host_map_selection(session_id: String, stage_id: String, revision: int) -> void:
	if not _map_active or not _map_host_authority or session_id != _map_session_id \
		or _map_pending_configure.is_empty() or room_client == null:
		return
	var lifecycle_generation := _lifecycle_generation
	_map_committing = true
	_busy = true
	_status.text = "正在保存地图与房主规则…"
	_refresh_room_view()
	var latest_reply: Dictionary = await room_client.refresh_state()
	if lifecycle_generation != _lifecycle_generation or session_id != _map_session_id:
		return
	if latest_reply.has("error"):
		_finish_map_commit_failure(session_id, str(latest_reply.get("error", "service_error")))
		return
	var latest := _as_dictionary(latest_reply.get("state"))
	_accept_state(latest)
	if str(latest.get("phase", "")) != "lobby" or not _has_both_committed_choices():
		_finish_map_commit_failure(session_id, "room_not_in_lobby")
		return
	var desired_rules := _selected_rules()
	var desired_stage := stage_id
	var result: Dictionary = {}
	var stale_retries := 0
	while true:
		if lifecycle_generation != _lifecycle_generation or session_id != _map_session_id:
			return
		latest = _as_dictionary(room_client.get_room_state())
		if str(latest.get("phase", "")) != "lobby":
			_finish_map_commit_failure(session_id, "room_not_in_lobby")
			return
		if desired_stage == str(latest.get("stage", "")) \
			and _same_rules(desired_rules, _as_dictionary(latest.get("rules"))):
			result = {"state": latest}
			break
		result = await room_client.command({
			"type": "configure",
			"revision": int(latest.get("setupRevision", 0)),
			"stage": desired_stage,
			"rules": desired_rules.duplicate(true),
		})
		if lifecycle_generation != _lifecycle_generation or session_id != _map_session_id:
			return
		if not result.has("error"):
			break
		if bool(result.get("uncertain", false)):
			_map_pending_configure = {
				"sessionId": session_id, "stageId": desired_stage, "revision": revision,
				"rules": desired_rules.duplicate(true),
			}
			_busy = false
			_map_committing = false
			_show_command_error(result)
			_show_room()
			_status.text = "地图设置结果尚未确认；请重试同一操作。"
			_refresh_room_view()
			return
		if str(result.get("error", "")) == "stale_revision" and stale_retries < 1:
			stale_retries += 1
			latest_reply = await room_client.refresh_state()
			if lifecycle_generation != _lifecycle_generation or session_id != _map_session_id:
				return
			if latest_reply.has("error"):
				_finish_map_commit_failure(session_id, str(latest_reply.get("error")))
				return
			latest = _as_dictionary(latest_reply.get("state"))
			_accept_state(latest)
			continue
		_finish_map_commit_failure(session_id, str(result.get("error", "configure_failed")))
		return
	var committed_state := _as_dictionary(result.get("state", room_client.get_room_state()))
	if str(committed_state.get("stage", "")) != desired_stage \
		or not _same_rules(_as_dictionary(committed_state.get("rules")), desired_rules):
		_finish_map_commit_failure(session_id, "configured_state_mismatch")
		return
	_publish_host_map_commit(session_id, desired_stage, revision, desired_rules, committed_state)


func _publish_host_map_commit(
	session_id: String, stage_id: String, revision: int, rules: Dictionary, committed_state: Dictionary
) -> void:
	if not _map_active or not _map_host_authority or session_id != _map_session_id:
		return
	if str(committed_state.get("phase", "")) != "lobby" \
		or str(committed_state.get("stage", "")) != stage_id \
		or not _same_rules(_as_dictionary(committed_state.get("rules")), rules):
		_finish_map_commit_failure(session_id, "configured_state_mismatch")
		return
	_accept_state(committed_state)
	_dirty = false
	_rules_draft.clear()
	_busy = false
	_map_pending_configure.clear()
	var commit := {
		"version": 1,
		"sessionId": session_id,
		"revision": revision,
		"stageId": stage_id,
		"setupRevision": int(committed_state.get("setupRevision", 0)),
	}
	_map_pending_commit = commit
	_map_handshake_stage_id = stage_id
	_map_handshake_setup_revision = int(commit.setupRevision)
	_status.text = "地图已保存；等待对手确认。"
	_show_room()
	_send_map_committed()
	_refresh_room_view()


func _selected_rules() -> Dictionary:
	return _rules_draft.duplicate(true) if not _rules_draft.is_empty() else {
		"time": _selected_number(_time_choice),
		"life": _selected_number(_life_choice),
	}


func _same_rules(left: Dictionary, right: Dictionary) -> bool:
	if left.size() != 2 or right.size() != 2 \
		or not left.has("time") or not right.has("time") \
		or not left.has("life") or not right.has("life"):
		return false
	var left_time: Variant = left.get("time")
	var right_time: Variant = right.get("time")
	var left_life: Variant = left.get("life")
	var right_life: Variant = right.get("life")
	if not _wire_nonnegative_integer(left_time) or not _wire_nonnegative_integer(right_time) \
		or not _wire_nonnegative_integer(left_life) or not _wire_nonnegative_integer(right_life):
		return false
	var time := int(left_time)
	var life := int(left_life)
	return time == int(right_time) and life == int(right_life) \
		and time in [30, 60, 90, 100] and life in [1, 2, 3, 4, 5]


func _send_map_committed() -> void:
	if _map_pending_commit.is_empty() or _slot != 0 or _room_connection == null \
		or not _room_connection_ready:
		return
	_map_commit_delivery_pending = not _room_connection.send_peer_message(
		"map_committed", _map_pending_commit.duplicate(true)
	)
	if _map_commit_delivery_pending:
		_status.text = "地图已保存，正在等待连接恢复后通知对手。"
		_refresh_room_view()


func _valid_map_commit(message: Dictionary, session_id: String) -> bool:
	return message.get("version") == 1 \
		and str(message.get("sessionId", "")) == session_id \
		and _wire_nonnegative_integer(message.get("revision")) \
		and message.get("stageId") is String and _stage_labels.has(message.get("stageId")) \
		and _wire_nonnegative_integer(message.get("setupRevision"))


func _verify_guest_map_commit(message: Dictionary) -> void:
	if _map_commit_verifying or _slot != 1 or not _map_active or _map_host_authority \
		or str(message.get("sessionId", "")) != _map_session_id \
		or not _valid_map_commit(message, _map_session_id):
		return
	if not bool(_map_pending_snapshot.get("confirmed", false)) \
		or int(_map_pending_snapshot.get("revision", -1)) != int(message.get("revision", -2)) \
		or str(_map_pending_snapshot.get("stageId", "")) != str(message.get("stageId", "")):
		return
	_map_pending_commit = message.duplicate(true)
	_map_commit_verifying = true
	var reply: Dictionary = await room_client.refresh_state()
	if not _map_active or str(message.get("sessionId", "")) != _map_session_id:
		_map_commit_verifying = false
		return
	if reply.has("error"):
		_map_commit_verifying = false
		_map_ack_pending = true
		_show_command_error(reply)
		_show_room()
		_status.text = "地图已保存；网络恢复后可重试同步确认。"
		_refresh_room_view()
		return
	var state := _as_dictionary(reply.get("state"))
	_accept_state(state)
	if str(state.get("phase", "")) != "lobby" \
		or str(state.get("stage", "")) != str(message.get("stageId", "")) \
		or int(state.get("setupRevision", -1)) != int(message.get("setupRevision", -2)) \
		or not _has_both_committed_choices():
		_map_commit_verifying = false
		_map_ack_pending = true
		_show_room()
		_show_error("map_commit_not_visible")
		_refresh_room_view()
		return
	_map_commit_verifying = false
	_map_handshake_stage_id = str(message.get("stageId", ""))
	_map_handshake_setup_revision = int(message.get("setupRevision", -1))
	var ack := _map_pending_commit.duplicate(true)
	if _room_connection == null or not _room_connection_ready \
		or not _room_connection.send_peer_message("map_ack", ack):
		_map_ack_pending = true
		_show_room()
		_show_error("map_ack_pending")
		_refresh_room_view()
		return
	_map_ack_pending = false
	_status.text = "地图已与房间同步；等待房主确认。"


func _receive_map_ack(message: Dictionary) -> void:
	if not _map_active or not _map_host_authority or _map_pending_commit.is_empty() \
		or not _valid_map_commit(message, _map_session_id) \
		or not _same_map_commit(message, _map_pending_commit):
		return
	_map_remote_ack = message.duplicate(true)
	if _room_connection == null or not _room_connection_ready \
		or not _room_connection.send_peer_message("map_done", _map_pending_commit.duplicate(true)):
		_map_done_delivery_pending = true
		_status.text = "对手已确认地图；正在完成同步。"
		return
	_map_done_delivery_pending = false
	_complete_map_handshake(_map_session_id, _map_pending_commit)


func _receive_map_done(message: Dictionary) -> void:
	if not _map_active or _map_host_authority or _map_pending_commit.is_empty() \
		or not _valid_map_commit(message, _map_session_id) \
		or not _same_map_commit(message, _map_pending_commit):
		return
	_complete_map_handshake(_map_session_id, message)


func _same_map_commit(left: Dictionary, right: Dictionary) -> bool:
	return str(left.get("sessionId", "")) == str(right.get("sessionId", "")) \
		and int(left.get("revision", -1)) == int(right.get("revision", -2)) \
		and str(left.get("stageId", "")) == str(right.get("stageId", "")) \
		and int(left.get("setupRevision", -1)) == int(right.get("setupRevision", -2))


func _complete_map_handshake(session_id: String, commit: Dictionary) -> void:
	if not _map_active or session_id != _map_session_id:
		return
	_map_handshake_complete = true
	_map_handshake_setup_revision = int(commit.get("setupRevision", -1))
	_map_handshake_stage_id = str(commit.get("stageId", ""))
	_map_initial_selection_started = true
	_end_map_selection_session(session_id, true)
	_status.text = "地图已确认；双方可以准备。"
	_refresh_room_view()


func _on_map_selection_cancelled(session_id: String) -> void:
	if not _map_active or session_id != _map_session_id or _map_committing:
		return
	if _map_host_authority:
		if _room_connection != null and _room_connection_ready:
			_room_connection.send_peer_message("map_cancel", {"version": 1, "sessionId": session_id})
		_end_map_selection_session(session_id, true)
		_status.text = "已取消选图；房间设置保持不变。"
	else:
		_map_cancel_waiting = true
		if _room_connection != null and _room_connection_ready:
			_room_connection.send_peer_message("map_cancel_request", {"version": 1, "sessionId": session_id})
		_status.text = "已请求房主取消选图。"
	_refresh_room_view()


func _receive_map_cancel_request(message: Dictionary) -> void:
	if not _map_active or not _map_host_authority or _map_committing \
		or message.get("version") != 1 or str(message.get("sessionId", "")) != _map_session_id:
		return
	if not _room_connection.send_peer_message("map_cancel", {"version": 1, "sessionId": _map_session_id}):
		return
	_end_map_selection_session(_map_session_id, true)
	_status.text = "对手取消了选图；房间设置保持不变。"
	_refresh_room_view()


func _receive_map_cancel(message: Dictionary) -> void:
	if not _map_active or message.get("version") != 1 \
		or str(message.get("sessionId", "")) != _map_session_id:
		return
	_end_map_selection_session(_map_session_id, true)
	_status.text = "选图已取消；房间设置保持不变。"
	_refresh_room_view()


func _finish_map_commit_failure(session_id: String, code: String) -> void:
	_busy = false
	_map_committing = false
	if _map_active and _map_host_authority and session_id == _map_session_id \
		and _room_connection != null and _room_connection_ready:
		_room_connection.send_peer_message("map_cancel", {"version": 1, "sessionId": session_id})
	_end_map_selection_session(session_id, true)
	_show_error(code)
	_refresh_room_view()


func _end_map_selection_session(session_id: String, show_room: bool) -> void:
	if not _map_active or session_id != _map_session_id:
		return
	if _map_adapter != null and is_instance_valid(_map_adapter):
		_map_adapter.call("end_selection")
	if _map_root_restore_pending and game_root != null and is_instance_valid(game_root):
		game_root.set_physics_process(_map_previous_root_physics)
	_map_previous_root_physics = false
	_map_root_restore_pending = false
	_map_active = false
	_map_host_authority = false
	_map_cancel_waiting = false
	_map_committing = false
	_map_commit_verifying = false
	_map_ack_pending = false
	_map_commit_delivery_pending = false
	_map_done_delivery_pending = false
	_map_session_id = ""
	_map_pending_snapshot.clear()
	_map_pending_configure.clear()
	_map_pending_commit.clear()
	_map_remote_ack.clear()
	if not _match_started:
		set_physics_process(false)
	if show_room and not _room_id.is_empty():
		_show_room()


func _maybe_begin_initial_selection() -> void:
	if _slot != 0 or not _room_connection_ready or _selection_active or _selection_auto_started:
		return
	if _remote_connection_profile_id.is_empty():
		return
	if _remote_connection_profile_id != _local_connection_profile_id:
		_status.text = "双方网络档位不同；请返回房间调整后重新连接。"
		return
	_selection_auto_started = true
	_start_host_selection_session()


func _start_host_selection_session() -> void:
	if _slot != 0 or not _room_connection_ready or _selection_active or _selection_commit_busy:
		return
	_map_handshake_complete = false
	_map_handshake_setup_revision = -1
	_map_handshake_stage_id = ""
	_map_initial_selection_started = false
	if _remote_connection_profile_id != _local_connection_profile_id:
		_status.text = "双方网络档位不同；请先调整为相同档位。"
		return
	var members := _as_array(_room_state.get("members", []))
	if members.size() != 2 or not members[1] is Dictionary:
		return
	var initial_choices: Array = []
	for member in members:
		initial_choices.append(_as_dictionary(_as_dictionary(member).get("choice")).duplicate(true))
	var session_id := Crypto.new().generate_random_bytes(16).hex_encode()
	if not _room_connection.send_peer_message("selection_open", {
		"version": 1, "sessionId": session_id, "initialChoices": initial_choices,
	}):
		_show_error("selection_channel_unavailable")
		return
	if _begin_selection_session(session_id, initial_choices):
		_selection_auto_started = true


func _begin_selection_session(session_id: String, initial_choices: Array) -> bool:
	if session_id.is_empty() or _slot not in [0, 1] or _selection_active or _map_active \
		or _selection_commit_busy or game_root == null:
		return false
	if initial_choices.size() != 2:
		return false
	if _selection_adapter == null or not is_instance_valid(_selection_adapter):
		_selection_adapter = ONLINE_SELECTION.new()
		_selection_adapter.name = "OnlineCharacterSelection"
		_selection_adapter.z_index = 200
		_selection_adapter.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
		_selection_adapter.snapshot_changed.connect(_on_selection_snapshot_changed)
		_selection_adapter.selection_completed.connect(_on_selection_completed)
		_selection_adapter.selection_cancelled.connect(_on_selection_cancelled)
		game_root.add_child(_selection_adapter)
	_selection_session_id = session_id
	_selection_completed_choice.clear()
	_selection_owner_commit.clear()
	_selection_guest_commit.clear()
	_pending_selection_snapshot.clear()
	_selection_active = true
	_selection_previous_root_physics = game_root.is_physics_processing()
	_selection_root_restore_pending = _selection_previous_root_physics
	game_root.set_physics_process(false)
	set_physics_process(true)
	_veil.visible = false
	_dialog.visible = false
	game_root.remove_meta("online_modal_open")
	var issue := str(_selection_adapter.begin(_slot, session_id, initial_choices))
	if not issue.is_empty():
		_end_selection_session(false)
		_show_error(issue)
		return false
	_refresh_room_view()
	return true


func _on_selection_snapshot_changed(snapshot: Dictionary) -> void:
	if not _selection_active or str(snapshot.get("sessionId", "")) != _selection_session_id:
		return
	_pending_selection_snapshot = snapshot.duplicate(true)
	if _room_connection != null and _room_connection_ready:
		_room_connection.send_peer_message("selection_snapshot", snapshot)


func _on_selection_completed(choice: Dictionary) -> void:
	if not _selection_active or choice.is_empty():
		return
	_selection_completed_choice = choice.duplicate(true)
	_status.text = "正在保存双方选择…"
	_show_room()
	if _slot == 0:
		_commit_owner_selection()
	else:
		_maybe_commit_guest_selection()


func _on_selection_cancelled() -> void:
	if not _selection_active:
		return
	if _room_connection_ready:
		_room_connection.send_peer_message("selection_cancel", {"version": 1, "sessionId": _selection_session_id})
	_end_selection_session(false)
	_show_room()
	_status.text = "选人已取消；已确认选择保持不变。"
	_refresh_room_view()


func _end_selection_session(_notify_peer: bool = false) -> void:
	var was_active := _selection_active or _selection_root_restore_pending
	_end_selection_commit()
	if _selection_adapter != null and is_instance_valid(_selection_adapter):
		_selection_adapter.end_selection()
	if _selection_root_restore_pending and game_root != null and is_instance_valid(game_root):
		game_root.set_physics_process(_selection_previous_root_physics)
	_selection_previous_root_physics = false
	_selection_root_restore_pending = false
	_selection_active = false
	_selection_session_id = ""
	_pending_selection_snapshot.clear()
	_selection_completed_choice.clear()
	_selection_owner_commit.clear()
	_selection_guest_commit.clear()
	if not _match_started:
		set_physics_process(false)
	if was_active and _dialog != null and is_instance_valid(_dialog) and not _room_id.is_empty():
		_veil.visible = true
		_dialog.visible = true
		_room_view.visible = true
		_home_view.visible = false
		_match_view.visible = false
		if game_root != null and is_instance_valid(game_root):
			game_root.set_meta("online_modal_open", true)


func _close_room_connection() -> void:
	var had_connection := _room_connection != null or _room_connection_ready or _room_connection_starting
	_room_connection_generation += 1
	_room_connection_ready = false
	_room_connection_starting = false
	_local_connection_profile_id = ""
	_remote_connection_profile_id = ""
	_selection_auto_started = false
	if _map_active:
		_end_map_selection_session(_map_session_id, false)
	_map_pending_open.clear()
	_map_handshake_complete = false
	_map_handshake_setup_revision = -1
	_map_handshake_stage_id = ""
	_map_initial_selection_started = false
	_prepare_attempt_revision = -1
	_prepare_attempt_room_id = ""
	_prepare_attempt_generation = -1
	_prepare_success_revision = -1
	_prepare_success_room_id = ""
	_prepare_success_generation = -1
	_prepare_in_flight = false
	_prepare_retry_available = false
	_end_selection_session(false)
	if _room_connection != null and is_instance_valid(_room_connection):
		var old_connection := _room_connection
		_room_connection = null
		old_connection.close()
		old_connection.queue_free()
	else:
		_room_connection = null
	# Signaling belongs to lobby presence. Closing it on every attempt replaces the
	# socket and used to invalidate the in-flight negotiation. Match start and
	# leave clear presence first, and that path still closes the socket.
	if had_connection and not _lobby_signaling_desired and room_client != null \
		and is_instance_valid(room_client) and room_client.has_method("close_signaling"):
		room_client.close_signaling()


func _choice_label(choice: Dictionary) -> String:
	return str(_fighter_labels.get(str(choice.get("fighter", "")), "未选择"))


func _choice_helper_label(choice: Dictionary) -> String:
	return str(_helper_labels.get(str(choice.get("helper", "")), "未选择"))


func _commit_owner_selection() -> void:
	if _selection_commit_busy or _slot != 0 or not _valid_selection_choice(_selection_completed_choice):
		return
	_begin_selection_commit()
	var session_id := _selection_session_id
	var choice := _selection_completed_choice.duplicate(true)
	var result := await _submit_selection_choice(choice, session_id)
	if session_id != _selection_session_id or not _selection_active:
		_end_selection_commit()
		return
	_end_selection_commit()
	if result.has("error") and bool(result.get("uncertain", false)):
		_retry_button.visible = true
		_retry_button.text = "重试未确认操作"
		_show_error("command_outcome_uncertain")
		_show_room()
		_refresh_room_view()
		return
	if result.has("error"):
		_status.text = "房主角色未能提交，请重新选择后重试。"
		if _room_connection_ready:
			_room_connection.send_peer_message("selection_cancel", {"version": 1, "sessionId": session_id})
		_end_selection_session(false)
		_show_room()
		_refresh_room_view()
		return
	var committed_state := _as_dictionary(result.get("state"))
	var setup_revision := int(committed_state.get("setupRevision", 0))
	_accept_state(committed_state)
	var commit := {
		"version": 1,
		"sessionId": session_id,
		"setupRevision": setup_revision,
		"choice": choice,
	}
	_selection_owner_commit[session_id] = commit
	if _room_connection == null or not _room_connection_ready \
		or not _room_connection.send_peer_message("selection_owner_committed", commit):
		_status.text = "房主选择已保存；正在等待对手同步确认。"
	_refresh_room_view()
	_maybe_finish_selection_from_room_state()


func _maybe_commit_guest_selection() -> void:
	if _slot != 1 or _selection_commit_busy or not _selection_active \
		or not _valid_selection_choice(_selection_completed_choice) \
		or not _selection_owner_commit.has(_selection_session_id):
		return
	_begin_selection_commit()
	var session_id := _selection_session_id
	var choice := _selection_completed_choice.duplicate(true)
	var result := await _submit_selection_choice(choice, session_id)
	if session_id != _selection_session_id or not _selection_active:
		_end_selection_commit()
		return
	_end_selection_commit()
	if result.has("error") and bool(result.get("uncertain", false)):
		_retry_button.visible = true
		_retry_button.text = "重试未确认操作"
		_show_error("command_outcome_uncertain")
		_show_room()
		_refresh_room_view()
		return
	if result.has("error"):
		_status.text = "你的角色未能提交，请重新选择后重试。"
		if _room_connection_ready:
			_room_connection.send_peer_message("selection_cancel", {"version": 1, "sessionId": session_id})
		_end_selection_session(false)
		_show_room()
		_refresh_room_view()
		return
	var committed_state := _as_dictionary(result.get("state"))
	_accept_state(committed_state)
	var commit := {
		"version": 1,
		"sessionId": session_id,
		"setupRevision": int(committed_state.get("setupRevision", 0)),
		"choice": choice,
	}
	_selection_guest_commit[session_id] = commit
	if _room_connection != null and _room_connection_ready:
		_room_connection.send_peer_message("selection_guest_committed", commit)
	_maybe_finish_selection_from_room_state()
	_refresh_room_view()


func _submit_selection_choice(choice: Dictionary, session_id: String) -> Dictionary:
	if not _valid_selection_choice(choice) or room_client == null:
		return {"error": "invalid_selection_choice"}
	var connection_generation := _room_connection_generation
	var stale_retries := 0
	var result: Dictionary
	var operation: Dictionary
	var refresh := await room_client.refresh_state()
	if connection_generation != _room_connection_generation or session_id != _selection_session_id:
		return {"error": "selection_cancelled"}
	if refresh.has("error"):
		return refresh
	_accept_state(refresh.get("state"))
	var latest := _as_dictionary(refresh.get("state"))
	while true:
		if connection_generation != _room_connection_generation or session_id != _selection_session_id:
			return {"error": "selection_cancelled"}
		if str(latest.get("phase", "")) != "lobby":
			return {"error": "room_not_in_lobby"}
		var members := _as_array(latest.get("members", []))
		if members.size() != 2 or not members[0] is Dictionary or not members[1] is Dictionary:
			return {"error": "room_member_missing"}
		var local_member := _as_dictionary(members[_slot])
		var current_choice := _as_dictionary(local_member.get("choice"))
		if current_choice == choice:
			return {"state": latest, "accepted": true}
		if room_client.has_uncertain_command():
			return {"error": "unrelated_pending_command", "uncertain": true}
		operation = {
			"type": "select",
			"revision": int(latest.get("setupRevision", 0)),
			"choice": choice.duplicate(true),
		}
		result = await room_client.command(operation)
		if connection_generation != _room_connection_generation or session_id != _selection_session_id:
			return {"error": "selection_cancelled"}
		if not result.has("error"):
			_accept_state(result.get("state"))
			return result
		if bool(result.get("uncertain", false)):
			var retry_count := 0
			while retry_count < 5 and bool(result.get("uncertain", false)):
				retry_count += 1
				await get_tree().create_timer(0.5).timeout
				if connection_generation != _room_connection_generation or session_id != _selection_session_id:
					return {"error": "selection_cancelled"}
				result = await room_client.retry_pending_command()
				if connection_generation != _room_connection_generation or session_id != _selection_session_id:
					return {"error": "selection_cancelled"}
			if not result.has("error"):
				_accept_state(result.get("state"))
				return result
			return result
		if str(result.get("error", "")) != "stale_revision" or stale_retries >= 1:
			return result
		stale_retries += 1
		refresh = await room_client.refresh_state()
		if connection_generation != _room_connection_generation or session_id != _selection_session_id:
			return {"error": "selection_cancelled"}
		if refresh.has("error"):
			return refresh
		_accept_state(refresh.get("state"))
		latest = _as_dictionary(refresh.get("state"))
	return {"error": "selection_retry_exhausted"}


func _valid_selection_choice(choice: Dictionary) -> bool:
	var fighter := str(choice.get("fighter", ""))
	var helper := str(choice.get("helper", ""))
	return not fighter.is_empty() and _fighter_labels.has(fighter) \
		and not helper.is_empty() and _helper_labels.has(helper)


func _begin_selection_commit() -> void:
	if _selection_commit_busy:
		return
	_selection_busy_previous = _busy
	_selection_commit_busy = true
	_busy = true


func _end_selection_commit() -> void:
	if not _selection_commit_busy:
		return
	_selection_commit_busy = false
	_busy = _selection_busy_previous
	_selection_busy_previous = false


func _maybe_finish_selection_from_room_state() -> void:
	if not _selection_active or _selection_commit_busy or not _valid_selection_choice(_selection_completed_choice):
		return
	var session_id := _selection_session_id
	var local_commit: Dictionary = _as_dictionary(
		_selection_owner_commit.get(session_id) if _slot == 0 else _selection_guest_commit.get(session_id)
	)
	if not _valid_selection_commit(local_commit):
		return
	var remote_commit: Dictionary = _as_dictionary(
		_selection_owner_commit.get(session_id) if _slot == 1 else _selection_guest_commit.get(session_id)
	)
	if not _valid_selection_commit(remote_commit) or not _valid_selection_choice(_as_dictionary(remote_commit.get("choice"))):
		return
	var members := _as_array(_room_state.get("members", []))
	if members.size() != 2 or not members[0] is Dictionary or not members[1] is Dictionary:
		return
	var local_choice := _as_dictionary(_as_dictionary(members[_slot]).get("choice"))
	var remote_choice := _as_dictionary(_as_dictionary(members[1 - _slot]).get("choice"))
	if local_choice != _selection_completed_choice or remote_choice != _as_dictionary(remote_commit.get("choice")):
		return
	_end_selection_session(false)
	_show_room()
	_status.text = "双方已确认角色与援助，可以准备对局。"
	_refresh_room_view()
	_consume_pending_map_open()
	_maybe_start_initial_map_selection()


func _show_room() -> void:
	_veil.visible = true
	_dialog.visible = true
	_home_view.visible = false
	_home_footer.visible = false
	_room_view.visible = true
	_match_view.visible = false
	_match_hud.visible = false
	if game_root != null and is_instance_valid(game_root):
		game_root.set_physics_process(false)
		game_root.set_meta("online_modal_open", true)
	_refresh_room_view()


func _accept_state(state: Variant) -> void:
	if not state is Dictionary:
		return
	var incoming: Dictionary = state.duplicate(true)
	if not _room_id.is_empty() and str(incoming.get("id", "")) != _room_id:
		return
	if str(_room_state.get("id", "")) == str(incoming.get("id", "")) \
		and int(incoming.get("revision", -1)) < int(_room_state.get("revision", -1)):
		return
	var next_network_profile := _network_profile_from_state(incoming)
	if next_network_profile.is_empty():
		_show_error("server_upgrade_required")
		return
	var previous_network_profile := _network_profile_authority.duplicate(true)
	_room_state = incoming
	_network_profile_authority = next_network_profile.duplicate(true)
	if not previous_network_profile.is_empty() \
		and not _same_network_profile(previous_network_profile, next_network_profile):
		var matches_pending := not _pending_network_profile.is_empty() \
			and _same_network_profile(_pending_network_profile, next_network_profile)
		_close_room_connection()
		if not matches_pending:
			_pending_network_profile.clear()
			_profile_draft_dirty = false
			_status.text = "房主网络设置已更新；旧连接和准备状态已清除。"
	if _map_handshake_complete and (
		int(_room_state.get("setupRevision", -1)) != _map_handshake_setup_revision
		or str(_room_state.get("stage", "")) != _map_handshake_stage_id
	):
		_map_handshake_complete = false
	_maybe_finish_selection_from_room_state()
	if _dialog != null and _dialog.visible:
		_refresh_room_view()
	if str(_room_state.get("phase", "")) == "preparing":
		_status.text = "双方正在建立连接并核对开局状态，请稍候…"
		var match_state := _as_dictionary(_room_state.get("match"))
		var epoch := str(match_state.get("epoch", ""))
		if not _startup_cancel_requested and not epoch.is_empty() and epoch != _starting_epoch:
			_start_prepared_match.call_deferred(_room_state.duplicate(true))
	elif str(_room_state.get("phase", "")) == "lobby":
		_maybe_accept_connection_request.call_deferred()
		_maybe_auto_prepare.call_deferred()
		_refresh_lobby_presence_status(false)


func _maybe_accept_connection_request() -> void:
	if _slot != 1 or _room_id.is_empty() or _room_state.get("phase") != "lobby" \
		or _busy or _startup_busy or _room_connection_starting or _room_connection_ready \
		or _selection_active or _selection_commit_busy or _map_active \
		or _profile_draft_dirty or not _pending_network_profile.is_empty():
		return
	if room_client == null or room_client.has_uncertain_command() or room_client.is_command_in_flight():
		return
	var members := _as_array(_room_state.get("members"))
	var negotiation := _as_dictionary(_room_state.get("negotiation"))
	if members.size() != 2 or not members[0] is Dictionary or not members[1] is Dictionary \
		or negotiation.get("epoch") != null or str(negotiation.get("id", "")).is_empty() \
		or float(negotiation.get("expires", 0)) <= Time.get_unix_time_from_system() * 1000.0:
		return
	var request_key := _room_id + ":" + str(negotiation.id)
	if request_key == _auto_connection_request:
		return
	# Polling can discover the host before this guest has a signaling socket.
	# Try each request once; a failed request must not cause a reconnect loop.
	_auto_connection_request = request_key
	await _start_room_connection()


func _on_room_state_changed(state: Dictionary) -> void:
	_accept_state(state)
	if str(state.get("phase", "")) == "closed":
		_stop_lobby_presence()
		_close_room_connection()
		_show_error("room_closed")


func _on_signaling_message(message: Dictionary) -> void:
	if message.get("type") == "socket_closed":
		_match_status.text = "房间信令已断开；正在等待恢复。"


func _on_socket_state_changed(connected: bool) -> void:
	_signal_connected = connected
	if _retry_button != null:
		_retry_button.visible = room_client != null and room_client.has_uncertain_command()
	if connected:
		_lobby_reconnect_attempt = 0
		_lobby_reconnect_wait = 0.0
		_refresh_lobby_presence_status(false)
	elif _lobby_signaling_desired and not _lobby_signaling_in_flight and _lobby_reconnect_wait <= 0.0 \
		and not _room_connection_starting and not _room_connection_ready:
		_schedule_lobby_reconnect()
		if _can_show_lobby_presence_status() and (
			_status_is_lobby_presence() or _status.text.begins_with("信令已断开")
		):
			_status.text = "信令已断开，约 %d 秒后重新连接。" % int(ceili(_lobby_reconnect_wait))


func _on_room_error(code: String) -> void:
	_show_error(code)


func _refresh_room_view() -> void:
	if _room_view == null or _room_state.is_empty():
		return
	var members := _as_array(_room_state.get("members", []))
	var local_member := _as_dictionary(members[_slot]) if _slot >= 0 and _slot < members.size() else {}
	var remote_slot := 1 - _slot
	var remote_member := _as_dictionary(members[remote_slot]) if remote_slot >= 0 and remote_slot < members.size() else {}
	var owner := _slot == 0
	var lobby_phase := str(_room_state.get("phase", "")) == "lobby"
	var local_ready := bool(local_member.get("ready", false))
	var remote_ready := bool(remote_member.get("ready", false))
	var any_ready := local_ready or remote_ready
	var has_both_members := members.size() == 2 \
		and members[0] is Dictionary and members[1] is Dictionary
	var both_choices := _has_both_committed_choices()
	_member_status.text = "房间 %s\n玩家1 %s　%s　·　玩家2 %s　%s" % [
		_room_id.substr(0, 12),
		_member_name(members, 0), _member_ready(members, 0),
		_member_name(members, 1), _member_ready(members, 1),
	]
	_invitation_row.visible = owner
	_copy_invite_button.visible = owner
	_room_code_output.text = _invite_code if not _invite_code.is_empty() else "等待加入码"
	_rotate_invite_button.visible = owner
	_rotate_invite_button.disabled = _busy or room_client.has_uncertain_command()
	if not _dirty and not _busy:
		_sync_network_profile_controls_from_state()
	_sync_network_profile_controls_from_state()
	var local_choice := _as_dictionary(local_member.get("choice"))
	var remote_choice := _as_dictionary(remote_member.get("choice"))
	var player_one_choice := _as_dictionary(_as_dictionary(members[0]).get("choice")) if members.size() > 0 else {}
	var player_two_choice := _as_dictionary(_as_dictionary(members[1]).get("choice")) if members.size() > 1 else {}
	_roster_status.text = "玩家1 %s / %s · 玩家2 %s / %s" % [
		_choice_label(player_one_choice), _choice_helper_label(player_one_choice),
		_choice_label(player_two_choice), _choice_helper_label(player_two_choice),
	]
	var network_profile := _authoritative_network_profile()
	var network_profile_id := str(network_profile.get("id", ""))
	var connection_profiles_match := not _local_connection_profile_id.is_empty() \
		and _local_connection_profile_id == _remote_connection_profile_id \
		and _local_connection_profile_id == network_profile_id
	_profile_status.text = "输入延迟 %d 帧 · 预测上限 %d 帧（房主统一设置）\n%s" % [
		int(network_profile.get("inputDelay", 0)), int(network_profile.get("predictionWindow", 0)),
		"已连接到房主设置" if connection_profiles_match else "请按房主设置重新连接",
	]
	_profile_status.text += "\n连接方式：" + ("本机 / 同一局域网" if network_profile_id.ends_with("-lan") else "互联网连接（需服务配置中转）")
	var stage_id := str(_room_state.get("stage", ""))
	var rules := _as_dictionary(_room_state.get("rules"))
	var stage_name := str(_stage_labels.get(stage_id, "未确认地图"))
	_stage_summary.text = "%s · %d秒 · 生命×%d" % [
		stage_name, int(rules.get("time", 90)), int(rules.get("life", 1)),
	]
	if not network_profile.is_empty():
		_stage_summary.text += "\n网络：延迟%d帧 · 预测%d帧 · %s" % [
			int(network_profile.get("inputDelay", 0)),
			int(network_profile.get("predictionWindow", 0)),
			"局域网" if network_profile_id.ends_with("-lan") else "互联网",
		]
	_stage_summary.text += "\n" + _roster_status.text
	_owner_settings.visible = owner
	_time_choice.disabled = _busy or _selection_active or _map_active or not lobby_phase
	_life_choice.disabled = _busy or _selection_active or _map_active or not lobby_phase
	var network_profile_busy := _busy or _room_connection_starting \
		or not _pending_network_profile.is_empty() \
		or (room_client != null and (room_client.has_uncertain_command() or room_client.is_command_in_flight()))
	var can_edit_network_profile := owner and lobby_phase and not network_profile_busy \
		and not _selection_active and not _selection_commit_busy and not _map_active and not _map_committing
	_delay_choice.disabled = not can_edit_network_profile
	_prediction_choice.disabled = not can_edit_network_profile
	_lan_candidate_opt_in.disabled = not can_edit_network_profile
	var map_matches_state := _map_handshake_complete \
		and _map_handshake_setup_revision == int(_room_state.get("setupRevision", -1)) \
		and _map_handshake_stage_id == stage_id
	var common_gate := lobby_phase and not _busy and not network_profile_busy and not _selection_active \
		and not _selection_commit_busy and not _map_active and not _map_committing
	var local_choice_ok := _valid_selection_choice(local_choice)
	var remote_choice_ok := _valid_selection_choice(remote_choice)
	var ready_gate := common_gate and not _dirty and not _profile_draft_dirty \
		and both_choices and map_matches_state and _room_connection_ready \
		and connection_profiles_match and local_choice_ok and remote_choice_ok \
		and has_both_members
	if not lobby_phase or _busy or _selection_active or _selection_commit_busy or _map_active:
		_room_primary_action = ""
		_connect_selection_button.visible = false
	else:
		_connect_selection_button.visible = true
		if not _room_connection_ready:
			_room_primary_action = "connect"
			_connect_selection_button.text = "连接并选择角色" if not _room_connection_starting else "正在连接…"
			_connect_selection_button.disabled = _busy or network_profile_busy or _profile_draft_dirty \
				or _room_connection_starting or not has_both_members \
				or remote_member.is_empty()
		elif not both_choices or not map_matches_state or not connection_profiles_match or _dirty:
			if owner and both_choices and map_matches_state and _dirty:
				_room_primary_action = "wait"
				_connect_selection_button.text = "先应用规则并选图"
				_connect_selection_button.disabled = true
			else:
				_room_primary_action = "wait"
				_connect_selection_button.text = "等待房主选图" if _slot == 1 else "请选择地图"
				_connect_selection_button.disabled = true
		elif local_ready and remote_ready and owner:
			if _prepare_retry_available:
				_room_primary_action = "retry_prepare"
				_connect_selection_button.text = "重试开局"
				_connect_selection_button.disabled = not ready_gate
			else:
				_room_primary_action = "wait"
				_connect_selection_button.text = "正在开始对局…"
				_connect_selection_button.disabled = true
		else:
			_room_primary_action = "ready"
			_connect_selection_button.text = "取消准备" if local_ready else "准备"
			_connect_selection_button.disabled = not ready_gate
	_setup_button.visible = owner and lobby_phase and _room_connection_ready and both_choices \
		and not _selection_active and not _map_active and not _selection_commit_busy
	_setup_button.text = "应用规则并选图" if _dirty else "改选地图"
	_setup_button.disabled = _busy or network_profile_busy or _profile_draft_dirty \
		or _map_committing or (local_ready and remote_ready and not owner)
	_reselect_button.visible = lobby_phase and _room_connection_ready and both_choices \
		and not _selection_active and not _map_active
	_reselect_button.disabled = _busy or network_profile_busy or _selection_commit_busy or not has_both_members
	_leave_button.disabled = _busy or not lobby_phase
	_retry_button.visible = room_client != null and room_client.has_uncertain_command() \
		or _prepare_retry_available or _map_ack_pending or _map_commit_delivery_pending or _map_done_delivery_pending
	if not _pending_network_profile.is_empty():
		_retry_button.text = "重试网络设置"
	elif _map_ack_pending:
		_retry_button.text = "重试地图同步"
	elif _map_commit_delivery_pending or _map_done_delivery_pending:
		_retry_button.text = "重试地图通知"
	elif _prepare_retry_available:
		_retry_button.text = "重试开局"
	if _advanced_toggle != null:
		_advanced_toggle.disabled = _busy or _selection_active or _map_active


func _sync_options_from_state() -> void:
	if _room_state.is_empty():
		return
	var rules := _as_dictionary(_room_state.get("rules"))
	_select_number(_time_choice, int(rules.get("time", 90)))
	_select_number(_life_choice, int(rules.get("life", 1)))
	_rules_draft = {"time": int(rules.get("time", 90)), "life": int(rules.get("life", 1))}


func _sync_network_profile_controls_from_state() -> void:
	var profile := _authoritative_network_profile()
	if not profile.is_empty() and (_slot != 0 or not _profile_draft_dirty):
		_select_number(_delay_choice, int(profile.get("inputDelay", 2)))
		_select_number(_prediction_choice, int(profile.get("predictionWindow", 6)))
		_lan_candidate_opt_in.set_pressed_no_signal(str(profile.get("id", "")).ends_with("-lan"))
		if _slot != 0:
			_profile_draft_dirty = false


func _on_setup_picker_changed(_index: int) -> void:
	if not _busy and not _selection_active and not _selection_commit_busy:
		_dirty = true
		_rules_draft = {
			"time": _selected_number(_time_choice),
			"life": _selected_number(_life_choice),
		}
		_refresh_room_view()


func _on_advanced_toggled(visible: bool) -> void:
	if _advanced_settings != null:
		_advanced_settings.visible = visible


func _on_room_primary_pressed() -> void:
	match _room_primary_action:
		"connect":
			await _on_connect_selection_pressed()
		"ready":
			await _on_ready_pressed()
		"retry_prepare":
			await _retry_auto_prepare()
		_:
			return


func _on_profile_picker_changed(_index: int) -> void:
	await _commit_network_profile_from_controls()


func _on_profile_option_toggled(_pressed: bool) -> void:
	await _commit_network_profile_from_controls()


func _commit_network_profile_from_controls() -> void:
	if _slot != 0 or _busy or _room_connection_starting or _room_state.is_empty() \
		or str(_room_state.get("phase", "")) != "lobby":
		_profile_draft_dirty = false
		_sync_network_profile_controls_from_state()
		_refresh_room_view()
		return
	if room_client == null or room_client.has_uncertain_command() or room_client.is_command_in_flight():
		_profile_draft_dirty = false
		_sync_network_profile_controls_from_state()
		_show_error("command_outcome_uncertain")
		_refresh_room_view()
		return
	var desired := _current_network_profile()
	var current := _authoritative_network_profile()
	if current.is_empty():
		_profile_draft_dirty = false
		_sync_network_profile_controls_from_state()
		_show_error("server_upgrade_required")
		_refresh_room_view()
		return
	if _same_network_profile(desired, current):
		_profile_draft_dirty = false
		_refresh_room_view()
		return
	_profile_draft_dirty = true
	_pending_network_profile = desired.duplicate(true)
	var request_generation := _lifecycle_generation
	var request_room_id := _room_id
	var setup_revision := int(_room_state.get("setupRevision", -1))
	_close_room_connection()
	_busy = true
	_status.text = "正在同步房主网络设置…"
	_refresh_room_view()
	var response: Dictionary = await room_client.command({
		"type": "configure_network",
		"revision": setup_revision,
		"profile": desired.duplicate(true),
	})
	if request_generation != _lifecycle_generation or request_room_id != _room_id:
		return
	_busy = false
	if response.has("error"):
		if bool(response.get("uncertain", false)):
			_show_command_error(response)
		else:
			_pending_network_profile.clear()
			_profile_draft_dirty = false
			_accept_state(room_client.get_room_state())
			_sync_network_profile_controls_from_state()
			_show_command_error(response)
		_refresh_room_view()
		return
	_accept_state(response.get("state"))
	var authoritative := _authoritative_network_profile()
	_pending_network_profile.clear()
	_profile_draft_dirty = false
	_sync_network_profile_controls_from_state()
	if not _same_network_profile(authoritative, desired):
		_show_error("network_profile_changed")
	else:
		_status.text = "房主网络设置已同步；双方需要重新连接并准备。"
	_refresh_room_view()


func _retry_pending_network_profile() -> void:
	if _busy or _pending_network_profile.is_empty() or not room_client.has_uncertain_command():
		return
	_busy = true
	var request_generation := _lifecycle_generation
	var request_room_id := _room_id
	_refresh_room_view()
	var response: Dictionary = await room_client.retry_pending_command()
	if request_generation != _lifecycle_generation or request_room_id != _room_id:
		return
	_busy = false
	if response.has("error"):
		if not bool(response.get("uncertain", false)):
			_pending_network_profile.clear()
			_profile_draft_dirty = false
			_accept_state(room_client.get_room_state())
			_sync_network_profile_controls_from_state()
		_show_command_error(response)
		_refresh_room_view()
		return
	_accept_state(response.get("state"))
	var expected_profile := _pending_network_profile.duplicate(true)
	var authoritative := _authoritative_network_profile()
	_pending_network_profile.clear()
	_profile_draft_dirty = false
	_sync_network_profile_controls_from_state()
	if _same_network_profile(authoritative, expected_profile):
		_status.text = "房主网络设置已同步；双方需要重新连接并准备。"
	else:
		_show_error("network_profile_changed")
	_refresh_room_view()


func _on_commit_setup_pressed() -> void:
	if _busy or _selection_active or _selection_commit_busy or _map_active \
		or _slot != 0 or _room_state.is_empty():
		return
	_start_host_map_selection()


func _on_ready_pressed() -> void:
	if _busy or _selection_active or _selection_commit_busy or _map_active or _room_state.is_empty():
		return
	var profile := _authoritative_network_profile()
	if profile.is_empty():
		_show_error("server_upgrade_required")
		return
	var members := _as_array(_room_state.get("members", []))
	var local_member := _as_dictionary(members[_slot]) if _slot >= 0 and _slot < members.size() else {}
	var ready := not bool(local_member.get("ready", false))
	if ready and not _can_ready_current_room():
		return
	await _submit_operation({
		"type": "ready", "revision": int(_room_state.get("setupRevision", 0)),
		"ready": ready, "profile": profile.duplicate(true),
	})


func _on_start_pressed() -> void:
	if _busy or _selection_active or _selection_commit_busy or _map_active or _slot != 0 \
		or not _can_prepare_current_room():
		return
	await _submit_operation({"type": "prepare", "revision": int(_room_state.get("setupRevision", 0))})


func _map_handshake_matches_room() -> bool:
	return _map_handshake_complete \
		and _map_handshake_setup_revision == int(_room_state.get("setupRevision", -1)) \
		and _map_handshake_stage_id == str(_room_state.get("stage", ""))


func _can_ready_current_room() -> bool:
	var profile := _authoritative_network_profile()
	if profile.is_empty() or _profile_draft_dirty or not _pending_network_profile.is_empty():
		return false
	return str(_room_state.get("phase", "")) == "lobby" \
		and not _dirty and not _selection_active and not _selection_commit_busy and not _map_active \
		and _room_connection_ready and _local_connection_profile_id == _remote_connection_profile_id \
		and not _local_connection_profile_id.is_empty() \
		and _local_connection_profile_id == str(profile.get("id", "")) \
		and (_slot != 0 or _same_network_profile(_current_network_profile(), profile)) \
		and _map_handshake_matches_room() \
		and _has_both_committed_choices()


func _can_prepare_current_room() -> bool:
	if _slot != 0 or not _can_ready_current_room():
		return false
	var members := _as_array(_room_state.get("members", []))
	if members.size() != 2 or not members[0] is Dictionary or not members[1] is Dictionary:
		return false
	var first := _as_dictionary(members[0])
	var second := _as_dictionary(members[1])
	var first_profile := _as_dictionary(first.get("profile"))
	var second_profile := _as_dictionary(second.get("profile"))
	var authority := _authoritative_network_profile()
	return bool(first.get("ready", false)) and bool(second.get("ready", false)) \
		and not authority.is_empty() and _same_network_profile(first_profile, authority) \
		and _same_network_profile(second_profile, authority)


func _maybe_auto_prepare(explicit_retry: bool = false) -> void:
	if _slot != 0 or str(_room_state.get("phase", "")) != "lobby":
		return
	var room_id := _room_id
	var setup_revision := int(_room_state.get("setupRevision", -1))
	if not _can_prepare_current_room():
		if not _prepare_in_flight:
			_prepare_attempt_revision = -1
			_prepare_attempt_room_id = ""
			_prepare_attempt_generation = -1
			_prepare_retry_available = false
		return
	if _busy or _prepare_in_flight or _startup_busy \
		or (_prepare_success_room_id == room_id \
		and _prepare_success_generation == _lifecycle_generation \
		and _prepare_success_revision == setup_revision):
		return
	if not explicit_retry and _prepare_attempt_room_id == room_id \
		and _prepare_attempt_generation == _lifecycle_generation \
		and _prepare_attempt_revision == setup_revision:
		return
	if room_client == null or not is_instance_valid(room_client) \
		or room_client.has_uncertain_command() or room_client.is_command_in_flight():
		return
	_prepare_attempt_revision = setup_revision
	_prepare_attempt_room_id = room_id
	_prepare_attempt_generation = _lifecycle_generation
	_prepare_retry_available = false
	_prepare_in_flight = true
	_auto_prepare_request.call_deferred(setup_revision, room_id, _lifecycle_generation)


func _auto_prepare_request(expected_revision: int, expected_room_id: String, generation: int) -> void:
	if generation != _lifecycle_generation or expected_room_id.is_empty() \
		or expected_room_id != _room_id or _prepare_success_room_id == expected_room_id \
		and _prepare_success_generation == generation \
		and _prepare_success_revision == expected_revision:
		_clear_prepare_attempt_if_current(expected_revision, expected_room_id, generation)
		return
	if not _prepare_in_flight or _prepare_attempt_room_id != expected_room_id \
		or _prepare_attempt_generation != generation \
		or _prepare_attempt_revision != expected_revision:
		return
	if _busy or _startup_busy or room_client == null or not is_instance_valid(room_client) \
		or room_client.has_uncertain_command() or room_client.is_command_in_flight():
		_clear_prepare_attempt_if_current(expected_revision, expected_room_id, generation)
		return
	if str(_room_state.get("phase", "")) != "lobby" \
		or int(_room_state.get("setupRevision", -1)) != expected_revision \
		or not _can_prepare_current_room():
		_clear_prepare_attempt_if_current(expected_revision, expected_room_id, generation)
		if _can_prepare_current_room():
			_maybe_auto_prepare.call_deferred()
		return
	_busy = true
	_status.text = "双方已准备，正在自动开始对局…"
	_refresh_room_view()
	var latest_reply: Dictionary = await room_client.refresh_state()
	if generation != _lifecycle_generation or expected_room_id != _room_id:
		return
	if latest_reply.has("error"):
		_prepare_in_flight = false
		_busy = false
		_prepare_retry_available = true
		_show_command_error(latest_reply)
		_refresh_room_view()
		return
	var latest := _as_dictionary(latest_reply.get("state"))
	_accept_state(latest)
	if str(latest.get("phase", "")) != "lobby" \
		or int(latest.get("setupRevision", -1)) != expected_revision \
		or not _can_prepare_current_room():
		_prepare_in_flight = false
		_busy = false
		_prepare_attempt_revision = -1
		_prepare_attempt_room_id = ""
		_prepare_attempt_generation = -1
		_refresh_room_view()
		if _can_prepare_current_room():
			_maybe_auto_prepare.call_deferred()
		return
	if room_client.has_uncertain_command() or room_client.is_command_in_flight():
		_clear_prepare_attempt_if_current(expected_revision, expected_room_id, generation)
		_busy = false
		_prepare_retry_available = false
		_refresh_room_view()
		return
	var result: Dictionary = await room_client.command({"type": "prepare", "revision": expected_revision})
	if generation != _lifecycle_generation or expected_room_id != _room_id:
		return
	_prepare_in_flight = false
	if result.has("error"):
		_busy = false
		_prepare_retry_available = true
		_show_command_error(result)
		_refresh_room_view()
		return
	var prepared_state := _as_dictionary(result.get("state"))
	if str(prepared_state.get("phase", "")) != "preparing":
		_busy = false
		_prepare_retry_available = true
		_accept_state(prepared_state)
		_status.text = "双方准备状态已变化；刷新房间后可重试。"
		_refresh_room_view()
		return
	_prepare_success_revision = expected_revision
	_prepare_success_room_id = expected_room_id
	_prepare_success_generation = generation
	_prepare_retry_available = false
	_startup_busy = true
	_busy = true
	_accept_state(prepared_state)
	_refresh_room_view()


func _clear_prepare_attempt_if_current(expected_revision: int, expected_room_id: String, generation: int) -> void:
	if _prepare_attempt_revision != expected_revision or _prepare_attempt_room_id != expected_room_id \
		or _prepare_attempt_generation != generation:
		return
	_prepare_in_flight = false
	_prepare_attempt_revision = -1
	_prepare_attempt_room_id = ""
	_prepare_attempt_generation = -1


func _retry_auto_prepare() -> void:
	if _busy or _slot != 0 or not _prepare_retry_available:
		return
	if room_client.has_uncertain_command():
		_busy = true
		var result: Dictionary = await room_client.retry_pending_command()
		_busy = false
		if result.has("error"):
			_show_command_error(result)
			_refresh_room_view()
			return
		var state := _as_dictionary(result.get("state"))
		if str(state.get("phase", "")) == "preparing":
			_prepare_success_revision = int(state.get("setupRevision", -1))
			_prepare_success_room_id = _room_id
			_prepare_success_generation = _lifecycle_generation
			_prepare_retry_available = false
			_startup_busy = true
			_busy = true
		_accept_state(state)
		_refresh_room_view()
		return
	_prepare_retry_available = false
	_prepare_attempt_revision = -1
	_prepare_attempt_room_id = ""
	_prepare_attempt_generation = -1
	_maybe_auto_prepare(true)


func _submit_operation(operation: Dictionary) -> void:
	var operation_type := str(operation.get("type", ""))
	if _selection_active or _selection_commit_busy or _map_active or _map_committing:
		if str(operation.get("type", "")) in ["configure", "ready", "prepare"]:
			return
	if operation_type == "ready" and bool(operation.get("ready", false)) and not _can_ready_current_room():
		return
	if operation_type == "prepare" and not _can_prepare_current_room():
		return
	var request_generation := _lifecycle_generation
	_busy = true
	if operation.get("type") == "prepare":
		_status.text = "正在提交开局请求（最长等待 15 秒）；确认后可取消连接等待。"
	_refresh_room_view()
	var response: Dictionary = await room_client.command(operation)
	if request_generation != _lifecycle_generation:
		return
	if operation.get("type") == "prepare" and not response.has("error") \
		and str(_as_dictionary(response.get("state")).get("phase", "")) == "preparing":
		_startup_busy = true
	_busy = _startup_busy
	if response.has("error"):
		_show_command_error(response)
		_refresh_room_view()
		return
	if operation.get("type") == "ready":
		_profile_draft_dirty = false
	_accept_state(response.state)
	_refresh_room_view()
	if operation_type == "ready":
		_maybe_auto_prepare.call_deferred()


func _show_command_error(response: Dictionary) -> void:
	if bool(response.get("uncertain", false)):
		_retry_button.visible = true
		_retry_button.text = "重试未确认操作"
		_show_error("command_outcome_uncertain")
	else:
		_show_error(str(response.get("error", "service_error")))


func _on_retry_signaling_pressed() -> void:
	if _busy:
		return
	if _admission_uncertain:
		await _on_retry_admission_pressed()
	elif not _pending_network_profile.is_empty() and room_client.has_uncertain_command():
		await _retry_pending_network_profile()
	elif _map_ack_pending and _slot == 1 and not _map_pending_commit.is_empty():
		await _verify_guest_map_commit(_map_pending_commit.duplicate(true))
	elif _map_commit_delivery_pending and _slot == 0:
		_send_map_committed()
	elif _map_done_delivery_pending and _slot == 0 and not _map_remote_ack.is_empty():
		if _room_connection != null and _room_connection_ready \
			and _room_connection.send_peer_message("map_done", _map_pending_commit.duplicate(true)):
			_map_done_delivery_pending = false
			_complete_map_handshake(_map_session_id, _map_pending_commit)
	elif not _map_pending_configure.is_empty() and room_client.has_uncertain_command():
		await _retry_pending_map_configure()
	elif room_client != null and is_instance_valid(room_client) and room_client.has_uncertain_command():
		_busy = true
		var response: Dictionary = await room_client.retry_pending_command()
		_busy = false
		if response.has("error"):
			_show_command_error(response)
		else:
			if response.has("invite_code"):
				_invite_code = str(response.invite_code)
			var state := _as_dictionary(response.get("state"))
			if str(state.get("phase", "")) == "preparing":
				_prepare_success_revision = int(state.get("setupRevision", -1))
				_prepare_success_room_id = _room_id
				_prepare_success_generation = _lifecycle_generation
				_prepare_retry_available = false
				_startup_busy = true
				_busy = true
			_accept_state(state)
			_retry_button.visible = false
			_retry_button.text = "重试未确认操作"
			_refresh_room_view()
			if _selection_active and not _selection_completed_choice.is_empty():
				if _slot == 0:
					_commit_owner_selection()
				else:
					_maybe_commit_guest_selection()
	elif _prepare_retry_available:
		await _retry_auto_prepare()
	else:
		await _on_connect_selection_pressed()


func _retry_pending_map_configure() -> void:
	if _busy or _map_pending_configure.is_empty() or not room_client.has_uncertain_command():
		return
	var context := _map_pending_configure.duplicate(true)
	var session_id := str(context.get("sessionId", ""))
	if session_id != _map_session_id or not _map_active or not _map_host_authority:
		return
	_busy = true
	var result: Dictionary = await room_client.retry_pending_command()
	if session_id != _map_session_id or not _map_active:
		return
	_busy = false
	if result.has("error"):
		if not bool(result.get("uncertain", false)):
			_finish_map_commit_failure(session_id, str(result.get("error", "configure_failed")))
		else:
			_show_command_error(result)
			_refresh_room_view()
		return
	var state := _as_dictionary(result.get("state"))
	var desired_rules := _as_dictionary(context.get("rules"))
	if desired_rules.is_empty():
		desired_rules = _selected_rules()
	_publish_host_map_commit(
		session_id,
		str(context.get("stageId", "")),
		int(context.get("revision", -1)),
		desired_rules,
		state
	)


func _start_prepared_match(state: Dictionary) -> void:
	var match_state := _as_dictionary(state.get("match"))
	var epoch := str(match_state.get("epoch", ""))
	if epoch.is_empty() or epoch == _starting_epoch:
		return
	_lifecycle_generation += 1
	var generation := _lifecycle_generation
	_stop_lobby_presence()
	_close_room_connection()
	_starting_epoch = epoch
	_startup_busy = true
	_startup_cancel_in_progress = false
	_startup_cancel_requested = false
	_startup_cancel_unconfirmed = false
	_busy = true
	_terminal_pending_epoch = ""
	_terminal_finished_epoch = ""
	_status.text = "正在建立点对点连接并核对初态…"
	_room_view.visible = true
	_home_view.visible = false
	_match_view.visible = false
	if not _signal_connected:
		await _cancel_lobby_signaling()
		if generation != _lifecycle_generation or _starting_epoch != epoch:
			return
		var socket_reply: Dictionary = await room_client.connect_signaling()
		if generation != _lifecycle_generation or _starting_epoch != epoch:
			return
		if socket_reply.has("error"):
			await _startup_failed(epoch, str(socket_reply.error), generation)
			return

	var apply_error := _configure_live_game(state)
	if not apply_error.is_empty():
		await _startup_failed(epoch, apply_error, generation)
		return
	var peer_script: Script = load("res://online_peer_transport.gd")
	if peer_script == null:
		await _startup_failed(epoch, "peer_transport_missing", generation)
		return
	peer_transport = peer_script.new()
	peer_transport.process_mode = Node.PROCESS_MODE_ALWAYS
	add_child(peer_transport)
	var slot_name := "p1" if _slot == 0 else "p2"
	var canonical_setup := {
		"members": _as_array(state.get("members", [])).duplicate(true),
		"stage": state.get("stage", ""),
		"rules": _as_dictionary(state.get("rules")).duplicate(true),
		"profile": _as_dictionary(match_state.get("profile")).duplicate(true),
		"seed": int(match_state.get("seed", 0)),
		"clockBaseline": int(match_state.get("clockBaseline", 0)),
		"setupRevision": int(state.get("setupRevision", 0)),
	}
	var match_script: Script = load("res://online_match.gd")
	if match_script == null:
		await _startup_failed(epoch, "match_coordinator_missing", generation)
		return
	coordinator = match_script.new()
	var configure_error := str(coordinator.configure(game_root, canonical_setup, slot_name, room_client, peer_transport))
	if not configure_error.is_empty():
		await _startup_failed(epoch, configure_error, generation)
		return
	if coordinator.has_signal("page_visibility_changed"):
		coordinator.page_visibility_changed.connect(_on_page_visibility_changed)
	coordinator.started.connect(_on_match_started.bind(epoch, generation))
	coordinator.recovery_changed.connect(_on_recovery_changed)
	coordinator.pause_changed.connect(_on_pause_changed)
	coordinator.pause_requested.connect(_on_pause_requested)
	coordinator.resume_requested.connect(_on_resume_requested)
	coordinator.result_confirmed.connect(_on_match_result_confirmed.bind(epoch, generation))
	coordinator.room_result_committed.connect(_on_room_result_committed.bind(epoch, generation))
	coordinator.diagnostic_abort.connect(_on_match_aborted.bind(epoch, generation))
	coordinator.room_match_aborted.connect(_on_room_match_aborted.bind(epoch, generation))
	var profile := _as_dictionary(match_state.get("profile"))
	var start_error := str(await coordinator.start(epoch, _coordinator_profile(profile), "p1"))
	if generation != _lifecycle_generation or _starting_epoch != epoch or _terminal_pending_epoch == epoch:
		return
	_startup_busy = false
	_startup_cancel_in_progress = false
	_busy = false
	_refresh_room_view()
	if not start_error.is_empty():
		await _startup_failed(epoch, start_error, generation, true)


func _on_page_visibility_changed(visible: bool) -> void:
	if not _startup_busy or _match_started:
		return
	_status.text = "正在建立点对点连接并核对初态…" if visible \
		else "本页已在后台，开局可能超时。请双方把游戏窗口并排并保持可见。"


func _on_cancel_start_pressed() -> void:
	if not _startup_busy or _starting_epoch.is_empty() or _startup_cancel_in_progress or coordinator == null:
		return
	if not coordinator.has_method("cancel_startup"):
		_show_error("cancel_start_unavailable")
		return
	_lifecycle_generation += 1
	var generation := _lifecycle_generation
	var epoch := _starting_epoch
	_startup_cancel_requested = true
	_startup_cancel_in_progress = true
	_busy = true
	_status.text = "正在安全取消开局，请稍候…"
	var issue := str(await coordinator.cancel_startup())
	if generation != _lifecycle_generation or epoch != _starting_epoch:
		return
	if not issue.is_empty():
		_startup_cancel_in_progress = false
		_busy = false
		_startup_cancel_unconfirmed = true
		_status.text = "服务端尚未确认开局取消。可重试取消，或放弃等待并返回主菜单；空闲房间在 30 分钟后关闭。"
		_refresh_room_view()
		return
	var settled_state := room_client.get_room_state()
	if str(settled_state.get("phase", "")) != "lobby":
		_startup_cancel_in_progress = false
		_busy = false
		_startup_cancel_unconfirmed = true
		_status.text = "服务端尚未确认开局取消。可重试取消，或放弃等待并返回主菜单；空闲房间在 30 分钟后关闭。"
		_refresh_room_view()
		return
	_close_match_runtime("startup_cancelled")
	get_tree().paused = false
	if render_surface != null:
		game_root = render_surface.recreate_game_scene()
	_room_state = settled_state
	_starting_epoch = ""
	_startup_busy = false
	_startup_cancel_in_progress = false
	_startup_cancel_requested = false
	_startup_cancel_unconfirmed = false
	_match_started = false
	_terminal_pending_epoch = ""
	_terminal_finished_epoch = ""
	_terminal_commit_queued_epoch = ""
	_busy = false
	set_physics_process(false)
	_show_room()
	_status.text = "开局已取消；你仍留在房间，可以重新准备。"
	_refresh_room_view()
	_arm_lobby_presence(false)


func _on_abandon_startup_pressed() -> void:
	if not _startup_busy or not _startup_cancel_unconfirmed or _busy:
		return
	_lifecycle_generation += 1
	_busy = true
	_startup_cancel_requested = true
	_startup_cancel_in_progress = true
	set_physics_process(false)
	_close_match_runtime("user_abandoned_unconfirmed_startup")
	if room_client != null:
		room_client.clear_credentials()
	_room_state.clear()
	_pending_network_profile.clear()
	_network_profile_authority.clear()
	_room_id = ""
	_invite_token = ""
	_invite_code = ""
	_slot = -1
	_signal_connected = false
	_stop_lobby_presence()
	_admission_uncertain = false
	_profile_draft_dirty = false
	_lan_candidate_opt_in.set_pressed_no_signal(false)
	_starting_epoch = ""
	_startup_busy = false
	_startup_cancel_in_progress = false
	_startup_cancel_requested = false
	_startup_cancel_unconfirmed = false
	_match_started = false
	_match_paused = false
	_terminal_pending_epoch = ""
	_terminal_finished_epoch = ""
	_terminal_commit_queued_epoch = ""
	_pending_control_action = ""
	_pending_control_request_id = ""
	_busy = false
	get_tree().paused = false
	if render_surface != null:
		game_root = render_surface.recreate_game_scene()
	_status.text = "本机已退出等待；服务端清理未确认，空闲房间在 30 分钟后关闭。"
	_close_home()


func _configure_live_game(state: Dictionary) -> String:
	if game_root == null or not is_instance_valid(game_root):
		return "game_scene_unavailable"
	if int(game_root.physics_tick) != 0 or str(game_root.session.root_label) != "MENU":
		return "match_scene_not_fresh"
	var players := {}
	var members := _as_array(state.get("members", []))
	if members.size() != 2 or not members[0] is Dictionary or not members[1] is Dictionary:
		return "incomplete_setup"
	for index in 2:
		var choice := _as_dictionary(members[index].get("choice"))
		var fighter := str(choice.get("fighter", ""))
		var helper := str(choice.get("helper", ""))
		if not _fighter_ids.has(fighter) or not _helper_ids.has(helper):
			return "unsupported_content"
		players["p%d" % (index + 1)] = {
			"resourcePath": "res://generated/fighters/" + fighter,
			"helper": {"resourcePath": "res://generated/helpers/" + helper},
		}
	var rules := _as_dictionary(state.get("rules"))
	game_root.session.maxhp = float(int(rules.get("life", 1)) * 1000)
	game_root.session.maxtime = int(rules.get("time", 90))
	game_root.session.modo = 3
	game_root.session.p1cpu = false
	game_root.session.p2cpu = false
	game_root.ko_recorded_timers = true
	game_root.recorded_training_timers = true
	var match_state := _as_dictionary(state.get("match"))
	game_root.source_random.use_seed(int(match_state.get("seed", 0)))
	if not game_root.source_clock.use_explicit_time(0):
		return "explicit_clock_unavailable"
	var roster_error := str(game_root.configure_diagnostic_roster(players))
	if not roster_error.is_empty():
		return roster_error
	var stage := str(state.get("stage", ""))
	if not _stage_ids.has(stage):
		return "unsupported_stage"
	game_root._load_selected_stage(stage)
	game_root._enter_current_fight(3)
	game_root.battle_intro.recorded_polling = true
	game_root.stage_sound.select()
	game_root.stage_sound.start()
	game_root.set_physics_process(false)
	return ""


func _coordinator_profile(profile: Dictionary) -> Dictionary:
	return {
		"id": str(profile.get("id", "")),
		"inputDelay": int(profile.get("inputDelay", -1)),
		"predictionWindow": int(profile.get("predictionWindow", -1)),
	}


func _on_match_started(epoch: String, generation: int) -> void:
	if generation != _lifecycle_generation or epoch != _starting_epoch:
		return
	_match_started = true
	_match_paused = false
	_startup_busy = false
	_startup_cancel_in_progress = false
	_startup_cancel_requested = false
	_startup_cancel_unconfirmed = false
	_busy = false
	_veil.visible = false
	_dialog.visible = false
	_match_hud.visible = true
	_match_status.text = "点对点对局已开始"
	_pause_button.text = "请求暂停"
	_exit_button.text = "退出本局"
	_intro_skip_button.visible = game_root != null and game_root.battle_intro.active \
		and game_root.battle_intro.polling
	_exit_confirmation_deadline = -1
	_sync_match_hud_controls()
	_register_web_match_hud()
	set_physics_process(true)


func _physics_process(_delta: float) -> void:
	if _selection_active and _selection_adapter != null and is_instance_valid(_selection_adapter) \
		and game_root != null and is_instance_valid(game_root):
		_selection_adapter.tick_local(game_root.session.menu_held())
		return
	if _map_active and _map_adapter != null and is_instance_valid(_map_adapter) \
		and game_root != null and is_instance_valid(game_root):
		_map_adapter.call("tick_local", game_root.session.menu_held())
		return
	if not _match_started or coordinator == null or game_root == null:
		return
	_intro_skip_button.visible = bool(game_root.battle_intro.active and game_root.battle_intro.polling)
	var local_input: Dictionary = game_root.session.fighter_input("p1")
	var issue := str(coordinator.process_tick(Time.get_ticks_msec(), local_input))
	if not issue.is_empty() and issue not in ["waiting_for_start", "waiting_for_peer", "waiting_for_input", "waiting_for_confirmation", "match_finished"]:
		_queue_match_abort({"reason": issue}, _starting_epoch, _lifecycle_generation)


func _process(delta: float) -> void:
	_tick_lobby_presence(delta)
	_tick_connection_wait_status()
	_tick_room_state_poll(delta)
	_sync_web_paste_target()
	if _home_footer != null:
		_home_footer.visible = _dialog.visible and _home_view.visible
	if _home_close_button != null:
		_home_close_button.disabled = not _can_close_home()
	if _admission_abandon_button != null:
		_admission_abandon_button.disabled = _busy or not _admission_uncertain
	if _startup_cancel_button != null:
		var cancel_supported := coordinator != null and coordinator.has_method("cancel_startup")
		_startup_cancel_button.visible = _startup_busy and not _match_started and cancel_supported
		_startup_cancel_button.disabled = _startup_cancel_in_progress or not cancel_supported
		_startup_abandon_button.visible = _startup_busy and not _match_started and _startup_cancel_unconfirmed
		_startup_abandon_button.disabled = _busy or not _startup_cancel_unconfirmed
		_startup_footer.visible = _startup_cancel_button.visible or _startup_abandon_button.visible
	var terminal_waiting := not _starting_epoch.is_empty() and _terminal_pending_epoch == _starting_epoch
	if _rematch_button != null:
		_rematch_button.disabled = _busy or terminal_waiting or _room_id.is_empty() \
			or room_client == null or room_client.get_room_id().is_empty()
	if _result_leave_button != null:
		_result_leave_button.disabled = _busy
	if _intro_skip_button != null and not _match_started:
		_intro_skip_button.visible = false
	_sync_match_hud_controls()
	_push_web_match_hud()


func _tick_connection_wait_status() -> void:
	if not _room_connection_starting or _status == null or _room_connection == null \
		or not is_instance_valid(_room_connection):
		return
	var phase := ""
	if _room_connection.has_method("get_startup_phase"):
		phase = str(_room_connection.get_startup_phase())
	var waiting := ""
	match phase:
		"wait_peer":
			waiting = "正在等待对手连接信令。对方进入房间后会自动开始连接。"
		"wait_negotiation":
			waiting = "正在等待房主发起连接。房主稍后按连接即可，不必在短时间内同时点击。"
		"data_channels":
			waiting = "正在建立对战通道…"
		"create_negotiation", "signaling", "create_peer":
			waiting = "正在建立选人连接…"
	if not waiting.is_empty() and _status.text != waiting:
		_status.text = waiting


func _tick_room_state_poll(delta: float) -> void:
	if not _should_poll_room_state():
		_room_state_poll_elapsed = 0.0
		return
	_room_state_poll_elapsed += delta
	# The socket already pushes room state. Poll only while it is down, and slowly:
	# a cross-region GET is about a second, so a 2s loop stacks in flight.
	if _room_state_poll_elapsed < 5.0:
		return
	_room_state_poll_elapsed = 0.0
	_poll_room_state.call_deferred()


func _should_poll_room_state() -> bool:
	if _room_id.is_empty() or room_client == null or not is_instance_valid(room_client):
		return false
	if str(_room_state.get("phase", "")) != "lobby" or _busy or _startup_busy \
		or _selection_active or _selection_commit_busy or _room_connection_starting:
		return false
	if room_client.has_method("is_signaling_connected") and room_client.is_signaling_connected():
		return false
	if room_client.has_method("has_uncertain_command") and room_client.has_uncertain_command():
		return false
	if room_client.has_method("is_command_in_flight") and room_client.is_command_in_flight():
		return false
	return not _room_state_poll_in_flight


func _poll_room_state() -> void:
	if not _should_poll_room_state():
		return
	_room_state_poll_in_flight = true
	var lifecycle_generation := _lifecycle_generation
	var requested_room_id := _room_id
	var response: Dictionary = await room_client.refresh_state()
	_room_state_poll_in_flight = false
	if lifecycle_generation != _lifecycle_generation or requested_room_id != _room_id:
		return
	if response.has("error"):
		return
	var state: Variant = response.get("state")
	if state is Dictionary:
		_accept_state(state)
		_refresh_room_view()


func _sync_match_hud_controls() -> void:
	var active := _match_started and coordinator != null and not _starting_epoch.is_empty()
	var terminal_waiting := not _starting_epoch.is_empty() and _terminal_pending_epoch == _starting_epoch
	if _pause_button != null:
		_pause_button.disabled = not active or _busy
	if _exit_button != null:
		_exit_button.disabled = not active or _busy or terminal_waiting
	if _intro_skip_button != null:
		_intro_skip_button.disabled = not active or _busy
	var can_reply := active and not _busy and not _pending_control_request_id.is_empty()
	if _control_accept_button != null:
		_control_accept_button.disabled = not can_reply
	if _control_refuse_button != null:
		_control_refuse_button.disabled = not can_reply


func _web_match_hud_fields() -> Dictionary:
	var active := _match_started and coordinator != null and not _starting_epoch.is_empty()
	var pause_request: Variant = null
	var request_visible := active and _control_reply_actions != null \
		and _control_reply_actions.visible and not _pending_control_request_id.is_empty()
	if request_visible:
		pause_request = {
			"id": _pending_control_request_id,
			"text": "对方请求暂停" if _pending_control_action == "pause" else "对方请求恢复",
		}
	var session := "%s:%d" % [_starting_epoch, _lifecycle_generation] if active else _web_match_hud_session
	return {
		"schemaVersion": 1,
		"active": active,
		"session": session,
		"status": _web_match_status_text() if active else "",
		"pauseLabel": "请求恢复" if _match_paused else "请求暂停",
		"canPause": active and not _match_paused and _button_enabled(_pause_button),
		"canResume": active and _match_paused and _button_enabled(_pause_button),
		"pauseRequest": pause_request,
		"canAcceptPause": request_visible and _button_enabled(_control_accept_button),
		"canRefusePause": request_visible and _button_enabled(_control_refuse_button),
		"canSkipIntro": active and _button_enabled(_intro_skip_button),
		"canExit": active and _button_enabled(_exit_button),
		"exitLabel": _exit_button.text if _exit_button != null else "退出本局",
	}


func _button_enabled(button: Button) -> bool:
	return button != null and button.visible and not button.disabled


func _web_match_status_text() -> String:
	if _match_status == null:
		return "联机对局已开始"
	return _match_status.text


func _humanize_match_issue(issue: String) -> String:
	var labels := {
		"Control request is not valid now": "当前无法发送暂停或恢复请求。",
		"A control request is already pending": "已有同步请求正在等待对方回应。",
		"Could not send control request": "暂停或恢复请求未送达，请检查连接后重试。",
		"Unknown control request": "该请求已失效，请等待新的请求。",
		"Intro skip is not available now": "当前没有可跳过的开场。",
		"Could not send intro-skip request": "跳过开场请求未送达，请稍后重试。",
	}
	if labels.has(issue):
		return str(labels[issue])
	if issue.contains("timeout") or issue.contains("timed out"):
		return "连接等待超时，请检查双方网络后重试。"
	return "联机操作未完成，请检查连接后重试。"


func _register_web_match_hud() -> bool:
	if not _match_started or _starting_epoch.is_empty():
		return false
	_unregister_web_match_hud()
	if not _web_match_bridge_available():
		_match_hud.visible = true
		return false
	_web_match_hud_session = "%s:%d" % [_starting_epoch, _lifecycle_generation]
	_web_match_hud_revision = 0
	_web_match_hud_consumed_revision = -1
	_web_match_hud_last_fields.clear()
	var callback := Callable(self, "_on_web_match_action")
	var callback_value: Variant = callback
	if _web_match_hud_bridge_override == null:
		callback_value = JavaScriptBridge.create_callback(callback)
	var token_value: Variant = _web_match_bridge_register(callback_value)
	var token := _integral_web_revision(token_value)
	if token <= 0:
		_web_match_hud_callback = null
		_match_hud.visible = true
		return false
	_web_match_hud_token = token
	_web_match_hud_callback = callback_value
	_web_match_hud_registered = true
	if not _push_web_match_hud(true):
		_unregister_web_match_hud()
		_match_hud.visible = true
		return false
	_match_hud.visible = false
	return true


func _web_match_bridge_available() -> bool:
	if _web_match_hud_bridge_override != null:
		return _web_match_hud_bridge_override.has_method("register") \
			and _web_match_hud_bridge_override.has_method("update") \
			and _web_match_hud_bridge_override.has_method("unregister")
	if not OS.has_feature("web"):
		return false
	if _web_window == null:
		_web_window = JavaScriptBridge.get_interface("window")
	return _web_window != null and _web_window.bvnOnlineControlsRegister != null \
		and _web_window.bvnOnlineControlsUpdate != null \
		and _web_window.bvnOnlineControlsUnregister != null


func _web_match_bridge_register(callback: Variant) -> Variant:
	if _web_match_hud_bridge_override != null:
		return _web_match_hud_bridge_override.call("register", callback)
	return _web_window.bvnOnlineControlsRegister(callback)


func _web_match_bridge_update(snapshot_json: String, token: int) -> bool:
	if _web_match_hud_bridge_override != null:
		return bool(_web_match_hud_bridge_override.call("update", snapshot_json, token))
	var result: Variant = _web_window.bvnOnlineControlsUpdate(snapshot_json, token)
	return result is bool and result


func _web_match_bridge_unregister(token: int) -> bool:
	if _web_match_hud_bridge_override != null:
		return bool(_web_match_hud_bridge_override.call("unregister", token))
	var result: Variant = _web_window.bvnOnlineControlsUnregister(token)
	return result is bool and result


func _push_web_match_hud(force_revision: bool = false) -> bool:
	if not _web_match_hud_registered or _web_match_hud_token <= 0:
		return false
	var fields := _web_match_hud_fields()
	if not force_revision and fields == _web_match_hud_last_fields:
		return true
	_web_match_hud_revision += 1
	fields["revision"] = _web_match_hud_revision
	var accepted := _web_match_bridge_update(JSON.stringify(fields), _web_match_hud_token)
	if not accepted:
		var old_token := _web_match_hud_token
		_web_match_bridge_unregister(old_token)
		_reset_web_match_hud_state()
		_match_hud.visible = true
		return false
	fields.erase("revision")
	_web_match_hud_last_fields = fields.duplicate(true)
	return true


func _unregister_web_match_hud() -> void:
	if not _web_match_hud_registered or _web_match_hud_token <= 0:
		_reset_web_match_hud_state()
		return
	var clear_fields := _web_match_hud_last_fields.duplicate(true)
	clear_fields["schemaVersion"] = 1
	clear_fields["active"] = false
	clear_fields["session"] = _web_match_hud_session
	clear_fields["revision"] = _web_match_hud_revision + 1
	clear_fields["status"] = ""
	clear_fields["canPause"] = false
	clear_fields["canResume"] = false
	clear_fields["pauseRequest"] = null
	clear_fields["canAcceptPause"] = false
	clear_fields["canRefusePause"] = false
	clear_fields["canSkipIntro"] = false
	clear_fields["canExit"] = false
	var token := _web_match_hud_token
	_web_match_bridge_update(JSON.stringify(clear_fields), token)
	_web_match_bridge_unregister(token)
	_reset_web_match_hud_state()


func _reset_web_match_hud_state() -> void:
	_web_match_hud_callback = null
	_web_match_hud_token = -1
	_web_match_hud_session = ""
	_web_match_hud_revision = 0
	_web_match_hud_consumed_revision = -1
	_web_match_hud_last_fields.clear()
	_web_match_hud_registered = false


func _integral_web_revision(value: Variant) -> int:
	if value is bool:
		return -1
	if value is int:
		return value if value >= 0 and value <= 9_007_199_254_740_991 else -1
	if value is float and is_finite(value) and value == floor(value) \
		and value >= 0.0 and value <= 9_007_199_254_740_991.0:
		return int(value)
	return -1


func _on_web_match_action(args: Array) -> void:
	if not _web_match_hud_registered or not _match_started or coordinator == null or _starting_epoch.is_empty():
		return
	if args.size() != 4 or not args[0] is String or not args[1] is String or not args[3] is String:
		return
	var action := str(args[0])
	var session := str(args[1])
	var revision := _integral_web_revision(args[2])
	var request_id := str(args[3])
	if action not in ["pause", "resume", "accept_pause", "refuse_pause", "skip_intro", "exit"]:
		return
	var current_session := "%s:%d" % [_starting_epoch, _lifecycle_generation]
	if session != _web_match_hud_session or session != current_session \
		or revision != _web_match_hud_revision or revision <= _web_match_hud_consumed_revision:
		return
	if not _web_match_action_enabled(action, request_id):
		return
	_web_match_hud_consumed_revision = revision
	match action:
		"pause": _on_pause_pressed()
		"resume": _on_pause_pressed()
		"accept_pause": _on_control_reply(true)
		"refuse_pause": _on_control_reply(false)
		"skip_intro": _on_intro_skip_pressed()
		"exit": _on_exit_match_pressed()
	_sync_match_hud_controls()
	_push_web_match_hud(true)


func _web_match_action_enabled(action: String, request_id: String) -> bool:
	if _busy or not _match_started or coordinator == null:
		return false
	match action:
		"pause": return request_id.is_empty() and not _match_paused and _button_enabled(_pause_button)
		"resume": return request_id.is_empty() and _match_paused and _button_enabled(_pause_button)
		"accept_pause", "refuse_pause":
			return request_id == _pending_control_request_id and not request_id.is_empty() \
				and _control_reply_actions != null and _control_reply_actions.visible \
				and _button_enabled(_control_accept_button if action == "accept_pause" else _control_refuse_button)
		"skip_intro": return request_id.is_empty() and _button_enabled(_intro_skip_button)
		"exit": return request_id.is_empty() and _button_enabled(_exit_button)
	return false


func _on_game_menu_confirmed(item_id: String) -> void:
	if item_id == "online":
		_open_home()


func _on_intro_skip_pressed() -> void:
	if coordinator == null or not _match_started or _busy or not _button_enabled(_intro_skip_button):
		return
	var issue := str(coordinator.request_intro_skip())
	if issue.is_empty():
		_match_status.text = "已提交开场跳过请求，将按同步帧执行。"
		_match_status.tooltip_text = ""
	else:
		_match_status.text = "无法跳过开场：" + _humanize_match_issue(issue)
		_match_status.tooltip_text = issue


func _on_diagnostic_download_pressed() -> void:
	if _diagnostic_report.is_empty():
		return
	var report_json := JSON.stringify(_diagnostic_report, "\t")
	if OS.has_feature("web"):
		var report_literal := JSON.stringify(report_json)
		JavaScriptBridge.eval("(() => { const blob = new Blob([" + report_literal + "], { type: 'application/json' }); const link = document.createElement('a'); link.href = URL.createObjectURL(blob); link.download = 'bvn26-online-diagnostic.json'; link.click(); setTimeout(() => URL.revokeObjectURL(link.href), 1000); })()")
		_result_status.text = _last_result_text + "\n诊断文件已交给浏览器下载。"
		return
	var path := "user://online-diagnostic-%s.json" % Time.get_datetime_string_from_system().replace(":", "-").replace(" ", "T")
	var file := FileAccess.open(path, FileAccess.WRITE)
	if file == null:
		_result_status.text = _last_result_text + "\n诊断文件写入失败。"
		return
	file.store_string(report_json)
	file.close()
	_result_status.text = _last_result_text + "\n诊断文件已保存：" + path


func _on_recovery_changed(state: String) -> void:
	_match_status.text = "网络状态：" + _recovery_label(state)


func _on_pause_changed(paused: bool) -> void:
	_match_paused = paused
	_control_reply_actions.visible = false
	_pending_control_action = ""
	_pending_control_request_id = ""
	_pause_button.text = "请求恢复" if paused else "请求暂停"
	_match_status.text = "双方已同意暂停" if paused else "对局进行中"


func _on_pause_requested(request: Dictionary) -> void:
	_show_control_request("pause", request)


func _on_resume_requested(request: Dictionary) -> void:
	_show_control_request("resume", request)


func _show_control_request(action: String, request: Dictionary) -> void:
	_pending_control_action = action
	_pending_control_request_id = str(request.get("id", ""))
	_match_status.text = "对方请求" + ("暂停" if action == "pause" else "恢复")
	_control_reply_actions.visible = not _pending_control_request_id.is_empty()


func _on_control_reply(accepted: bool) -> void:
	var response_button := _control_accept_button if accepted else _control_refuse_button
	if coordinator == null or not _match_started or _busy or _pending_control_request_id.is_empty() \
		or _control_reply_actions == null or not _control_reply_actions.visible \
		or not _button_enabled(response_button):
		return
	var action := _pending_control_action
	var request_id := _pending_control_request_id
	_busy = true
	_sync_match_hud_controls()
	var issue := str(coordinator.respond_pause(request_id, accepted) if action == "pause" else coordinator.respond_resume(request_id, accepted))
	_busy = false
	_control_reply_actions.visible = false
	_pending_control_action = ""
	_pending_control_request_id = ""
	if not issue.is_empty():
		_match_status.text = "请求未完成：" + _humanize_match_issue(issue)
		_match_status.tooltip_text = issue
	else:
		_match_status.tooltip_text = ""
	_sync_match_hud_controls()
	_push_web_match_hud()


func _on_pause_pressed() -> void:
	if coordinator == null or not _match_started or _busy or not _button_enabled(_pause_button):
		return
	_busy = true
	_sync_match_hud_controls()
	var issue := str(coordinator.request_resume() if _match_paused else coordinator.request_pause())
	_busy = false
	if not issue.is_empty():
		_match_status.text = "请求未完成：" + _humanize_match_issue(issue)
		_match_status.tooltip_text = issue
	else:
		_match_status.tooltip_text = ""
	_sync_match_hud_controls()
	_push_web_match_hud()


func _on_exit_match_pressed() -> void:
	if coordinator == null or not _match_started or not _button_enabled(_exit_button) \
		or (not _starting_epoch.is_empty() and _terminal_pending_epoch == _starting_epoch):
		return
	var now := Time.get_ticks_msec()
	if now > _exit_confirmation_deadline:
		_exit_confirmation_deadline = now + 4000
		_exit_button.text = "再点一次确认退出"
		_push_web_match_hud()
		return
	_exit_confirmation_deadline = -1
	_exit_button.text = "退出本局"
	_unregister_web_match_hud()
	_lifecycle_generation += 1
	var generation := _lifecycle_generation
	var epoch := _starting_epoch
	coordinator.close("local_exit")
	coordinator = null
	if peer_transport != null:
		peer_transport.close_peer()
		peer_transport.queue_free()
		peer_transport = null
	_match_started = false
	set_physics_process(false)
	_match_hud.visible = false
	get_tree().paused = false
	if render_surface != null:
		game_root = render_surface.recreate_game_scene()
	if not epoch.is_empty():
		await _abort_room_match(epoch, generation)
	if generation != _lifecycle_generation:
		return
	_starting_epoch = ""
	_show_room()
	_room_view.visible = true
	_status.text = "你已退出本局；房间仍可重新准备。"
	_refresh_room_view()


func _on_match_result_confirmed(result: Dictionary, epoch: String, generation: int) -> void:
	_queue_match_result(result, epoch, generation)


func _queue_match_result(result: Dictionary, epoch: String, generation: int) -> void:
	if generation != _lifecycle_generation or epoch != _starting_epoch or _terminal_pending_epoch == epoch:
		return
	_terminal_pending_epoch = epoch
	_finish_match_result.call_deferred(result.duplicate(true), epoch, generation)


func _finish_match_result(result: Dictionary, epoch: String, generation: int) -> void:
	if generation != _lifecycle_generation or epoch != _starting_epoch or _terminal_pending_epoch != epoch:
		return
	_last_result_text = _format_result(result)
	_diagnostic_report.clear()
	_diagnostic_button.visible = false
	_unregister_web_match_hud()
	_match_started = false
	set_physics_process(false)
	get_tree().paused = false
	_show_result(result, "结果已一致，正在等待房间服务确认后再战。")
	_rematch_button.disabled = true
	

func _on_room_result_committed(result: Dictionary, epoch: String, generation: int) -> void:
	_queue_room_result_commit(result, epoch, generation)


func _queue_room_result_commit(result: Dictionary, epoch: String, generation: int) -> void:
	if generation != _lifecycle_generation or epoch != _starting_epoch or _terminal_finished_epoch == epoch or _terminal_commit_queued_epoch == epoch:
		return
	_terminal_commit_queued_epoch = epoch
	_finish_room_result_commit.call_deferred(result.duplicate(true), epoch, generation)


func _finish_room_result_commit(result: Dictionary, epoch: String, generation: int) -> void:
	if generation != _lifecycle_generation or epoch != _starting_epoch or _terminal_pending_epoch != epoch or _terminal_finished_epoch == epoch:
		return
	_terminal_finished_epoch = epoch
	_close_match_runtime("confirmed_result_committed")
	get_tree().paused = false
	if render_surface != null:
		game_root = render_surface.recreate_game_scene()
	if generation != _lifecycle_generation or epoch != _starting_epoch:
		return
	var last_result := _as_dictionary(room_client.get_room_state().get("lastResult"))
	if not last_result.is_empty():
		result = last_result
	_last_result_text = _format_result(result)
	_starting_epoch = ""
	_terminal_pending_epoch = ""
	_terminal_commit_queued_epoch = ""
	_room_state = room_client.get_room_state()
	_result_status.text = _last_result_text + "\n双方确认结果，已可以返回房间再战。"
	_rematch_button.disabled = false
	_result_leave_button.disabled = false


func _show_result(result: Variant, status_line: String = "双方确认结果后，可再次准备开始新的一局。") -> void:
	if _last_result_text.is_empty():
		_last_result_text = _format_result(result if result is Dictionary else {})
	_match_hud.visible = false
	_veil.visible = true
	_dialog.visible = true
	_home_view.visible = false
	_room_view.visible = false
	_match_view.visible = true
	_result_status.text = _last_result_text + "\n" + status_line
	_diagnostic_button.visible = false
	_room_state = room_client.get_room_state()


func _on_match_aborted(report: Dictionary, epoch: String, generation: int) -> void:
	var local_report := report.duplicate(true)
	if not local_report.has("performance") and coordinator != null and coordinator.has_method("performance_report"):
		local_report["performance"] = coordinator.call("performance_report")
	_queue_match_abort(local_report, epoch, generation)


func _queue_match_abort(report: Dictionary, epoch: String, generation: int) -> void:
	if generation != _lifecycle_generation or epoch != _starting_epoch or _terminal_pending_epoch == epoch:
		return
	_terminal_pending_epoch = epoch
	_finish_match_abort.call_deferred(report.duplicate(true), epoch, generation)


func _finish_match_abort(report: Dictionary, epoch: String, generation: int) -> void:
	if generation != _lifecycle_generation or epoch != _starting_epoch or _terminal_pending_epoch != epoch:
		return
	_unregister_web_match_hud()
	_match_started = false
	_match_hud.visible = false
	_intro_skip_button.visible = false
	_match_status.text = "对局已结束：" + _abort_reason(report)
	set_physics_process(false)
	get_tree().paused = false
	_last_result_text = "同步未完成，本局不记胜负。\n" + _abort_reason(report)
	_diagnostic_report = report.duplicate(true)
	_match_view.visible = true
	_room_view.visible = false
	_home_view.visible = false
	_veil.visible = true
	_dialog.visible = true
	_result_status.text = _last_result_text + "\n正在等待房间服务确认取消本局。"
	_diagnostic_button.visible = true
	_rematch_button.text = "返回房间"
	_rematch_button.disabled = true


func _on_room_match_aborted(report: Dictionary, epoch: String, generation: int) -> void:
	_queue_room_match_abort(report, epoch, generation)


func _queue_room_match_abort(report: Dictionary, epoch: String, generation: int) -> void:
	if generation != _lifecycle_generation or epoch != _starting_epoch or _terminal_finished_epoch == epoch or _terminal_commit_queued_epoch == epoch:
		return
	_terminal_commit_queued_epoch = epoch
	_finish_room_match_abort.call_deferred(report.duplicate(true), epoch, generation)


func _finish_room_match_abort(report: Dictionary, epoch: String, generation: int) -> void:
	if generation != _lifecycle_generation or epoch != _starting_epoch or _terminal_pending_epoch != epoch or _terminal_finished_epoch == epoch:
		return
	_terminal_finished_epoch = epoch
	_close_match_runtime("diagnostic_abort_committed")
	get_tree().paused = false
	if render_surface != null:
		game_root = render_surface.recreate_game_scene()
	if generation != _lifecycle_generation or epoch != _starting_epoch:
		return
	var service_terminal := str(report.get("service_terminal", "match_aborted"))
	var service_state: Dictionary = room_client.get_room_state() if room_client != null else {}
	var service_result := _as_dictionary(report.get("last_result"))
	if service_result.is_empty():
		service_result = _as_dictionary(service_state.get("lastResult"))
	_diagnostic_report = report.duplicate(true)
	_match_started = false
	set_physics_process(false)
	_match_view.visible = true
	_room_view.visible = false
	_home_view.visible = false
	_match_hud.visible = false
	_veil.visible = true
	_dialog.visible = true
	_diagnostic_button.visible = true
	if service_terminal == "room_unavailable":
		var known_result: bool = service_result.get("epoch") == epoch and not service_result.is_empty()
		var result_line := _format_result(service_result) if known_result else "本局最终结果未能从房间服务确认。"
		room_client.clear_credentials()
		_room_state.clear()
		_pending_network_profile.clear()
		_network_profile_authority.clear()
		_profile_draft_dirty = false
		_room_id = ""
		_invite_token = ""
		_invite_code = ""
		_slot = -1
		_signal_connected = false
		_stop_lobby_presence()
		_starting_epoch = ""
		_terminal_pending_epoch = ""
		_terminal_commit_queued_epoch = ""
		_last_result_text = "房间已不可用。\n" + result_line
		_result_status.text = _last_result_text + "\n不能返回此房间；请清理本机状态后回到标题菜单。"
		_rematch_button.text = "房间不可用"
		_rematch_button.disabled = true
		_result_leave_button.text = "清理并返回标题菜单"
		_result_leave_button.disabled = false
		return
	_starting_epoch = ""
	_terminal_pending_epoch = ""
	_terminal_commit_queued_epoch = ""
	_room_state = service_state
	if service_terminal == "match_already_finished":
		_last_result_text = _format_result(service_result) if not service_result.is_empty() else "服务端已确认本局结束；结果详情暂时不可用。"
		_result_status.text = _last_result_text + "\n房间服务已确认这局结束；可返回房间查看当前状态。"
		_rematch_button.text = "返回房间"
		_rematch_button.disabled = false
		_result_leave_button.text = "离开联机模式"
		_result_leave_button.disabled = false
		return
	_last_result_text = "同步未完成，本局不记胜负。\n" + _abort_reason(report)
	_result_status.text = _last_result_text + "\n房间服务已确认取消，可以返回房间。"
	_rematch_button.text = "返回房间"
	_rematch_button.disabled = false
	_result_leave_button.text = "离开联机模式"
	_result_leave_button.disabled = false


func _close_match_runtime(reason: String) -> void:
	_unregister_web_match_hud()
	if coordinator != null:
		coordinator.close(reason)
		coordinator = null
	if peer_transport != null:
		peer_transport.close_peer()
		peer_transport.queue_free()
		peer_transport = null


func _startup_failed(epoch: String, reason: String, generation: int = -1, abort_owned_by_coordinator: bool = false) -> void:
	if generation < 0:
		generation = _lifecycle_generation
	if generation != _lifecycle_generation or epoch != _starting_epoch or _terminal_pending_epoch == epoch:
		return
	_lifecycle_generation += 1
	var cleanup_generation := _lifecycle_generation
	_busy = true
	set_physics_process(false)
	_starting_epoch = ""
	_startup_busy = false
	_startup_cancel_in_progress = false
	_startup_cancel_requested = false
	_startup_cancel_unconfirmed = false
	if coordinator != null:
		coordinator.close("startup_failed")
		coordinator = null
	if peer_transport != null:
		peer_transport.close_peer()
		peer_transport.queue_free()
		peer_transport = null
	var current_room := room_client.get_room_state()
	var match_state := _as_dictionary(current_room.get("match"))
	if abort_owned_by_coordinator and room_client.has_uncertain_command():
		var retry_result: Dictionary = await room_client.retry_pending_command()
		if cleanup_generation != _lifecycle_generation:
			return
		if not retry_result.has("error"):
			_accept_state(retry_result.get("state"))
		current_room = room_client.get_room_state()
		match_state = _as_dictionary(current_room.get("match"))
	if abort_owned_by_coordinator:
		var refreshed_room: Dictionary = await room_client.refresh_state()
		if cleanup_generation != _lifecycle_generation:
			return
		if not refreshed_room.has("error"):
			_accept_state(refreshed_room.get("state"))
	if not abort_owned_by_coordinator and str(match_state.get("epoch", "")) == epoch and str(current_room.get("phase", "")) in ["preparing", "active"]:
		var abort_result: Dictionary = await room_client.command({"type": "abort", "epoch": epoch})
		if abort_result.get("uncertain", false):
			abort_result = await room_client.retry_pending_command()
		if cleanup_generation != _lifecycle_generation:
			return
		if not abort_result.has("error"):
			_accept_state(abort_result.get("state"))
	get_tree().paused = false
	if render_surface != null:
		game_root = render_surface.recreate_game_scene()
	_busy = false
	_show_room()
	_show_error(reason)
	_arm_lobby_presence(false)


func _abort_room_match(epoch: String, generation: int) -> void:
	var room_state := room_client.get_room_state()
	if str(room_state.get("phase", "")) not in ["preparing", "active"]:
		return
	var match_state := _as_dictionary(room_state.get("match"))
	if str(match_state.get("epoch", "")) != epoch:
		return
	var response: Dictionary = await room_client.command({"type": "abort", "epoch": epoch})
	if response.get("uncertain", false):
		response = await room_client.retry_pending_command()
	if generation == _lifecycle_generation and not response.has("error"):
		_accept_state(response.get("state"))


func _on_rematch_pressed() -> void:
	if _busy or not _starting_epoch.is_empty() or _terminal_pending_epoch == _starting_epoch and not _starting_epoch.is_empty():
		return
	if _room_id.is_empty() or room_client == null or room_client.get_room_id().is_empty():
		return
	_lifecycle_generation += 1
	set_physics_process(false)
	_close_match_runtime("return_to_lobby")
	_starting_epoch = ""
	_terminal_pending_epoch = ""
	_terminal_finished_epoch = ""
	_terminal_commit_queued_epoch = ""
	_match_started = false
	_last_result_text = ""
	_diagnostic_report.clear()
	_diagnostic_button.visible = false
	if render_surface != null:
		game_root = render_surface.recreate_game_scene()
	_room_state = room_client.get_room_state()
	_show_room()
	_status.text = "角色、援助和规则仍在房间内；再次准备后由房主开始新的一局。"
	_refresh_room_view()
	_arm_lobby_presence(false)


func _on_leave_room_pressed() -> void:
	if _busy:
		return
	if not _starting_epoch.is_empty() and _terminal_pending_epoch == _starting_epoch:
		await _abandon_pending_terminal()
		return
	if room_client == null or _room_id.is_empty():
		_on_close_pressed()
		return
	_lifecycle_generation += 1
	_stop_lobby_presence()
	set_physics_process(false)
	_close_room_connection()
	_busy = true
	await _cancel_lobby_signaling()
	if room_client == null or _room_id.is_empty():
		_busy = false
		return
	_close_match_runtime("room_leave")
	var room_state := room_client.get_room_state()
	var match_state := _as_dictionary(room_state.get("match"))
	if room_client.has_uncertain_command():
		var pending: Dictionary = await room_client.retry_pending_command()
		if pending.has("error"):
			_busy = false
			_show_command_error(pending)
			_arm_lobby_presence(false)
			return
		room_state = _as_dictionary(pending.get("state"))
		match_state = _as_dictionary(room_state.get("match"))
	if str(room_state.get("phase", "")) in ["preparing", "active"] and not str(match_state.get("epoch", "")).is_empty():
		var abort_result: Dictionary = await room_client.command({"type": "abort", "epoch": str(match_state.get("epoch", ""))})
		if abort_result.get("uncertain", false):
			abort_result = await room_client.retry_pending_command()
		if abort_result.has("error"):
			_busy = false
			_show_command_error(abort_result)
			_arm_lobby_presence(false)
			return
	var leave_result: Dictionary = await room_client.command({"type": "leave"})
	if leave_result.get("uncertain", false):
		leave_result = await room_client.retry_pending_command()
	if leave_result.has("error"):
		_busy = false
		_show_command_error(leave_result)
		_arm_lobby_presence(false)
		return
	room_client.clear_credentials()
	_room_state.clear()
	_pending_network_profile.clear()
	_network_profile_authority.clear()
	_room_id = ""
	_invite_token = ""
	_invite_code = ""
	_slot = -1
	_match_started = false
	_signal_connected = false
	_profile_draft_dirty = false
	_lan_candidate_opt_in.set_pressed_no_signal(false)
	_starting_epoch = ""
	_terminal_pending_epoch = ""
	_terminal_finished_epoch = ""
	_terminal_commit_queued_epoch = ""
	_busy = false
	get_tree().paused = false
	if render_surface != null:
		game_root = render_surface.recreate_game_scene()
	_veil.visible = false
	_dialog.visible = false


func _abandon_pending_terminal() -> void:
	_busy = true
	_stop_lobby_presence()
	_lifecycle_generation += 1
	var generation := _lifecycle_generation
	var epoch := _starting_epoch
	set_physics_process(false)
	_close_match_runtime("user_left_while_result_pending")
	var leave_issue := ""
	var current_room := room_client.get_room_state()
	if room_client.has_uncertain_command():
		var retry_result: Dictionary = await room_client.retry_pending_command()
		if generation != _lifecycle_generation:
			return
		if retry_result.has("error"):
			leave_issue = str(retry_result.get("error", "server_unreachable"))
		else:
			current_room = _as_dictionary(retry_result.get("state"))
	var match_state := _as_dictionary(current_room.get("match"))
	var can_send_next := leave_issue.is_empty()
	if can_send_next and str(current_room.get("phase", "")) in ["preparing", "active"] and str(match_state.get("epoch", "")) == epoch:
		var abort_reply: Dictionary = await room_client.command({"type": "abort", "epoch": epoch})
		if abort_reply.get("uncertain", false):
			abort_reply = await room_client.retry_pending_command()
		if generation != _lifecycle_generation:
			return
		if abort_reply.has("error"):
			leave_issue = str(abort_reply.get("error", "server_unreachable"))
			can_send_next = false
		else:
			current_room = _as_dictionary(abort_reply.get("state"))
	if can_send_next:
		var leave_reply: Dictionary = await room_client.command({"type": "leave"})
		if leave_reply.get("uncertain", false):
			leave_reply = await room_client.retry_pending_command()
		if generation != _lifecycle_generation:
			return
		if leave_reply.has("error"):
			leave_issue = str(leave_reply.get("error", "server_unreachable"))
	room_client.clear_credentials()
	_room_state.clear()
	_pending_network_profile.clear()
	_network_profile_authority.clear()
	_profile_draft_dirty = false
	_room_id = ""
	_invite_token = ""
	_invite_code = ""
	_slot = -1
	_signal_connected = false
	_starting_epoch = ""
	_terminal_pending_epoch = ""
	_terminal_finished_epoch = ""
	_terminal_commit_queued_epoch = ""
	_busy = false
	get_tree().paused = false
	if render_surface != null:
		game_root = render_surface.recreate_game_scene()
	_open_home()
	_status.text = "已离开联机模式。" if leave_issue.is_empty() else "已离开本机联机模式；服务端房间可能仍在，网络恢复前无法确认清理。"


func _abort_reason(report: Dictionary) -> String:
	var reason := str(report.get("reason", report.get("kind", "同步失败")))
	var labels := {
		"peer_disconnect_timeout": "对手连接超时",
		"clock_regression": "本机计时异常",
		"state_mismatch": "双方战斗状态不一致",
		"peer_protocol": "收到无法识别的对手消息",
		"simulation": "战斗同步计算失败",
		"invalid_peer_result": "收到无效的对局结果",
		"result_mismatch": "双方结果不一致",
		"peer_start_hash": "双方开局状态不一致",
		"local_start_hash": "本机开局状态校验失败",
		"service_result_mismatch": "房间服务结果不一致",
	}
	return str(labels.get(reason, reason.replace("_", " ")))


func _copy_invitation() -> void:
	if _invite_code.is_empty():
		return
	DisplayServer.clipboard_set(_invite_code)
	_status.text = "加入码已复制；请通过你信任的渠道发送给好友。"


func _on_rotate_invitation_pressed() -> void:
	if _busy or _slot != 0 or _room_state.get("phase") != "lobby":
		return
	_busy = true
	_refresh_room_view()
	_status.text = "正在更新加入码…"
	var response: Dictionary = await room_client.rotate_invitation()
	_busy = false
	if response.has("error"):
		_show_command_error(response)
		_refresh_room_view()
		return
	_invite_code = str(response.get("invite_code", ""))
	_accept_state(response.get("state"))
	_status.text = "加入码已更新；之前的加入码已失效。"
	_refresh_room_view()


func _parse_invitation(value: String) -> Dictionary:
	var normalized := value.strip_edges()
	var pieces := normalized.split(".", false, 2)
	if pieces.size() == 2 and pieces[0].length() == 64 and pieces[1].length() == 43:
		return {"kind": "legacy", "room_id": pieces[0], "invite_token": pieces[1]}
	if not normalized.is_empty() and not normalized.contains("."):
		return {"kind": "code", "code": normalized.to_lower()}
	return {}


func _member_name(members: Array, index: int) -> String:
	if index >= members.size() or not members[index] is Dictionary:
		return "等待加入"
	return str(members[index].get("nickname", "玩家"))


func _member_ready(members: Array, index: int) -> String:
	if index >= members.size() or not members[index] is Dictionary:
		return ""
	return "已准备" if bool(members[index].get("ready", false)) else "未准备"


func _selected_id(option: OptionButton) -> String:
	if option.selected < 0:
		return ""
	return str(option.get_item_metadata(option.selected))


func _selected_number(option: OptionButton) -> int:
	if option.selected < 0:
		return 0
	return int(option.get_item_metadata(option.selected))


func _select_by_metadata(option: OptionButton, value: String) -> void:
	for index in option.item_count:
		if str(option.get_item_metadata(index)) == value:
			option.select(index)
			return


func _select_number(option: OptionButton, value: int) -> void:
	for index in option.item_count:
		if int(option.get_item_metadata(index)) == value:
			option.select(index)
			return


func _add_options(parent: GridContainer, label: String, option: OptionButton, ids: Array[String], names: Dictionary) -> void:
	parent.add_child(_label(label))
	parent.add_child(option)
	for id in ids:
		option.add_item(str(names.get(id, id)))
		option.set_item_metadata(option.item_count - 1, id)
	if option.item_count > 0:
		option.select(0)


func _add_number_options(parent: GridContainer, label: String, option: OptionButton, values: Array, suffix := "") -> void:
	parent.add_child(_label(label))
	parent.add_child(option)
	for value in values:
		option.add_item(str(value) + suffix)
		option.set_item_metadata(option.item_count - 1, value)
	if option.item_count > 0:
		option.select(0)


func _option() -> OptionButton:
	var option := OptionButton.new()
	option.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	return option


func _label(value: String) -> Label:
	var label := Label.new()
	label.text = value
	label.vertical_alignment = VERTICAL_ALIGNMENT_CENTER
	return label


func _line_edit(value: String, placeholder: String) -> LineEdit:
	var edit := LineEdit.new()
	edit.text = value
	edit.placeholder_text = placeholder
	edit.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	edit.focus_entered.connect(_on_online_edit_focus_entered.bind(edit))
	edit.focus_exited.connect(_on_online_edit_focus_exited.bind(edit))
	return edit


func _row(label: String, input: Control) -> HBoxContainer:
	var row := HBoxContainer.new()
	row.add_child(_label(label))
	row.add_child(input)
	return row


func _button(text: String, callback: Callable) -> Button:
	var button := Button.new()
	button.text = text
	button.pressed.connect(callback)
	return button


func _format_result(result: Dictionary) -> String:
	var winner: Variant = result.get("winner", null)
	if (winner is int or winner is float) and int(winner) in [0, 1] and float(winner) == int(winner):
		return "玩家 %d 获胜" % (int(winner) + 1)
	if str(result.get("reason", "")) == "agreed":
		return "双方确认：平局"
	return "对局已结束；双方未确认出胜者。"


func _recovery_label(state: String) -> String:
	if state.begins_with("recovering"):
		return "正在恢复连接"
	if state.begins_with("waiting"):
		return "等待网络恢复"
	if state.begins_with("failed"):
		return "连接恢复失败"
	if state.begins_with("healthy"):
		return "连接正常"
	match state:
		_: return "网络状态未知"


func _show_error(code: String) -> void:
	# Keep only machine codes and stages, never room credentials, SDP or URLs.
	var safe_code := code if RegEx.create_from_string("^[a-z0-9_]{1,80}$").search(code) != null else "unclassified_error"
	var diagnostic := get_connection_diagnostic()
	diagnostic.erase("lastError")
	diagnostic["code"] = safe_code
	_last_connection_error = diagnostic
	push_warning("Online lobby diagnostic: " + JSON.stringify(diagnostic))
	var messages := {
		"invalid_service_url": "服务地址需以 http:// 或 https:// 开头。",
		"invalid_invitation": "加入码格式不正确。",
		"invalid_invite": "加入码不正确。请核对朋友发来的口令。",
		"invite_expired": "加入码已过期，房间已关闭。请让房主重新创建房间。",
		"room_expired": "房间已过期。请让房主重新创建房间。",
		"incompatible_build": "双方游戏版本或启用内容不一致。",
		"room_full": "房间已有两位玩家。",
		"room_closed": "房间已关闭或过期。",
		"incomplete_setup": "请先确认角色与援助。",
		"not_ready": "双方准备状态或网络参数尚未一致。",
		"command_outcome_uncertain": "服务器尚未确认上一步；请重试原操作。",
		"admission_retry_required": "上次创建/加入请求结果未知；请先重试原请求，避免重复建房。",
		"already_in_room": "你已在一个房间中；请先离开当前房间。",
		"peer_transport_missing": "点对点传输模块尚未加载。",
		"match_coordinator_missing": "在线对局协调器尚未加载。",
		"secure_random_unavailable": "浏览器安全随机数不可用。",
		"server_upgrade_required": "房间服务版本过旧，暂不支持房主统一网络设置；请升级服务后重试。",
		"network_profile_not_committed": "房主网络设置尚未同步完成；请重试后再连接。",
		"network_profile_changed": "房主网络设置已变化；请按新设置重新连接并准备。",
		"network_profile_mismatch": "当前连接与房主网络设置不一致；请重新连接。",
		"turn_not_configured": "服务未配置互联网中转。若使用本机或同一局域网，请由房主开启对应模式并重新连接；跨网络对战需先配置 TURN 服务。",
		"signal_delivery_failed": "连接邀请未送达对方。请确认对方仍在房间内，再由房主重试连接。",
		"negotiation_timeout": "等待房主连接请求超时，请由房主按连接并选择角色。",
		"peer_wait_timeout": "等待对手超时。请确认对方仍在房间，然后重新按连接。",
		"stale_negotiation": "连接握手已过期。请再按一次连接。",
		"connection_starting": "正在连接，请稍候，不必重复点击。",
		"signaling_disconnected": "信令在建立通道时断开。请再按一次连接。",
		"data_channels_timeout": "双方未能建立对战通道，请重试连接；跨网络对战请关闭本机 / 同一局域网模式。",
	}
	if code.contains("turn_not_configured"):
		_status.text = str(messages.turn_not_configured)
	else:
		_status.text = str(messages.get(code, "操作未完成：" + code))
	if code in ["http_transport_failed", "http_request_start_failed"] and room_client != null:
		var last_http := _as_dictionary(room_client.get_last_http_diagnostic())
		var safe_diagnostic := {
			"phase": str(last_http.get("phase", "unknown")),
			"transportResult": last_http.get("transportResult", "unknown"),
			"httpStatus": int(last_http.get("httpStatus", 0)),
			"requestErrorCode": int(last_http.get("requestErrorCode", -1)),
		}
		push_warning("Online HTTP diagnostic (redacted): " + JSON.stringify(safe_diagnostic))


func _as_dictionary(value: Variant) -> Dictionary:
	return value if value is Dictionary else {}


func _as_array(value: Variant) -> Array:
	return value if value is Array else []


func _is_title_menu() -> bool:
	return is_instance_valid(game_root) and str(game_root.session.root_label) == "MENU"
