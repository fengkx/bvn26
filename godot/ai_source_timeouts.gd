class_name AiSourceTimeouts
extends Node

signal registered(id: int, delay_ms: int)
signal fired(id: int)

var recorded: bool = false
var _next_id: int = 0
var _pending: Dictionary = {}


func _ready() -> void:
	process_mode = Node.PROCESS_MODE_ALWAYS


func schedule(callback: Callable, delay_ms: int) -> int:
	assert(callback.is_valid() and delay_ms > 0)
	_next_id += 1
	var id := _next_id
	var timer: Timer = null
	if not recorded:
		timer = Timer.new()
		timer.one_shot = true
		timer.process_mode = Node.PROCESS_MODE_ALWAYS
		timer.ignore_time_scale = true
		add_child(timer)
		timer.timeout.connect(_finish.bind(id))
	_pending[id] = {"callback": callback, "timer": timer}
	registered.emit(id, delay_ms)
	if timer != null and _pending.has(id):
		timer.start(float(delay_ms) / 1000.0)
	return id


func fire_recorded(id: int) -> bool:
	assert(recorded)
	return _finish(id)


func cancel(id: int) -> bool:
	if not _pending.has(id):
		return false
	var timer: Timer = _pending[id]["timer"]
	_pending.erase(id)
	if timer != null:
		timer.stop()
		timer.queue_free()
	return true


func clear() -> void:
	for id: int in _pending.keys():
		cancel(id)


func pending_count() -> int:
	return _pending.size()


func _finish(id: int) -> bool:
	if not _pending.has(id):
		return false
	var callback: Callable = _pending[id]["callback"]
	# Remove before executing: a callback may register another timeout or clear
	# the match. It must not be confused with the registration being fired.
	cancel(id)
	if not callback.is_valid():
		return false
	fired.emit(id)
	if not callback.is_valid():
		return false
	callback.call()
	return true
