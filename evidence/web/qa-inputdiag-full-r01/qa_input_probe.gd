extends Node

# QA-only probe: observes the browser input path without calling game actions.
func _init() -> void:
	process_mode = Node.PROCESS_MODE_ALWAYS

var _tick := 0
var _last := ""

func _ready() -> void:
	print("QA_INPUT_PROBE_READY")

func _input(event: InputEvent) -> void:
	if event is InputEventKey and (event.keycode in [KEY_D, KEY_J, KEY_K, KEY_KP_1, KEY_KP_5, KEY_KP_6]):
		print("QA_INPUT_EVENT ", {"keycode": event.keycode, "physical": event.physical_keycode, "pressed": event.pressed, "echo": event.echo})

func _physics_process(_delta: float) -> void:
	_tick += 1
	var surface := get_tree().current_scene
	var game: Variant = surface.get("game") if surface != null else null
	var session: Variant = game.get("session") if game != null else null
	var state := {
		"tick": _tick,
		"physical_d": Input.is_physical_key_pressed(KEY_D),
		"physical_j": Input.is_physical_key_pressed(KEY_J),
		"physical_kp1": Input.is_physical_key_pressed(KEY_KP_1),
		"root_label": str(session.get("root_label")) if session != null else "",
		"modo": int(session.get("modo")) if session != null else -1,
		"paused": bool(game.get("super_runtime").get("game_paused")) if game != null and game.get("super_runtime") != null else false,
	}
	if game != null and session != null and str(session.get("root_label")) == "游戏场景":
		state["p1"] = game.get("session").fighter_input("p1")
		state["p2"] = game.get("session").fighter_input("p2")
	var encoded := JSON.stringify(state)
	if encoded != _last and (_tick < 20 or state.physical_d or state.physical_j or state.physical_kp1):
		print("QA_INPUT_PROBE ", encoded)
		_last = encoded
