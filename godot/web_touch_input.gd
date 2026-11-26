extends Node

# Display ticks sample complete pad states, including taps that start and end
# between two physics frames. Physical keyboards keep their own pressed state.
const SLOTS := GameSession.P1_SLOTS
const MAX_MASK := 0x3ff

var surface: RenderSurface
var window: JavaScriptObject
var callback: JavaScriptObject
var mode := ""
var transform_ready := false
var transform_charged := false
var mask := 0
var pending: Array[int] = []


func _ready() -> void:
	surface = get_parent() as RenderSurface
	process_physics_priority = -100
	window = JavaScriptBridge.get_interface("window")
	callback = JavaScriptBridge.create_callback(_on_pad_state)
	window.bvnTouchRegister(callback)


func _exit_tree() -> void:
	if window != null:
		window.bvnTouchRegister(null)


func _on_pad_state(args: Array) -> void:
	var value := int(args[0])
	if value == -1:
		_clear()
	elif value == -2 and mode == "fight":
		surface.game.deliver_match_control({"button": "confirm", "pressed": false})
	elif value >= 0 and value <= MAX_MASK:
		var previous := mask if pending.is_empty() else int(pending.back())
		if previous == value:
			return
		if not pending.is_empty():
			var base := mask if pending.size() == 1 else pending[-2]
			# Independent edges share a display tick. Preserve a short press followed by release.
			if ((base ^ previous) & (previous ^ value)) == 0:
				pending[-1] = value
				return
		if pending.size() >= 16:
			pending.clear()
		pending.append(value)


func _clear() -> void:
	pending.clear()
	mask = 0
	if is_instance_valid(surface.game):
		surface.game.session.touch_slots.clear()


func _physics_process(_delta: float) -> void:
	var game = surface.game
	var next_mode := surface.online_lobby.touch_control_mode()
	if next_mode == "" and game.presentation_only:
		next_mode = "hidden"
	if next_mode == "":
		match game.session.root_label:
			"游戏场景": next_mode = "pause" if game.pause_menu.visible else "fight"
			"继续": next_mode = "continue"
			"选人画面":
				var selector: CharacterSelection = game.character_selection
				next_mode = "menu2" if selector.mode == 3 and selector.enabled == [false, true] else "menu"
			_: next_mode = "menu"
	if next_mode != mode:
		_clear()
		mode = next_mode
		transform_ready = false
		transform_charged = false
		window.bvnTouchSetMode(mode)
	if pending.is_empty():
		return
	var next := pending.pop_front() as int
	var changed := mask ^ next
	mask = next
	var session: GameSession = game.session
	var slots := GameSession.P2_SLOTS if mode == "menu2" else GameSession.P1_SLOTS
	for i in SLOTS.size():
		if changed & (1 << i):
			if mask & (1 << i):
				session.touch_slots[slots[i]] = true
			else:
				session.touch_slots.erase(slots[i])
	# The held map is complete before an event-driven menu reads it.
	for i in SLOTS.size():
		if not (changed & (1 << i)):
			continue
		var code := session.flash_to_key(session.codes[slots[i]])
		if mode == "continue" and i in [4, 5]:
			code = KEY_Y if i == 4 else KEY_N
		elif mode == "pause":
			code = {"w": KEY_UP, "s": KEY_DOWN, "j": KEY_ENTER}.get(SLOTS[i], KEY_NONE)
		if code != KEY_NONE and mode not in ["fight", "online-fight", "hidden"]:
			var event := InputEventKey.new()
			event.keycode = code
			event.physical_keycode = code
			event.pressed = bool(mask & (1 << i))
			surface.source_viewport.push_input(event, true)


func _process(_delta: float) -> void:
	var ready := false
	var charged := false
	if mode == "fight":
		ready = surface.game.touch_transform_ready("p1")
		charged = surface.game.touch_transform_charged("p1")
	elif mode == "online-fight" and surface.online_lobby.coordinator != null:
		ready = surface.online_lobby.coordinator.local_touch_transform_ready()
		charged = ready
	if ready != transform_ready or charged != transform_charged:
		transform_ready = ready
		transform_charged = charged
		window.bvnTouchSetTransformReady(ready, charged)
