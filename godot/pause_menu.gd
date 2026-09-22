class_name BattlePauseMenu
extends Node2D

signal title_requested
signal resume_requested
signal opened

var selection: int = 2
var _spec: Dictionary
var _selector: Sprite2D
var _panel: Sprite2D
var _timeline: Sprite2D
var source_frame: int = 1
var _playing: bool = false
var _back_pressed: bool = false
var _frame_textures: Dictionary = {}


func _ready() -> void:
	_spec = JSON.parse_string(FileAccess.get_file_as_string("res://generated/main/pause_menu/presentation.json"))
	for part in ["panel", "selector"]:
		var sprite := Sprite2D.new()
		sprite.texture = load("res://generated/main/pause_menu/%s.png" % part)
		sprite.centered = false
		var xy: Array = _spec[part + "_position"]
		sprite.position = Vector2(xy[0], xy[1])
		add_child(sprite)
		if part == "selector":
			_selector = sprite
		else:
			_panel = sprite
	_timeline = Sprite2D.new()
	_timeline.centered = false
	var xy: Array = _spec["timeline_position"]
	_timeline.position = Vector2(xy[0], xy[1])
	add_child(_timeline)
	for frame in range(2, int(_spec["detail_frame"]) + 1):
		_frame_textures[frame] = load("res://generated/main/pause_menu/frame-%d.png" % frame)
	visible = false
	_refresh()


func tick() -> void:
	if visible and _playing:
		source_frame += 1
		_playing = source_frame < int(_spec["detail_frame"])
		_refresh()


func handle_mouse(event: InputEventMouseButton) -> void:
	handle_control(control_from_event(event))


func control_from_event(event: InputEvent) -> Dictionary:
	if event is InputEventKey and not event.echo:
		var button := ""
		match event.keycode:
			KEY_ENTER, KEY_KP_ENTER: button = "confirm"
			KEY_UP: button = "up"
			KEY_DOWN: button = "down"
		if not button.is_empty():
			return {"button": button, "pressed": event.pressed}
	if event is InputEventMouseButton and event.button_index == MOUSE_BUTTON_LEFT:
		var bounds: Array = _spec["back_rect"]
		var inside := Rect2(bounds[0], bounds[1], bounds[2], bounds[3]).has_point(event.position)
		return {"button": "back", "pressed": event.pressed, "inside": inside}
	return {}


func _show_panel() -> void:
	# DefineButton2_2009: gotoAndStop(1), without resuming the battle.
	source_frame = 1
	_playing = false
	_refresh()


func handle_key(event: InputEventKey) -> void:
	handle_control(control_from_event(event))


func handle_control(control: Dictionary) -> void:
	if control.is_empty():
		return
	var button: String = control.button
	if button == "back":
		if not visible or source_frame != int(_spec["detail_frame"]):
			return
		if control.pressed:
			_back_pressed = control.inside
		else:
			if _back_pressed and control.inside:
				_show_panel()
			_back_pressed = false
		return
	# Preserve Button2009 keyPress before DefineSprite_1991 onKeyUp.
	if control.pressed:
		if visible and source_frame == int(_spec["detail_frame"]) and button == "confirm":
			_show_panel()
		return
	if not visible:
		if button == "confirm":
			selection = 2
			_show_panel()
			visible = true
			_refresh()
			opened.emit()
		return
	if button == "down":
		selection = (selection + 1) % 3
	elif button == "up":
		selection = (selection + 2) % 3
	elif button == "confirm":
		match selection:
			0:
				title_requested.emit()
			1:
				selection = 2
				_playing = true
			2:
				visible = false
				resume_requested.emit()
	_refresh()


func _refresh() -> void:
	_panel.visible = source_frame == 1
	_selector.visible = source_frame == 1
	_timeline.visible = source_frame > 1
	if source_frame > 1:
		_timeline.texture = _frame_textures[source_frame]
	_selector.position.y = float(_spec["selector_position"][1]) + float(_spec["selection_y"][selection])
