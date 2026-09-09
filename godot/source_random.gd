class_name SourceRandom
extends RefCounted

signal diverged(message: String)

var failure: String = ""
var consumed: Array[Dictionary] = []
var _tape: Array = []
var _cursor: int = 0
var _replaying: bool = false
var _rng := RandomNumberGenerator.new()


func use_recorded_tape(records: Array) -> bool:
	_tape = records.duplicate(true)
	_cursor = 0
	_replaying = true
	failure = ""
	consumed.clear()
	for i in _tape.size():
		var record: Variant = _tape[i]
		if not record is Dictionary or not record.has("site") or not record.has("value"):
			_fail("Malformed random record at index %d" % (i + 1))
			return false
		if not record["site"] is String or not (record["value"] is float or record["value"] is int):
			_fail("Invalid random record types at index %d" % (i + 1))
			return false
		if int(record.get("index", i + 1)) != i + 1:
			_fail("Non-contiguous random index at %d" % (i + 1))
			return false
		var v := float(record["value"])
		if is_nan(v) or v < 0.0 or v >= 1.0:
			_fail("Random value outside [0, 1) at index %d" % (i + 1))
			return false
	return true


func use_live_random() -> void:
	_replaying = false
	_tape.clear()
	_cursor = 0
	failure = ""
	consumed.clear()
	_rng.randomize()


func next_value(site: String) -> float:
	if failure != "":
		return NAN
	var v: float
	if _replaying:
		if _cursor >= _tape.size():
			return _fail("Random tape exhausted before " + site)
		var record: Dictionary = _tape[_cursor]
		if str(record["site"]) != site:
			return _fail("Random consumer mismatch at %d: expected %s, got %s" % [
				_cursor + 1, record["site"], site
			])
		v = float(record["value"])
	else:
		v = _rng.randf()
		# Math.random excludes 1.0; Godot's randf can include its upper bound.
		while v >= 1.0:
			v = _rng.randf()
	_cursor += 1
	consumed.append({"index": _cursor, "site": site, "value": v})
	return v


func replay_complete() -> bool:
	return _replaying and failure == "" and _cursor == _tape.size()


func _fail(message: String) -> float:
	failure = message
	diverged.emit(message)
	return NAN
