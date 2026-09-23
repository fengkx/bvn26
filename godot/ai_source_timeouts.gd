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
	_pending[id] = {"callback": callback, "timer": timer, "delay_ms": delay_ms}
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


func save_state(identify: Callable) -> Dictionary:
	if not recorded:
		return {"error": "Live timeout deadlines require an external delivery schedule"}
	var queue := []
	var delays := {}
	for id in _pending:
		queue.append({"order": id, "operation": _pending[id].callback})
		delays[str(id)] = _pending[id].delay_ms
	var operations := preload("res://pending_operation_state.gd").save(queue, identify)
	if operations.has("error"):
		return operations
	return {"version": 1, "next_id": _next_id, "operations": operations, "delays": delays}


func load_state(snapshot: Variant, resolve: Callable) -> String:
	if not recorded:
		return "Timeout restoration requires externally delivered callbacks"
	if not snapshot is Dictionary or snapshot.get("version") != 1 or not snapshot.get("next_id") is int or snapshot.next_id < 0:
		return "Invalid timeout state"
	if not snapshot.get("delays") is Dictionary:
		return "Missing timeout delays"
	var prepared := preload("res://pending_operation_state.gd").prepare(snapshot.get("operations"), resolve)
	if prepared.has("error"):
		return prepared.error
	if prepared.queue.size() != snapshot.delays.size():
		return "Timeout delays do not match registrations"
	var pending := {}
	for entry in prepared.queue:
		var delay: Variant = snapshot.delays.get(str(entry.order))
		if entry.order <= 0 or entry.order > snapshot.next_id or not delay is int or delay <= 0:
			return "Invalid timeout registration/delay"
		pending[entry.order] = {"callback": entry.operation, "timer": null, "delay_ms": delay}
	clear()
	_pending = pending
	_next_id = snapshot.next_id
	return ""


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
