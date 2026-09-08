extends Control

@onready var tick_label: Label = %TickLabel
@onready var state_label: Label = %StateLabel
@onready var game_world: GameWorld = %Game
@onready var naruto: FighterRuntime = %Naruto
@onready var ichigo: FighterRuntime = %Ichigo
@onready var current_world: TimelinePreview = %CurrentWorld
@onready var naruto_energy: EnergyBar = %NarutoEnergy
@onready var ichigo_energy: EnergyBar = %IchigoEnergy

var physics_tick: int = 0
var naruto_helper: HelperRuntime
var ichigo_helper: HelperRuntime
var screen_flash: ColorRect
var screen_flash_age: int = -1

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
	_setup_screen_flash()
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
	naruto.sync_body_collision_position()
	ichigo.sync_body_collision_position()
	naruto.hit_effect_requested.connect(_spawn_hit_effect)
	ichigo.hit_effect_requested.connect(_spawn_hit_effect)
	naruto.screen_flash_requested.connect(_start_screen_flash)
	ichigo.screen_flash_requested.connect(_start_screen_flash)
	# This slice locks assistance to 我爱罗. 魂 has combat metadata only.
	naruto_helper = _make_helper("res://generated/helpers/woailuo")
	ichigo_helper = _make_helper("res://generated/helpers/kon")
	game_world.snap(naruto, ichigo)
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


func _physics_process(_delta: float) -> void:
	_advance_screen_flash()
	physics_tick += 1
	tick_label.text = "Fixed simulation tick: %d" % physics_tick
	var fighters: Array[FighterRuntime] = [ichigo, naruto]
	var helpers: Array = []
	if naruto_helper != null:
		helpers.append(naruto_helper)
	if ichigo_helper != null:
		helpers.append(ichigo_helper)
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
	_apply_ko_focus()
	_update_facing()
	game_world.enter_frame(naruto, ichigo, helpers)
	state_label.text = "Naruto  HP %d  MP %d  %s:%d    Ichigo  HP %d  MP %d  %s:%d" % [
		int(naruto.health),
		int(naruto.energy),
		_status_name(naruto),
		naruto.current_source_frame(),
		int(ichigo.health),
		int(ichigo.energy),
		_status_name(ichigo),
		ichigo.current_source_frame(),
	]
	naruto_energy.energy = naruto.energy
	ichigo_energy.energy = ichigo.energy


func _input_for(fighter: FighterRuntime) -> Dictionary:
	if fighter == naruto:
		return {
			"up": _key(KEY_W),
			"down": _key(KEY_S),
			"left": _key(KEY_A),
			"right": _key(KEY_D),
			"attack": _key(KEY_J),
			"jump": _key(KEY_K),
			"dash": _key(KEY_L),
			"ranged": _key(KEY_U),
			"special": _key(KEY_I),
			"summon": _key(KEY_O),
		}
	return {
		"up": _key(KEY_UP),
		"down": _key(KEY_DOWN),
		"left": _key(KEY_LEFT),
		"right": _key(KEY_RIGHT),
		"attack": _key(KEY_KP_1),
		"jump": _key(KEY_KP_2),
		"dash": _key(KEY_KP_3),
		"ranged": _key(KEY_KP_4),
		"special": _key(KEY_KP_5),
		"summon": _key(KEY_KP_6),
	}


func _key(keycode: Key) -> bool:
	# Physical keys keep the original control layout independent of IME text input.
	# Logical state is also needed for synthetic browser events used by Web tests.
	return Input.is_physical_key_pressed(keycode) or Input.is_key_pressed(keycode)


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
	helper.z_index = 3
	game_world.add_child(helper)
	return helper


func _spawn_hit_effect(effect_name: String, source_position: Vector2, source_facing: int) -> void:
	var effect := HitEffectRuntime.new()
	effect.configure(effect_name, source_position, source_facing)
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


func _apply_ko_focus() -> void:
	# Source KOplay(pn): 焦点 is the KO'd fighter. KO clip / blackStg("KO")
	# assets are not imported yet.
	if naruto.sw:
		game_world.focus = naruto.player_slot
	elif ichigo.sw:
		game_world.focus = ichigo.player_slot


func _status_name(fighter: FighterRuntime) -> String:
	var name := _action_name(fighter.action)
	return "%s/KO" % name if fighter.sw else name


func _action_name(label: String) -> String:
	# Source timeline labels are the move IDs; do not invent a second name set.
	return label if label != "" else "站立"
