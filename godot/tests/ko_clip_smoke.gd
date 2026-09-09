extends SceneTree

var state := {"_root.game.p1.mc.hp": 0, "_root.game.p2.mc.hp": 1000, "_root.maxhp": 1000,
	"_root.p1ws": 1, "_root.p2ws": 1, "_root.maxtime": 99, "_root.modo": 2}

func service(operation: String, args: Array) -> Variant:
	if operation == "read":
		assert(state.has(args[0]))
		return state[args[0]]
	if operation == "write":
		state[args[0]] = args[1]
	return 1 if operation == "interval" else null


func _initialize() -> void:
	_run.call_deferred()


func _run() -> void:
	var host := KoTimeline.new()
	host.configure(JSON.parse_string(FileAccess.get_file_as_string("res://generated/main/ko/timeline.json")),
		JSON.parse_string(FileAccess.get_file_as_string("res://generated/main/ko/controller.json")),
		load("res://generated/main/ko/controller.gd"), service)
	var clip := KoClip.new()
	clip.scheduler = host
	root.add_child(clip)
	assert(clip.position.is_equal_approx(Vector2(96.35, 115.6)))
	assert(clip.scale.is_equal_approx(Vector2(1.2990723, 1.2990723)))
	host.play()
	while host.root_clip.frame < 94:
		host.advance()
	clip.refresh_from_scheduler()
	var winner: Dictionary = host.root_clip.children.values()[0]
	assert(clip._placement_transform(winner.placement).origin.x == 120)
	var saw_perfect := false
	for tick in 100:
		host.advance()
		clip.refresh_from_scheduler()
		for child: Dictionary in host._ordered(host.root_clip):
			if child.symbol == 1843 and child.frame == 15:
				saw_perfect = true
				assert(clip._nested_frame(child.placement, 999, 15) == 15)
	assert(saw_perfect)
	assert(winner.frame == 50 and not winner.playing)
	assert(clip._nested_frame(winner.placement, 999, 50) == 50)
	await process_frame
	var visible_sprites := 0
	for child in clip.get_children():
		if child is Sprite2D and not child.is_queued_for_deletion():
			assert(child.texture != null)
			visible_sprites += 1
	assert(visible_sprites > 0)
	clip.queue_free()
	await process_frame
	print("KO_CLIP_SMOKE_OK")
	quit()
