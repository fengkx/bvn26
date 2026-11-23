class_name TitleMenu
extends Control

signal confirmed(item_id: String)

const ONLINE_SLOT := 6
const ONLINE_ART := preload("res://ui/title_online.png")
const ONLINE_ITEM := {"id": "online", "title": "联机对战", "modo": 0, "goto": "", "frames": 20, "confirm_frame": 15, "source": null}

static var ITEMS: Array = JSON.parse_string(FileAccess.get_file_as_string("res://generated/main/title_menu/menu.json"))["items"]
var spec: Dictionary = JSON.parse_string(FileAccess.get_file_as_string("res://generated/main/title_menu/menu.json"))
var controller: RefCounted = load("res://generated/main/title_menu/controller.gd").new()
var select: int:
	get: return controller.select
var hint_text: String:
	get: return controller.hint
var hint_shown: String = ""
var pending_item: Dictionary = {}
var source_frame: int = 1
var button_frame: int = 1
const HIDDEN_ITEMS := ["single", "more", "exit"]
var _navigation_direction: int = 1
var _wheel_born: bool = false
var _selected_button: int = 0
var _background: Sprite2D
var _wheel: Control
var _buttons: Dictionary = {}
var _hint: Label
var _textures: Dictionary = {}
var _sounds: Dictionary = {}
var _hint_timer: Timer
var _online_entry: TextureButton
var _online_tint: Color

func _init() -> void:
	controller.positions = {13: NAN, 14: NAN}
	controller.reset()
	_skip_unavailable(true)

func _ready() -> void:
	mouse_filter = Control.MOUSE_FILTER_STOP
	set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	clip_contents = true
	_background = Sprite2D.new()
	_background.centered = false
	add_child(_background)
	_wheel = Control.new()
	_wheel.clip_contents = true
	_wheel.mouse_filter = Control.MOUSE_FILTER_IGNORE
	add_child(_wheel)
	var shader := Shader.new()
	shader.code = TimelinePreview.CXFORM_SHADER
	for name: String in spec.wheel_placements:
		var sprite := Sprite2D.new()
		sprite.centered = false
		var material := ShaderMaterial.new()
		material.shader = shader
		var color: Dictionary = spec.wheel_placements[name].get("color_transform", {})
		material.set_shader_parameter("cx_add", Color(float(color.get("redAddTerm", 0))/255.0, float(color.get("greenAddTerm", 0))/255.0, float(color.get("blueAddTerm", 0))/255.0, 0))
		sprite.material = material
		_wheel.add_child(sprite)
		_buttons[int(name.trim_prefix("btm"))] = sprite
	_online_tint = _buttons[ONLINE_SLOT].material.get_shader_parameter("cx_add")
	# The wheel sprite draws the title. This transparent control handles pointer input.
	_online_entry = TextureButton.new()
	_online_entry.name = "OnlineMenuItem"
	_online_entry.accessibility_name = ONLINE_ITEM.title
	_online_entry.tooltip_text = "联机对战 · 创建或加入好友房间"
	_online_entry.focus_mode = Control.FOCUS_NONE
	_online_entry.mouse_default_cursor_shape = Control.CURSOR_POINTING_HAND
	_online_entry.pressed.connect(_request_online_confirmation)
	_wheel.add_child(_online_entry)
	var footer := Sprite2D.new()
	footer.centered = false
	footer.texture = _texture("footer.png")
	footer.position = Vector2(float(spec.ui.downtxts.translateX + spec.ui.footer_bounds[0]), float(spec.ui.downtxts.translateY + spec.ui.footer_bounds[1])) / 20.0 - Vector2(5, 5)
	add_child(footer)
	var version := Label.new()
	version.position = Vector2(float(spec.ui.vertxt.translateX), float(spec.ui.vertxt.translateY)) / 20.0
	version.add_theme_font_size_override("font_size", 12)
	version.text = "V 2.6"
	add_child(version)
	_hint = Label.new()
	_hint.position = Vector2(float(spec.ui.downtxts.translateX + spec.ui.hint.translateX), float(spec.ui.downtxts.translateY + spec.ui.hint.translateY)) / 20.0
	_hint.size = Vector2(278, 22)
	_hint.add_theme_font_size_override("font_size", 12)
	_hint.add_theme_font_override("font", load("res://generated/main/title_menu/menu-font.ttf"))
	add_child(_hint)
	_hint_timer = Timer.new()
	_hint_timer.wait_time = 0.03
	_hint_timer.timeout.connect(_advance_hint)
	add_child(_hint_timer)
	_hint_timer.start()
	for number in [1, 2]:
		var player := AudioStreamPlayer.new()
		player.stream = load("res://generated/main/title_menu/keysound%d.mp3" % number)
		add_child(player)
		_sounds[number] = player
	_refresh()

func _item_index(index: int) -> int:
	return {9: 8, 10: 7, 11: 1, 12: 2}.get(index, index)


func _menu_item(index: int) -> Dictionary:
	if _item_index(index) == ONLINE_SLOT:
		return ONLINE_ITEM
	return ITEMS[_item_index(index) - 1]


func current_item() -> Dictionary:
	return _menu_item(select)


func contains_online_entry_point(point: Vector2) -> bool:
	return _online_entry != null and _online_entry.is_visible_in_tree() and _wheel.get_global_rect().has_point(point) and _online_entry.get_global_rect().has_point(point)

func apply_held(held: Dictionary) -> Dictionary:
	# Sprite 666 stops at 72; the controller is placed on frame 63.
	source_frame = mini(spec.wheel_frames.size(), source_frame + 1)
	var placement: Variant = spec.wheel_frames[source_frame - 1]
	if placement != null:
		if not _wheel_born:
			_wheel_born = true
			controller.reset()
			_skip_unavailable(true)
		else:
			if not pending_item.is_empty():
				button_frame += 1
				if button_frame == int(pending_item.confirm_frame):
					var item := pending_item.duplicate()
					confirmed.emit(str(item.id))
					_refresh()
					return item
			controller.hint_reset = false
			controller.sounds.clear()
			if held.get("up", false): _navigation_direction = -1
			if held.get("down", false): _navigation_direction = 1
			controller.tick(held)
			_skip_unavailable()
			if controller.confirmed_index != 0 and str(_menu_item(controller.confirmed_index).id) in HIDDEN_ITEMS:
				controller.confirmed_index = controller.select
			for number: int in controller.sounds:
				if _sounds.has(number):
					_sounds[number].play()
			if controller.hint_reset:
				hint_shown = ""
			if _item_index(controller.select) == ONLINE_SLOT:
				controller.hint = "联机对战：创建或加入好友房间"
			if controller.confirmed_index != 0 and pending_item.is_empty():
				_selected_button = controller.confirmed_index
				pending_item = _menu_item(_selected_button).duplicate()
				button_frame = 1
	_refresh()
	return {}

func _advance_hint() -> void:
	if visible and hint_shown.length() < hint_text.length():
		hint_shown = hint_text.substr(0, hint_shown.length() + 1)
		_hint.text = hint_shown

func reset() -> void:
	controller.reset()
	_skip_unavailable(true)
	controller.confirmed_index = 0
	controller.hint = ""
	controller.sounds.clear()
	pending_item = {}
	hint_shown = ""
	source_frame = 1
	button_frame = 1
	_selected_button = 0
	_wheel_born = false
	_refresh()

func _texture(name: String) -> Texture2D:
	if not _textures.has(name):
		_textures[name] = load("res://generated/main/title_menu/" + name)
	return _textures[name]


func _request_online_confirmation() -> void:
	if not pending_item.is_empty():
		return
	_selected_button = ONLINE_SLOT
	controller.select = ONLINE_SLOT
	controller.confirmed_index = ONLINE_SLOT
	controller.anj = 1
	pending_item = ONLINE_ITEM.duplicate(true)
	button_frame = 1
	_refresh()

func _refresh() -> void:
	if _background == null:
		return
	_background.texture = _texture("background-%d.png" % source_frame)
	_hint.text = hint_shown
	var placement: Variant = spec.wheel_frames[source_frame - 1]
	_wheel.visible = placement != null
	if placement == null:
		return
	var matrix: Dictionary = placement.matrix
	var mask: Dictionary = spec.mask.matrix
	var bounds: Dictionary = spec.mask_bounds_twips
	var mask_position := Vector2((float(mask.translateX) + float(bounds.Xmin) * float(mask.scaleX)) / 20.0, (float(mask.translateY) + float(bounds.Ymin) * float(mask.scaleY)) / 20.0)
	_wheel.position = Vector2(float(matrix.translateX), float(matrix.translateY)) / 20.0 + mask_position
	_wheel.size = Vector2((float(bounds.Xmax) - float(bounds.Xmin)) * float(mask.scaleX), (float(bounds.Ymax) - float(bounds.Ymin)) * float(mask.scaleY)) / 20.0
	for index: int in _buttons:
		var sprite: Sprite2D = _buttons[index]
		var item := _menu_item(index)
		sprite.visible = str(item.id) not in HIDDEN_ITEMS
		var alpha := float(placement.get("color_transform", {}).get("alphaMultTerm", 256)) / 256.0
		sprite.material.set_shader_parameter("cx_mul", Color(1, 1, 1, alpha))
		var p: Dictionary = spec.wheel_placements["btm%d" % index]
		var frame := button_frame if index == _selected_button else 1
		if index == ONLINE_SLOT:
			sprite.texture = ONLINE_ART
			# The source confirmation flashes white on frames 3-4, 7-8 and 11-12.
			var flash := frame in [3, 4, 7, 8, 11, 12]
			sprite.material.set_shader_parameter("cx_add", Color(1, 1, 1, 0) if flash else _online_tint)
		else:
			sprite.texture = _texture("button-%d-%d.png" % [_item_index(index), mini(frame, int(item.frames))])
		# The rasterizer's border is outside the authored button bounds.
		sprite.position = Vector2(float(p.matrix.translateX)/20.0, float(controller.positions[index])) - mask_position - Vector2(5, 5)
	var online_sprite: Sprite2D = _buttons[ONLINE_SLOT]
	# The authored placement centers the wider Information title in this slot.
	online_sprite.position.x += (_texture("button-%d-1.png" % ONLINE_SLOT).get_width() - ONLINE_ART.get_width()) * 0.5
	_online_entry.position = online_sprite.position
	_online_entry.size = ONLINE_ART.get_size()


func _skip_unavailable(initial: bool = false) -> void:
	# Only expose destinations implemented by the Web port.
	if initial:
		controller.reset()
		controller.select = 2
		for index in controller.positions:
			controller.positions[index] -= 56.0
	elif str(current_item().id) in HIDDEN_ITEMS:
		controller.select = ONLINE_SLOT if _navigation_direction < 0 else 2
		controller.an = 1
