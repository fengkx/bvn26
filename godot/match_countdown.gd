class_name MatchCountdown
extends Label

var root_service: Callable
var timer: Timer
var controller: RefCounted
var unlimited := false
var locals := {"tm": 0, "shi": 0, "gs": 0, "played": 0}

class Adapter extends RefCounted:
	var owner: WeakRef
	func read(key: String) -> Variant:
		var host: MatchCountdown = owner.get_ref()
		return host.locals[key] if host.locals.has(key) else host.root_service.call("read", [key])
	func write(key: String, value: Variant) -> void:
		var host: MatchCountdown = owner.get_ref()
		if host.locals.has(key): host.locals[key] = value
		else: host.root_service.call("write", [key, value])
	func set_playing(target: String, value: bool) -> void:
		owner.get_ref().root_service.call("playing", [target, value])
	func goto_clip(_target: String, _frame: Variant, _playing: bool) -> void:
		pass # The two compiled digit frames are presented by refresh().

func configure(service: Callable, recorded: bool) -> void:
	root_service = service
	var spec: Dictionary = JSON.parse_string(FileAccess.get_file_as_string("res://generated/main/timeout/timer.json"))
	controller = load("res://generated/main/timeout/timer.gd").new()
	var adapter := Adapter.new()
	adapter.owner = weakref(self)
	controller.adapter = adapter
	var limit := int(service.call("read", ["_root.maxtime"]))
	service.call("write", ["_root.gametime", limit])
	unlimited = limit == int(spec.unlimited_value) or int(service.call("read", ["_root.modo"])) == int(spec.training_mode)
	text = "∞" if unlimited else str(limit).pad_zeros(2)
	position = Vector2(267, 12)
	size = Vector2(66, 34)
	horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	add_theme_font_size_override("font_size", 28)
	mouse_filter = Control.MOUSE_FILTER_IGNORE
	if not unlimited:
		timer = Timer.new()
		timer.process_mode = Node.PROCESS_MODE_ALWAYS
		timer.ignore_time_scale = true
		timer.wait_time = float(spec.interval_ms) / 1000.0
		add_child(timer)
		timer.timeout.connect(fire)
		if not recorded: timer.start()

func fire() -> void:
	if unlimited: return
	controller.time()
	text = str(int(locals.tm)).pad_zeros(2)

func stop() -> void:
	if timer != null: timer.stop()
