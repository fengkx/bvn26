class_name AiColorState
extends RefCounted

# BODY frame 1 declares colors without initialization and initializes _csn=0.
# Wrapper setColor only replaces the array; resColor does not reset _csn.
var colors: Variant = null
var index: int = 0
var gap: int = 0
var transform: Dictionary = {}
var matrix: Array = []


func receive(operation: Dictionary) -> void:
	match str(operation.get("op", "")):
		"set_colors":
			colors = operation["colors"].duplicate(true)
		"set_color_matrix":
			matrix = operation["matrix"].duplicate()


func apply_colors() -> bool:
	if colors == null or colors.is_empty():
		return false
	assert(index >= 0 and index < colors.size(), "Unsupported Color.setTransform(undefined)")
	transform = colors[index].duplicate()
	index += 1
	if index > colors.size() - 1:
		index = 0
	return true


func reset_color() -> void:
	colors = null
	gap = 1
	transform = {"ra": 100, "rb": 0, "ga": 100, "gb": 0, "ba": 100, "bb": 0, "aa": 100, "ab": 0}
	matrix = []
