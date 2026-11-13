extends Control

signal snapshot_changed(snapshot: Dictionary)
signal selection_confirmed(stage_id: String, session_id: String, revision: int)
signal selection_cancelled(session_id: String)

const Widgets = preload("res://online_lobby_widgets.gd")
var session_id := ""
var stage_id := ""
var revision := 0
var _buttons: Array[Button] = []
var _stages: Array[String] = []
var _heading: Label
var _active := false

func _ready() -> void:
	var background := ColorRect.new()
	background.color = Color("191719")
	background.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	add_child(background)
	var margin := MarginContainer.new()
	margin.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	for edge in ["left", "right", "top", "bottom"]:
		margin.add_theme_constant_override("margin_" + edge, 22)
	add_child(margin)
	var box := VBoxContainer.new()
	box.add_theme_constant_override("separation", 12)
	margin.add_child(box)
	_heading = Label.new()
	_heading.text = "选择地图 · 由房主决定"
	_heading.add_theme_font_size_override("font_size", 22)
	box.add_child(_heading)
	var hint := Label.new()
	hint.text = "确认后双方重新准备，再由房主开始对战。"
	box.add_child(hint)
	var grid := GridContainer.new()
	grid.columns = 5
	grid.add_theme_constant_override("h_separation", 8)
	grid.add_theme_constant_override("v_separation", 10)
	box.add_child(grid)
	var spec: Dictionary = JSON.parse_string(FileAccess.get_file_as_string("res://generated/main/map_selection/presentation.json"))
	for card: Dictionary in spec.cards:
		var cell := VBoxContainer.new()
		grid.add_child(cell)
		var picture := TextureRect.new()
		picture.texture = load("res://generated/main/map_selection/" + str(card.texture))
		picture.custom_minimum_size = Vector2(102, 62)
		picture.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
		picture.stretch_mode = TextureRect.STRETCH_KEEP_ASPECT_CENTERED
		cell.add_child(picture)
		var button := Widgets.button(str(card.id), _select.bind(str(card.id)))
		button.toggle_mode = true
		cell.add_child(button)
		_buttons.append(button)
		_stages.append(str(card.id))
	var actions := HBoxContainer.new()
	box.add_child(actions)
	actions.add_child(Widgets.button("返回房间", _cancel))
	var confirm := Widgets.button("确认地图", _confirm)
	Widgets.primary(confirm)
	actions.add_child(confirm)
	visible = false

func begin(new_session_id: String, is_host: bool, initial_stage: String) -> String:
	if not is_host: return "owner_required"
	if initial_stage not in _stages: return "unsupported_stage"
	session_id = new_session_id
	revision = 0
	_active = true
	show()
	_select(initial_stage)
	_buttons[_stages.find(initial_stage)].grab_focus()
	return ""

func _select(value: String) -> void:
	if not _active: return
	stage_id = value
	revision += 1
	for i in _buttons.size():
		_buttons[i].set_pressed_no_signal(_stages[i] == stage_id)
	_heading.text = "选择地图 · " + stage_id
	snapshot_changed.emit({"version": 1, "sessionId": session_id, "revision": revision, "stageId": stage_id, "confirmed": false})

func _confirm() -> void:
	if not _active: return
	selection_confirmed.emit(stage_id, session_id, revision)

func _cancel() -> void:
	if _active: selection_cancelled.emit(session_id)

func tick_local(_held: Dictionary) -> void:
	pass

func end_selection() -> void:
	_active = false
	hide()

func _unhandled_key_input(event: InputEvent) -> void:
	if _active and event.is_action_pressed("ui_cancel"):
		_cancel()
		get_viewport().set_input_as_handled()
