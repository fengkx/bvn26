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
@onready var black_mu: TimelinePreview = %BlackMu
@onready var ts_face: TimelinePreview = %TsFace

var pause_menu: BattlePauseMenu
var health_hud: HealthHud
var map_selection: MapSelection
var stage_background: TimelinePreview
var battle_intro: BattleIntro
var stage_sound: StageSound
var source_random := SourceRandom.new()
var source_clock = preload("res://source_clock.gd").new()
var selected_stage: String = "现世"
var cpu_driver: AiCpuDriver
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

var session := GameSession.new()
var super_runtime := SuperRuntime.new()
var super_presentation := SuperPresentation.new()
var physics_tick: int = 0
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
# Source DefineSprite_1991: setInterval(zdbx, 1000) when modo==4. 30 Hz → 30 ticks.
var zdbx_ticks: int = 0

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
	cpu_profile = JSON.parse_string(FileAccess.get_file_as_string("res://generated/main/execution_profile.json"))
	cpu_stage_registry.configure(JSON.parse_string(FileAccess.get_file_as_string("res://generated/effects/XG_baoqi/stage_hit.json")))
	source_random.use_live_random()
	stage_sound = StageSound.new()
	stage_sound.random_source = source_random
	add_child(stage_sound)
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
	naruto.ko_requested.connect(_on_ko_requested)
	ichigo.ko_requested.connect(_on_ko_requested)
	session.load_store()
	key_settings.session = session
	key_settings.refresh_view()
	title_menu.confirmed.connect(_on_menu_confirmed)
	key_settings.back_to_menu.connect(_goto_menu)
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
	naruto.super_event_applied.connect(func(event: Dictionary) -> void: _on_super_event(event, naruto))
	ichigo.super_event_applied.connect(func(event: Dictionary) -> void: _on_super_event(event, ichigo))
	combo_hud.load_spec("res://generated/main/hit_receive.json")
	# This slice locks P1/P2 assistance to Gaara/Kon.
	naruto_helper = _make_helper("res://generated/helpers/woailuo")
	ichigo_helper = _make_helper("res://generated/helpers/kon")
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
	if session.root_label != "游戏场景" or battle_intro.active or naruto.sw or ichigo.sw or not ko_menu_enabled:
		return
	if event is InputEventKey:
		pause_menu.handle_key(event)
	elif event is InputEventMouseButton:
		pause_menu.handle_mouse(event)


func _pause_battle() -> void:
	# frame_8 pauseGame2: stopMc is conditional; hit effects keep advancing.
	for actor in [naruto, ichigo, naruto_helper, ichigo_helper]:
		super_runtime.stop_mc(actor)
	super_runtime.game_paused = true
	naruto.root_zhanting = true
	ichigo.root_zhanting = true


func _resume_battle() -> void:
	super_runtime.game_paused = false
	naruto.root_zhanting = false
	ichigo.root_zhanting = false
	super_runtime.zhanting = false
	for actor in [naruto, ichigo, naruto_helper, ichigo_helper]:
		super_runtime.play_mc(actor)
	super_presentation.resume_black_stg()
	_sync_super_stage()


func _physics_process(_delta: float) -> void:
	match session.root_label:
		"MENU":
			title_menu.apply_held(session.menu_held())
		"键位设置":
			key_settings.apply_held(session.menu_held())
		"地图":
			map_selection.tick(session.menu_held())
		"游戏场景":
			pause_menu.tick()
			_advance_fight()


func _on_menu_confirmed(item_id: String) -> void:
	for item in TitleMenu.ITEMS:
		if str(item["id"]) != item_id:
			continue
		if item_id == "key_settings":
			_goto_key_settings()
			return
		if int(item["modo"]) in [2, 3, 4]:
			_goto_map_selection(int(item["modo"]))
		return


func _goto_map_selection(modo: int) -> void:
	# The requested slice skips fighter/assist selection, entering xure@地图.
	session.modo = modo
	session.root_label = "地图"
	title_menu.visible = false
	key_settings.visible = false
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
	_stop_ko()
	_stop_cpu()
	if battle_intro != null:
		battle_intro.cancel()
	stage_sound.stop()
	map_selection.leave()
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


func _goto_key_settings() -> void:
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
	_stop_ko()
	_stop_cpu()
	# Fighters/assists remain locked; the map comes from the original map selector.
	# Source 597/600/603: only modo=2 enables p2cpu. Selection is fixed here.
	session.modo = modo
	session.p1cpu = false
	session.p2cpu = modo == 2
	session.root_label = "游戏场景"
	title_menu.visible = false
	key_settings.visible = false
	fight_hud.visible = false
	health_hud.visible = true
	if stage_background != null:
		stage_background.visible = true
	game_world.visible = true
	if black_mu != null:
		black_mu.visible = true
	if ts_face != null:
		ts_face.visible = true
	combo_hud.visible = true
	naruto_energy.visible = true
	ichigo_energy.visible = true
	_initialize_fight()
	health_hud.set_wins(1, 1)
	if session.p2cpu:
		_start_cpu()
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
	zdbx_ticks = 0
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


func _advance_fight(recorded_events: Array = [], root_observer: Callable = Callable()) -> void:
	# Snapshot before frame scripts attach new XG instances. Their frame 1
	# is queued behind the caller; frame 2 belongs to the next display tick.
	var existing_hit_effects: Array[HitEffectRuntime] = []
	for child in game_world.get_children():
		if child is HitEffectRuntime and not child.is_queued_for_deletion():
			existing_hit_effects.append(child)
	battle_intro.tick(1.0 / Engine.physics_ticks_per_second, session.is_slot_down("j") or session.is_slot_down("N1"), true)
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
	tick_label.text = "Fixed simulation tick: %d" % physics_tick
	if hit_fx_pause_count > 0 and cpu_driver == null:
		# Source pauseGame() stopMc on p1/p2/helpers. XG clip keeps playing.
		battle_intro.run_frame_actions()
		_advance_hit_effects(existing_hit_effects)
		_refresh_fight_labels()
		return
	var fighters: Array[FighterRuntime] = [ichigo, naruto]
	var helpers: Array = []
	if naruto_helper != null:
		helpers.append(naruto_helper)
	if ichigo_helper != null:
		helpers.append(ichigo_helper)
	naruto.super_helpers = helpers
	ichigo.super_helpers = helpers
	if player_body_driver != null:
		player_body_driver.begin_tick(physics_tick, _input_for(naruto))
	if cpu_driver != null:
		cpu_driver.prepare_display_tick(physics_tick)
	for fighter in fighters:
		if fighter == ichigo and cpu_driver != null:
			cpu_driver.advance_timeline()
		elif fighter == naruto and player_body_driver != null:
			player_body_driver.advance_timeline()
		else:
			fighter.advance_timeline()
	if cpu_services != null:
		cpu_services.advance_stage_timelines()
	if player_body_services != null:
		player_body_services.advance_stage_timelines()
	# Recorded callbacks carry their phase explicitly; do not infer it from
	# milliseconds or move an already queued frame script past the callback.
	for event: Dictionary in recorded_events:
		if event["phase"] == "before_root_observer":
			continue
		assert(event["phase"] == "after_actor_advance", "Unsupported intro callback phase")
		if event.get("kind", "intro_poll") == "ai_random":
			var sampled := ichigo.ai_random_clock.fire_recorded(int(event["time_ms"]))
			assert(sampled, "Rejected recorded AI random refresh")
			continue
		assert(event.get("kind", "intro_poll") == "intro_poll", "Unknown recorded event kind")
		before_recorded_intro_poll.emit(event)
		var delivered := battle_intro.deliver_recorded_poll(int(event["sequence"]), int(event["time_ms"]))
		assert(delivered, "Rejected recorded intro callback: " + battle_intro.poll_replay_error)
	battle_intro.observe_fighter_frames()
	for helper in helpers:
		helper.advance_timeline()
	if player_body_driver != null:
		player_body_driver.prepare_callbacks()
	var initial_frame_counts := {}
	for fighter in fighters:
		initial_frame_counts[fighter] = fighter._ai_pending_frames.size()
	if cpu_driver != null:
		cpu_driver.begin_display_tick(physics_tick)
		cpu_driver.controller.context.helper_action = naruto_helper.source_action if naruto_helper != null else null
		cpu_driver.initial_frame_count = int(initial_frame_counts[ichigo])
		if player_body_driver != null:
			player_body_driver.prepare_frame_actions(int(initial_frame_counts[naruto]))
		source_callbacks.dispatch(physics_tick)
		if ko_terminal_pending:
			_ko_return_to_fixed_selection()
			if root_observer.is_valid():
				root_observer.call()
			return
	else:
		for fighter in fighters:
			fighter.enter_frame(_input_for(fighter))
	for helper in helpers:
		helper.enter_frame()
	if cpu_driver != null:
		if player_body_driver == null and not naruto.root_zhanting:
			naruto.resolve_body_collision(ichigo)
			CombatResolver.resolve_incoming(naruto, ichigo, ichigo_helper, cpu_stage_registry, cpu_services.stage_lookup_order)
	else:
		CombatResolver.resolve_body_pair(naruto, ichigo)
		CombatResolver.resolve_pair(naruto, ichigo)
		CombatResolver.resolve_helpers(helpers, fighters)
	for fighter in fighters:
		if cpu_driver == null or (fighter == naruto and player_body_driver == null):
			fighter.run_frame_actions(false, int(initial_frame_counts[fighter]) if cpu_driver != null else -1)
	if ko_timeline != null:
		ko_timeline.run_frame_actions()
		ko_clip.refresh_from_scheduler()
	battle_intro.run_frame_actions()
	# The older HUD callback observes newer fighter frame-script settlement
	# before the root snapshot (r15 source sequences 48536–48541).
	if source_health_rules != null:
		source_health_rules.run_pending_frame()
	health_hud.spec["placement"] = battle_intro.spec["hud_frames"][str(battle_intro.hud_frame)]
	for event: Dictionary in recorded_events:
		if event["phase"] == "before_root_observer":
			assert(event["kind"] == "nextfight" and ko_recorded_timers)
			assert(ko_nextfight_timer != null, "Recorded nextfight has no live source interval")
			ko_nextfight_timer.timeout.emit()
	# The analysis root observer precedes callback-generated target scripts.
	# Its terminal capture issues fscommand(quit) at this point. Live play has
	# no observer and always completes the remaining frame work.
	if root_observer.is_valid() and root_observer.call():
		return
	# Goto targets wait behind the other actors' already queued frame scripts.
	while true:
		if cpu_driver == null:
			var pending := false
			for fighter in fighters:
				if not fighter._ai_pending_frames.is_empty():
					pending = true
					fighter.flush_queued_frame_scripts()
			if not pending:
				break
			continue
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
		next_fighter.flush_queued_frame_scripts(1)
	if cpu_driver != null:
		cpu_driver.controller.synchronize(physics_tick)
	if cpu_services != null:
		cpu_services.run_stage_frames()
	if player_body_services != null:
		player_body_services.run_stage_frames()
	if cpu_driver == null:
		_advance_hit_effects(existing_hit_effects)
	for child in game_world.get_children():
		if child is HitEffectRuntime and not child.is_queued_for_deletion():
			child.run_initial_frame()
	_activate_helper(naruto, naruto_helper)
	_activate_helper(ichigo, ichigo_helper)
	_apply_focus()
	_update_facing()
	game_world.enter_frame(naruto, ichigo, helpers)
	if super_presentation != null:
		_sync_super_stage()
	_tick_zdbx()
	_refresh_fight_labels()


func _tick_zdbx() -> void:
	# First fire is after 1000 ms, not on the placement tick.
	if session.modo != 4:
		return
	zdbx_ticks += 1
	if zdbx_ticks < 30:
		return
	zdbx_ticks = 0
	session.apply_zdbx([naruto, ichigo], true)


func _input_for(fighter: FighterRuntime) -> Dictionary:
	if fighter == ichigo and session.p2cpu:
		return {}
	return session.fighter_input(fighter.player_slot)


func _start_ko() -> void:
	ko_metadata = JSON.parse_string(FileAccess.get_file_as_string("res://generated/main/ko/controller.json"))
	ko_state = ko_metadata.root_initializers.duplicate()
	ko_state.merge(ko_metadata.time_defaults, true)
	ko_state["_root.焦点"] = "all"
	ko_timeline = KoTimeline.new()
	ko_timeline.configure(JSON.parse_string(FileAccess.get_file_as_string("res://generated/main/ko/timeline.json")),
		ko_metadata, load("res://generated/main/ko/controller.gd"), _ko_service)
	ko_clip = KoClip.new()
	ko_clip.scheduler = ko_timeline
	add_child(ko_clip)


func _stop_ko() -> void:
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
				if actor.ai_timeline_controlled:
					actor.goto_ai_label(str(args[1]), bool(args[2]))
				else:
					actor.start_action(str(args[1]))
					actor.timeline_playing = bool(args[2])
			elif args[0] == "_root.qjxg":
				battle_intro.clips.qjxg.visible = true
				battle_intro._goto("qjxg", int(battle_intro.spec.clips.qjxg.labels[args[1]]), bool(args[2]))
			elif args[0] == "_root" and args[1] == "选人画面":
				# This user-requested slice fixes fighters and already skips selection.
				ko_terminal_pending = true
			else:
				assert(false, "Unbound KO goto target")
		"playing":
			assert(args[0] == "_root.ready")
			battle_intro.clips.ready.visible = true
			battle_intro.playing.ready = bool(args[1])
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
				ko_nextfight_timer.queue_free()
				ko_nextfight_timer = null
		"airanset":
			if cpu_driver != null:
				ichigo.ai_random_clock.cancel()
		"kcint":
			if battle_intro != null:
				battle_intro.polling = false
		_:
			# These source intervals have no native registrations in this slice.
			assert(interval_name in ["timeset", "xtset", "scrnset", "feiint", "feiint2", "zdbxint"])


func _ko_nextfight() -> void:
	if ko_timeline != null:
		ko_timeline.controller.nextfight()


func _ko_fight_started() -> void:
	ko_active = false
	ko_paused = false
	ko_menu_enabled = true


func _ko_return_to_fixed_selection() -> void:
	_goto_menu()
	_goto_map_selection(2)


func _start_cpu() -> void:
	_stop_cpu()
	assert(cpu_profile["measured_rules"]["callback_registry"]["order"] == "reverse_instance_registration")
	source_callbacks = SourceCallbackRegistry.new()
	# The source HUD exists before asynchronously loaded fighter bodies.
	source_health_rules = preload("res://source_health_rules.gd").new()
	var health_fighters: Array[FighterRuntime] = [naruto, ichigo]
	source_health_rules.configure(health_fighters, func() -> float: return session.maxhp)
	source_health_registration = source_callbacks.register(source_health_rules, "queue_frame", physics_tick)
	_start_ko()
	ko_timeline.bind_registry(source_callbacks, physics_tick)
	source_frame_sequence = 0
	source_child_frames.clear()
	for fighter: FighterRuntime in [naruto, ichigo]:
		fighter.frame_script_sequence = _next_source_frame_sequence
		fighter.source_child_frame_requested.connect(_queue_source_child_frame)
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
	player_body_driver.configure(naruto, "res://generated/fighters/minren/player_controller", platforms,
		naruto._ground_y, game_world.map_size_x, player_body_services.invoke, source_callbacks)
	cpu_driver = AiCpuDriver.new()
	add_child(cpu_driver)
	cpu_driver.configure(ichigo, "res://generated/fighters/yihu/ai_controller", platforms,
		ichigo._ground_y, game_world.map_size_x, {"touchFloor": null}, cpu_services.invoke, false, source_callbacks)
	cpu_driver.body.updateDirect()
	cpu_driver.begin_display_tick(physics_tick)
	cpu_driver.start_random(source_random, 5)


func _next_source_frame_sequence() -> int:
	source_frame_sequence += 1
	return source_frame_sequence


func _queue_source_child_frame(operation: Callable) -> void:
	source_child_frames.append({"order": _next_source_frame_sequence(), "operation": operation})


func _stop_cpu() -> void:
	source_child_frames.clear()
	for fighter: FighterRuntime in [naruto, ichigo]:
		if is_instance_valid(fighter):
			fighter.frame_script_sequence = Callable()
			if fighter.source_child_frame_requested.is_connected(_queue_source_child_frame):
				fighter.source_child_frame_requested.disconnect(_queue_source_child_frame)
	if player_body_driver != null:
		player_body_driver.stop()
		player_body_driver.queue_free()
		player_body_driver = null
	if player_body_services != null:
		player_body_services.clear()
		player_body_services = null
	if cpu_driver != null:
		cpu_driver.stop()
		cpu_driver.queue_free()
		cpu_driver = null
	if cpu_services != null:
		cpu_services.clear()
		cpu_services = null
	cpu_stage_registry.clear_effects()
	if is_instance_valid(game_world):
		for child in game_world.get_children():
			if child is HitEffectRuntime:
				child.unregister_source_frames()
	if source_callbacks != null:
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


func _update_facing() -> void:
	if naruto.action == "站立" and player_body_driver == null:
		naruto.set_facing(1 if naruto.position.x <= ichigo.position.x else -1)
	if ichigo.action == "站立" and cpu_driver == null:
		ichigo.set_facing(1 if ichigo.position.x <= naruto.position.x else -1)


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


func _play_combo_hud(board_pn: int, hit_count: int) -> void:
	combo_hud.play(board_pn, hit_count)


func _on_hit_fx_pause() -> void:
	if super_runtime.game_paused:
		return
	if cpu_driver != null:
		# pauseGame stops eligible timelines, not enterFrame dispatch. In
		# particular beidax applies colors before its root-pause return.
		hit_fx_pause_count = 1
		super_runtime.zhanting = true
		naruto.root_zhanting = true
		ichigo.root_zhanting = true
		for actor in [naruto, ichigo, naruto_helper, ichigo_helper]:
			super_runtime.stop_mc(actor)
		return
	hit_fx_pause_count += 1
	naruto.zhanting = true
	ichigo.zhanting = true


func _on_hit_fx_resume() -> void:
	if cpu_driver != null:
		if super_runtime.game_paused or ko_paused:
			return
		hit_fx_pause_count = 0
		super_runtime.zhanting = false
		naruto.root_zhanting = false
		ichigo.root_zhanting = false
		for actor in [naruto, ichigo, naruto_helper, ichigo_helper]:
			super_runtime.play_mc(actor)
		super_presentation.resume_black_stg()
		return
	hit_fx_pause_count = maxi(0, hit_fx_pause_count - 1)
	if hit_fx_pause_count == 0 and not super_runtime.game_paused:
		naruto.zhanting = false
		ichigo.zhanting = false


func _advance_hit_effects(effects: Array[HitEffectRuntime]) -> void:
	for effect in effects:
		if is_instance_valid(effect) and not effect.is_queued_for_deletion():
			effect.advance_effect()


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
	effect.configure(effect_name, source_position, source_facing, offset_y)
	game_world.add_child(effect)
	if cpu_driver != null:
		effect.register_source_frames(source_callbacks, physics_tick)


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


func _on_super_event(_event: Dictionary, _caster: FighterRuntime) -> void:
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
