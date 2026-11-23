extends SceneTree

const Lobby = preload("res://online_lobby.gd")
const Adapter = preload("res://online_character_selection.gd")
const DisplayProjection = preload("res://authority_projection.gd")
var completed := {}

class Game extends Control:
	var title_menu: TitleMenu

class Room extends OnlineRoomClient:
	var state: Dictionary = {}
	var operations: Array[Dictionary] = []
	var cursors: Array = []
	func send_lineup_cursor(choice: Variant, request_peer: bool = false) -> void:
		cursors.append({"choice": choice, "requestPeer": request_peer})
	func refresh_state() -> Dictionary:
		return {"state": state.duplicate(true)}
	func command(operation: Dictionary) -> Dictionary:
		operations.append(operation.duplicate(true))
		if operation.type == "select": state.members[0].choice = operation.choice
		elif operation.type == "configure":
			state.stage = operation.stage
			state.rules = operation.rules
			state.mapConfirmed = true
		state.revision += 1
		state.setupRevision += 1
		return {"state": state.duplicate(true)}

func _initialize() -> void:
	call_deferred("run")

func run() -> void:
	root.size = Vector2i(900, 600)
	root.content_scale_size = Vector2i(600, 400)
	root.content_scale_mode = Window.CONTENT_SCALE_MODE_CANVAS_ITEMS
	var game := Game.new()
	root.add_child(game)
	game.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	var lobby := Lobby.new()
	root.add_child(lobby)
	lobby.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	await process_frame
	lobby.configure(null, game)
	lobby.set_process(false)
	lobby._slot = 0
	lobby._room_id = "test-room"
	var profile := {"id": "chrome-exp-d2-p6", "inputDelay": 2, "predictionWindow": 6}
	lobby._room_state = {
		"id": "test-room", "revision": 1, "setupRevision": 1, "phase": "lobby",
		"mode": "host-authoritative", "mapConfirmed": false, "stage": "流魂街",
		"rules": {"time": 60, "life": 2}, "networkProfile": profile,
		"members": [{"nickname": "Host", "signaling": true, "choice": null, "ready": false, "profile": null}, null]}
	lobby.room_client.free()
	var client := Room.new()
	lobby.add_child(client)
	client.state = lobby._room_state.duplicate(true)
	lobby.room_client = client
	lobby._network_profile_authority = profile
	lobby._show_room()
	assert(not lobby._endpoint.is_visible_in_tree())
	assert(not lobby._lan_candidate_opt_in.is_visible_in_tree())
	assert(not lobby._rotate_invite_button.is_visible_in_tree())
	assert(not lobby._rollback_options.visible)
	assert(not lobby._stage_summary.text.contains("流魂街"))
	assert(not lobby._stage_summary.text.contains("实验"))
	assert(not lobby._reselect_button.disabled)
	assert(lobby._connect_selection_button.disabled)
	assert(lobby._rules_draft == {"time": 60, "life": 2})
	lobby._open_lineup()
	lobby.set_physics_process(false)
	assert(lobby._selection_adapter is CharacterSelection)
	assert(lobby._selection_adapter.independent_selection)
	assert(not lobby._dialog.visible)
	assert(client.cursors.size() == 1 and client.cursors[0].requestPeer)
	var selector := lobby._selection_adapter
	assert(selector.selected[1] == -1)
	var peer_choice := {"fighter": "neji", "helper": ""}
	lobby._on_signaling_message({"type": "lineup_cursor", "choice": peer_choice, "requestPeer": true})
	assert(selector.selected[1] >= 0 and selector.available.fighters[selector.fighters[1]] == "neji")
	assert(client.cursors.size() == 2 and not client.cursors.back().requestPeer)
	selector.tick_local({"right": true})
	assert(client.cursors.back().choice == selector._local_choice_resource_ids())
	assert(client.operations.is_empty())
	lobby._on_selection_cancelled()
	assert(client.cursors.back().choice == null)
	assert(lobby._dialog.visible)
	assert(lobby._room_state.members[0].choice == null)
	lobby._open_lineup()
	lobby.set_physics_process(false)
	lobby._selection_adapter._on_local_confirmation_timeout(0)
	lobby._selection_adapter._on_local_confirmation_timeout(0)
	await process_frame
	assert(not lobby._selection_active and lobby._dialog.visible)
	assert(client.operations.size() == 1 and client.operations[0].type == "select")
	assert(lobby._room_state.members[0].choice != null)
	lobby._on_commit_setup_pressed()
	lobby.set_physics_process(false)
	assert(lobby._map_active and not lobby._dialog.visible)
	lobby._map_adapter._select("流魂街")
	lobby._map_adapter._confirm()
	await process_frame
	assert(not lobby._map_active and lobby._room_state.mapConfirmed)
	assert(lobby._room_state.stage == "流魂街")
	assert(lobby._stage_summary.text.contains("流魂街"))
	lobby._room_state.mapConfirmed = false
	var choice := {"fighter": "sasuke", "helper": "you"}
	lobby._room_state.members[0].choice = choice
	lobby._room_state.members[1] = {"nickname": "Guest", "signaling": true, "choice": {"fighter": "rifagu", "helper": "kon"}, "ready": false, "profile": null}
	lobby._refresh_room_view()
	assert(lobby._mode_choice.disabled)
	assert(not lobby._can_ready_current_room())
	lobby._room_state.mapConfirmed = true
	assert(lobby._can_ready_current_room())
	for member in lobby._room_state.members:
		member.ready = true
		member.profile = profile
	lobby._refresh_room_view()
	assert(lobby._reselect_button.disabled)
	assert(not lobby._start_button.disabled)
	lobby._maybe_auto_prepare()
	await process_frame
	assert(not lobby._prepare_in_flight)
	assert(lobby._room_state.phase == "lobby")
	if "--capture" in OS.get_cmdline_user_args():
		await capture("room")
		lobby._on_advanced_toggled(true)
		await capture("settings")
		lobby._on_advanced_toggled(false)
		lobby._on_commit_setup_pressed()
		lobby.set_physics_process(false)
		await capture("map")
		lobby._on_map_selection_cancelled(lobby._map_session_id)
	lobby._slot = 1
	lobby._refresh_room_view()
	assert(not lobby._setup_button.visible and not lobby._start_button.visible)
	lobby._room_state.mapConfirmed = false
	assert(not lobby._can_ready_current_room())
	assert(lobby._parse_invitation("https://example.test/play?invite=Calm-Otter-ABCDEFGH").code == "calm-otter-abcdefgh")
	var adapter := Adapter.new()
	root.add_child(adapter)
	adapter.independent_selection = true
	adapter.selection_completed.connect(func(value: Dictionary): completed = value)
	assert(adapter.begin(1, "independent", [{}, choice]) == "")
	adapter._on_local_confirmation_timeout(1)
	assert(adapter.phase == 1)
	adapter._on_local_confirmation_timeout(1)
	assert(not completed.is_empty())
	assert(completed.fighter == "sasuke")
	var projection := DisplayProjection.new()
	assert("res://generated/fighters/sasuke" in projection.resources)
	assert("res://generated/helpers/you" in projection.resources)
	assert(projection.resources == DisplayProjection.new().resources)
	adapter.free()
	lobby._slot = 0
	var departed: Dictionary = lobby._room_state.duplicate(true)
	departed.revision += 1
	departed.members[1] = null
	departed.members[0].ready = false
	lobby._accept_state(departed)
	assert(lobby._needs_new_invite and lobby._invite_code.is_empty())
	assert(lobby._room_state.members[0].choice == choice)
	assert(not lobby._mode_choice.disabled and lobby._start_button.disabled)
	lobby.free()
	game.free()
	print("ONLINE_MENU_FLOW_OK independent_selection=true empty_host=true map_gate=true ready_lock=true explicit_start=true guest_permissions=true invite_link=true expanded_projection=true")
	quit()


func capture(label: String) -> void:
	await process_frame
	await RenderingServer.frame_post_draw
	root.get_texture().get_image().save_png("/private/tmp/bvn-menu-" + label + ".png")
