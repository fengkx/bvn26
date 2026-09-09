extends SceneTree


func _initialize() -> void:
	var decoder = preload("res://tests/source_trace_number.gd")
	assert(decoder.decode("f:1:-2:89478485:22369621") == 1.0 / 3.0)
	assert(decoder.decode("f:1:2:89478485:22369621") == 80.0 / 15.0)
	assert(decoder.decode("f:1:-4:107374182:26843546") == 0.1)
	assert(decoder.decode("f:-1:-2:89478485:22369621") == -1.0 / 3.0)
	# Converting the exact integer avoids the engine's large decimal-literal rounding.
	assert(decoder.decode("f:1:52:134217727:67108863") == float(9007199254740991))
	assert(decoder.decode("f:1:-100:67108864:0") == pow(2.0, -100))
	assert(1.0 / decoder.decode("f:-1:0:0:0") == -INF)
	assert(decoder.decode("undefined") == null and decoder.decode("false") == false)
	print("SOURCE_NUMBER_SMOKE_OK")
	quit()
