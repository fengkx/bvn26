extends Control

const DIRECTORY := "res://ui/battle_loading/"
const WAIT_FRAME := 172
const SKIP_KEY_FRAME := 27
var timeline: Dictionary = JSON.parse_string(FileAccess.get_file_as_string(DIRECTORY + "loading.json"))
var frame := 1
var progress := 0.0
var meter_frame := 0
var loaded := false
var elapsed := 0.0
var labels: Array = []
var textures := {}
var foreground_texture: Texture2D
var failed := false
var choice := ""
var session: GameSession
var cue := AudioStreamPlayer.new()


func _ready() -> void:
	set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	z_as_relative = false
	z_index = 4000
	mouse_filter = Control.MOUSE_FILTER_STOP
	cue.stream = load(DIRECTORY + "entrance.mp3")
	add_child(cue)
	var row := HBoxContainer.new()
	row.name = "Actions"
	row.position = Vector2(220, 180)
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
		if event.pressed and not event.echo:
			var code: int = event.keycode
			var confirm := code == session.flash_to_key(session.codes.j) or code == session.flash_to_key(session.codes.N1)
			if failed:
				if confirm or code == KEY_ENTER: choice = "retry"
				if code in [KEY_K, KEY_ESCAPE]: choice = "back"
			elif confirm and meter_frame == timeline.meter.size() - 1 and frame >= SKIP_KEY_FRAME and frame < timeline.skip:
				frame = int(timeline.skip)
				cue.stop()
				queue_redraw()
		get_viewport().set_input_as_handled()


func _process(delta: float) -> void:
	elapsed += delta * float(timeline.fps)
	while elapsed >= 1.0 and frame < timeline.frames.size():
		elapsed -= 1.0
		if loaded:
			queue_redraw()
			meter_frame = mini(meter_frame + 1, timeline.meter.size() - 1)
		if frame == WAIT_FRAME and meter_frame < timeline.meter.size() - 1:
			continue
		frame += 1
		if frame == 4: cue.play()
		queue_redraw()


func prepare(ids: Array, player_labels: Array) -> bool:
	labels = player_labels
	var bridge = JavaScriptBridge.get_interface("bvnBattlePacks") if OS.has_feature("web") else null
	var needed: Array = []
	for id in ids:
		if bridge != null and bridge.needed(id) and id not in needed:
			needed.append(id)
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
			$Actions.theme = Theme.new()
			$Actions.theme.default_font = OnlineUserTextFont.with_cjk_fallback(load("res://generated/main/title_menu/menu-font.ttf"))
			$Actions.show()
			while choice.is_empty(): await get_tree().process_frame
			if choice == "back": return false
			choice = ""
			failed = false
			$Actions.hide()
	progress = 1.0
	loaded = true
	while frame < timeline.frames.size():
		await get_tree().process_frame
	return true


func _texture(id: String) -> Texture2D:
	if not textures.has(id):
		textures[id] = load(DIRECTORY + id + ".png")
	return textures[id]


func _layer(image: Array) -> void:
	if not image.is_empty():
		draw_texture(_texture(image[0]), Vector2(image[1], image[2]))


func _banner(index: int, position_data: Array) -> void:
	if position_data.is_empty() or index >= labels.size(): return
	# An unknown Flash frame label leaves the stopped portrait at frame one.
	var image: Array = timeline.portraits.get(labels[index], timeline.portraits["一护"])
	var origin := Vector2(position_data[0], position_data[1]) / 20.0
	draw_set_transform(origin, 0, Vector2(-1 if position_data[2] else 1, 1))
	draw_texture(_texture(image[0]), Vector2(image[1] - 10, image[2] - 6))
	draw_set_transform(Vector2.ZERO)


func _draw() -> void:
	var layers: Dictionary = timeline.frames[frame - 1]
	_layer(layers.background)
	_banner(1, layers.p2)
	_banner(0, layers.p1)
	if loaded:
		_layer(timeline.meter[meter_frame])
	else:
		_layer(timeline.empty_meter)
		var fill: Array = timeline.fill
		var texture := _texture(fill[0])
		var size_px := texture.get_size() * Vector2(roundf(progress * 100.0) / 100.0, 1.0)
		draw_texture_rect(texture, Rect2(Vector2(fill[1], fill[2]), size_px), false)
	# The large VS and shutter frames play once. Keep only the current one resident.
	var front: Array = layers.front
	if not front.is_empty():
		var path := DIRECTORY + str(front[0]) + ".png"
		if foreground_texture == null or foreground_texture.resource_path != path:
			foreground_texture = load(path)
		draw_texture(foreground_texture, Vector2(front[1], front[2]))
