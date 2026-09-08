extends Control

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
var stage_sound: StageSound
var selected_stage: String = "现世"

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
	stage_sound = StageSound.new()
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
	if session.root_label != "游戏场景" or naruto.sw or ichigo.sw:
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
	# Fighters/assists remain locked; the map comes from the original map selector.
	# Source DefineSprite_600 (modo=3) / DefineSprite_603 (modo=4):
	# p1cpu=false, p2cpu=false, then 选人画面. This slice jumps to 游戏场景.
	session.modo = modo
	session.p1cpu = false
	session.p2cpu = false
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
	_chushi()
	_refresh_bind_label()


func _chushi() -> void:
	health_hud.reset()
	# Source frame_8 `chushi`: assign keys, hp=maxhp, place p1/p2, face.
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


func _advance_fight() -> void:
	_advance_screen_flash()
	combo_hud.tick()
	if super_presentation != null:
		super_presentation.tick()
	physics_tick += 1
	tick_label.text = "Fixed simulation tick: %d" % physics_tick
	if hit_fx_pause_count > 0:
		# Source pauseGame() stopMc on p1/p2/helpers. XG clip keeps playing.
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
	for fighter in fighters:
		fighter.advance_timeline()
	for helper in helpers:
		helper.advance_timeline()
	for fighter in fighters:
		fighter.enter_frame(_input_for(fighter))
	for helper in helpers:
		helper.enter_frame()
	CombatResolver.resolve_body_pair(naruto, ichigo)
	CombatResolver.resolve_pair(naruto, ichigo)
	CombatResolver.resolve_helpers(helpers, fighters)
	for fighter in fighters:
		fighter.run_frame_actions()
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
	return session.fighter_input(fighter.player_slot)


func _refresh_bind_label() -> void:
	var p1 := []
	for slot in GameSession.P1_SLOTS:
		p1.append(session.show_key_name(int(session.codes[slot])))
	var p2 := []
	for slot in GameSession.P2_SLOTS:
		p2.append(session.show_key_name(int(session.codes[slot])))
	config_label.text = "P1 %s  ·  P2 %s" % [" ".join(p1), " ".join(p2)]


func _update_facing() -> void:
	if naruto.action == "站立":
		naruto.set_facing(1 if naruto.position.x <= ichigo.position.x else -1)
	if ichigo.action == "站立":
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
	hit_fx_pause_count += 1
	naruto.zhanting = true
	ichigo.zhanting = true


func _on_hit_fx_resume() -> void:
	hit_fx_pause_count = maxi(0, hit_fx_pause_count - 1)
	if hit_fx_pause_count == 0 and not super_runtime.game_paused:
		naruto.zhanting = false
		ichigo.zhanting = false


func _spawn_hit_effect(effect_name: String, source_position: Vector2, source_facing: int, offset_y: float = -25.0) -> void:
	if not FileAccess.file_exists("res://generated/effects/%s/timeline.json" % effect_name):
		# Compiled but not imported yet: bdxg element tiers
		# (XG_fire/ice/leidian/stone).
		return
	var effect := HitEffectRuntime.new()
	effect.pause_requested.connect(_on_hit_fx_pause)
	effect.resume_requested.connect(_on_hit_fx_resume)
	effect.shine_requested.connect(_start_screen_flash)
	effect.configure(effect_name, source_position, source_facing, offset_y)
	game_world.add_child(effect)


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
	# Source KOplay(pn) wins over cbsd's 焦点. KO clip / blackStg("KO")
	# assets are not imported yet.
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
