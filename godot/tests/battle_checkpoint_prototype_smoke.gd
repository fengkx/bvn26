extends SceneTree

const Checkpoint = preload("res://battle_checkpoint.gd")

func _initialize() -> void:
	_run.call_deferred()

func _run() -> void:
	var owner := Node.new()
	root.add_child(owner)
	var checkpoint := Checkpoint.new()
	checkpoint.configure(owner)

	var plain_dictionary: Dictionary = {}
	var string_to_int: Dictionary[String, int] = {}
	var int_to_string: Dictionary[int, String] = {}
	var string_to_variant: Dictionary[String, Variant] = {}
	var integers: Array[int] = []
	var strings: Array[String] = []

	var plain_key := checkpoint._empty_prototype_key(plain_dictionary)
	var string_to_int_key := checkpoint._empty_prototype_key(string_to_int)
	if not _check(string_to_int_key == checkpoint._empty_prototype_key(string_to_int), "typed dictionary cache hit"):
		return
	var int_to_string_key := checkpoint._empty_prototype_key(int_to_string)
	var string_to_variant_key := checkpoint._empty_prototype_key(string_to_variant)
	if not _check(plain_key != string_to_int_key, "typed and untyped dictionaries stay distinct"):
		return
	if not _check(string_to_int_key != int_to_string_key, "typed key/value direction stays distinct"):
		return
	if not _check(string_to_int_key != string_to_variant_key, "typed value metadata stays distinct"):
		return

	var string_to_int_prototype: Dictionary = checkpoint._constants[string_to_int_key]
	if not _check(string_to_int_prototype.is_typed_key() and string_to_int_prototype.is_typed_value(), "typed key/int value metadata preserved"):
		return
	if not _check(string_to_int_prototype.get_typed_key_builtin() == TYPE_STRING, "string key metadata preserved"):
		return
	if not _check(string_to_int_prototype.get_typed_value_builtin() == TYPE_INT, "int value metadata preserved"):
		return
	var int_to_string_prototype: Dictionary = checkpoint._constants[int_to_string_key]
	if not _check(int_to_string_prototype.get_typed_key_builtin() == TYPE_INT, "int key metadata preserved"):
		return
	if not _check(int_to_string_prototype.get_typed_value_builtin() == TYPE_STRING, "string value metadata preserved"):
		return
	var string_to_variant_prototype: Dictionary = checkpoint._constants[string_to_variant_key]
	if not _check(not string_to_variant_prototype.is_typed_value(), "Variant value remains dynamically typed"):
		return
	if not _check(string_to_variant_prototype.is_typed_key(), "string key metadata remains typed"):
		return
	if not _check(var_to_bytes(string_to_variant_prototype) == var_to_bytes(string_to_variant), "Variant value prototype bytes preserved"):
		return

	var integers_key := checkpoint._empty_prototype_key(integers)
	var strings_key := checkpoint._empty_prototype_key(strings)
	if not _check(integers_key != strings_key, "typed array element types stay distinct"):
		return
	var integers_prototype: Array = checkpoint._constants[integers_key]
	var strings_prototype: Array = checkpoint._constants[strings_key]
	if not _check(integers_prototype.get_typed_builtin() == TYPE_INT, "typed int array metadata preserved"):
		return
	if not _check(strings_prototype.get_typed_builtin() == TYPE_STRING, "typed string array metadata preserved"):
		return

	var mutable_array := [1]
	var mutable_array_key := checkpoint._constant(mutable_array)
	mutable_array.clear()
	if not _check(checkpoint._constant(mutable_array) == mutable_array_key, "cleared constant array keeps identity key"):
		return
	var mutable_dictionary := {"value": 1}
	var mutable_dictionary_key := checkpoint._constant(mutable_dictionary)
	mutable_dictionary.clear()
	if not _check(checkpoint._constant(mutable_dictionary) == mutable_dictionary_key, "cleared constant dictionary keeps identity key"):
		return

	checkpoint.close()
	owner.free()
	await process_frame
	print("BATTLE_CHECKPOINT_PROTOTYPE_SMOKE_OK typed_dictionary_and_array_signatures=true")
	quit()

func _check(condition: bool, description: String) -> bool:
	if condition: return true
	push_error("BATTLE_CHECKPOINT_PROTOTYPE_SMOKE_FAILED " + description)
	quit(1)
	return false
