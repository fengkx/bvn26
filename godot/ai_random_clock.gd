class_name AiRandomClock
extends Node

signal sampled(sequence: int, time_ms: int)

var sample_count: int = 0
var difficulty: int = 5
var registered_ms: int = -1
var _state: AiSourceState
var _random: SourceRandom
var _spec: Dictionary
var _timer: Timer
var _recorded: bool = false


func _ready() -> void:
	process_mode = Node.PROCESS_MODE_ALWAYS
	_timer = Timer.new()
	_timer.process_mode = Node.PROCESS_MODE_ALWAYS
	_timer.ignore_time_scale = true
	_timer.timeout.connect(_on_timeout)
	add_child(_timer)


func initialize(state: AiSourceState, random: SourceRandom, level: int, recorded: bool = false) -> void:
	assert(_timer != null)
	assert(level >= 1 and level <= 5)
	# Repeated source setInterval calls are distinct registrations, not a
	# restart of one timer. The match adapter must explicitly cancel the old
	# registration or create another clock when that source path is exercised.
	assert(_state == null, "AI interval already registered")
	_state = state
	_random = random
	_spec = state.spec["random_refresh"]
	difficulty = level
	_recorded = recorded
	sample_count = 0
	registered_ms = Time.get_ticks_msec()
	# initCtrl registers setInterval without an immediate randAI call. Do not
	# reset existing random fields when the same receiver is initialized again.
	if not recorded:
		_timer.start(float(_spec["interval_ms"]) / 1000.0)


func cancel() -> void:
	if _timer != null:
		_timer.stop()
	_state = null
	_random = null
	registered_ms = -1


func fire_recorded(time_ms: int) -> bool:
	assert(_recorded)
	return _refresh(time_ms)


func _on_timeout() -> void:
	_refresh(Time.get_ticks_msec())


func _refresh(time_ms: int) -> bool:
	if _state == null or _random == null:
		return false
	var multiplier := float(_spec["difficulty_multiplier"]) * difficulty
	for assignment: Dictionary in _spec["assignments"]:
		var value := _random.next_value(assignment["site"])
		if is_nan(value):
			_timer.stop()
			return false
		_state.values[assignment["field"]] = value * multiplier
	sample_count += 1
	sampled.emit(sample_count, time_ms)
	return true
