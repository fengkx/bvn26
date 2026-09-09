extends SceneTree

var state: Dictionary
var events: Array

func service(operation: String, args: Array) -> Variant:
	if operation == "read":
		assert(state.has(args[0]), "Missing KO timeline fixture: " + str(args[0]))
		return state[args[0]]
	if operation == "write":
		state[args[0]] = args[1]
	events.append([operation, args.duplicate()])
	return 42 if operation == "interval" else null


func _initialize() -> void:
	var timeline: Dictionary = JSON.parse_string(FileAccess.get_file_as_string("res://generated/main/ko/timeline.json"))
	var metadata: Dictionary = JSON.parse_string(FileAccess.get_file_as_string("res://generated/main/ko/controller.json"))
	for hp: Array in [[1000, 0], [0, 1000], [0, 0]]:
		state = {"_root.game.p1.mc.hp": hp[0], "_root.game.p2.mc.hp": hp[1], "_root.maxhp": 1000, "_root.maxtime": 99, "_root.modo": 2}
		state.merge(metadata.root_initializers, true)
		assert(state["_root.p1ws"] == 1 and state["_root.p2ws"] == 1)
		events = []
		var host := KoTimeline.new()
		host.configure(timeline, metadata, load("res://generated/main/ko/controller.gd"), service)
		assert(host.root_clip.frame == 1 and not host.root_clip.playing)
		host.play()
		host.advance()
		assert(events.is_empty())
		host.advance()
		assert(events == [["call", ["KOstart"]]])
		var seen_winner := false
		var seen_perfect := false
		for tick in 500:
			host.advance()
			if host.root_clip.frame == 94:
				seen_winner = true
				var child: Dictionary = host.root_clip.children.values()[0]
				assert(child.name == "winmc")
				assert(child.x_override == (0 if hp[0] > hp[1] else 120))
			for clip: Dictionary in host._ordered(host.root_clip):
				if clip.symbol == 1843 and clip.frame == 15:
					assert(not clip.playing)
					seen_perfect = true
			if host.root_clip.frame == 1 and not host.root_clip.playing:
				break
		assert(host.root_clip.frame == 1 and not host.root_clip.playing)
		assert(seen_winner == (hp[0] != hp[1]))
		assert(seen_perfect == (hp[0] != hp[1]))
		assert(state["_root.nxtfht"] == 42)
		assert(state["_root.p1ws"] + state["_root.p2ws"] == (2 if hp[0] == hp[1] else 3))
		assert(events.has(["call", ["KOend"]]))
		assert(events.has(["interval", ["nextfight", 1000]]))
	print("KO_TIMELINE_SMOKE_OK")
	quit()
