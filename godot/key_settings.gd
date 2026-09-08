class_name KeySettings
extends Control

# Source: scripts/main.json
# - DefineSprite_836 cselect==1 + J → gotoAndStop("键位设置")
# - DefineButton2_754–807 set _parent.key then kck.gotoAndStop("enterkey")
# - DefineSprite_835 frame 5: txt="输入任意键继续"; keyDown writes
#   `_root[_parent._parent.key] = Key.getCode()` then gotoAndStop(1)
# - K or cselect==6 + J saves SharedObject and gotoAndStop("MENU")

signal back_to_menu

# Source strings are Chinese (`输入任意键继续`, `回主菜单`, `键位设置`).
# This slice shows the English wheel wording so the default font can render.
const TITLE := "KEY SETTING"
const CAPTURE_HINT := "Press any key"
const BACK_HINT := "Back to MENU"

var session: GameSession
var row: int = 1
var side: int = 1
var capturing: bool = false
var capture_slot: String = ""
var waiting_release: bool = false
var hint_text: String = TITLE
var hint_shown: String = ""
var _held := {
	"up": false,
	"down": false,
	"left": false,
	"right": false,
	"confirm": false,
	"back": false,
}
var _p1_rows: Array[Label] = []
var _p2_rows: Array[Label] = []
var _hint: Label
var _back: Label


func _ready() -> void:
	mouse_filter = Control.MOUSE_FILTER_STOP
	set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	_build()
	_reset_hint(TITLE)
	_refresh()


func _unhandled_input(event: InputEvent) -> void:
	if not capturing or waiting_release:
		return
	if not (event is InputEventKey) or not event.pressed or event.echo:
		return
	var key_event := event as InputEventKey
	var keycode := key_event.physical_keycode if key_event.physical_keycode != KEY_NONE else key_event.keycode
	if session == null or capture_slot == "":
		return
	session.bind_slot(capture_slot, session.key_to_flash(keycode))
	capturing = false
	capture_slot = ""
	_reset_hint(TITLE)
	_refresh()
	get_viewport().set_input_as_handled()


func reset() -> void:
	row = 1
	side = 1
	capturing = false
	capture_slot = ""
	waiting_release = false
	_held = {
		"up": false,
		"down": false,
		"left": false,
		"right": false,
		"confirm": false,
		"back": false,
	}
	_reset_hint(TITLE)
	_refresh()


func refresh_view() -> void:
	_refresh()


func apply_held(held: Dictionary) -> String:
	var edge := _edges(held)
	if waiting_release:
		if not bool(_held["confirm"]) and not bool(_held["back"]):
			waiting_release = false
			if capture_slot != "":
				capturing = true
				_reset_hint(CAPTURE_HINT)
		_advance_hint()
		_refresh()
		return ""
	if capturing:
		_advance_hint()
		_refresh()
		return ""
	if bool(edge["back"]):
		_request_back()
		return "MENU"
	if bool(edge["up"]):
		row = 10 if row == 1 else row - 1
		_reset_hint(TITLE)
	elif bool(edge["down"]):
		row = 1 if row == 10 else row + 1
		_reset_hint(TITLE)
	elif bool(edge["left"]):
		side = 1
		_reset_hint(TITLE)
	elif bool(edge["right"]):
		side = 2
		_reset_hint(TITLE)
	elif bool(edge["confirm"]):
		_begin_capture(_current_slot())
	_advance_hint()
	_refresh()
	return ""


func _edges(held: Dictionary) -> Dictionary:
	var edges := {}
	for name in _held.keys():
		var now := bool(held.get(name, false))
		edges[name] = now and not bool(_held[name])
		_held[name] = now
	return edges


func _current_slot() -> String:
	var slots := GameSession.P1_SLOTS if side == 1 else GameSession.P2_SLOTS
	return slots[row - 1]


func _begin_capture(slot: String) -> void:
	capture_slot = slot
	waiting_release = true
	capturing = false
	_reset_hint(CAPTURE_HINT)


func _request_back() -> void:
	if session:
		session.save_store()
	back_to_menu.emit()


func _reset_hint(text: String) -> void:
	hint_text = text
	hint_shown = ""


func _advance_hint() -> void:
	if hint_shown.length() < hint_text.length():
		hint_shown = hint_text.substr(0, hint_shown.length() + 1)


func _build() -> void:
	var panel := ColorRect.new()
	panel.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	panel.color = Color(0.035, 0.043, 0.063, 1)
	add_child(panel)
	var title := Label.new()
	title.position = Vector2(40, 16)
	title.size = Vector2(520, 24)
	title.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	title.add_theme_color_override("font_color", Color(1, 0.77, 0.22))
	title.add_theme_font_size_override("font_size", 18)
	title.text = TITLE
	add_child(title)
	var p1_head := Label.new()
	p1_head.position = Vector2(40, 48)
	p1_head.size = Vector2(240, 18)
	p1_head.text = "P1"
	p1_head.add_theme_color_override("font_color", Color(0.83, 0.86, 0.92))
	add_child(p1_head)
	var p2_head := Label.new()
	p2_head.position = Vector2(320, 48)
	p2_head.size = Vector2(240, 18)
	p2_head.text = "P2"
	p2_head.add_theme_color_override("font_color", Color(0.83, 0.86, 0.92))
	add_child(p2_head)
	for index in 10:
		var left := Label.new()
		left.position = Vector2(40, 72 + index * 26)
		left.size = Vector2(240, 24)
		left.add_theme_font_size_override("font_size", 13)
		left.gui_input.connect(_on_row_gui.bind(1, index + 1))
		left.mouse_filter = Control.MOUSE_FILTER_STOP
		_p1_rows.append(left)
		add_child(left)
		var right := Label.new()
		right.position = Vector2(320, 72 + index * 26)
		right.size = Vector2(240, 24)
		right.add_theme_font_size_override("font_size", 13)
		right.gui_input.connect(_on_row_gui.bind(2, index + 1))
		right.mouse_filter = Control.MOUSE_FILTER_STOP
		_p2_rows.append(right)
		add_child(right)
	_back = Label.new()
	_back.position = Vector2(40, 338)
	_back.size = Vector2(520, 20)
	_back.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	_back.add_theme_font_size_override("font_size", 13)
	_back.text = BACK_HINT + "  (K)"
	add_child(_back)
	_hint = Label.new()
	_hint.position = Vector2(16, 372)
	_hint.size = Vector2(568, 20)
	_hint.add_theme_color_override("font_color", Color(0.83, 0.86, 0.92))
	_hint.add_theme_font_size_override("font_size", 12)
	add_child(_hint)


func _on_row_gui(event: InputEvent, next_side: int, next_row: int) -> void:
	if capturing or waiting_release:
		return
	if event is InputEventMouseButton and event.pressed and event.button_index == MOUSE_BUTTON_LEFT:
		side = next_side
		row = next_row
		_begin_capture(_current_slot())
		_refresh()


func _refresh() -> void:
	if session == null or _p1_rows.is_empty():
		return
	_fill_column(_p1_rows, GameSession.P1_SLOTS, 1)
	_fill_column(_p2_rows, GameSession.P2_SLOTS, 2)
	if _hint:
		_hint.text = hint_shown
	if _back:
		_back.add_theme_color_override("font_color", Color(0.72, 0.76, 0.84))


func _fill_column(rows: Array[Label], slots: PackedStringArray, column: int) -> void:
	for index in slots.size():
		var slot := slots[index]
		var selected := column == side and index + 1 == row
		var flash_code := int(session.codes[slot])
		var name := session.show_key_name(flash_code)
		if name == "":
			name = str(flash_code)
		var capturing_here := capturing and capture_slot == slot
		var marker := "> " if selected else "  "
		rows[index].text = "%s%s  %s" % [marker, session.slot_action(slot), name]
		rows[index].add_theme_color_override(
			"font_color",
			Color(1, 0.55, 0.35) if capturing_here else (
				Color(1, 0.92, 0.45) if selected else Color(0.72, 0.76, 0.84)
			)
		)
