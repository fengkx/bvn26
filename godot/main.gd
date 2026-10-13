extends Control

signal before_recorded_intro_poll(event: Dictionary)

@onready var tick_label: Label = %TickLabel
@onready var state_label: Label = %StateLabel
@onready var config_label: Label = %Config
@onready var game_world: GameWorld = %Game
@onready var naruto: FighterRuntime = %Naruto
@onready var ichigo: FighterRuntime = %Ichigo
@onready var current_world: TimelinePreview = %CurrentWorld
@onready var naruto_energy: EnergyBar = %NarutoEnergy
@onready var ichigo_energy: EnergyBar = %IchigoEnergy
@onready var fight_hud: Control = %FightHud
@onready var title_menu: TitleMenu = %TitleMenu
@onready var key_settings: KeySettings = %KeySettings
@onready var combo_hud: ComboHud = %ComboHud
@onready var black_mu: ScriptedTimelinePreview = %BlackMu
@onready var ts_face: TimelinePreview = %TsFace

var countdown: MatchCountdown
var timeout_timeline: KoTimeline
var timeout_clip: KoClip
var nextfight_from_timeout := false
var _source_nextfight_goto_phase := false
var _intro_just_finished := false
var config_menu: ConfigMenu
var pause_menu: BattlePauseMenu
var health_hud: HealthHud
var character_selection: CharacterSelection
var map_selection: MapSelection
var stage_background: TimelinePreview
var battle_intro: BattleIntro
var stage_sound: StageSound
var source_random := SourceRandom.new()
var source_clock = preload("res://source_clock.gd").new()
var selected_stage: String = "现世"
var opponent_driver: AiCpuDriver
var opponent_input_context: AiBodyContext
var cpu_services: AiCombatServices
var cpu_stage_registry := StageHitRegistry.new()
var cpu_profile: Dictionary
var cpu_visual_spec: Dictionary = JSON.parse_string(FileAccess.get_file_as_string("res://generated/main/ai_visual_services.json"))
var cpu_unresolved_services: Dictionary = {}
var ko_recorded_timers: bool = false
var ko_timeline: KoTimeline
var ko_clip: KoClip
var ko_state: Dictionary = {}
var ko_metadata: Dictionary
var ko_active: bool = false
var ko_paused: bool = false
var ko_menu_enabled: bool = true
var ko_terminal_pending: bool = false
var ko_nextfight_timer: Timer
var ko_interval_sequence: int = 0

var match_input := preload("res://match_input.gd").new()
var input_recording_path := ""
var _match_inputs: Dictionary = {}
var _match_input_active := false

var session := GameSession.new()
var diagnostics := DiagnosticRuntime.new()
var _diagnostic_initial_players: Dictionary = {}
var _diagnostic_progress_signature := ""
var _diagnostic_progress_tick := 0
var _diagnostic_last_progress_ms := 0
var _diagnostic_watchdog_elapsed_ms := 0
var _diagnostic_stall_reported := false
var super_runtime := SuperRuntime.new()
var super_presentation := SuperPresentation.new()
var physics_tick: int = 0
var diagnostic_input_provider: Callable
var naruto_helper: HelperRuntime
var ichigo_helper: HelperRuntime
var screen_flash: ColorRect
var screen_flash_age: int = -1
# Source pauseGame()/resumeGame() from XG_*x clips. Stops fighter/helper mcs.
var hit_fx_pause_count: int = 0
var player_body_driver: Node
var source_callbacks: SourceCallbackRegistry
var source_health_rules: RefCounted
var source_health_registration: int
var source_frame_sequence: int = 0
var source_child_frames: Array[Dictionary] = []
var player_body_services: AiCombatServices
var training_timer: Timer
var recorded_training_timers := false

# main.swf DefineSprite 1745 frames 2-9 after shinemc.cmc.gotoAndPlay(2).
const SHINE_ALPHA_TERMS: PackedInt32Array = [114, 100, 85, 71, 57, 43, 28, 14]
const SHINE_SHADER := """
shader_type canvas_item;
uniform sampler2D screen_texture : hint_screen_texture, repeat_disable, filter_nearest;
uniform vec3 tint = vec3(1.0);
uniform float opacity = 0.0;

void fragment() {
	vec3 base = textureLod(screen_texture, SCREEN_UV, 0.0).rgb;
	vec3 low = 2.0 * base * tint;
	vec3 high = 1.0 - 2.0 * (1.0 - base) * (1.0 - tint);
	vec3 overlay = mix(low, high, step(vec3(0.5), base));
	COLOR = vec4(mix(base, overlay, opacity), 1.0);
}
"""


func _ready() -> void:
	# Form replacement is incomplete; keep transformation out of playable matches.
	naruto.disabled_actions = ["万解"]
	ichigo.disabled_actions = ["万解"]
	cpu_profile = JSON.parse_string(FileAccess.get_file_as_string("res://generated/main/execution_profile.json"))
	cpu_stage_registry.configure(JSON.parse_string(FileAccess.get_file_as_string("res://generated/effects/XG_baoqi/stage_hit.json")))
	source_random.use_live_random()
	add_child(diagnostics)
	diagnostics.snapshot_provider = Callable(self, "_diagnostic_snapshot")
	diagnostics.visibility_changed.connect(_on_diagnostic_visibility_changed)
	source_random.value_consumed.connect(_on_random_value_consumed)
	source_clock.value_consumed.connect(_on_clock_value_consumed)
	stage_sound = StageSound.new()
	stage_sound.random_source = source_random
	add_child(stage_sound)
	character_selection = CharacterSelection.new()
	character_selection.z_index = 200
	character_selection.visible = false
	add_child(character_selection)
	character_selection.confirmed.connect(_on_characters_confirmed)
	character_selection.cancelled.connect(_goto_menu)
	map_selection = MapSelection.new()
	map_selection.z_index = 200
	map_selection.visible = false
	add_child(map_selection)
	map_selection.confirmed.connect(_on_map_confirmed)
	map_selection.cancelled.connect(_goto_menu)
	pause_menu = BattlePauseMenu.new()
	pause_menu.z_index = 157
	add_child(pause_menu)
	pause_menu.opened.connect(_pause_battle)
	pause_menu.resume_requested.connect(_resume_battle)
	pause_menu.title_requested.connect(_return_to_title)
	health_hud = HealthHud.new()
	health_hud.z_index = 110
	health_hud.mouse_filter = Control.MOUSE_FILTER_IGNORE
	add_child(health_hud)
	health_hud.fighters = [naruto, ichigo]
	battle_intro = BattleIntro.new()
	add_child(battle_intro)
	battle_intro.interval_cleared.connect(_ko_clear_interval)
	battle_intro.fight_started.connect(_ko_fight_started)
	battle_intro.fight_started.connect(_diagnostic_fight_started)
	naruto.ko_requested.connect(_on_ko_requested)
	ichigo.ko_requested.connect(_on_ko_requested)
	session.load_store()
	config_menu = ConfigMenu.new()
	config_menu.session = session
	add_child(config_menu)
	config_menu.visible = false
	config_menu.key_settings_requested.connect(_goto_key_settings)
	config_menu.menu_requested.connect(_goto_menu)
	key_settings.session = session
	key_settings.refresh_view()
	title_menu.confirmed.connect(_on_menu_confirmed)
	key_settings.back_to_config.connect(_goto_config)
	_setup_screen_flash()
	super_presentation.load_spec("res://generated/main/hit_receive.json")
	super_runtime.presentation = super_presentation
	super_runtime.xg_requested.connect(_spawn_hit_effect)
	_place_fighters_from_map()
	# isHitBan uses ban._x/_y/_width, not shape-bounds top (global bounds
	# also include the camera transform after GameWorld.enter_frame).
	var platforms := current_world.named_instance_ledges("ban")
	var p1_origin := current_world.named_instance_origin("p1")
	var ground_y := p1_origin.y if p1_origin != Vector2.INF else naruto.position.y
	var wall_max := game_world.wall_max()
	naruto.configure_stage(ground_y, platforms, GameWorld.WALL_LEFT, wall_max)
	ichigo.configure_stage(ground_y, platforms, GameWorld.WALL_LEFT, wall_max)
	naruto.player_slot = "p1"
	ichigo.player_slot = "p2"
	naruto.opponent = ichigo
	ichigo.opponent = naruto
	naruto.super_runtime = super_runtime
	ichigo.super_runtime = super_runtime
	super_runtime.shine_requested.connect(_start_screen_flash)
	naruto.sync_body_collision_position()
	ichigo.sync_body_collision_position()
	naruto.hit_effect_requested.connect(_spawn_hit_effect)
	ichigo.hit_effect_requested.connect(_spawn_hit_effect)
	naruto.screen_flash_requested.connect(_start_screen_flash)
	ichigo.screen_flash_requested.connect(_start_screen_flash)
	naruto.combo_hud_requested.connect(_play_combo_hud)
	ichigo.combo_hud_requested.connect(_play_combo_hud)
	naruto.super_event_applied.connect(_on_selected_super_event.bind(naruto))
	ichigo.super_event_applied.connect(_on_selected_super_event.bind(ichigo))
	combo_hud.load_spec("res://generated/main/hit_receive.json")
	# This slice locks P1/P2 assistance to Gaara/Kon.
	naruto_helper = _make_helper("res://generated/helpers/woailuo")
	ichigo_helper = _make_helper("res://generated/helpers/kon")
	_set_diagnostic_actor(naruto, "p1")
	_set_diagnostic_actor(ichigo, "p2")
	var helper_presentation: Dictionary = JSON.parse_string(FileAccess.get_file_as_string("res://generated/main/helper_portraits/presentation.json"))
	var depths: Dictionary = helper_presentation["depths"]
	naruto.z_index = int(depths["p1"])
	ichigo.z_index = int(depths["p2"])
	naruto_helper.z_index = int(depths["p1fz"])
	ichigo_helper.z_index = int(depths["p2fz"])
	naruto_energy.set_helper(naruto_helper.helper_id)
	ichigo_energy.set_helper(ichigo_helper.helper_id)
	game_world.snap(naruto, ichigo)
	_goto_menu()
	print(
		"M0_BOOT_OK ",
		JSON.stringify(
			{
				"godot": Engine.get_version_info()["string"],
				"physics_hz": Engine.physics_ticks_per_second,
				"display_server": DisplayServer.get_name(),
			}
		)
	)


func _input(event: InputEvent) -> void:
	if session.root_label == "游戏设置" and event is InputEventKey and event.pressed:
		config_menu.key_down(session.menu_held())
		get_viewport().set_input_as_handled()
		return
	if match_input.playback:
		return
	var control := pause_menu.control_from_event(event)
	if not control.is_empty():
		deliver_match_control(control)


func deliver_match_control(control: Dictionary, from_playback: bool = false) -> void:
	if match_input.playback != from_playback or not match_input.valid_control(control):
		return
	if session.root_label != "游戏场景" or battle_intro.active or naruto.sw or ichigo.sw or not ko_menu_enabled:
		if from_playback:
			match_input.error = "Recorded control rejected by the current match gate"
		return
	if not from_playback:
		match_input.record_control(physics_tick, control)
	pause_menu.handle_control(control)


func _deliver_recorded_controls() -> bool:
	for control: Dictionary in match_input.take_controls(physics_tick):
		deliver_match_control(control, true)
	return _check_match_input() and session.root_label == "游戏场景"


func _check_match_input() -> bool:
	if match_input.error.is_empty():
		return true
	set_physics_process(false)
	_stop_ko()
	_stop_training_recovery()
	_stop_combat_drivers()
	state_label.text = "Input playback stopped: " + match_input.error
	push_error(state_label.text)
	return false


func arm_input_recording(path: String) -> String:
	if physics_tick != 0 or session.root_label == "游戏场景" or match_input.playback or path.is_empty():
		return "Recording must be armed before a fresh match, with an output path"
	input_recording_path = path
	return ""


func _input_setup() -> Dictionary:
	return {
		"start_tick": physics_tick, "stage": selected_stage,
		"modo": session.modo, "maxhp": session.maxhp, "ai_level": session.ai_level,
		"maxtime": session.maxtime, "engine": Engine.get_version_info().string,
		"fighters": [naruto.fighter_directory.get_file(), ichigo.fighter_directory.get_file()],
		"helpers": [naruto_helper.helper_directory.get_file(), ichigo_helper.helper_directory.get_file()],
	}


func start_input_playback(data: Variant) -> String:
	if session.root_label == "游戏场景" or physics_tick != 0 or _match_input_active:
		return "Playback requires a fresh main scene"
	if not input_recording_path.is_empty():
		return "Playback cannot start while recording is armed"
	var problem: String = match_input.validate(data)
	if not problem.is_empty():
		return problem
	var setup: Dictionary = data.setup
	if setup.get("engine") != Engine.get_version_info().string:
		return "Recording engine version differs"
	for key in ["modo", "maxhp", "ai_level", "maxtime"]:
		if not (setup.get(key) is int or setup.get(key) is float) or not is_finite(float(setup[key])):
			return "Missing numeric setup field: " + key
	for key in ["modo", "ai_level", "maxtime", "start_tick"]:
		if setup[key] != int(setup[key]):
			return "Non-integral setup field: " + key
	if int(setup.modo) not in [2, 3, 4] or setup.maxhp <= 0 or int(setup.ai_level) not in [1, 2, 3, 4, 5] or setup.maxtime < 0:
		return "Unsupported match settings"
	var selected := {}
	for kind in ["fighters", "helpers"]:
		if not setup.get(kind) is Array or setup[kind].size() != 2:
			return "Missing match roster: " + kind
		selected[kind] = []
		for name in setup[kind]:
			if not name is String or name.contains("/"):
				return "Invalid roster resource"
			var id := _selection_id_for_resource(kind, name)
			if id.is_empty():
				return "Unavailable roster resource: " + name
			selected[kind].append(id)
	var catalog: Dictionary = JSON.parse_string(FileAccess.get_file_as_string("res://generated/stages/catalog/catalog.json"))
	var stage_found := false
	for stage: Dictionary in catalog.stages:
		stage_found = stage_found or stage.id == setup.get("stage")
	if not stage_found:
		return "Unavailable recorded stage"
	problem = match_input.begin_playback(data)
	if not problem.is_empty():
		return problem
	session.maxhp = float(setup.maxhp)
	session.ai_level = int(setup.ai_level)
	session.maxtime = int(setup.maxtime)
	physics_tick = int(setup.start_tick)
	_replace_selected_actors(selected.fighters, selected.helpers)
	_load_selected_stage(setup.stage)
	_enter_current_fight(int(setup.modo))
	stage_sound.select()
	stage_sound.start()
	return ""


func _finish_match_input(reason: String) -> void:
	if not _match_input_active:
		return
	_match_input_active = false
	match_input.finish(physics_tick, reason)
	if not input_recording_path.is_empty() and match_input.document.get("complete", false):
		var output := FileAccess.open(input_recording_path, FileAccess.WRITE)
		if output == null:
			push_error("Cannot save input recording: " + input_recording_path)
		else:
			output.store_string(JSON.stringify(match_input.document))
			print("MATCH_INPUT_SAVED ", input_recording_path)
		input_recording_path = ""
	_check_match_input()


func _pause_battle() -> void:
	# frame_8 pauseGame2: stopMc is conditional; hit effects keep advancing.
	for actor in [naruto, ichigo, naruto_helper, ichigo_helper]:
		super_runtime.stop_mc(actor)
	super_runtime.game_paused = true
	naruto.root_zhanting = true
	ichigo.root_zhanting = true
	diagnostics.pause_snapshot("user_pause", _diagnostic_snapshot())


func _resume_battle() -> void:
	super_runtime.game_paused = false
	naruto.root_zhanting = false
	ichigo.root_zhanting = false
	super_runtime.zhanting = false
	for actor in [naruto, ichigo, naruto_helper, ichigo_helper]:
		super_runtime.play_mc(actor)
	super_presentation.resume_black_stg()
	_sync_super_stage()
	diagnostics.pause_snapshot("user_resume", _diagnostic_snapshot())


func _physics_process(_delta: float) -> void:
	match session.root_label:
		"MENU":
			title_menu.apply_held(session.menu_held())
		"游戏设置":
			config_menu.tick()
		"键位设置":
			key_settings.apply_held(key_settings.navigation_held())
		"选人画面":
			var p2 := session.fighter_input("p2")
			p2["confirm"] = p2.attack
			p2["back"] = p2.jump
			character_selection.tick(session.menu_held(), p2)
		"地图":
			map_selection.tick(session.menu_held())
		"游戏场景":
			if not _deliver_recorded_controls():
				return
			pause_menu.tick()
			_advance_fight()


func _process(delta: float) -> void:
	if diagnostics.match_id.is_empty():
		return
	_diagnostic_watchdog_elapsed_ms += int(delta * 1000.0)
	if _diagnostic_watchdog_elapsed_ms < 1000:
		return
	_diagnostic_watchdog_elapsed_ms = 0
	_diagnostic_watchdog_step(Time.get_ticks_msec())


func _diagnostic_watchdog_step(now_ms: int) -> void:
	if diagnostics.match_id.is_empty():
		return
	var pause := _diagnostic_pause_state()
	if bool(pause.userPaused) or not diagnostics.page_visible or battle_intro.active:
		_diagnostic_reset_progress_watch()
		return
	var signature := JSON.stringify({"players": [
		_diagnostic_player(naruto, naruto_helper),
		_diagnostic_player(ichigo, ichigo_helper)], "pause": pause})
	if signature != _diagnostic_progress_signature:
		_diagnostic_progress_signature = signature
		_diagnostic_last_progress_ms = now_ms
		_diagnostic_progress_tick = physics_tick
		_diagnostic_stall_reported = false
		return
	if not _diagnostic_stall_reported and now_ms - _diagnostic_last_progress_ms >= 10000:
		_diagnostic_stall_reported = true
		var reason := "suspected_super_pause_stall" if bool(pause.globalSuperPaused) else "suspected_stall"
		if has_meta("online_wait") and physics_tick == _diagnostic_progress_tick:
			reason = "online_simulation_stall"
		diagnostics.freeze_diagnostic(reason, {
			"onlineWait": get_meta("online_wait", ""),
			"simulationAdvanced": physics_tick != _diagnostic_progress_tick,
			"classification": "heuristic_not_deadlock_proof",
			"noProgressMs": now_ms - _diagnostic_last_progress_ms,
			"userPaused": false,
			"globalSuperPaused": bool(pause.globalSuperPaused),
			"pageVisible": diagnostics.page_visible,
		}, _diagnostic_snapshot())


func _diagnostic_reset_progress_watch() -> void:
	_diagnostic_progress_signature = ""
	_diagnostic_last_progress_ms = Time.get_ticks_msec()
	_diagnostic_stall_reported = false


func _on_diagnostic_visibility_changed(_visible: bool) -> void:
	_diagnostic_reset_progress_watch()


func _on_menu_confirmed(item_id: String) -> void:
	for item in TitleMenu.ITEMS:
		if str(item["id"]) != item_id:
			continue
		if item_id == "key_settings":
			_goto_config()
			return
		if int(item["modo"]) in [2, 3, 4]:
			_goto_character_selection(int(item["modo"]))
		return


func _goto_character_selection(modo: int) -> void:
	_finish_match_input("selection")
	session.modo = modo
	session.root_label = "选人画面"
	title_menu.visible = false
	key_settings.visible = false
	config_menu.visible = false
	map_selection.leave()
	character_selection.reset(modo)


func _on_characters_confirmed(fighters: Array, helpers: Array) -> void:
	_replace_selected_actors(fighters, helpers)
	character_selection.leave()
	_goto_map_selection(session.modo)


func _replace_selected_actors(fighters: Array, helpers: Array) -> void:
	_stop_combat_drivers()
	var replacements: Array[FighterRuntime] = []
	var helper_replacements: Array[HelperRuntime] = []
	for i in 2:
		var old: FighterRuntime = naruto if i == 0 else ichigo
		var fighter := FighterRuntime.new()
		fighter.disabled_actions = ["万解"]
		fighter.fighter_directory = "res://generated/fighters/" + str(character_selection.available.fighters[fighters[i]])
		fighter.name = old.name
		fighter.player_slot = "p%d" % (i + 1)
		fighter.position = old.position
		fighter.facing = old.facing
		fighter.z_index = old.z_index
		fighter.display_depth = old.display_depth
		game_world.remove_child(old)
		old.queue_free()
		game_world.add_child(fighter)
		fighter.owner = self
		fighter.unique_name_in_owner = true
		fighter.super_runtime = super_runtime
		fighter.ko_requested.connect(_on_ko_requested)
		fighter.hit_effect_requested.connect(_spawn_hit_effect)
		fighter.screen_flash_requested.connect(_start_screen_flash)
		fighter.combo_hud_requested.connect(_play_combo_hud)
		fighter.super_event_applied.connect(_on_selected_super_event.bind(fighter))
		replacements.append(fighter)
		var old_helper: HelperRuntime = naruto_helper if i == 0 else ichigo_helper
		var helper := _make_helper("res://generated/helpers/" + str(character_selection.available.helpers[helpers[i]]))
		helper.z_index = old_helper.z_index
		game_world.remove_child(old_helper)
		old_helper.queue_free()
		helper_replacements.append(helper)
	naruto = replacements[0]
	ichigo = replacements[1]
	naruto.opponent = ichigo
	ichigo.opponent = naruto
	naruto_helper = helper_replacements[0]
	ichigo_helper = helper_replacements[1]
	_set_diagnostic_actor(naruto, "p1")
	_set_diagnostic_actor(ichigo, "p2")
	health_hud.fighters = [naruto, ichigo]
	health_hud.set_fighter_portraits(fighters)
	naruto_energy.set_helper(naruto_helper.helper_id)
	ichigo_energy.set_helper(ichigo_helper.helper_id)


func configure_diagnostic_roster(players: Dictionary) -> String:
	var fighter_ids: Array[String] = []
	var helper_ids: Array[String] = []
	for slot in ["p1", "p2"]:
		var player: Dictionary = players.get(slot, {})
		var fighter_id := _selection_id_for_resource("fighters", str(player.get("resourcePath", "")))
		var helper: Dictionary = player.get("helper", {})
		var helper_id := _selection_id_for_resource("helpers", str(helper.get("resourcePath", "")))
		if fighter_id.is_empty() or helper_id.is_empty():
			return "Unavailable fighter/helper resource for " + slot
		fighter_ids.append(fighter_id)
		helper_ids.append(helper_id)
	var same_fighters := naruto.fighter_directory.get_file() == str(character_selection.available.fighters[fighter_ids[0]]) \
		and ichigo.fighter_directory.get_file() == str(character_selection.available.fighters[fighter_ids[1]])
	var same_helpers := naruto_helper.helper_directory.get_file() == str(character_selection.available.helpers[helper_ids[0]]) \
		and ichigo_helper.helper_directory.get_file() == str(character_selection.available.helpers[helper_ids[1]])
	if not same_fighters or not same_helpers:
		_replace_selected_actors(fighter_ids, helper_ids)
	return ""


func _selection_id_for_resource(kind: String, resource_path: String) -> String:
	var collection: Dictionary = character_selection.available.get(kind, {})
	var resource_name := resource_path.trim_suffix("/").get_file()
	for selection_id in collection:
		if str(collection[selection_id]) == resource_name:
			return str(selection_id)
	return ""


func _on_selected_super_event(event: Dictionary, fighter: FighterRuntime) -> void:
	_on_super_event(event, fighter)


func _goto_map_selection(modo: int) -> void:
	session.modo = modo
	session.root_label = "地图"
	title_menu.visible = false
	key_settings.visible = false
	config_menu.visible = false
	map_selection.visible = true
	map_selection.reset()


func _on_map_confirmed(stage_id: String) -> void:
	_load_selected_stage(stage_id)
	map_selection.leave()
	_enter_current_fight(session.modo)
	stage_sound.select()
	stage_sound.start()


func _load_selected_stage(stage_id: String) -> void:
	var catalog: Dictionary = JSON.parse_string(FileAccess.get_file_as_string("res://generated/stages/catalog/catalog.json"))
	for stage: Dictionary in catalog["stages"]:
		if str(stage["id"]) != stage_id:
			continue
		if stage_background != null:
			remove_child(stage_background)
			stage_background.queue_free()
		stage_background = TimelinePreview.new()
		stage_background.fighter_directory = "res://generated/stages/catalog/" + str(stage["background_directory"])
		stage_background.initial_frame = int(stage["background_frame"])
		stage_background.autoplay = false
		add_child(stage_background)
		move_child(stage_background, 1)
		var replacement := TimelinePreview.new()
		replacement.name = "CurrentWorld"
		replacement.fighter_directory = "res://generated/stages/catalog/" + str(stage["directory"])
		replacement.initial_frame = int(stage["frame"])
		replacement.autoplay = false
		replacement.preserve_root_depths = true
		game_world.remove_child(current_world)
		current_world.queue_free()
		current_world = replacement
		game_world.add_child(current_world)
		current_world.owner = self
		current_world.unique_name_in_owner = true
		game_world.move_child(current_world, 0)
		stage_sound.stop()
		stage_sound.load_manifest("res://generated/stages/catalog/music/frame_%d.json" % int(stage["frame"]))
		selected_stage = stage_id
		game_world.map_size_x = float(catalog["map_size_x"])
		game_world.lock_min = 0.0
		game_world.lock_max = 0.0
		var platforms := current_world.named_instance_ledges("ban")
		for fighter in [naruto, ichigo]:
			fighter.configure_stage(float(catalog["floor_y"]), platforms, GameWorld.WALL_LEFT, game_world.wall_max())
		return
	push_error("Unknown source stage: " + stage_id)


func _return_to_title() -> void:
	# Leaving the source battle frame destroys its clips. Recreate the scene
	# so hitstun, airborne motion, helpers and input history cannot survive.
	_goto_menu()
	get_tree().reload_current_scene()


func _goto_menu() -> void:
	_finish_match_input("title")
	diagnostics.end_match("left_battle")
	_stop_ko()
	_stop_combat_drivers()
	if battle_intro != null:
		battle_intro.cancel()
	stage_sound.stop()
	map_selection.leave()
	character_selection.leave()
	# Source frame_10: stop(); _root.stage = 0; downtxts.clean(); vertxt.
	pause_menu.visible = false
	super_runtime.game_paused = false
	for child in game_world.get_children():
		if child is HitEffectRuntime:
			game_world.remove_child(child)
			child.queue_free()
	for helper in [naruto_helper, ichigo_helper]:
		if helper != null:
			helper.deactivate()
	hit_fx_pause_count = 0
	screen_flash.visible = false
	screen_flash_age = -1
	session.root_label = "MENU"
	title_menu.visible = true
	key_settings.visible = false
	config_menu.visible = false
	fight_hud.visible = false
	health_hud.visible = false
	if stage_background != null:
		stage_background.visible = false
	game_world.visible = false
	if black_mu != null:
		black_mu.visible = false
	if ts_face != null:
		ts_face.visible = false
	combo_hud.visible = false
	naruto_energy.visible = false
	ichigo_energy.visible = false
	if super_runtime != null:
		_reset_super()
	title_menu.reset()


func _goto_config() -> void:
	session.root_label = "游戏设置"
	title_menu.visible = false
	key_settings.visible = false
	config_menu.visible = true
	config_menu.reset()


func _goto_key_settings() -> void:
	config_menu.visible = false
	# Source: cselect==1 + J → gotoAndStop("键位设置")
	session.root_label = "键位设置"
	title_menu.visible = false
	key_settings.visible = true
	fight_hud.visible = false
	health_hud.visible = false
	if stage_background != null:
		stage_background.visible = false
	game_world.visible = false
	if black_mu != null:
		black_mu.visible = false
	if ts_face != null:
		ts_face.visible = false
	combo_hud.visible = false
	key_settings.reset()


func _enter_current_fight(modo: int) -> void:
	if match_input.finished:
		match_input = preload("res://match_input.gd").new()
	_stop_ko()
	_stop_combat_drivers()
	# Fighters/assists remain locked; the map comes from the original map selector.
	# Source 597/600/603: only modo=2 enables p2cpu. Selection is fixed here.
	session.modo = modo
	session.p1cpu = false
	session.p2cpu = modo == 2
	_set_diagnostic_actor(naruto, "p1")
	_set_diagnostic_actor(ichigo, "p2")
	session.root_label = "游戏场景"
	title_menu.visible = false
	key_settings.visible = false
	config_menu.visible = false
	fight_hud.visible = false
	health_hud.visible = true
	if stage_background != null:
		stage_background.visible = true
	game_world.visible = true
	if black_mu != null:
		black_mu.visible = true
	if ts_face != null:
		ts_face.visible = true
	combo_hud.visible = not combo_hud.has_meta("suppress_display")
	naruto_energy.visible = true
	ichigo_energy.visible = true
	_initialize_fight()
	health_hud.set_wins(1, 1)
	_start_combat_drivers()
	_start_countdown()
	_start_training_recovery()
	diagnostics.begin_match(_diagnostic_snapshot(true))
	_match_input_active = true
	if not input_recording_path.is_empty():
		match_input.begin_recording(_input_setup())
	battle_intro.begin([naruto, ichigo])
	health_hud.spec["placement"] = battle_intro.spec["hud_frames"]["1"]
	game_world.focus = battle_intro.focus
	_refresh_bind_label()


func _initialize_fight() -> void:
	health_hud.reset()
	# Fresh match allocation also resets presentation and runtime state.
	naruto.modo = session.modo
	ichigo.modo = session.modo
	naruto.sw = false
	ichigo.sw = false
	naruto.health = session.maxhp
	ichigo.health = session.maxhp
	naruto.max_health = session.maxhp
	ichigo.max_health = session.maxhp
	naruto.displayed_health = session.maxhp
	ichigo.displayed_health = session.maxhp
	naruto.hits = 0
	ichigo.hits = 0
	naruto.energy = 0.0
	ichigo.energy = 0.0
	_place_fighters_from_map()
	naruto.set_facing(1)
	ichigo.set_facing(-1)
	naruto.start_action("站立")
	ichigo.start_action("站立")
	naruto.sync_body_collision_position()
	ichigo.sync_body_collision_position()
	game_world.focus = "all"
	game_world.snap(naruto, ichigo)
	_reset_super()


func _chushi() -> void:
	# main frame_8 only restores keys, spawn transforms, HP and roster metadata.
	# BODY frame scripts own action state; nextfight retains energy and pause.
	for fighter: FighterRuntime in [naruto, ichigo]:
		fighter.health = session.maxhp
	_place_fighters_from_map()
	naruto.set_facing(1)
	ichigo.set_facing(-1)
	naruto.sync_body_collision_position()
	ichigo.sync_body_collision_position()


func _advance_fight(recorded_events: Array = [], root_observer: Callable = Callable(), event_supplier: Callable = Callable()) -> void:
	if not _deliver_recorded_controls():
		return
	black_mu.advance_display_timeline()
	# Both keyboard and AI actors use the same registered source callbacks.
	var skip := match_input.poll_intro(physics_tick + 1, func() -> bool:
		return session.is_slot_down("j") or session.is_slot_down("N1"))
	if not _check_match_input():
		return
	battle_intro.tick(1.0 / Engine.physics_ticks_per_second, skip, true)
	# The ready clip's terminal frame writes the fight-start flag after the
	# current root snapshot. Keep the pre-callback floor state for that sample.
	var intro_boundary_pending: bool = battle_intro.active and battle_intro.clips.ready.current_source_frame() == 127
	if timeout_timeline != null:
		timeout_timeline.display_tick = physics_tick + 1
		timeout_timeline.advance_timelines()
		timeout_clip.refresh_from_scheduler()
	if ko_timeline != null:
		ko_timeline.display_tick = physics_tick + 1
		ko_timeline.advance_timelines()
		ko_clip.refresh_from_scheduler()
		if ko_terminal_pending:
			return
	_advance_screen_flash()
	health_hud.spec["placement"] = battle_intro.spec["hud_frames"][str(battle_intro.hud_frame)]
	combo_hud.tick()
	if super_presentation != null:
		super_presentation.tick()
	physics_tick += 1
	for fighter: FighterRuntime in [naruto, ichigo]:
		fighter.diagnostic_tick = physics_tick
	for helper: HelperRuntime in [naruto_helper, ichigo_helper]:
		if helper != null:
			helper.diagnostic_tick = physics_tick
	if tick_label.is_visible_in_tree():
		tick_label.text = "Fixed simulation tick: %d" % physics_tick
	assert(opponent_driver != null and player_body_driver != null and source_callbacks != null)
	var fighters: Array[FighterRuntime] = [ichigo, naruto]
	var helpers: Array = []
	if naruto_helper != null:
		helpers.append(naruto_helper)
	if ichigo_helper != null:
		helpers.append(ichigo_helper)
	naruto.super_helpers = helpers
	ichigo.super_helpers = helpers
	_match_inputs = match_input.poll_players(physics_tick, _sample_match_player)
	if not _check_match_input():
		return
	if player_body_driver != null:
		player_body_driver.begin_tick(physics_tick, _input_for(naruto))
	if opponent_input_context != null:
		opponent_input_context.inputs = _input_for(ichigo)
	opponent_driver.prepare_display_tick(physics_tick)
	for helper in helpers:
		helper.advance_timeline()
	for fighter in fighters:
		if fighter == ichigo:
			opponent_driver.advance_timeline()
		else:
			player_body_driver.advance_timeline()
	if cpu_services != null:
		cpu_services.advance_stage_timelines()
	if player_body_services != null:
		player_body_services.advance_stage_timelines()
	# Recorded callbacks carry their phase explicitly; do not infer it from
	# milliseconds or move an already queued frame script past the callback.
	for event: Dictionary in _recorded_events_for_phase(recorded_events, "after_actor_advance", event_supplier):
		assert(event["phase"] == "after_actor_advance", "Unsupported intro callback phase")
		if event.get("kind") == "countdown":
			assert(ko_recorded_timers and countdown != null)
			countdown.fire()
			continue
		if event.get("kind") == "body_timeout":
			var driver: Node = player_body_driver._driver if event.slot == "p1" else opponent_driver
			var fired: bool = driver.timeouts.recorded and driver.timeouts.fire_recorded(int(event.id))
			if not fired and event_supplier.is_valid():
				continue
			if not fired:
				match_input.error = "Rejected recorded BODY timeout"
				return
			continue
		if event.get("kind", "intro_poll") == "training_recovery":
			assert(recorded_training_timers and training_timer != null)
			training_timer.timeout.emit()
			continue
		if event.get("kind", "intro_poll") == "ai_random":
			var sampled := ichigo.ai_random_clock.fire_recorded(int(event["time_ms"]))
			assert(sampled, "Rejected recorded AI random refresh")
			continue
		assert(event.get("kind", "intro_poll") == "intro_poll", "Unknown recorded event kind")
		before_recorded_intro_poll.emit(event)
		var delivered := battle_intro.deliver_recorded_poll(int(event["sequence"]), int(event["time_ms"]))
		assert(delivered, "Rejected recorded intro callback: " + battle_intro.poll_replay_error)
	battle_intro.observe_fighter_frames()
	if player_body_driver != null:
		player_body_driver.prepare_callbacks()
	var initial_frame_counts := {}
	for fighter in fighters:
		initial_frame_counts[fighter] = fighter._ai_pending_frames.size()
	opponent_driver.begin_display_tick(physics_tick)
	opponent_driver.controller.context.helper_action = naruto_helper.source_action if naruto_helper != null else null
	opponent_driver.initial_frame_count = int(initial_frame_counts[ichigo])
	player_body_driver.prepare_frame_actions(int(initial_frame_counts[naruto]))
	source_callbacks.dispatch(physics_tick)
	if ko_terminal_pending:
		if not has_meta("rollback_terminal_barrier"):
			_ko_return_to_fixed_selection()
		if root_observer.is_valid():
			root_observer.call()
		return
	if timeout_timeline != null:
		timeout_timeline.run_frame_actions()
		timeout_clip.refresh_from_scheduler()
	if ko_timeline != null:
		ko_timeline.run_frame_actions()
		ko_clip.refresh_from_scheduler()
	# The older HUD callback observes newer fighter frame-script settlement
	# before the root snapshot (r15 source sequences 48536–48541).
	if source_health_rules != null:
		source_health_rules.run_pending_frame()
	health_hud.spec["placement"] = battle_intro.spec["hud_frames"][str(battle_intro.hud_frame)]
	# DefineSprite_1991's older enterFrame clamps the world after actor
	# callbacks, before the root observer and deferred goto frame scripts. The
	# first fight snapshot is a boundary: Flash observes it before the intro
	# clip's final frame can clamp touchFloor, so defer this one world callback.
	var defer_world_for_intro_boundary: bool = _intro_just_finished or intro_boundary_pending
	_intro_just_finished = false
	if not defer_world_for_intro_boundary:
		_apply_focus()
		game_world.enter_frame(naruto, ichigo, helpers)
	for event: Dictionary in _recorded_events_for_phase(recorded_events, "before_root_observer", event_supplier):
		assert(event["kind"] == "nextfight" and ko_recorded_timers)
		if ko_nextfight_timer != null:
			ko_nextfight_timer.timeout.emit()
		elif not event_supplier.is_valid():
			assert(false, "Recorded nextfight has no live source interval")
	if not match_input.error.is_empty():
		return
	# Ready's frame actions are source callbacks. They run after actor BODY
	# callbacks but before the root state snapshot on the same display.
	var intro_was_active := battle_intro.active
	battle_intro.run_frame_actions()
	if intro_was_active and not battle_intro.active:
		_intro_just_finished = true
	# The analysis root observer precedes callback-generated target scripts.
	# Its terminal capture issues fscommand(quit) at this point. Live play has
	# no observer and always completes the remaining frame work.
	var observer_terminal := false
	if root_observer.is_valid():
		observer_terminal = root_observer.call()
	if observer_terminal:
		return
	if defer_world_for_intro_boundary:
		_apply_focus()
		game_world.enter_frame(naruto, ichigo, helpers)
	# Goto targets wait behind the other actors' already queued frame scripts.
	while true:
		var next_fighter: FighterRuntime
		for fighter in fighters:
			if not fighter._ai_pending_frames.is_empty():
				if next_fighter == null or int(fighter._ai_pending_frames[0]["order"]) < int(next_fighter._ai_pending_frames[0]["order"]):
					next_fighter = fighter
		if not source_child_frames.is_empty() and (
			next_fighter == null
			or int(source_child_frames[0]["order"]) < int(next_fighter._ai_pending_frames[0]["order"])
		):
			var child_frame: Dictionary = source_child_frames.pop_front()
			var operation: Callable = child_frame["operation"]
			if operation.is_valid():
				operation.call()
			continue
		if next_fighter == null:
			break
		var pending_before_flush := next_fighter._ai_pending_frames.size()
		next_fighter.flush_queued_frame_scripts(1)
		# A newly placed source frame may be intentionally deferred to the next
		# display tick. Do not spin on an entry that the lifecycle gate rejected.
		if next_fighter._ai_pending_frames.size() == pending_before_flush:
			break
	if opponent_driver != null:
		opponent_driver.controller.synchronize(physics_tick)
	if cpu_services != null:
		cpu_services.run_stage_frames()
	if player_body_services != null:
		player_body_services.run_stage_frames()
	for child in game_world.get_children():
		if child is HitEffectRuntime and not child.is_queued_for_deletion():
			child.run_initial_frame()
	_activate_helper(naruto, naruto_helper)
	_activate_helper(ichigo, ichigo_helper)
	if super_presentation != null:
		_sync_super_stage()
	_refresh_fight_labels()


func _recorded_events_for_phase(recorded_events: Array, phase: String, event_supplier: Callable) -> Array:
	if event_supplier.is_valid():
		var supplied: Variant = event_supplier.call(phase, physics_tick)
		if not supplied is Array:
			match_input.error = "Online event supplier returned a non-array"
			return []
		for event in supplied:
			if not event is Dictionary or event.get("phase") != phase:
				match_input.error = "Online event supplier returned an invalid phase"
				return []
		return supplied
	var matching: Array = []
	for event: Dictionary in recorded_events:
		assert(event.get("phase") in ["after_actor_advance", "before_root_observer"], "Unsupported recorded callback phase")
		if event.get("phase") == phase:
			matching.append(event)
	return matching


func _start_training_recovery() -> void:
	if session.modo != int(session.training_spec.mode):
		return
	training_timer = Timer.new()
	training_timer.process_mode = Node.PROCESS_MODE_ALWAYS
	training_timer.ignore_time_scale = true
	training_timer.wait_time = float(session.training_spec.interval_ms) / 1000.0
	training_timer.timeout.connect(_recover_training)
	add_child(training_timer)
	if not recorded_training_timers:
		training_timer.start()


func _recover_training() -> void:
	session.apply_zdbx([naruto, ichigo], true)


func _stop_training_recovery() -> void:
	if training_timer != null:
		training_timer.stop()
		training_timer.queue_free()
		training_timer = null


func _sample_match_player(slot: String) -> Dictionary:
	if diagnostic_input_provider.is_valid() and not (slot == "p2" and session.p2cpu):
		return diagnostic_input_provider.call(slot, physics_tick)
	return session.fighter_input(slot)


func _input_for(fighter: FighterRuntime) -> Dictionary:
	if fighter == ichigo and session.p2cpu:
		return {}
	var inputs: Dictionary = _match_inputs[fighter.player_slot].duplicate()
	if diagnostics.enabled and not diagnostics.replaying:
		var input_source := "playback" if match_input.playback else "player"
		if diagnostic_input_provider.is_valid() and not match_input.playback:
			input_source = "diagnostic_tape"
		diagnostics.push_event("input_consumed", {
			"slot": fighter.player_slot,
			"source": input_source,
			"phase": "before_actor_advance",
			"keys": inputs,
		}, physics_tick)
	return inputs


func _start_ko() -> void:
	ko_metadata = JSON.parse_string(FileAccess.get_file_as_string("res://generated/main/ko/controller.json"))
	ko_state = ko_metadata.root_initializers.duplicate()
	ko_state.merge(ko_metadata.time_defaults, true)
	ko_state["_root.maxtime"] = session.maxtime
	ko_state["_root.to"] = false
	ko_state["_root.焦点"] = "all"
	ko_timeline = KoTimeline.new()
	ko_timeline.configure(JSON.parse_string(FileAccess.get_file_as_string("res://generated/main/ko/timeline.json")),
		ko_metadata, load("res://generated/main/ko/controller.gd"), _ko_service)
	ko_clip = KoClip.new()
	ko_clip.scheduler = ko_timeline
	add_child(ko_clip)


func _stop_ko() -> void:
	if countdown != null:
		health_hud.countdown = null
		countdown.stop()
		countdown.queue_free()
		countdown = null
	if timeout_timeline != null:
		timeout_timeline.unbind_registry()
		timeout_timeline = null
	if timeout_clip != null:
		timeout_clip.queue_free()
		timeout_clip = null
	nextfight_from_timeout = false
	_ko_clear_interval("nxtfht")
	if ko_clip != null:
		ko_clip.queue_free()
	ko_clip = null
	if ko_timeline != null:
		ko_timeline.unbind_registry()
	ko_timeline = null
	ko_active = false
	ko_paused = false
	ko_menu_enabled = true
	ko_terminal_pending = false


func _on_ko_requested(opponent_number: int) -> void:
	nextfight_from_timeout = false
	if ko_timeline == null:
		return
	ko_timeline.play()
	ko_active = true
	ko_state["_root.焦点"] = "p1" if opponent_number != 1 else "p2"
	for frame: Dictionary in black_mu._timeline.frames:
		if "KO" in frame.labels:
			super_presentation.black_stg(int(frame.frame))
			break
	_sync_super_stage()


func _ko_actor(target: String) -> FighterRuntime:
	if target == "_root.game.p1.mc":
		return naruto
	if target == "_root.game.p2.mc":
		return ichigo
	return null


func _ko_service(operation: String, args: Array) -> Variant:
	match operation:
		"read":
			var key := str(args[0])
			if key == "_root.maxtime": return session.maxtime
			if key == "_root.zhanting": return naruto.root_zhanting
			if key == "_root.timeover.played": return timeout_timeline.root_clip.variables.get("played", 0)
			if key == "_root.maxhp":
				return session.maxhp
			if key == "_root.modo":
				return session.modo
			var actor := _ko_actor(key.get_slice(".mc.", 0) + ".mc")
			if actor != null:
				var field := key.get_slice(".mc.", 1)
				return actor.health if field == "hp" else actor.ai_source_state.read_field(field)
			assert(ko_state.has(key), "Unbound KO root field: " + key)
			return ko_state[key]
		"write":
			var key := str(args[0])
			var actor := _ko_actor(key.get_slice(".mc.", 0) + ".mc")
			if actor != null:
				var field := key.get_slice(".mc.", 1)
				actor.ai_source_state.values[field] = args[1]
				if field == "sw":
					actor.sw = bool(args[1])
			else:
				ko_state[key] = args[1]
				if key == "_root.zhanting":
					naruto.root_zhanting = bool(args[1])
					ichigo.root_zhanting = bool(args[1])
					super_runtime.zhanting = bool(args[1])
				if key == "_root.rounds":
					battle_intro.clips.ready.round_number = int(args[1])
		"goto":
			var actor := _ko_actor(str(args[0]))
			if actor != null:
				# This service is called by an extracted MovieClip controller.
				# Its goto must preserve actor state until the destination frame
				# script runs; AI controller gotos use goto_ai_label directly.
				actor.source_goto_label(str(args[1]), bool(args[2]), _source_nextfight_goto_phase)
			elif args[0] in ["_root.p1win", "_root.p2win"]:
				# Sprite 1848 frame 67 addresses missing root aliases. The real
				# HUD clips live under xuetiao; only updateWins reaches them.
				return null
			elif args[0] == "_root.qjxg":
				battle_intro.clips.qjxg.visible = true
				battle_intro._goto("qjxg", int(battle_intro.spec.clips.qjxg.labels[args[1]]), bool(args[2]))
			elif args[0] == "_root" and args[1] == "选人画面":
				# This user-requested slice fixes fighters and already skips selection.
				ko_terminal_pending = true
			else:
				assert(false, "Unbound KO goto target")
		"playing":
			if args[0] == "_root.timeover":
				timeout_timeline.play()
				nextfight_from_timeout = true
				return null
			if args[0] in ["_root.p1win.bzxg", "_root.p2win.bzxg"]:
				return null
			assert(args[0] == "_root.ready")
			battle_intro.clips.ready.visible = true
			battle_intro.set_clip_playing("ready", bool(args[1]), _source_nextfight_goto_phase)
			battle_intro.active = true
			battle_intro.polling = false
			battle_intro.focus = "all"
		"interval":
			assert(args[0] == "nextfight")
			assert(ko_nextfight_timer == null, "Repeated nextfight registration needs another interval instance")
			ko_interval_sequence += 1
			ko_nextfight_timer = Timer.new()
			ko_nextfight_timer.process_mode = Node.PROCESS_MODE_ALWAYS
			ko_nextfight_timer.ignore_time_scale = true
			add_child(ko_nextfight_timer)
			ko_nextfight_timer.timeout.connect(_ko_nextfight)
			ko_nextfight_timer.wait_time = float(args[1]) / 1000.0
			if not ko_recorded_timers:
				ko_nextfight_timer.start()
			return ko_interval_sequence
		"call":
			match str(args[0]):
				"KOstart":
					ko_paused = true
					ko_menu_enabled = false
					pause_menu.visible = false
					_on_hit_fx_pause()
				"KOend":
					super_presentation.resume_black_stg()
					ko_paused = false
					super_runtime.game_paused = false
					_on_hit_fx_resume()
				"fadoutXuetiao":
					battle_intro.goto_hud("out")
				"updateWins":
					health_hud.set_wins(int(ko_state["_root.p1ws"]), int(ko_state["_root.p2ws"]))
				"chushi":
					_chushi()
				"clearint":
					for interval_name: String in ko_metadata.clear_intervals:
						_ko_clear_interval(interval_name)
				_:
					assert(false, "Unbound KO service: " + str(args[0]))
	return null


func _ko_clear_interval(interval_name: String) -> void:
	match interval_name:
		"nxtfht":
			if ko_nextfight_timer != null:
				ko_nextfight_timer.stop()
				preload("res://rollback_lifetime.gd").retire(ko_nextfight_timer)
				ko_nextfight_timer = null
		"zdbxint":
			_stop_training_recovery()
		"timeset":
			if countdown != null: countdown.stop()
		"airanset":
			if opponent_driver != null:
				ichigo.ai_random_clock.cancel()
		"kcint":
			if battle_intro != null:
				battle_intro.polling = false
		_:
			# These source intervals have no native registrations in this slice.
			assert(interval_name in ["timeset", "xtset", "scrnset", "feiint", "feiint2"])


func _ko_nextfight() -> void:
	_source_nextfight_goto_phase = true
	if nextfight_from_timeout and timeout_timeline != null:
		timeout_timeline.controller.nextfight()
	elif ko_timeline != null:
		ko_timeline.controller.nextfight()
	_source_nextfight_goto_phase = false


func _ko_fight_started() -> void:
	ko_active = false
	ko_paused = false
	ko_menu_enabled = true


func _diagnostic_fight_started() -> void:
	diagnostics.push_event("fight_started", {
		"mode": session.modo,
		"map": selected_stage,
		"players": _diagnostic_snapshot().get("players", {}),
	}, physics_tick)


func _ko_return_to_fixed_selection() -> void:
	var mode := session.modo
	_goto_menu()
	_goto_character_selection(mode)


func _start_combat_drivers() -> void:
	_stop_combat_drivers()
	assert(cpu_profile["measured_rules"]["callback_registry"]["order"] == "reverse_instance_registration")
	source_callbacks = SourceCallbackRegistry.new()
	# The source HUD exists before asynchronously loaded fighter bodies.
	source_health_rules = preload("res://source_health_rules.gd").new()
	var health_fighters: Array[FighterRuntime] = [naruto, ichigo]
	source_health_rules.configure(health_fighters, _source_max_health)
	source_health_registration = source_callbacks.register(source_health_rules, "queue_frame", physics_tick)
	_start_ko()
	ko_timeline.bind_registry(source_callbacks, physics_tick)
	source_frame_sequence = 0
	source_child_frames.clear()
	for fighter: FighterRuntime in [naruto, ichigo]:
		fighter.frame_script_sequence = _next_source_frame_sequence
		fighter.source_child_frame_requested.connect(_queue_source_child_frame)
		fighter.helper_spawn_requested.connect(_on_helper_spawn_requested.bind(fighter))
	cpu_unresolved_services.clear()
	ichigo.ai_color_state = AiColorState.new()
	ichigo.set_source_color({}, [])
	cpu_services = AiCombatServices.new()
	cpu_services.fighter = ichigo
	cpu_services.super_runtime = super_runtime
	cpu_services.effect_parent = game_world
	cpu_services.stage_registry = cpu_stage_registry
	var spec: Dictionary = JSON.parse_string(FileAccess.get_file_as_string("res://generated/effects/XG_baoqi/stage_hit.json"))
	# Enumeration order is explicit and still awaits whole-match comparison.
	cpu_services.stage_lookup_order = spec["registry"]["lookup_prefixes"]
	for helper in [naruto_helper, ichigo_helper]:
		if helper != null:
			cpu_services.helpers.append(helper)
	cpu_services.remaining_services = _cpu_visual_service
	var platforms := {}
	for placement: Dictionary in current_world._frames[current_world.current_source_frame()]["display_list"]:
		var instance_name := str(placement.get("name", ""))
		if instance_name.begins_with("ban") and instance_name.trim_prefix("ban").is_valid_int():
			var origin := current_world.named_instance_origin(instance_name)
			platforms[int(instance_name.trim_prefix("ban"))] = Rect2(origin, Vector2(current_world._placement_bounds(placement).size.x, 0))
	for fighter: FighterRuntime in [naruto, ichigo]:
		fighter.source_random = source_random
		fighter.source_clock = source_clock
		fighter.ai_source_state.configure(fighter.ai_source_state.spec)
		fighter.ai_source_state.apply_load()
		fighter.ai_source_state.apply_frame(1)
	player_body_services = AiCombatServices.new()
	player_body_services.fighter = naruto
	player_body_services.super_runtime = super_runtime
	player_body_services.helpers = cpu_services.helpers.duplicate()
	player_body_services.stage_registry = cpu_stage_registry
	player_body_services.stage_lookup_order = cpu_services.stage_lookup_order.duplicate()
	player_body_services.effect_parent = game_world
	player_body_services.remaining_services = _player_visual_service
	player_body_driver = preload("res://player_body_driver.gd").new()
	add_child(player_body_driver)
	player_body_driver.configure(naruto, naruto.fighter_directory + "/player_controller", platforms,
		naruto._ground_y, game_world.map_size_x, player_body_services.invoke, source_callbacks)
	opponent_driver = AiCpuDriver.new()
	add_child(opponent_driver)
	opponent_input_context = null
	if not session.p2cpu:
		opponent_input_context = preload("res://player_body_driver.gd").Context.new(ichigo)
		opponent_input_context.use_ai = false
	opponent_driver.configure(ichigo, ichigo.fighter_directory + "/player_controller", platforms,
		ichigo._ground_y, game_world.map_size_x, {"touchFloor": null}, cpu_services.invoke, false,
		source_callbacks, opponent_input_context)
	opponent_driver.controller.context.use_ai = session.p2cpu
	if opponent_input_context != null:
		opponent_driver.controller.key_reader = opponent_input_context.source_key
	opponent_driver.body.updateDirect()
	opponent_driver.begin_display_tick(physics_tick)
	# Loaded helper timelines retain their place between the fighter bodies
	# and newer action clips in Flash's global instance traversal.
	for helper in [naruto_helper, ichigo_helper]:
		helper.bind_source_frames(source_callbacks, physics_tick)
		helper.source_child_frame_requested.connect(_queue_source_child_frame)
	if session.p2cpu:
		opponent_driver.start_random(source_random, session.ai_level)



func _next_source_frame_sequence() -> int:
	source_frame_sequence += 1
	return source_frame_sequence


func _queue_source_child_frame(operation: Callable) -> void:
	source_child_frames.append({"order": _next_source_frame_sequence(), "operation": operation})


func _on_helper_spawn_requested(fighter: FighterRuntime) -> void:
	var helper: HelperRuntime
	if fighter == naruto:
		helper = naruto_helper
	elif fighter == ichigo:
		helper = ichigo_helper
	else:
		return
	if helper == null or fighter.helper_spawn.is_empty():
		return
	# yfgj() places the helper during the fighter's source callback. Consume the
	# request immediately; the end-of-tick fallback remains for older callers.
	var spawn := fighter.helper_spawn.duplicate(true)
	fighter.helper_spawn.clear()
	helper.activate(spawn, fighter)
	diagnostics.push_event("helper_lifecycle", {
		"event": "activate", "ownerSlot": fighter.player_slot,
		"helper": helper.helper_id, "resourcePath": helper.helper_directory,
		"spawn": spawn,
	}, physics_tick)


func _stop_combat_drivers() -> void:
	_stop_training_recovery()
	for helper in [naruto_helper, ichigo_helper]:
		if is_instance_valid(helper):
			if helper.source_child_frame_requested.is_connected(_queue_source_child_frame):
				helper.source_child_frame_requested.disconnect(_queue_source_child_frame)
			helper.unbind_source_frames()
	source_child_frames.clear()
	for fighter: FighterRuntime in [naruto, ichigo]:
		if is_instance_valid(fighter):
			fighter.frame_script_sequence = Callable()
			if fighter.source_child_frame_requested.is_connected(_queue_source_child_frame):
				fighter.source_child_frame_requested.disconnect(_queue_source_child_frame)
			for connection in fighter.helper_spawn_requested.get_connections():
				var callable: Callable = connection["callable"]
				if callable.get_object() == self:
					fighter.helper_spawn_requested.disconnect(callable)
	if player_body_driver != null:
		player_body_driver.stop()
		player_body_driver.queue_free()
		player_body_driver = null
	if player_body_services != null:
		player_body_services.clear()
		player_body_services = null
	if opponent_driver != null:
		opponent_driver.stop()
		opponent_driver.queue_free()
		opponent_driver = null
	opponent_input_context = null
	if cpu_services != null:
		cpu_services.clear()
		cpu_services = null
	cpu_stage_registry.clear_effects()
	if is_instance_valid(game_world):
		for child in game_world.get_children():
			if child is ShadowSnapshot:
				child.dispose()
			elif child is HitEffectRuntime:
				child.unregister_source_frames()
	if source_callbacks != null:
		if timeout_timeline != null:
			timeout_timeline.unbind_registry()
		if ko_timeline != null:
			ko_timeline.unbind_registry()
		if source_health_rules != null:
			source_callbacks.unregister(source_health_registration)
			source_health_rules = null
		assert(source_callbacks.size() == 0, "Source callbacks survived match teardown")
		source_callbacks = null


func _cpu_visual_service(service: String, args: Array) -> Variant:
	return _fighter_visual_service(ichigo, service, args)


func _player_visual_service(service: String, args: Array) -> Variant:
	return _fighter_visual_service(naruto, service, args)


func _fighter_visual_service(actor: FighterRuntime, service: String, _args: Array) -> Variant:
	if service == "showdow":
		if ShadowSnapshot.should_capture(actor):
			var shadow := ShadowSnapshot.new()
			game_world.add_child(shadow)
			shadow.capture(actor, _args[0], source_callbacks, physics_tick)
		return null
	if service == "addChildXG":
		# Source arguments are offsetY then offsetX, in world coordinates.
		_spawn_hit_effect(str(_args[0]), actor.position + Vector2(float(_args[2]), 0), actor.facing, float(_args[1]))
		return null
	if service == "frame_child_effect":
		var effect: Dictionary = _args[0]
		_spawn_hit_effect(effect["clip"], actor.position + Vector2(float(effect["offset_x"]), 0), actor.facing, float(effect["offset_y"]))
		return null
	if service == "root_position":
		var write: Dictionary = _args[0]
		_apply_root_position(write["axis"], write["operator"], float(write["pixels"]))
		return null
	if service == "resColor":
		actor.reset_ai_colors()
		return null
	if service == "applyColors":
		actor.apply_ai_colors()
		return null
	var wrappers: Dictionary = cpu_visual_spec["wrappers"]
	if wrappers.has(service):
		# The retained game calls attachMovie with these missing linkage names.
		# A missing export creates no clip; do not invent a replacement effect.
		assert(wrappers[service]["exported_by"].is_empty(), "Exported AI effect needs a native adapter")
		return null
	assert(service in ["resColor", "applyColors", "jumpxg", "luodixg", "showdow", "addChildXG"],
		"Unconnected CPU gameplay service: " + service)
	if not cpu_unresolved_services.has(service):
		cpu_unresolved_services[service] = true
		push_warning("CPU visual service remains unimplemented: " + service)
	return null


func _refresh_bind_label() -> void:
	var p1 := []
	for slot in GameSession.P1_SLOTS:
		p1.append(session.show_key_name(int(session.codes[slot])))
	var p2 := []
	for slot in GameSession.P2_SLOTS:
		p2.append(session.show_key_name(int(session.codes[slot])))
	config_label.text = "P1 %s  ·  P2 %s" % [" ".join(p1), " ".join(p2)]


func _place_fighters_from_map() -> void:
	var p1_origin := current_world.named_instance_origin("p1")
	var p2_origin := current_world.named_instance_origin("p2")
	if p1_origin != Vector2.INF:
		naruto.position = p1_origin
	if p2_origin != Vector2.INF:
		ichigo.position = p2_origin


func _make_helper(directory: String) -> HelperRuntime:
	var helper := HelperRuntime.new()
	helper.helper_directory = directory
	helper.fighter_directory = directory
	helper.autoplay = false
	helper.effect_requested.connect(_spawn_hit_effect)
	game_world.add_child(helper)
	return helper


func _refresh_fight_labels() -> void:
	if state_label.is_visible_in_tree():
		var mode_name := "TRAINING" if session.modo == 4 else "VS MODE"
		# HP readout follows bar2 (displayed_health), not the instant mc.hp.
		state_label.text = "%s    Naruto  HP %d  MP %d  %s:%d    Ichigo  HP %d  MP %d  %s:%d" % [
			mode_name,
			int(naruto.displayed_health),
			int(naruto.energy),
			_status_name(naruto),
			naruto.current_source_frame(),
			int(ichigo.displayed_health),
			int(ichigo.energy),
			_status_name(ichigo),
			ichigo.current_source_frame(),
		]
	health_hud.refresh()
	naruto_energy.energy = naruto.energy
	ichigo_energy.energy = ichigo.energy
	# The qt301 nested child follows the source display clock, independently
	# from ql assignments. Both bars receive the same completed display tick.
	naruto_energy.advance_display_tick(physics_tick)
	ichigo_energy.advance_display_tick(physics_tick)


func _set_diagnostic_actor(fighter: FighterRuntime, slot: String) -> void:
	fighter.diagnostic_runtime = diagnostics
	fighter.diagnostic_slot = slot
	fighter.diagnostic_role = "cpu" if slot == "p2" and session.p2cpu else "player"
	fighter.diagnostic_tick = physics_tick
	if slot == "p1":
		fighter.diagnostic_helper = naruto_helper
		if naruto_helper != null:
			naruto_helper.diagnostic_runtime = diagnostics
			naruto_helper.diagnostic_slot = slot
	else:
		fighter.diagnostic_helper = ichigo_helper
		if ichigo_helper != null:
			ichigo_helper.diagnostic_runtime = diagnostics
			ichigo_helper.diagnostic_slot = slot


func _diagnostic_snapshot(capture_initial: bool = false) -> Dictionary:
	var current_players := {
		"p1": _diagnostic_player(naruto, naruto_helper),
		"p2": _diagnostic_player(ichigo, ichigo_helper),
	}
	if capture_initial or _diagnostic_initial_players.is_empty():
		_diagnostic_initial_players = current_players.duplicate(true)
	return {
		"matchId": diagnostics.match_id,
		"mode": session.modo,
		"modeName": _diagnostic_mode_name(session.modo),
		"p1cpu": session.p1cpu,
		"p2cpu": session.p2cpu,
		"map": selected_stage,
		"stageResourcePath": current_world.fighter_directory if current_world != null else "",
		"physicsHz": Engine.physics_ticks_per_second,
		"fightTick": physics_tick,
		"players": current_players,
		"initialState": _diagnostic_initial_players,
		"inputBindings": session.codes.duplicate(true),
		"pause": _diagnostic_pause_state(),
		"random": source_random.diagnostic_state(),
		"clock": source_clock.diagnostic_state(),
		"pageVisible": diagnostics.page_visible,
		"replayability": {
			"inputSource": "diagnostic_input_provider" if diagnostic_input_provider.is_valid() else "session_consumption_events",
			"randomCapturedFromStart": capture_initial,
			"clockCapturedFromStart": capture_initial,
			"checkpointKind": "fresh_match_recipe" if capture_initial else "latest_observation",
			"randomStartIndex": source_random.absolute_index,
			"clockStartIndex": source_clock.absolute_index,
			"canonicalInitialization": capture_initial,
			"completeCheckpoint": false,
			"limitation": "This recipe describes a fresh Main match only; snapshots do not restore arbitrary scene state.",
		},
	}


func _diagnostic_player(fighter: FighterRuntime, helper: HelperRuntime) -> Dictionary:
	var helper_state := {}
	if helper != null:
		helper_state = {
			"id": helper.helper_id,
			"resourcePath": helper.helper_directory,
			"action": helper.source_action,
			"sourceFrame": helper.current_source_frame(),
			"x": helper.position.x,
			"y": helper.position.y,
			"facing": helper.facing,
			"attacking": helper.attacking,
			"bs": helper.bs,
			"hited": helper.hited,
			"timelinePlaying": helper.timeline_playing,
		}
	return {
		"slot": fighter.player_slot,
		"fighter": fighter.fighter_name,
		"form": fighter.ai_source_state.read_field("形态"),
		"resourcePath": fighter.fighter_directory,
		"helper": helper_state,
		"action": fighter.action,
		"sourceFrame": fighter.current_source_frame(),
		"x": fighter.source_x,
		"y": fighter.source_y,
		"facing": fighter.facing,
		"hp": fighter.health,
		"energy": fighter.energy,
		"bs": fighter.bs,
		"hited": fighter.hited,
		"zhanting": fighter.zhanting,
		"timelinePlaying": fighter.timeline_playing,
		"sw": fighter.sw,
		"guarding": fighter.guarding,
	}


func _diagnostic_pause_state() -> Dictionary:
	return {
		"globalSuperPaused": super_runtime.zhanting,
		"userPaused": super_runtime.game_paused,
		"fighterZhanting": {"p1": naruto.zhanting, "p2": ichigo.zhanting},
		"rootZhanting": {"p1": naruto.root_zhanting, "p2": ichigo.root_zhanting},
	}


func _diagnostic_mode_name(mode: int) -> String:
	match mode:
		2: return "vs_com"
		3: return "versus"
		4: return "training"
		_: return "unknown"


func _on_random_value_consumed(record: Dictionary) -> void:
	diagnostics.push_event("random_consumed", record, physics_tick if not diagnostics.match_id.is_empty() else -1)


func _on_clock_value_consumed(record: Dictionary) -> void:
	diagnostics.push_event("clock_consumed", record, physics_tick if not diagnostics.match_id.is_empty() else -1)


func _play_combo_hud(board_pn: int, hit_count: int) -> void:
	combo_hud.play(board_pn, hit_count)


func _on_hit_fx_pause() -> void:
	if super_runtime.game_paused or source_callbacks == null:
		return
	# pauseGame stops timelines, while registered enterFrame callbacks remain.
	hit_fx_pause_count = 1
	super_runtime.zhanting = true
	naruto.root_zhanting = true
	ichigo.root_zhanting = true
	for actor in [naruto, ichigo, naruto_helper, ichigo_helper]:
		super_runtime.stop_mc(actor)


func _on_hit_fx_resume() -> void:
	if source_callbacks == null or super_runtime.game_paused or ko_paused:
		return
	hit_fx_pause_count = 0
	super_runtime.zhanting = false
	naruto.root_zhanting = false
	ichigo.root_zhanting = false
	for actor in [naruto, ichigo, naruto_helper, ichigo_helper]:
		super_runtime.play_mc(actor)
	super_presentation.resume_black_stg()


func _spawn_hit_effect(effect_name: String, source_position: Vector2, source_facing: int, offset_y: float = -25.0) -> void:
	if not FileAccess.file_exists("res://generated/effects/%s/timeline.json" % effect_name):
		# Compiled but not imported yet: bdxg element tiers
		# (XG_fire/ice/leidian/stone).
		return
	var effect := HitEffectRuntime.new()
	effect.auto_advance = false
	effect.defer_initial_frame = true
	effect.source_random = source_random
	effect.pause_requested.connect(_on_hit_fx_pause)
	effect.resume_requested.connect(_on_hit_fx_resume)
	effect.shine_requested.connect(_start_screen_flash)
	effect.root_position_requested.connect(_apply_root_position)
	effect.configure(effect_name, source_position, source_facing, offset_y)
	game_world.add_child(effect)
	if opponent_driver != null:
		effect.register_source_frames(source_callbacks, physics_tick)


func _apply_root_position(axis: String, operator: String, pixels: float) -> void:
	assert(axis in ["x", "y"])
	var index := 0 if axis == "x" else 1
	match operator:
		"=": position[index] = pixels
		"+=": position[index] += pixels
		"-=": position[index] -= pixels
		_: assert(false, "Uncompiled root position assignment")


func _setup_screen_flash() -> void:
	screen_flash = ColorRect.new()
	screen_flash.name = "ScreenFlash"
	screen_flash.mouse_filter = Control.MOUSE_FILTER_IGNORE
	screen_flash.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	screen_flash.z_index = 100
	var shader := Shader.new()
	shader.code = SHINE_SHADER
	var material := ShaderMaterial.new()
	material.shader = shader
	screen_flash.material = material
	screen_flash.visible = false
	add_child(screen_flash)


func _start_screen_flash(color_rgb24: int) -> void:
	var tint := Color(
		float((color_rgb24 >> 16) & 0xFF) / 255.0,
		float((color_rgb24 >> 8) & 0xFF) / 255.0,
		float(color_rgb24 & 0xFF) / 255.0
	)
	var material := screen_flash.material as ShaderMaterial
	material.set_shader_parameter("tint", Vector3(tint.r, tint.g, tint.b))
	material.set_shader_parameter("opacity", float(SHINE_ALPHA_TERMS[0]) / 256.0)
	screen_flash_age = 0
	screen_flash.visible = true


func _advance_screen_flash() -> void:
	if screen_flash_age < 0:
		return
	screen_flash_age += 1
	if screen_flash_age >= SHINE_ALPHA_TERMS.size():
		screen_flash_age = -1
		screen_flash.visible = false
		return
	var material := screen_flash.material as ShaderMaterial
	material.set_shader_parameter(
		"opacity", float(SHINE_ALPHA_TERMS[screen_flash_age]) / 256.0
	)


func _activate_helper(fighter: FighterRuntime, helper: HelperRuntime) -> void:
	if helper == null or fighter.helper_spawn.is_empty():
		return
	helper.activate(fighter.helper_spawn, fighter)
	fighter.helper_spawn = {}


func _on_super_event(event: Dictionary, caster: FighterRuntime) -> void:
	diagnostics.push_event("super_state", {
		"slot": caster.player_slot,
		"sourceEvent": event,
		"pause": _diagnostic_pause_state(),
	}, physics_tick)
	# FighterRuntime already applied SuperRuntime (stopMc / zhanting / shine).
	# Sync blackMu/ts_face on this tick so gotoAndPlay("in") shows frame 5 now.
	_sync_super_stage()


func _reset_super() -> void:
	super_runtime.reset(naruto, ichigo, [naruto_helper, ichigo_helper])
	_sync_super_stage()
	game_world.focus = "all"


func _sync_super_stage() -> void:
	# Source blackStg hides game.bgmc/fgmc; blackMu/ts_face are root clips
	# behind game (main.swf 游戏场景 depths 3 and 5).
	var hidden: PackedStringArray = []
	if super_presentation != null and not super_presentation.bgmc_visible:
		hidden = super_presentation.hide_stage_instances()
	current_world.set_hidden_instances(hidden)
	if black_mu != null and super_presentation != null:
		black_mu.play_source_frame(super_presentation.black_mu_frame)
	_sync_ts_face()


func _sync_ts_face() -> void:
	if ts_face == null or super_presentation == null:
		return
	ts_face.set_instance_clip_frame(
		"bg", super_presentation.bg_frame, super_presentation.bg_playing
	)
	ts_face.set_instance_clip_frame(
		"face_p1", super_presentation.face_p1_frame, super_presentation.face_p1_playing
	)
	ts_face.set_instance_clip_frame(
		"face_p2", super_presentation.face_p2_frame, super_presentation.face_p2_playing
	)
	var portrait := super_presentation.portrait_frame(super_presentation.face_label)
	if portrait > 0:
		ts_face.set_instance_clip_frame("face", portrait, false)
	ts_face.refresh_display()


func _apply_focus() -> void:
	if ko_active:
		game_world.focus = str(ko_state.get("_root.焦点", "all"))
		return
	if battle_intro.active:
		game_world.focus = battle_intro.focus
		return
	# Legacy non-CPU death focus; CPU mode uses the KO timeline writes above.
	if naruto.sw:
		game_world.focus = naruto.player_slot
	elif ichigo.sw:
		game_world.focus = ichigo.player_slot
	else:
		game_world.focus = super_runtime.last_focus


func _status_name(fighter: FighterRuntime) -> String:
	var name := _action_name(fighter.action)
	return "%s/KO" % name if fighter.sw else name


func _action_name(label: String) -> String:
	# Source timeline labels are the move IDs; do not invent a second name set.
	return label if label != "" else "站立"


func _start_countdown() -> void:
	timeout_timeline = KoTimeline.new()
	timeout_timeline.configure(JSON.parse_string(FileAccess.get_file_as_string("res://generated/main/timeout/timeline.json")),
		JSON.parse_string(FileAccess.get_file_as_string("res://generated/main/timeout/controller.json")),
		load("res://generated/main/timeout/controller.gd"), _ko_service)
	if source_callbacks != null:
		timeout_timeline.bind_registry(source_callbacks, physics_tick)
	timeout_clip = KoClip.new()
	timeout_clip.fighter_directory = "res://generated/main/timeout"
	timeout_clip.scheduler = timeout_timeline
	add_child(timeout_clip)
	countdown = MatchCountdown.new()
	add_child(countdown)
	health_hud.countdown = countdown
	countdown.presentation_changed.connect(health_hud.queue_redraw)
	countdown.configure(_ko_service, ko_recorded_timers)
	health_hud.queue_redraw()


func _source_max_health() -> float:
	return session.maxhp
