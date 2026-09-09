class_name KoTimeline
extends RefCounted

var root_clip: Dictionary
var clips: Dictionary = {}
var methods: Dictionary = {}
var callbacks: Array = []
var load_callbacks: Array = []
var root_service: Callable
var controller: RefCounted
var tick: int = 0
var _generation: int = 0
var _pending: Array = []
var _executing: Dictionary
var registry: SourceCallbackRegistry
var display_tick: int = 0

class InstanceDispatch extends RefCounted:
	var owner: WeakRef
	var clip: Dictionary
	func dispatch() -> void:
		var host: KoTimeline = owner.get_ref()
		if host != null and clip.alive:
			host._run_clip_callback(clip)
			host._run_clip_frames(clip)

func bind_registry(value: SourceCallbackRegistry, placed_tick: int) -> void:
	assert(registry == null)
	registry = value
	display_tick = placed_tick
	_register_clip(root_clip)

func _register_clip(clip: Dictionary) -> void:
	var target := InstanceDispatch.new()
	target.owner = weakref(self)
	target.clip = clip
	clip.dispatch_target = target
	clip.registration = registry.register(target, "dispatch", display_tick)
	for child: Dictionary in clip.children.values():
		_register_clip(child)

func unbind_registry() -> void:
	if registry == null:
		return
	for clip: Dictionary in _ordered(root_clip):
		registry.unregister(int(clip.registration))
		clip.erase("dispatch_target")
	registry = null

func _run_clip_frames(clip: Dictionary) -> void:
	var pending_frames: Array = []
	for pending: Array in _pending:
		if pending[0].generation == clip.generation:
			pending_frames.append(pending)
	for pending: Array in pending_frames:
		_pending.erase(pending)
		if not clip.alive:
			continue
		_executing = clip
		var key := "%d:%d" % [clip.symbol, pending[1]]
		if methods.has(key):
			controller.call(methods[key])


class Adapter extends RefCounted:
	var host: WeakRef
	func read(key: String) -> Variant:
		var owner: KoTimeline = host.get_ref()
		if key == "_currentframe": return owner._executing.frame
		if key == "played": return owner._executing.variables.get(key, 0)
		return owner.root_service.call("read", [key])
	func write(key: String, value: Variant) -> void:
		var owner: KoTimeline = host.get_ref()
		if key == "played":
			owner._executing.variables[key] = value
		elif key == "_X":
			owner._executing.x_override = value
		elif key == "winmc._x":
			for child: Dictionary in owner._executing.children.values():
				if child.name == "winmc":
					child.x_override = value
					return
			assert(false, "Missing live KO winmc")
		else:
			owner.root_service.call("write", [key, value])
	func goto_clip(target: String, label: Variant, playing: bool) -> void:
		var owner: KoTimeline = host.get_ref()
		if target == "this":
			owner._goto(owner._executing, label, playing)
		else:
			owner.root_service.call("goto", [target, label, playing])
	func set_playing(target: String, playing: bool) -> void:
		var owner: KoTimeline = host.get_ref()
		if target == "this":
			owner._executing.playing = playing
		else:
			owner.root_service.call("playing", [target, playing])
	func call_root(name: String) -> void:
		host.get_ref().root_service.call("call", [name])
	func register_interval(name: String, delay: int) -> int:
		return int(host.get_ref().root_service.call("interval", [name, delay]))


func configure(timeline: Dictionary, metadata: Dictionary, script: Script, service: Callable) -> void:
	root_service = service
	clips[int(timeline.sprite_id)] = {"frames": timeline.frames.map(func(frame: Dictionary) -> Array: return frame.display_list), "labels": {}}
	for frame: Dictionary in timeline.frames:
		for label: String in frame.labels:
			clips[int(timeline.sprite_id)].labels[label] = int(frame.frame)
	for definition: Dictionary in timeline.definitions:
		if definition.type == "DefineSpriteTag":
			clips[int(definition.character_id)] = {"frames": definition.display_list_frames, "labels": {}}
	for event: Dictionary in metadata.events:
		if event.kind == "frame":
			methods["%d:%d" % [int(event.sprite_id), int(event.frame)]] = event.method
		elif event.kind == "load":
			load_callbacks.append(event)
		else:
			callbacks.append(event)
	controller = script.new()
	var adapter := Adapter.new()
	adapter.host = weakref(self)
	controller.adapter = adapter
	root_clip = _new_clip(int(timeline.sprite_id), {}, "KO")
	run_frame_actions()


func _new_clip(symbol: int, placement: Dictionary, instance_name: String) -> Dictionary:
	_generation += 1
	var clip := {"symbol": symbol, "frame": 1, "playing": true, "generation": _generation,
		"placed_tick": tick, "children": {}, "placement": placement, "name": instance_name,
		"variables": {}, "x_override": null, "alive": true, "parent_symbol": -1}
	if registry != null:
		_register_clip(clip)
	_synchronize(clip)
	_pending.append([clip, 1])
	return clip


func _remove(clip: Dictionary) -> void:
	clip.alive = false
	if registry != null:
		registry.unregister(int(clip.registration))
		clip.erase("dispatch_target")
	for child: Dictionary in clip.children.values():
		_remove(child)


func _synchronize(clip: Dictionary) -> void:
	var retained := {}
	for placement: Dictionary in clips[clip.symbol].frames[clip.frame - 1]:
		var symbol := int(placement.character_id)
		if not clips.has(symbol):
			continue
		var key := "%d:%d:%d" % [int(placement.depth), symbol, int(placement.placed_frame)]
		retained[key] = true
		if not clip.children.has(key):
			clip.children[key] = _new_clip(symbol, placement, str(placement.get("name", "")))
			clip.children[key].parent_symbol = clip.symbol
			for event: Dictionary in load_callbacks:
				if int(event.sprite_id) == int(clip.symbol) and int(event.frame) == int(placement.placed_frame) and int(event.depth) == int(placement.depth):
					var previous := _executing
					_executing = clip.children[key]
					controller.call(event.method)
					_executing = previous
		else:
			clip.children[key].placement = placement
	for key: String in clip.children.keys():
		if not retained.has(key):
			_remove(clip.children[key])
			clip.children.erase(key)


func _goto(clip: Dictionary, label: Variant, playing: bool) -> void:
	var frame := int(clips[clip.symbol].labels[label]) if label is String else int(label)
	assert(frame >= 1 and frame <= clips[clip.symbol].frames.size())
	clip.frame = frame
	clip.playing = playing
	_synchronize(clip)
	_pending.append([clip, frame])


func _ordered(clip: Dictionary) -> Array:
	var result: Array = []
	var children: Array = clip.children.values()
	children.sort_custom(func(a: Dictionary, b: Dictionary) -> bool: return int(a.placement.depth) > int(b.placement.depth))
	for child: Dictionary in children:
		result.append_array(_ordered(child))
	result.append(clip)
	return result


func advance_timelines() -> void:
	tick += 1
	# Snapshot before placement: new children do not advance on their birth tick.
	for clip: Dictionary in _ordered(root_clip):
		if clip.alive and clip.playing and clip.placed_tick < tick:
			_goto(clip, clip.frame % clips[clip.symbol].frames.size() + 1, true)


func _run_clip_callback(clip: Dictionary) -> void:
	if not clip.alive or clip.placed_tick >= tick or clip.placement.is_empty():
		return
	for event: Dictionary in callbacks:
		if int(event.sprite_id) == clip.parent_symbol and int(event.child_id) == clip.symbol and int(event.depth) == int(clip.placement.depth) and int(event.frame) == int(clip.placement.placed_frame):
			_executing = clip
			controller.call(event.method)

func run_enter_frame() -> void:
	for clip: Dictionary in _ordered(root_clip):
		_run_clip_callback(clip)


func run_frame_actions() -> void:
	while not _pending.is_empty():
		var pending: Array = _pending.pop_front()
		_executing = pending[0]
		if not _executing.alive:
			continue
		var key := "%d:%d" % [_executing.symbol, pending[1]]
		if methods.has(key):
			controller.call(methods[key])


func play() -> void:
	root_clip.playing = true


func advance() -> void:
	advance_timelines()
	run_enter_frame()
	run_frame_actions()
