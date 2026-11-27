extends SceneTree

const Fixture = preload("res://tests/rollback_fixture.gd")
const Inputs = preload("res://rollback_test_session.gd")


func _initialize() -> void:
	_run.call_deferred()


func _run() -> void:
	var fixture := Fixture.create(self, ["一护万解", "迪达拉"], ["松本", "夜一"], "流魂街")
	var game: Node = fixture.game
	var fighter: FighterRuntime = game.naruto
	var transform_tick := -1
	var saw_pause := false
	var saw_release := false
	var attacked := false
	for tick in range(1, 901):
		var players := {"p1": {}, "p2": {}}
		for slot in players:
			for button in Inputs.BUTTONS:
				players[slot][button] = false
		if transform_tick < 0 and not game.battle_intro.active:
			transform_tick = tick
			fighter.energy = 300
		if transform_tick > 0 and tick < transform_tick + 4:
			players.p1.attack = true
			players.p1.jump = true
		elif saw_release and fighter.action == "站立":
			players.p1.attack = true
		var callbacks := []
		if game.battle_intro.polling and tick % 15 == 0:
			callbacks.append({"kind": "intro_poll", "phase": "after_actor_advance", "sequence": tick, "time_ms": tick * 33})
		assert(fixture.battle.set_frame_events(tick, tick * 33, false, callbacks).is_empty())
		assert(fixture.battle.advance(tick, players).is_empty())
		if fighter.source_parent_frame != 3 or not fighter.source_body_available:
			continue
		match fighter.current_source_frame():
			1028:
				assert(game.super_runtime.zhanting and game.super_presentation.black_overlay_visible())
				saw_pause = true
			1029:
				assert(not game.super_runtime.zhanting, "Hollow Ichigo must release the super pause at opening frame 1029")
				assert(not fighter.read_parent_field("万解") and not fighter.zhanting)
				assert(not game.super_presentation.black_overlay_visible() and game.ichigo.timeline_playing)
				saw_release = true
		if fighter.action == "砍1":
			attacked = true
			break
	assert(saw_pause and saw_release and attacked, "The second transformation must return control to the player")
	for audio: AudioStreamPlayer in game.find_children("*", "AudioStreamPlayer", true, false):
		audio.stop()
		audio.stream = null
	Fixture.dispose(game, fixture.battle)
	await create_timer(0.1).timeout
	print("YIHU_HOLLOW_TRANSFORM_OK")
	quit()
