class_name ConfigMenu
extends Control

signal key_settings_requested
signal menu_requested

var session: GameSession
var spec: Dictionary = JSON.parse_string(FileAccess.get_file_as_string("res://generated/main/config/config.json"))
var selected := 1
var levels: Dictionary = {}
var _labels: Array[Label] = []
var _sounds: Array[AudioStreamPlayer] = []
const NAMES := ["KEY CONFIG", "COM LEVEL", "QUALITY", "TIME", "LIFE", "RETURN TO MENU"]
const VALUES := {
	"difficulty": ["VERY EASY", "EASY", "NORMAL", "HARD", "VERY HARD"],
	"quality": ["HIGH", "MEDIUM", "LOW"],
	"time": ["30", "60", "90", "∞"],
	"health": ["100%", "200%", "300%", "400%", "500%"],
}

func _ready() -> void:
	set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	var background := ColorRect.new()
	background.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	background.color = Color(0.035, 0.043, 0.063)
	add_child(background)
	var title := Label.new()
	title.text = "CONFIG"
	title.position = Vector2(40, 20)
	title.add_theme_font_size_override("font_size", 28)
	add_child(title)
	for index in 6:
		var label := Label.new()
		label.position = Vector2(65, 82 + index * 43)
		label.size.x = 490
		label.add_theme_font_size_override("font_size", 18)
		add_child(label)
		_labels.append(label)
	var hint := Label.new()
	hint.text = "W / S: Select     A / D: Change     J: Confirm     K: Save and return"
	hint.position = Vector2(40, 365)
	hint.add_theme_font_size_override("font_size", 12)
	add_child(hint)
	for index in [1, 2]:
		var sound := AudioStreamPlayer.new()
		sound.stream = load("res://generated/main/title_menu/keysound%d.mp3" % index)
		add_child(sound)
		_sounds.append(sound)

func reset() -> void:
	selected = 1
	levels = {"difficulty": 6 - session.ai_level, "quality": ["HIGH", "MEDIUM", "LOW"].find(session.render_quality) + 1,
		"time": [30, 60, 90, 100].find(session.maxtime) + 1, "health": int(session.maxhp / 1000)}
	_refresh()

func tick() -> void:
	# These writes belong to source enterFrame, after the keyDown changes cl.
	for option: Dictionary in spec.rows:
		for write: Dictionary in option.writes:
			if int(write.frame) == int(levels[option.id]):
				session.write_option(str(write.field), write.value)
	_refresh()

func key_down(held: Dictionary) -> void:
	# The selector (depth 33) precedes the option callbacks. Independent ifs
	# preserve simultaneous-key behavior; bounds intentionally retain cl=0/N+1.
	if held.get("up", false):
		selected = 6 if selected == 1 else selected - 1
		_sound(1)
	if held.get("down", false):
		selected = 1 if selected == 6 else selected + 1
		_sound(1)
	if held.get("confirm", false):
		if selected == 1:
			_sound(2)
			key_settings_requested.emit()
			return
		if selected == 6:
			session.save_store()
			_sound(2)
			menu_requested.emit()
			return
	if held.get("back", false):
		session.save_store()
		menu_requested.emit()
		return
	for option: Dictionary in spec.rows:
		if int(option.row) != selected:
			continue
		if held.get("left", false):
			if option.id != "quality" or int(levels[option.id]) >= int(option.left_guard):
				_sound(1)
			if int(levels[option.id]) >= int(option.left_guard):
				levels[option.id] -= 1
		if held.get("right", false):
			if option.id != "quality" or int(levels[option.id]) <= int(option.right_guard):
				_sound(1)
			if int(levels[option.id]) <= int(option.right_guard):
				levels[option.id] += 1
	_refresh()

func _sound(index: int) -> void:
	if _sounds.size() >= index:
		_sounds[index - 1].play()

func _refresh() -> void:
	for index in _labels.size():
		var value := ""
		for option: Dictionary in spec.rows:
			if int(option.row) == index + 1 and levels.has(option.id):
				var choices: Array = VALUES[option.id]
				value = "     " + str(choices[clampi(int(levels[option.id]) - 1, 0, choices.size() - 1)])
		_labels[index].text = ("> " if selected == index + 1 else "  ") + NAMES[index] + value
		_labels[index].modulate = Color(1, 0.77, 0.22) if selected == index + 1 else Color.WHITE
