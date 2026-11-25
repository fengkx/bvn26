class_name CharacterSelection
extends Control

signal confirmed(fighters: Array, helpers: Array)
signal cancelled

const DIRECTORY := "res://generated/main/character_selection"
var spec: Dictionary = JSON.parse_string(FileAccess.get_file_as_string(DIRECTORY + "/selection.json"))
var available: Dictionary = JSON.parse_string(FileAccess.get_file_as_string(DIRECTORY + "/available.json"))
var mode: int = 2
var phase: int = 0
var source_frame: int = 1
var fighters: Array = ["", ""]
var helpers: Array = ["", ""]
var enabled: Array = [true, false]
var selected: Array = [-1, -1]
var repeats: Array = [10, 10]
var cards: Array = []
var _cards: Array[TimelinePreview] = []
var _cursors: Array[TimelinePreview] = []
var _cursor_frames: Array = [1, 1]
var _timers: Array[Timer] = []
var _background_frame: int = 1
var _sounds: Array[AudioStreamPlayer] = []
var _active: bool = false
var _portrait_spec: Dictionary = {}
var _footer_spec: Dictionary = {}
var _portrait_frames: Array = [1, 1]
var _text_counts: Array = [0, 0]
var _typing_timer: Timer
var _wipe: Sprite2D
var _footer_layer: Node2D
var _textures: Dictionary = {}


func _ready() -> void:
	mouse_filter = Control.MOUSE_FILTER_IGNORE
	_portrait_spec = JSON.parse_string(FileAccess.get_file_as_string(DIRECTORY + "/portraits.json"))
	_footer_spec = JSON.parse_string(FileAccess.get_file_as_string(DIRECTORY + "/footer.json"))
	_wipe = Sprite2D.new()
	_wipe.centered = false
	_wipe.z_index = 20
	_wipe.texture = load("res://generated/main/map_selection/wipe.png")
	_wipe.scale = Vector2(915.2, 422.1) / _wipe.texture.get_size()
	add_child(_wipe)
	_footer_layer = Node2D.new()
	_footer_layer.z_index = 30
	_footer_layer.draw.connect(_draw_footer)
	add_child(_footer_layer)
	_typing_timer = Timer.new()
	_typing_timer.wait_time = 0.03
	_typing_timer.timeout.connect(func() -> void:
		for i in 2:
			_text_counts[i] += 1
		_footer_layer.queue_redraw())
	add_child(_typing_timer)
	for i in 2:
		var cursor := _make_clip("player%d" % (i + 1))
		cursor.z_index = 10
		_cursors.append(cursor)
		var timer := Timer.new()
		timer.one_shot = true
		timer.timeout.connect(_finish_confirmation.bind(i))
		add_child(timer)
		_timers.append(timer)
		var sound := AudioStreamPlayer.new()
		sound.stream = load("res://generated/main/title_menu/keysound%d.mp3" % (i + 1))
		add_child(sound)
		_sounds.append(sound)


func _make_clip(directory: String) -> TimelinePreview:
	var clip := TimelinePreview.new()
	clip.fighter_directory = DIRECTORY + "/" + directory
	clip.autoplay = false
	clip.show_collision_shapes = false
	add_child(clip)
	return clip


func reset(selected_mode: int) -> void:
	leave()
	mode = selected_mode
	fighters = ["", ""]
	helpers = ["", ""]
	visible = true
	_active = true
	_typing_timer.start()
	_enter_phase(0)


func leave() -> void:
	_active = false
	if _typing_timer != null:
		_typing_timer.stop()
	enabled = [false, false]
	for timer in _timers:
		timer.stop()
	visible = false


func _enter_phase(next_phase: int) -> void:
	phase = next_phase
	source_frame = int(spec.phases[phase].entry_frame)
	selected = [-1, -1]
	enabled = [true, mode == 3]
	repeats = [10, 10]
	_cursor_frames = [1, 1]
	for card in _cards:
		remove_child(card)
		card.queue_free()
	_cards.clear()
	cards.clear()
	var roster: Dictionary = available.fighters if phase == 0 else available.helpers
	for card: Dictionary in spec.phases[phase].cards:
		if not roster.has(card.id):
			continue
		cards.append(card)
		var clip := _make_clip("card")
		clip.set_instance_clip_frame("namemc", int(card.portrait_frame), false)
		clip.play_source_frame(1)
		_cards.append(clip)
	assert(not cards.is_empty(), "No implemented entries for selection phase")
	_show_player(0)
	if mode == 3:
		_show_player(1)
	_update_view()


func _show_player(player: int) -> void:
	enabled[player] = true
	if player == 0:
		for x in range(5, 0, -1):
			if _select_grid(Vector2i(x, 7), player):
				return
	else:
		for x in range(7, 12):
			if _select_grid(Vector2i(x, 7), player):
				return
	# Filtering unpublished content can remove the original initial cells.
	for card: Dictionary in cards:
		if _select_grid(Vector2i(int(card.grid[0]), int(card.grid[1])), player):
			return
	assert(false, "No eligible implemented selection")


func _select_grid(point: Vector2i, player: int) -> bool:
	for index in cards.size():
		var card: Dictionary = cards[index]
		if point != Vector2i(int(card.grid[0]), int(card.grid[1])):
			continue
		if phase == 1 and fighters[player] == card.id:
			return false
		selected[player] = index
		_portrait_frames[player] = 1
		_text_counts[player] = 0
		if phase == 0:
			fighters[player] = str(card.id)
		else:
			helpers[player] = str(card.id)
		_update_view()
		return true
	return false


func tick(p1: Dictionary, p2: Dictionary) -> void:
	if not _active:
		return
	source_frame = mini(source_frame + 1, int(spec.phases[phase].stop_frame))
	_background_frame = _background_frame % 4 + 1
	for player in 2:
		_portrait_frames[player] = 4 if int(_portrait_frames[player]) == 5 else int(_portrait_frames[player]) + 1
		if _cursor_frames[player] > 1:
			_cursor_frames[player] = int(_cursor_frames[player]) % 20 + 1
			_cursors[player].play_source_frame(int(_cursor_frames[player]))
		if not enabled[player]:
			continue
		var held := p1 if player == 0 or mode in [2, 4] else p2
		repeats[player] += 1
		if repeats[player] < int(spec.repeat_frames):
			continue
		for direction in ["left", "right", "up", "down"]:
			if bool(held.get(direction, false)):
				repeats[player] = 0
				var grid: Array = cards[selected[player]].grid
				SelectionGrid.move(cards, Vector2i(int(grid[0]), int(grid[1])), direction, _select_grid.bind(player))
				_sounds[0].play()
		if bool(held.get("confirm", false)):
			repeats[player] = 0
			enabled[player] = false
			_cursor_frames[player] = 2
			_sounds[1].play()
			_timers[player].start(float(spec.confirm_delay_ms) / 1000.0)
		if bool(held.get("back", false)):
			leave()
			cancelled.emit()
			return
	_update_view()


func _finish_confirmation(player: int) -> void:
	if not _active:
		return
	if player == 0 and mode in [2, 4]:
		_show_player(1)
		return
	if not enabled[1 - player]:
		if phase == 0:
			_enter_phase(1)
		else:
			_active = false
			confirmed.emit(fighters.duplicate(), helpers.duplicate())


func _update_view() -> void:
	if _cards.is_empty():
		return
	var outer: Dictionary = {}
	for placement: Dictionary in spec.outer_display_list:
		if placement.get("name") == "xure":
			outer = placement.matrix
	_wipe.visible = false
	var grid_matrix: Dictionary = {}
	for placement: Dictionary in spec.selector_frames[source_frame - 1].display_list:
		if placement.get("name") == "xrmc":
			grid_matrix = placement.matrix
		elif not placement.has("name"):
			_wipe.visible = true
			_wipe.position = Vector2(float(outer.translateX + placement.matrix.translateX), float(outer.translateY + placement.matrix.translateY)) / 20.0
	var origin := Vector2(float(outer.translateX + grid_matrix.translateX), float(outer.translateY + grid_matrix.translateY)) / 20.0
	for i in cards.size():
		var matrix: Dictionary = cards[i].placement.matrix
		_cards[i].position = origin + Vector2(float(matrix.translateX), float(matrix.translateY)) / 20.0
		_cards[i].modulate.a = 1.0 if i in selected else 0.5
	for i in 2:
		_cursors[i].visible = selected[i] >= 0
		if selected[i] >= 0:
			_cursors[i].position = _cards[selected[i]].position
	_footer_layer.queue_redraw()
	queue_redraw()


func _texture(name: String) -> Texture2D:
	if not _textures.has(name):
		_textures[name] = load(name if name.begins_with("res://") else DIRECTORY + "/" + name)
	return _textures[name]


func _draw() -> void:
	draw_texture_rect(_texture("res://generated/main/map_selection/background_%d.png" % _background_frame), Rect2(0, 0, 600, 400), false)
	if phase == 0 or source_frame == 20:
		for player in 2:
			if fighters[player] == "" or not _portrait_spec.has(fighters[player]):
				continue
			var portrait: Dictionary = _portrait_spec[fighters[player]]
			var texture := _texture(str(portrait.textures[int(_portrait_frames[player]) - 1]))
			var raster_scale := float(portrait.get("raster_scale", 1.0))
			var raster_border := float(portrait.get("raster_border", 5.0))
			var position := Vector2(float(portrait.bounds_twips[0]), float(portrait.bounds_twips[1])) / 20.0 - Vector2.ONE * raster_border
			var logical_size := Vector2(texture.get_width(), texture.get_height()) / raster_scale
			for placement: Dictionary in spec.outer_display_list:
				if placement.get("name") == "p%dbst" % (player + 1):
					var matrix: Dictionary = placement.matrix
					draw_set_transform(Vector2(float(matrix.translateX), float(matrix.translateY)) / 20.0, 0, Vector2(float(matrix.get("scaleX", 1)), float(matrix.get("scaleY", 1))))
					draw_texture_rect(texture, Rect2(position, logical_size), false)
			draw_set_transform(Vector2.ZERO)


func _draw_footer() -> void:
	_footer_layer.draw_texture_rect(_texture("res://generated/main/map_selection/footer.png"), Rect2(0, 381.5, 600, 20), false)
	for player in 2:
		var id: String = str(fighters[player] if phase == 0 else helpers[player])
		if not _footer_spec.has(id):
			continue
		var entry: Dictionary = _footer_spec[id]
		var texture := _texture(str(entry.texture))
		var count := mini(int(_text_counts[player]), str(entry.text).length())
		var width := texture.get_width() * float(count) / str(entry.text).length()
		var position := Vector2(7.5, 385.85) if player == 0 else Vector2(592.2 - width / 2.0, 385.2)
		_footer_layer.draw_texture_rect_region(texture, Rect2(position, Vector2(width, texture.get_height()) / 2.0), Rect2(0, 0, width, texture.get_height()))
