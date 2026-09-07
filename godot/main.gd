extends Control

@onready var tick_label: Label = %TickLabel
@onready var state_label: Label = %StateLabel
@onready var naruto: FighterRuntime = %Naruto
@onready var ichigo: FighterRuntime = %Ichigo

var physics_tick: int = 0


func _ready() -> void:
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
	physics_tick += 1
	tick_label.text = "Fixed simulation tick: %d" % physics_tick
	var fighters: Array[FighterRuntime] = [ichigo, naruto]
	for fighter in fighters:
		fighter.advance_timeline()
	for fighter in fighters:
		var opponent := naruto if fighter == ichigo else ichigo
		fighter.enter_frame(_input_for(fighter))
		fighter.incoming_attack_hits(opponent)
	for fighter in fighters:
		fighter.run_frame_actions()
	_update_facing()
	state_label.text = "Naruto  HP %d  MP %d  %s:%d    Ichigo  HP %d  MP %d  %s:%d" % [
		int(naruto.health),
		int(naruto.energy),
		_action_name(naruto.action),
		naruto.current_source_frame(),
		int(ichigo.health),
		int(ichigo.energy),
		_action_name(ichigo.action),
		ichigo.current_source_frame(),
	]


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


func _action_name(label: String) -> String:
	return {
		"站立": "idle",
		"走": "walk",
		"砍1": "attack1",
		"砍2": "attack2",
		"砍3": "attack3",
		"被打": "hurt",
		"跳": "jump",
		"跳2": "double_jump",
		"落": "fall",
		"落2": "fall_fast",
		"落地": "land",
		"瞬步": "dash",
		"防御": "guard_start",
		"防御2": "guard",
		"防住": "guard_hit",
		"招1": "ranged",
		"招2": "down_ranged",
		"招3": "up_ranged",
		"砍技1": "down_attack",
		"砍技2": "up_attack",
		"招换": "summon",
		"必杀": "special",
		"上必杀": "up_special",
		"超必杀": "super_special",
		"必杀0": "special_end",
	}.get(label, "action")
