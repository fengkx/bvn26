extends RefCounted

var instances := AiControllerInstances.new()
var _hooks: Array = []
var _ordered_paths: Array = []
var _body: RefCounted
var enabled: Callable


class BodyCallback extends RefCounted:
	var body: RefCounted
	var method: String
	var args: Array
	var enabled: Callable

	func enter_frame() -> void:
		if enabled.is_valid() and not enabled.call():
			return
		body.callv(method, args)


func configure(metadata: Dictionary, body: RefCounted) -> void:
	clear()
	_body = body
	_hooks = metadata["hurt_hooks"].duplicate(true)
	_hooks.sort_custom(func(a: Dictionary, b: Dictionary) -> bool: return a["depth"] < b["depth"])
	for hook: Dictionary in _hooks:
		hook["member_frames"] = PackedInt32Array(hook["member_frames"])
		_ordered_paths.append(hook["path"])
	_ordered_paths.reverse()


func observe(source_frame: int, display_tick: int) -> void:
	instances.synchronize(_hooks, source_frame, display_tick, _create)


func dispatch(display_tick: int) -> void:
	instances.dispatch(_ordered_paths, display_tick)


func clear() -> void:
	instances.clear()
	_hooks.clear()
	_ordered_paths.clear()
	_body = null


func _create(hook: Dictionary, _generation: int) -> RefCounted:
	var callback := BodyCallback.new()
	callback.body = _body
	callback.enabled = enabled
	callback.method = hook.get("body_method", "beidax")
	callback.args = hook.get("body_args", [true if hook.get("flying", false) else null])
	return callback
