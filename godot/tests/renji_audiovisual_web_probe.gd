extends Node2D

const CASES := [
	{"label": "瞬步", "source_frame": 21},
	{"label": "砍1", "source_frame": 177},
	{"label": "必杀", "source_frame": 516},
	{"label": "上必杀", "source_frame": 606},
	{"label": "超必杀", "source_frame": 689},
	{"label": "超必杀", "source_frame": 832}
]

var _index := 0
var _preview: TimelinePreview


func _ready() -> void:
	_preview = TimelinePreview.new()
	_preview.fighter_directory = "res://generated/fighters/renji"
	_preview.autoplay = false
	_preview.play_timeline_sounds = false
	_preview.position = Vector2(300, 300)
	add_child(_preview)
	await get_tree().process_frame
	_show_case()


func _unhandled_input(event: InputEvent) -> void:
	if not event is InputEventKey or not event.pressed or event.echo:
		return
	if event.keycode == KEY_D:
		_index = (_index + 1) % CASES.size()
		_show_case()
	elif event.keycode == KEY_A:
		_index = (_index - 1 + CASES.size()) % CASES.size()
		_show_case()


func _show_case() -> void:
	var item: Dictionary = CASES[_index]
	_preview.play_source_frame(int(item["source_frame"]))
	print("RENJI_WEB_STAGE_READY ", JSON.stringify({
		"index": _index,
		"label": item["label"],
		"source_frame": item["source_frame"],
		"sound_probe": "res://tests/renji_audiovisual_probe.gd"
	}))
