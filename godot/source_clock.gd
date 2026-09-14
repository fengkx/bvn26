extends RefCounted

signal value_consumed(record: Dictionary)

const LIVE_CONSUMED_LIMIT := 4096

var failure: String = ""
var consumed: Array = []
var _records: Array = []
var _cursor := 0
var _recorded := false
var absolute_index := 0
var live_retained_dropped := 0


func use_recorded_tape(records: Array) -> bool:
	_records = records.duplicate(true)
	_cursor = 0
	absolute_index = 0
	live_retained_dropped = 0
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
		var live_value := Time.get_ticks_msec()
		absolute_index += 1
		var live_record := {"index": absolute_index, "site": site, "value": live_value}
		if consumed.size() < LIVE_CONSUMED_LIMIT:
			consumed.append(live_record)
		else:
			live_retained_dropped += 1
		value_consumed.emit(live_record)
		return live_value
	if _cursor >= _records.size():
		failure = "Clock tape exhausted before " + site
		return null
	var record: Dictionary = _records[_cursor]
	if record["site"] != site:
		failure = "Clock consumer mismatch at %d: expected %s, got %s" % [_cursor + 1, record["site"], site]
		return null
	_cursor += 1
	absolute_index += 1
	var consumed_record := record.duplicate()
	consumed.append(consumed_record)
	var observed_record := consumed_record.duplicate()
	observed_record["diagnosticIndex"] = absolute_index
	value_consumed.emit(observed_record)
	return int(record["value"])


func diagnostic_state() -> Dictionary:
	return {"mode": "recorded" if _recorded else "live",
		"absoluteIndex": absolute_index, "replaying": _recorded,
		"retainedDropped": live_retained_dropped,
		"retainedPolicy": "first_4096" if not _recorded else "complete_replay_tape",
		"failure": failure}


func replay_complete() -> bool:
	return _recorded and failure == "" and _cursor == _records.size()
