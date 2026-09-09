extends RefCounted

var failure: String = ""
var consumed: Array = []
var _records: Array = []
var _cursor := 0
var _recorded := false


func use_recorded_tape(records: Array) -> bool:
	_records = records.duplicate(true)
	_cursor = 0
	_recorded = true
	failure = ""
	consumed.clear()
	var previous := -1
	for index in records.size():
		var record: Variant = records[index]
		if not record is Dictionary or not record.get("site") is String:
			failure = "Malformed clock record at %d" % (index + 1)
			return false
		var value: Variant = record.get("value")
		if not (value is int or value is float) or not is_finite(float(value)):
			failure = "Invalid clock value at %d" % (index + 1)
			return false
		if float(value) != floor(float(value)) or int(value) < 0 or int(value) < previous:
			failure = "Non-integral or backwards clock at %d" % (index + 1)
			return false
		previous = int(value)
	return true


func read(site: String) -> Variant:
	if failure != "":
		return null
	if not _recorded:
		return Time.get_ticks_msec()
	if _cursor >= _records.size():
		failure = "Clock tape exhausted before " + site
		return null
	var record: Dictionary = _records[_cursor]
	if record["site"] != site:
		failure = "Clock consumer mismatch at %d: expected %s, got %s" % [_cursor + 1, record["site"], site]
		return null
	_cursor += 1
	consumed.append(record.duplicate())
	return int(record["value"])


func replay_complete() -> bool:
	return _recorded and failure == "" and _cursor == _records.size()
