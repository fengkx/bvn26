extends SourceCallbackRegistry


class WeakTargetProxy extends RefCounted:
	var _target: WeakRef
	var _method: StringName
	var _observer: Callable
	var _identity: Dictionary
	var _registry: WeakRef
	var _registration_id := -1

	func configure(target: Object, method: StringName, observer: Callable, identity: Dictionary) -> void:
		_target = weakref(target)
		_method = method
		_observer = observer
		_identity = identity.duplicate(true)

	func delegate_alive() -> bool:
		return _target != null and _target.get_ref() != null

	func set_registration(registry: SourceCallbackRegistry, registration_id: int) -> void:
		_registry = weakref(registry)
		_registration_id = registration_id

	func frame_1088_depth_29() -> Variant:
		return _invoke()

	func frame_1098_depth_29() -> Variant:
		return _invoke()

	func frame_1133_depth_30() -> Variant:
		return _invoke()

	func _invoke() -> Variant:
		var target: Object = _target.get_ref()
		if target == null:
			var registry: SourceCallbackRegistry = _registry.get_ref() if _registry != null else null
			if registry != null and _registration_id >= 0:
				registry.unregister(_registration_id)
			return null
		var event := _identity.duplicate(true)
		event["phase"] = "enter"
		event["target_alive"] = true
		_observer.call(event)
		var result: Variant
		result = target.call(_method)
		event["phase"] = "exit"
		event["target_alive"] = true
		_observer.call(event)
		return result


var _proxies: Dictionary = {}
var traced_paths: Dictionary = {}
var identity_lookup: Callable
var observer: Callable


func adopt(existing: SourceCallbackRegistry) -> void:
	assert(_entries.is_empty() and _next_id == 0)
	_entries = existing._entries.duplicate()
	_next_id = existing._next_id
	current_tick = existing.current_tick
	_dispatching = existing._dispatching


func register(target: Object, method: StringName, placed_tick: int) -> int:
	if observer.is_valid() and identity_lookup.is_valid():
		var identity: Dictionary = identity_lookup.call(target.get_instance_id())
		var source_path := str(identity.get("source_path", ""))
		if traced_paths.has(source_path):
			var proxy := WeakTargetProxy.new()
			proxy.configure(target, method, observer, identity)
			assert(proxy.has_method(method), "No trace proxy method for " + str(method))
			var registration := super.register(proxy, method, placed_tick)
			proxy.set_registration(self, registration)
			proxy._identity["registration_id"] = registration
			proxy._identity["placed_tick"] = placed_tick
			_proxies[registration] = proxy
			return registration
	return super.register(target, method, placed_tick)


func unregister(registration: int) -> void:
	super.unregister(registration)
	_proxies.erase(registration)


func dispatch(display_tick: int) -> void:
	# A proxy is strongly held here, unlike the production registry's weak target.
	# Remove dead delegates before the inherited dispatcher can mistake the proxy
	# for a live callback and invoke it.
	for registration: int in _proxies.keys():
		var proxy: WeakTargetProxy = _proxies[registration]
		if not proxy.delegate_alive():
			super.unregister(registration)
			_proxies.erase(registration)
	super.dispatch(display_tick)


func clear() -> void:
	super.clear()
	_proxies.clear()
