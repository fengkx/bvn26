class_name TitleMenu
extends Control

# Source: scripts/main.json
# - root label MENU / frame_10/DoAction.as
# - DefineSprite_620 controller: W/S change select, J plays btmN
# This slice keeps three reachable entries and skips 选人画面.

signal confirmed(item_id: String)

# Display strings match the English MENU wheel art (btm clips), not the
# Chinese downtxts / script names. goto stays the source frame label.
const ITEMS := [
	{
		"id": "versus",
		"title": "VS MODE",
		"hint": "VS MODE",
		"modo": 3,
		"goto": "游戏场景",
	},
	{
		"id": "training",
		"title": "TRAINING",
		"hint": "TRAINING",
		"modo": 4,
		"goto": "游戏场景",
	},
	{
		"id": "key_settings",
		"title": "KEY SETTING",
		"hint": "KEY SETTING",
		"modo": 0,
		"goto": "键位设置",
	},
]

var select: int = 1
var hint_text: String = "VS MODE"
var hint_shown: String = ""
var pending_item: Dictionary = {}
var _held := {
	"up": false,
	"down": false,
	"confirm": false,
}
var _title: Label
var _hint: Label
var _rows: Array[Label] = []


func _ready() -> void:
	mouse_filter = Control.MOUSE_FILTER_STOP
	set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	_build()
	_refresh()


func apply_held(held: Dictionary) -> Dictionary:
	# Original an/anj lock one step until the wheel settles / button clip
	# returns. Without imported button clips, a rising edge is the sourced
	# "one Key.isDown while an==0" step.
	var edge_up := bool(held.get("up", false)) and not bool(_held["up"])
	var edge_down := bool(held.get("down", false)) and not bool(_held["down"])
	var edge_confirm := bool(held.get("confirm", false)) and not bool(_held["confirm"])
	_held["up"] = bool(held.get("up", false))
	_held["down"] = bool(held.get("down", false))
	_held["confirm"] = bool(held.get("confirm", false))
	if not pending_item.is_empty():
		if not bool(_held["confirm"]):
			var item: Dictionary = pending_item.duplicate()
			pending_item = {}
			confirmed.emit(str(item["id"]))
			return item
		return {}
	if edge_up:
		select = ITEMS.size() if select == 1 else select - 1
		_reset_hint()
	elif edge_down:
		select = 1 if select == ITEMS.size() else select + 1
		_reset_hint()
	elif edge_confirm:
		pending_item = ITEMS[select - 1].duplicate()
	_advance_hint()
	_refresh()
	return {}


func reset() -> void:
	select = 1
	pending_item = {}
	_held = {"up": false, "down": false, "confirm": false}
	_reset_hint()
	_refresh()


func current_item() -> Dictionary:
	return ITEMS[select - 1]


func _reset_hint() -> void:
	hint_text = str(ITEMS[select - 1]["hint"])
	hint_shown = ""


func _advance_hint() -> void:
	# downtxts: setInterval(wenzi, 30) adds one character per 30 ms / tick.
	if hint_shown.length() < hint_text.length():
		hint_shown = hint_text.substr(0, hint_shown.length() + 1)


func _build() -> void:
	var panel := ColorRect.new()
	panel.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	panel.color = Color(0.035, 0.043, 0.063, 1)
	add_child(panel)
	_title = Label.new()
	_title.position = Vector2(40, 28)
	_title.size = Vector2(520, 28)
	_title.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	_title.add_theme_color_override("font_color", Color(1, 0.77, 0.22))
	_title.add_theme_font_size_override("font_size", 20)
	_title.text = "BLEACH VS NARUTO 2.6"
	add_child(_title)
	for index in ITEMS.size():
		var row := Label.new()
		row.position = Vector2(80, 110 + index * 48)
		row.size = Vector2(440, 36)
		row.add_theme_font_size_override("font_size", 18)
		_rows.append(row)
		add_child(row)
	_hint = Label.new()
	_hint.position = Vector2(16, 372)
	_hint.size = Vector2(568, 20)
	_hint.add_theme_color_override("font_color", Color(0.83, 0.86, 0.92))
	_hint.add_theme_font_size_override("font_size", 12)
	add_child(_hint)
	_reset_hint()


func _refresh() -> void:
	if _rows.is_empty():
		return
	for index in ITEMS.size():
		var item: Dictionary = ITEMS[index]
		var marker := "> " if select == index + 1 else "  "
		_rows[index].text = marker + str(item["title"])
		_rows[index].add_theme_color_override(
			"font_color",
			Color(1, 0.92, 0.45) if select == index + 1 else Color(0.72, 0.76, 0.84)
		)
	if _hint:
		_hint.text = hint_shown
