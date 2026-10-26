extends SceneTree

const Callbacks = preload("res://tests/fixtures/missing_form_fields.gd")

class Adapter extends RefCounted:
	var destination := ""

	func goto_label(label: String, playing: bool) -> void:
		assert(playing)
		destination = label

	func controller_alive() -> bool:
		return true


func _initialize() -> void:
	var source := AiSourceState.new()
	source.configure({"undefined_declarations": ["khitn", "nn"],
		"frame_writes": {"128": Callbacks.KHIT_WRITES}})
	var callbacks := Callbacks.new(source.values)
	var adapter := Adapter.new()
	callbacks.adapter = adapter
	assert(source.read_field("khitn") == null)
	source.apply_frame(128)
	assert(is_nan(source.read_field("khitn")))
	assert(callbacks.source_less2(source.read_field("khitn"), 3) == null)
	callbacks.sasuke_callback()
	assert(adapter.destination == "")
	source.values.khitn = 0
	callbacks.sasuke_callback()
	assert(adapter.destination == "跳砍")
	source.values.merge({"y": 0, "root_paused": false, "touch": true})
	adapter.destination = ""
	assert(source.read_field("nn") == null)
	callbacks.yihu_callback()
	assert(adapter.destination == "跳招2")
	assert(source.read_field("nn") == null)
	assert(source.read_field("y") == 10)
	source.values.nn = 0
	adapter.destination = ""
	callbacks.yihu_callback()
	assert(adapter.destination == "")
	assert(source.read_field("y") == 20)
	print("MISSING_FORM_FIELDS_REFERENCE_OK sources=2 branches=4")
	quit()
