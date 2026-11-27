extends Control

signal quote_requested
signal selected(action: String)

const DIRECTORY := "res://generated/main/arcade/"
static var data: Dictionary = JSON.parse_string(FileAccess.get_file_as_string(DIRECTORY + "campaign.json"))

const KEY_CAPS := {
	"w": Vector2i(138, 287), "s": Vector2i(138, 324), "a": Vector2i(100, 324),
	"d": Vector2i(176, 324), "u": Vector2i(393, 290), "i": Vector2i(437, 290),
	"o": Vector2i(482, 290), "j": Vector2i(393, 332), "k": Vector2i(437, 332),
	"l": Vector2i(482, 332),
}

var session: GameSession
var stage := 0
var player := ""
var helper := ""
var screen := ""
var frame := 0
var _length := 0
var _pages: Array
var _changes: Dictionary
var _sounds: Dictionary
var _page_cache: Dictionary = {}
var _canvas := Image.create_empty(600, 400, false, Image.FORMAT_RGB8)
var _texture: ImageTexture
var _quote: Label
var _audio: Array[AudioStreamPlayer] = []


func _ready() -> void:
	size = Vector2(600, 400)
	mouse_filter = Control.MOUSE_FILTER_STOP
	_texture = ImageTexture.create_from_image(_canvas)
	_quote = Label.new()
	_quote.position = Vector2(55, 244)
	_quote.size = Vector2(356, 62)
	_quote.add_theme_font_size_override("font_size", 12)
	_quote.autowrap_mode = TextServer.AUTOWRAP_ARBITRARY
	_quote.mouse_filter = Control.MOUSE_FILTER_IGNORE
	add_child(_quote)
	hide()


func reset_run() -> void:
	stage = 0
	player = ""
	helper = ""
	close()


func encounter() -> Dictionary:
	return data.encounters[data.routes[player][stage]]


func open(label: String, winner_id := "") -> void:
	close()
	screen = label
	var clip := "win-" + winner_id if label == "win" else label
	var animation: Dictionary = JSON.parse_string(FileAccess.get_file_as_string(DIRECTORY + clip + ".json"))
	_pages = animation.pages
	_changes = animation.changes
	var spec: Dictionary = data.screens.get(label, {})
	_length = int(spec.get("length", 24))
	_sounds = spec.get("sounds", {})
	_quote.text = ""
	show()
	_display_frame(1)


func set_quote(value: String) -> void:
	if not value.is_empty() and not _quote.has_theme_font_override("font"):
		_quote.add_theme_font_override("font", OnlineUserTextFont.get_cjk_fallback())
	_quote.text = value


func close() -> void:
	hide()
	screen = ""
	frame = 0
	_page_cache.clear()
	for sound in _audio:
		sound.stop()
		sound.queue_free()
	_audio.clear()


func _display_frame(value: int) -> void:
	frame = value
	var key := str(frame)
	var patches: Array = _changes.get(key, [])
	for rect: Array in patches:
		var index := int(rect[0])
		if not _page_cache.has(index):
			_page_cache.clear()
			var path := DIRECTORY + str(_pages[index])
			var image := Image.new()
			if image.load_webp_from_buffer(FileAccess.get_file_as_bytes(path)) != OK:
				push_error("Unable to decode arcade page: " + path)
				continue
			image.convert(Image.FORMAT_RGB8)
			_page_cache[index] = image
		_canvas.blit_rect(_page_cache[index], Rect2i(int(rect[1]), int(rect[2]), int(rect[3]), int(rect[4])), Vector2i(int(rect[5]), int(rect[6])))
	if not patches.is_empty():
		_texture.update(_canvas)
		queue_redraw()
	if value == _length:
		_page_cache.clear()
	if screen == "win" and frame == 20:
		quote_requested.emit()
	_quote.visible = screen == "win" and frame >= 20
	for cue: Array in _sounds.get(key, []):
		var audio := AudioStreamPlayer.new()
		var stream: AudioStreamMP3 = load(DIRECTORY + str(cue[0]) + ".mp3")
		if stream.loop != bool(cue[1]):
			stream = stream.duplicate()
			stream.loop = bool(cue[1])
		audio.stream = stream
		add_child(audio)
		_audio.append(audio)
		audio.play()


func tick() -> void:
	if frame < _length:
		_display_frame(frame + 1)
	if screen == "win" and frame == 3:
		stage += 1
		if stage == data.routes[player].size():
			selected.emit("ending")
	elif screen == "tutorial" and frame == _length:
		selected.emit("select")
	elif screen == "gameover" and frame == _length:
		selected.emit("menu")


func key_down(event: InputEventKey, session: GameSession) -> bool:
	var code := event.keycode
	var confirm := code == session.flash_to_key(session.codes.j) or code == session.flash_to_key(session.codes.N1)
	if screen == "tutorial" and confirm and frame >= 15 and frame < 1249:
		_display_frame(1249)
	elif screen == "win" and frame == 24 and (confirm or code in [KEY_ENTER, KEY_SPACE]):
		selected.emit("next")
	elif screen == "continue" and code in [KEY_Y, KEY_N]:
		selected.emit("select" if code == KEY_Y else "gameover")
	elif screen == "ending" and frame == _length and (confirm or code == KEY_ENTER):
		selected.emit("menu")
	else:
		return false
	return true


func _gui_input(event: InputEvent) -> void:
	if not event is InputEventMouseButton or event.button_index != MOUSE_BUTTON_LEFT or event.pressed:
		return
	var point: Vector2 = event.position
	if screen == "continue":
		if Rect2(117, 215, 151, 65).has_point(point):
			selected.emit("select")
		elif Rect2(355, 215, 125, 65).has_point(point):
			selected.emit("gameover")
	elif screen == "win" and frame == 24:
		if Rect2(66, 135, 258, 58).has_point(point):
			selected.emit("next")
		elif Rect2(27, 323, 63, 33).has_point(point):
			selected.emit("menu")
	elif screen == "ending" and frame == _length and Rect2(460, 343, 115, 51).has_point(point):
		selected.emit("menu")


func _draw() -> void:
	if _texture != null:
		draw_texture(_texture, Vector2.ZERO)
	if screen != "tutorial":
		return
	for slot: String in KEY_CAPS:
		if session.codes[slot] == GameSession.DEFAULT_CODES[slot]:
			continue
		var corner: Vector2i = KEY_CAPS[slot]
		var area := Rect2(corner, Vector2(19, 19))
		# Sample the empty edge of this key so its highlight follows the movie.
		draw_texture_rect_region(_texture, area, Rect2(corner + Vector2i(19, 0), Vector2(1, 19)))
		var name := session.show_key_name(int(session.codes[slot]))
		var font_size := 14 if name.length() <= 2 else 9
		var ink := _canvas.get_pixelv(corner + Vector2i(5, 8))
		ink = Color(minf(ink.r, 0.2), minf(ink.g, 0.2), minf(ink.b, 0.2))
		draw_string(ThemeDB.fallback_font, Vector2(corner) + Vector2(-4, 15), name,
			HORIZONTAL_ALIGNMENT_CENTER, 27, font_size, ink)
