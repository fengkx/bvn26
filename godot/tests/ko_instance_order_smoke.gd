extends SceneTree

var observed: Array = []
var state := {"_root.game.p1.mc.hp": 1000, "_root.game.p2.mc.hp": 0, "_root.maxhp": 1000}

func service(operation: String, args: Array) -> Variant:
	if operation == "read":
		return state.get(args[0])
	observed.append([operation, args.duplicate()])
	return null

func actor_callback() -> void:
	observed.append(["actor", []])

func check(value: bool, message: String) -> bool:
	if not value:
		push_error(message)
		quit(1)
	return value

func _initialize() -> void:
	var registry := SourceCallbackRegistry.new()
	var host := KoTimeline.new()
	host.configure(JSON.parse_string(FileAccess.get_file_as_string("res://generated/main/ko/timeline.json")),
		JSON.parse_string(FileAccess.get_file_as_string("res://generated/main/ko/controller.json")),
		load("res://generated/main/ko/controller.gd"), service)
	host.bind_registry(registry, 0)
	var actor_id := registry.register(self, "actor_callback", 0)
	host._goto(host.root_clip, 29, true)
	host.display_tick = 1
	host.advance_timelines()
	registry.dispatch(1)
	if not check(observed == [["actor", []], ["call", ["KOend"]]], "Older KO root must resume after the actor"):
		return
	host._goto(host.root_clip, "winner", false)
	host.run_frame_actions()
	var child: Dictionary = host.root_clip.children.values()[0]
	host._goto(child, 39, true)
	host.display_tick = 2
	host.advance_timelines()
	observed.clear()
	registry.dispatch(2)
	if not check(observed == [["write", ["_root.zhanting", true]], ["actor", []]], "New winner child must pause before the actor"):
		return
	# Removing this placement must cancel its queued frame and registration.
	host._goto(child, 49, true)
	host._goto(host.root_clip, "next", false)
	observed.clear()
	host.run_frame_actions()
	if not check(observed.is_empty(), "Removed winner child executed a queued frame"):
		return
	host.unbind_registry()
	registry.unregister(actor_id)
	if not check(registry.size() == 0, "KO registrations survived teardown"):
		return
	print("KO_INSTANCE_ORDER_SMOKE_OK")
	quit()
