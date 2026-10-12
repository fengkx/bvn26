extends SceneTree

var _events: Array[Dictionary] = []
var _game: Node


func _initialize() -> void:
	_run.call_deferred()


func _run() -> void:
	_game = load("res://main.tscn").instantiate()
	root.add_child(_game)
	_game.set_physics_process(false)
	await process_frame
	_game.diagnostics.event_recorded.connect(func(event: Dictionary) -> void:
		_events.append(event.duplicate(true)))
	_game._load_selected_stage("现世")
	_game._enter_current_fight(3)
	_game.battle_intro.active = false
	_game.super_runtime.zhanting = true
	_game.naruto.bs = 1
	_game.naruto.play_source_frame(883)
	_game.ichigo.play_source_frame(863)
	_game._diagnostic_watchdog_step(1000)
	_game.naruto.play_source_frame(884)
	_game.ichigo.play_source_frame(864)
	_game._diagnostic_watchdog_step(11000)
	assert(_incident_count() == 0, "A progressing long super pause must not be reported")
	_game.naruto.play_source_frame(887)
	_game.ichigo.play_source_frame(867)
	_game._diagnostic_watchdog_step(12000)
	_game._diagnostic_watchdog_step(22001)
	_game._diagnostic_watchdog_step(33000)
	assert(_incident_count() == 1, "A frozen super pause must produce one diagnostic incident")
	var incident := _find_incident()
	assert(incident.get("payload", {}).get("reason") == "suspected_super_pause_stall")
	assert(incident.get("payload", {}).get("detail", {}).get("globalSuperPaused") == true)
	assert(_game.super_runtime.zhanting and not _game.super_runtime.game_paused)
	assert(_game.naruto.bs == 1)
	assert(_game.naruto.current_source_frame() == 887 and _game.ichigo.current_source_frame() == 867)
	_game.super_runtime.zhanting = false
	_game.super_runtime.game_paused = true
	_game._diagnostic_watchdog_step(44000)
	_game._diagnostic_watchdog_step(60000)
	assert(_incident_count() == 1, "User pause must not produce a stall incident")
	_game.super_runtime.game_paused = false
	_game.diagnostics.page_visible = false
	_game._diagnostic_watchdog_step(70000)
	_game._diagnostic_watchdog_step(90000)
	assert(_incident_count() == 1, "A hidden page must not produce a stall incident")
	_game.diagnostics.page_visible = true
	_game.super_runtime.zhanting = true
	_game.set_meta("online_wait", "recovery")
	_game._diagnostic_watchdog_step(100000)
	_game._diagnostic_watchdog_step(110001)
	assert(_incident_count() == 2)
	assert(_events.back().payload.reason == "online_simulation_stall")
	assert(_game.super_runtime.zhanting, "Network waits must never force-unpause source effects")
	print("DIAGNOSTIC_WATCHDOG_OK progressing_super=0 frozen_super=1 user_pause=0 hidden=0")
	_game.queue_free()
	await process_frame
	quit()


func _incident_count() -> int:
	var count := 0
	for event in _events:
		if event.get("type") == "diagnostic_exception":
			count += 1
	return count


func _find_incident() -> Dictionary:
	for event in _events:
		if event.get("type") == "diagnostic_exception":
			return event
	return {}
