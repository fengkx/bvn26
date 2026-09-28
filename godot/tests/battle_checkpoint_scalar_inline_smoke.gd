extends SceneTree

const Checkpoint = preload("res://battle_checkpoint.gd")

func _initialize() -> void:
	_run.call_deferred()

func _run() -> void:
	var checkpoint := Checkpoint.new()
	var values: Array = [null, false, 42, 1.25, "plain", &"interned", INF, NAN]
	assert(checkpoint._encode(values) == {"ref": 0})
	assert(checkpoint.error.is_empty(), checkpoint.error)
	var entries: Array = checkpoint._records[0].entries
	assert(entries.size() == values.size())
	for index in range(5):
		assert(typeof(entries[index]) == typeof(values[index]), "Builtin scalar was not stored directly at index %d" % index)
	for index in range(5, values.size()):
		assert(entries[index] is Dictionary and entries[index].has("value"), "Special scalar bypassed its value codec at index %d" % index)
		var decoded: Variant = checkpoint._decode(entries[index])
		assert(typeof(decoded) == typeof(values[index]), "Scalar type changed at index %d" % index)
		if index == 5: assert(decoded == values[index], "StringName value changed")
		if index == 6: assert(decoded == INF, "Infinite float value changed")
		if index == 7: assert(is_nan(decoded), "NaN value changed")
	print("BATTLE_CHECKPOINT_SCALAR_INLINE_SMOKE_OK direct=nil_bool_int_finite_float_string wrapped=StringName_Inf_NaN")
	quit()
