extends SceneTree


func _initialize() -> void:
	var state := AiSourceState.new()
	state.values = {"khitn": null, "known": 2}
	state.apply_write({"field": "khitn", "op": "increment", "delta": 1})
	assert(state.values.khitn is float and is_nan(state.values.khitn))
	state.apply_write({"field": "khitn", "op": "increment", "delta": 1})
	assert(is_nan(state.values.khitn))
	state.apply_write({"field": "known", "op": "increment", "delta": 1})
	assert(state.values.known == 3)
	print("SOURCE_UNDEFINED_INCREMENT_OK declared undefined becomes NaN; known increments retained")
	quit()
