extends Control

const EMPTY := preload("res://ui/battle_loading/empty.png")
const FULL := preload("res://ui/battle_loading/full.png")
var progress := 0.0
var names: Array = []
var portraits: Array = []
var failed := false
var choice := ""
var viewport_size := Vector2(600, 400)


func _ready() -> void:
	set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	z_as_relative = false
	z_index = 4000
	theme = Theme.new()
	theme.default_font = OnlineUserTextFont.with_cjk_fallback(load("res://generated/main/title_menu/menu-font.ttf"))
	mouse_filter = Control.MOUSE_FILTER_STOP
	var row := HBoxContainer.new()
	row.name = "Actions"
	row.position = Vector2(220, 265)
	add_child(row)
	for pair in [["重试", "retry"], ["返回", "back"]]:
		var button := Button.new()
		button.text = pair[0]
		button.custom_minimum_size = Vector2(80, 36)
		row.add_child(button)
		button.pressed.connect(func(): choice = pair[1])
	row.hide()


func _input(event: InputEvent) -> void:
	if event is InputEventKey:
		if failed and event.pressed and not event.echo:
			if event.keycode in [KEY_J, KEY_ENTER]: choice = "retry"
			if event.keycode in [KEY_K, KEY_ESCAPE]: choice = "back"
		get_viewport().set_input_as_handled()


func prepare(ids: Array, labels: Array, selection: CharacterSelection) -> bool:
	var bridge = JavaScriptBridge.get_interface("bvnBattlePacks")
	var needed: Array = []
	for id in ids:
		if bridge.needed(id) and id not in needed:
			needed.append(id)
	names = labels
	for label in labels:
		portraits.append(selection.loading_portrait(label))
	for i in needed.size():
		var id: String = needed[i]
		if not bridge.needed(id): continue
		while true:
			bridge.start(id)
			while str(bridge.state(id)) == "loading":
				progress = (i + float(bridge.progress(id))) / needed.size()
				queue_redraw()
				await get_tree().process_frame
			if str(bridge.state(id)) == "ready" and ProjectSettings.load_resource_pack(str(bridge.path(id)), false):
				bridge.mounted(id)
				break
			push_error("Failed to load battle pack: " + id)
			failed = true
			$Actions.show()
			queue_redraw()
			while choice.is_empty(): await get_tree().process_frame
			if choice == "back": return false
			choice = ""
			failed = false
			$Actions.hide()
	return true


func _draw() -> void:
	draw_texture_rect(EMPTY, Rect2(Vector2.ZERO, viewport_size), false)
	var bar := Rect2(102, 376, 488 * progress, 20)
	draw_texture_rect_region(FULL, bar, bar)
	for i in portraits.size():
		var texture: Texture2D = portraits[i]
		if texture == null: continue
		var area := Vector2(145, 150)
		var bounds := texture.get_size()
		var scaled := bounds * minf(area.x / bounds.x, area.y / bounds.y)
		var origin := Vector2(145 + 160 * i, 100) + (area - scaled) * 0.5
		draw_texture_rect(texture, Rect2(origin, scaled), false)
	draw_string(theme.default_font, Vector2(130, 259), "   VS   ".join(names), HORIZONTAL_ALIGNMENT_CENTER, 340, 15)
	if failed:
		draw_string(theme.default_font, Vector2(130, 326), "资源加载失败", HORIZONTAL_ALIGNMENT_CENTER, 340, 14)
