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
var _explicit := false
var _explicit_ms := 0


func use_explicit_time(time_ms: int) -> bool:
	if time_ms < 0:
		return false
	_recorded = false
	_explicit = true
	_explicit_ms = time_ms
	_records.clear()
	_cursor = 0
	absolute_index = 0
	live_retained_dropped = 0
	failure = ""
	consumed.clear()
	return true


func set_explicit_time(time_ms: int) -> bool:
	if not _explicit or time_ms < _explicit_ms:
		return false
	_explicit_ms = time_ms
	return true


func save_state() -> Dictionary:
	return {"version": 1, "recorded": _recorded, "explicit": _explicit,
		"time_ms": _explicit_ms, "records": _records.duplicate(true), "cursor": _cursor,
		"absolute_index": absolute_index, "dropped": live_retained_dropped,
		"failure": failure, "consumed": consumed.duplicate(true)}


func validate_state(state: Variant) -> String:
	var value_problem := preload("res://simulation_state.gd").validate_value(state)
	if not value_problem.is_empty():
		return value_problem
	if not state is Dictionary or state.get("version") != 1:
		return "Unsupported clock state"
	for key in ["recorded", "explicit"]:
		if not state.get(key) is bool:
			return "Invalid clock mode"
	if state.recorded == state.explicit:
		return "Restoring a live or ambiguous clock is not deterministic"
	for key in ["time_ms", "cursor", "absolute_index", "dropped"]:
		if not state.get(key) is int or state[key] < 0:
			return "Invalid clock field: " + key
	if not state.get("records") is Array or not state.get("consumed") is Array or not state.get("failure") is String:
		return "Invalid clock records/failure"
	if state.cursor > state.records.size() or state.absolute_index < state.cursor:
		return "Clock cursor outside tape"
	for records in [state.records, state.consumed]:
		var previous := -1
		for record in records:
			if not record is Dictionary or not record.get("site") is String:
				return "Invalid clock record"
			var value: Variant = record.get("value")
			if not (value is float or value is int) or not is_finite(float(value)) or value != floor(float(value)) or value < previous or value < 0:
				return "Invalid clock value"
			previous = int(value)
	return ""


func load_state(state: Variant) -> String:
	var problem := validate_state(state)
	if not problem.is_empty():
		return problem
	_recorded = state.recorded
	_explicit = state.explicit
	_explicit_ms = state.time_ms
	_records = state.records.duplicate(true)
	_cursor = state.cursor
	absolute_index = state.absolute_index
	live_retained_dropped = state.dropped
	failure = state.failure
	consumed = state.consumed.duplicate(true)
	return ""


func use_recorded_tape(records: Array, start_index: int = 0) -> bool:
	_records = records.duplicate(true)
	_cursor = 0
	absolute_index = start_index
	live_retained_dropped = 0
	_recorded = true
	_explicit = false
	failure = ""
	consumed.clear()
	var previous := -1
	for index in records.size():
		var record: Variant = records[index]
		if not record is Dictionary or not record.get("site") is String:
			failure = "Malformed clock record at %d" % (index + 1)
			return false
		if int(record.get("index", start_index + index + 1)) != start_index + index + 1:
			failure = "Non-contiguous clock index at %d" % (index + 1)
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
		var live_value := _explicit_ms if _explicit else Time.get_ticks_msec()
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
	return {"mode": "recorded" if _recorded else ("explicit" if _explicit else "live"),
		"absoluteIndex": absolute_index, "replaying": _recorded,
		"retainedDropped": live_retained_dropped,
		"retainedPolicy": "first_4096" if not _recorded else "complete_replay_tape",
		"failure": failure}


func replay_complete() -> bool:
	return _recorded and failure == "" and _cursor == _records.size()
