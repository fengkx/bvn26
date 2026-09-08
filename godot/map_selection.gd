class_name MapSelection
extends Control

signal confirmed(stage_id: String)
signal cancelled

const DIRECTORY := "res://generated/main/map_selection"
var spec: Dictionary = {}
var selected_index: int = 0
var source_frame: int = 35
var repeat_count: int = 10
var enabled: bool = false
var _background_frame: int = 1
var _textures: Dictionary = {}
var _confirm_timer: Timer
var _typing_timer: Timer
var _shown_characters: int = 0
var _sounds: Dictionary = {}


func _ready() -> void:
	mouse_filter = Control.MOUSE_FILTER_IGNORE
	spec = JSON.parse_string(FileAccess.get_file_as_string(DIRECTORY + "/presentation.json"))
	for card: Dictionary in spec["cards"]:
		_texture(str(card["texture"]))
	_confirm_timer = Timer.new()
	_confirm_timer.one_shot = true
	_confirm_timer.timeout.connect(_finish_confirmation)
	add_child(_confirm_timer)
	_typing_timer = Timer.new()
	_typing_timer.wait_time = float(spec["typing_interval_ms"]) / 1000.0
	_typing_timer.timeout.connect(func() -> void:
		_shown_characters = mini(_shown_characters + 1, selected_stage().length())
		queue_redraw()
	)
	add_child(_typing_timer)
	for key: String in spec["sounds"]:
		var player := AudioStreamPlayer.new()
		player.stream = load(DIRECTORY + "/" + str(spec["sounds"][key]))
		add_child(player)
		_sounds[key] = player


func reset() -> void:
	_confirm_timer.stop()
	_typing_timer.start()
	source_frame = int(spec["entry_frame"])
	_background_frame = 1
	repeat_count = 10
	enabled = true
	_select_grid(Vector2i(int(spec["initial_grid"][0]), int(spec["initial_grid"][1])))
	queue_redraw()


func leave() -> void:
	enabled = false
	_confirm_timer.stop()
	_typing_timer.stop()
	for player: AudioStreamPlayer in _sounds.values():
		player.stop()
	visible = false


func selected_stage() -> String:
	return str(spec["cards"][selected_index]["id"])


func _select_grid(point: Vector2i) -> bool:
	for index in spec["cards"].size():
		var grid: Array = spec["cards"][index]["grid"]
		if point == Vector2i(int(grid[0]), int(grid[1])):
			selected_index = index
			_shown_characters = 0
			queue_redraw()
			return true
	return false


func move_selection(direction: String) -> void:
	# Source left/right/up/down scan sparse grid cells, then adjacent lines.
	var card: Dictionary = spec["cards"][selected_index]
	var point := Vector2i(int(card["grid"][0]), int(card["grid"][1]))
	var horizontal := direction == "left" or direction == "right"
	var step := -1 if direction == "left" or direction == "up" else 1
	var low := 9999
	var high := 0
	for item: Dictionary in spec["cards"]:
		var value := int(item["grid"][0 if horizontal else 1])
		low = mini(low, value)
		high = maxi(high, value)
	var start := point.x if horizontal else point.y
	if step < 0 and start <= low:
		start = high + 1
	elif step > 0 and start >= high:
		start = low - 1
	for offset in [0, -2, 2]:
		var coordinate := start + step
		while coordinate >= low and coordinate <= high:
			var candidate := Vector2i(coordinate, point.y + offset) if horizontal else Vector2i(point.x + offset, coordinate)
			if _select_grid(candidate):
				return
			coordinate += step


func tick(held: Dictionary) -> void:
	source_frame = mini(source_frame + 1, int(spec["stop_frame"]))
	_background_frame = _background_frame % 4 + 1
	queue_redraw()
	if not enabled:
		return
	repeat_count += 1
	if repeat_count < int(spec["repeat_frames"]):
		return
	# These are separate if statements in caozuo, including simultaneous J/K.
	for direction in ["left", "right", "up", "down"]:
		if bool(held.get(direction, false)):
			repeat_count = 0
			move_selection(direction)
			_sounds["keysound1"].play()
	if bool(held.get("confirm", false)):
		repeat_count = 0
		enabled = false
		_sounds["keysound2"].play()
		_confirm_timer.start(float(spec["confirm_delay_ms"]) / 1000.0)
	if bool(held.get("back", false)):
		repeat_count = 0
		leave()
		cancelled.emit()


func _finish_confirmation() -> void:
	if visible and not enabled:
		confirmed.emit(selected_stage())


func _texture(filename: String) -> Texture2D:
	if not _textures.has(filename):
		_textures[filename] = load(DIRECTORY + "/" + filename)
	return _textures[filename]


func _draw() -> void:
	if spec.is_empty():
		return
	draw_texture_rect(_texture("background_%d.png" % _background_frame), Rect2(0, 0, 600, 400), false)
	var rect: Array = spec["card_rect"]
	for index in spec["cards"].size():
		var card: Dictionary = spec["cards"][index]
		var position := Vector2(float(card["position"][0]), float(card["position"][1]))
		var alpha := float(spec["selected_alpha"] if index == selected_index else spec["unselected_alpha"])
		draw_texture_rect(_texture(str(card["texture"])), Rect2(position + Vector2(rect[0], rect[1]), Vector2(rect[2], rect[3])), false, Color(1, 1, 1, alpha))
	for frame: Dictionary in spec["transition_frames"]:
		if int(frame["frame"]) != source_frame:
			continue
		for placement: Dictionary in frame["display_list"]:
			if placement.has("name"):
				continue
			var matrix: Dictionary = placement["matrix"]
			var outer: Dictionary = spec["outer_matrix"]
			var position := Vector2(float(matrix["translateX"]) + float(outer["translateX"]), float(matrix["translateY"]) + float(outer["translateY"])) / 20.0
			draw_texture_rect(_texture("wipe.png"), Rect2(position, Vector2(915.2, 422.1)), false)
	var footer: Array = spec["footer_position"]
	draw_texture_rect(_texture("footer.png"), Rect2(float(footer[0]), float(footer[1]), 600, 20), false)
	var name_texture := _texture("name_%d.png" % selected_index)
	var raster_scale := float(spec["raster_scale"])
	var width := name_texture.get_width() * float(_shown_characters) / selected_stage().length()
	var name_position: Array = spec["footer_name_position"]
	draw_texture_rect_region(name_texture, Rect2(float(name_position[0]), float(name_position[1]), width / raster_scale, name_texture.get_height() / raster_scale), Rect2(0, 0, width, name_texture.get_height()))
	var helper_name := _texture("name_10.png")
	draw_texture_rect(helper_name, Rect2(Vector2(600 - 7.5 - helper_name.get_width() / raster_scale, 385.2), helper_name.get_size() / raster_scale), false)
