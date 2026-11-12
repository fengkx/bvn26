extends Node

const Timing = preload("res://g0/timing.gd")
const Battle = preload("res://rollback_battle.gd")
const Inputs = preload("res://rollback_session.gd")
var surface: Control
var game: Control
var battle := Battle.new()
var tape: Array
var samples: Array = []
var pending: Array = []
var frame := 0
var draw_started := 0
var finished := false
var viewports: Array[Viewport] = []

func _ready() -> void:
	surface = load("res://render_surface.tscn").instantiate()
	add_child(surface)
	game = surface.game
	game.set_physics_process(false)
	game.set_process(false)
	game.ko_recorded_timers = true
	game.recorded_training_timers = true
	game.source_random.use_seed(727)
	game.source_clock.use_explicit_time(0)
	game.session.maxhp = 1000.0
	game.session.maxtime = 60
	game.session.ai_level = 5
	game.session.render_quality = "HIGH"
	surface.apply_quality("HIGH")
	game._replace_selected_actors(["鸣人", "一护"], ["我爱罗", "松本"])
	game._load_selected_stage("现世")
	game._enter_current_fight(3)
	# Synthetic workload precondition, not a gameplay rule or mid-run refill.
	game.naruto.energy = 300.0
	game.ichigo.energy = 300.0
	game.battle_intro.recorded_polling = true
	for timer in game.title_menu.find_children("*", "Timer", true, false): timer.stop()
	var configured := battle.configure(game)
	if not configured.is_empty():
		_fail(configured)
		return
	tape = JSON.parse_string(FileAccess.get_file_as_string("res://g0/tape.json"))
	RenderingServer.frame_pre_draw.connect(_pre_draw)
	RenderingServer.frame_post_draw.connect(_post_draw)
	Timing.enabled = true
	if OS.has_feature("web"): JavaScriptBridge.eval("g0.start()")

func _physics_process(_delta: float) -> void:
	if frame >= tape.size() or finished: return
	frame += 1
	var entry: Dictionary = tape[frame - 1]
	var sampled := Time.get_ticks_usec()
	var before := {"action": game.naruto.action, "position": game.naruto.position}
	var skip := frame >= 30 and frame < 90
	var events := []
	if game.battle_intro.polling and frame % 15 == 0 and not (skip and game.battle_intro.step > 1 and game.battle_intro.step < 4):
		events.append({"kind": "intro_poll", "phase": "after_actor_advance", "sequence": frame, "time_ms": frame * 33})
	var envelope := battle.set_frame_events(frame, frame * 33, skip, events)
	if not envelope.is_empty():
		_fail(envelope)
		return
	var problem := battle.advance(frame, entry.players)
	if not problem.is_empty():
		_fail(problem)
		return
	var sample := Timing.take()
	sample.merge({"tick": frame, "segment": entry.segment, "input_sample_us": sampled,
		"action_before": before.action, "action_after": game.naruto.action,
		"response": "state_changed_not_causal_proof" if before.action != game.naruto.action or before.position != game.naruto.position else "no_observed_response",
		"p1_energy": game.naruto.energy, "helper_visible": game.naruto_helper.attacking,
		"super_active": bool(game._diagnostic_pause_state().globalSuperPaused)})
	pending.append(sample)

func _pre_draw() -> void:
	viewports.clear()
	_collect_viewports(get_tree().root)
	draw_started = Time.get_ticks_usec()

func _collect_viewports(node: Node) -> void:
	if node is Viewport:
		viewports.append(node)
		RenderingServer.viewport_set_measure_render_time(node.get_viewport_rid(), true)
	for child in node.get_children(): _collect_viewports(child)

func _post_draw() -> void:
	if finished: return
	var submitted := Time.get_ticks_usec()
	var display := Timing.take()
	var viewport_cpu := []
	var render_cpu_ms := RenderingServer.get_frame_setup_time_cpu()
	for viewport in viewports:
		if not is_instance_valid(viewport): continue
		var cpu := RenderingServer.viewport_get_measured_render_time_cpu(viewport.get_viewport_rid())
		viewport_cpu.append({"path": str(viewport.get_path()), "cpu_ms": cpu})
		render_cpu_ms += cpu
	var row := {"submit_us": submitted, "latest_tick": frame,
		"submit_start_us": draw_started, "display_spans_us": display.display_spans_us,
		"submit_interval_wall_us": submitted - draw_started,
		"display_script_exclusive_us": display.exclusive_us,
		"viewport_cpu": viewport_cpu, "render_cpu_ms": render_cpu_ms,
		"render_setup_cpu_ms": RenderingServer.get_frame_setup_time_cpu(),
		"draw_calls": Performance.get_monitor(Performance.RENDER_TOTAL_DRAW_CALLS_IN_FRAME),
		"render_objects": Performance.get_monitor(Performance.RENDER_TOTAL_OBJECTS_IN_FRAME),
		"video_memory_bytes": Performance.get_monitor(Performance.RENDER_VIDEO_MEM_USED),
		"ticks": pending.duplicate(true)}
	for tick in row.ticks:
		tick["display_status"] = "submitted" if tick.tick == frame else "superseded_before_submit"
		tick["input_to_submit_us"] = submitted - int(tick.input_sample_us) if tick.tick == frame else null
	pending.clear()
	samples.append(row)
	if frame == tape.size():
		finished = true
		Timing.enabled = false
		var report := {"kind": "g0-instrumentation-v1", "g0_passed": false,
			"validity": "not-a-pass", "gpu_time_ms": "UNKNOWN",
			"gpu_reason": "No disjoint-safe WebGL GPU completion timer is joined to these samples",
			"engine": Engine.get_version_info(), "samples": samples,
			"source_viewport_size": [surface.source_viewport.size.x, surface.source_viewport.size.y],
			"sample_grid": surface.sample_grid}
		if OS.has_feature("web"):
			JavaScriptBridge.eval("g0.finish(" + JSON.stringify(report) + ")")
		else:
			print("G0_DRY_RUN ", JSON.stringify(report))
			get_tree().quit()

func _fail(problem: String) -> void:
	finished = true
	set_physics_process(false)
	push_error(problem)
	if OS.has_feature("web"):
		JavaScriptBridge.eval("document.querySelector('#status').textContent = " + JSON.stringify("G0 FAILED: " + problem))
