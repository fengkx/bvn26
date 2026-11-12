extends Node

const Battle = preload("res://rollback_battle.gd")
const DisplayProjection = preload("res://authority_projection.gd")
const Wire = preload("res://authority_wire.gd")
const Inputs = preload("res://authority_input_queue.gd")
var game: Node
var guest: Node
var battle := Battle.new()
var capture := DisplayProjection.new()
var display := DisplayProjection.new()
var wire := Wire.new()
var frame := 0
var finished := false
var max_bytes := 0
var super_ticks := 0

func _ready() -> void:
	var surface: RenderSurface = load("res://render_surface.tscn").instantiate()
	add_child(surface)
	guest = surface.recreate_game_scene(true)
	display.configure_presenter(guest)
	var host_view := SubViewport.new()
	host_view.size = Vector2i(600, 400)
	host_view.render_target_update_mode = SubViewport.UPDATE_ALWAYS
	add_child(host_view)
	game = load("res://main.tscn").instantiate()
	host_view.add_child(game)
	game.set_physics_process(false)
	game.set_process(false)
	game.ko_recorded_timers = true
	game.recorded_training_timers = true
	game.source_random.use_seed(727)
	game.source_clock.use_explicit_time(0)
	game._replace_selected_actors(["鸣人", "一护"], ["我爱罗", "魂"])
	game._load_selected_stage("现世")
	game._enter_current_fight(3)
	game.battle_intro.recorded_polling = true
	game.naruto.energy = 300.0
	game.ichigo.energy = 300.0
	game.combo_hud.set_presentation_enabled(false)
	game.set_meta("authority_projector", capture)
	game.set_meta("authority_audio", capture.audio)
	game.stage_sound.start()
	var problem := battle.configure(game, false)
	if not problem.is_empty(): _fail(problem)

func _physics_process(_delta: float) -> void:
	if finished or game == null: return
	frame += 1
	var players := {"p1": Inputs.neutral(), "p2": Inputs.neutral()}
	for instruction in [[165,190,["right"]],[195,200,["attack"]],[235,237,["ranged"]],[300,302,["summon"]],[450,452,["down","special"]],[600,602,["special"]],[750,752,["summon"]]]:
		if frame >= instruction[0] and frame < instruction[1]:
			for button in instruction[2]: players.p1[button] = true
	var skip := frame >= 30 and frame < 90
	var events := []
	if game.battle_intro.polling and frame % 15 == 0 and not (skip and game.battle_intro.step > 1 and game.battle_intro.step < 4):
		events.append({"kind": "intro_poll", "phase": "after_actor_advance", "sequence": frame, "time_ms": frame * 33})
	var problem := battle.set_frame_events(frame, frame * 33, skip, events)
	if problem.is_empty(): problem = battle.advance(frame, players)
	if not problem.is_empty(): return _fail(problem)
	if game._diagnostic_pause_state().globalSuperPaused: super_ticks += 1
	var snapshot := capture.capture(game)
	if not capture.error.is_empty(): return _fail(capture.error)
	var packet := wire.encode(snapshot)
	if packet.is_empty(): return _fail(wire.error)
	max_bytes = maxi(max_bytes, packet.size())
	# Drop two out of three display samples deliberately; keep heavy effects.
	if frame % 3 == 0:
		problem = display.apply(wire.decode(packet))
		if not problem.is_empty(): return _fail(problem)
	if guest.physics_tick != 0: return _fail("guest_simulated")
	if frame % 30 == 0:
		JavaScriptBridge.eval("globalThis.authoritySmoke = " + JSON.stringify({"phase": "playing", "frame": frame, "maxBytes": max_bytes}))
	if frame == 900:
		finished = true
		var result := {"phase": "complete", "hostTicks": frame, "guestTicks": guest.physics_tick,
			"superTicks": super_ticks, "maxBytes": max_bytes, "applied": 300, "notAPass": true}
		JavaScriptBridge.eval("globalThis.authoritySmoke = " + JSON.stringify(result))
		print("AUTHORITY_BROWSER_PROJECTION_OK " + JSON.stringify(result))

func _fail(reason: String) -> void:
	finished = true
	JavaScriptBridge.eval("globalThis.authoritySmoke = " + JSON.stringify({"phase": "failed", "reason": reason, "frame": frame}))
	push_error(reason)
