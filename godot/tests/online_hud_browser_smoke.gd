extends "res://render_surface.gd"

class FakeCoordinator:
	extends RefCounted

	# Keep the harness isolated from matchmaking, signaling, and combat.
	var pause_requests := 0
	var closed := false

	func process_tick(_now_ms: int, _held: Dictionary) -> String:
		return ""

	func request_pause() -> String:
		pause_requests += 1
		return ""

	func request_resume() -> String:
		return ""

	func close(_reason: String = "") -> void:
		closed = true

var _fake_coordinator: FakeCoordinator
var _last_published_pause_requests := -1


func _ready() -> void:
	super._ready()
	call_deferred("_start_hud_smoke")


func _start_hud_smoke() -> void:
	if not OS.has_feature("web"):
		_publish({"phase": "failed", "error": "web_feature_required"})
		return

	game.set_physics_process(false)
	_fake_coordinator = FakeCoordinator.new()
	online_lobby.coordinator = _fake_coordinator
	online_lobby._starting_epoch = "online-hud-browser-smoke"
	online_lobby._lifecycle_generation = 1
	online_lobby._on_match_started(online_lobby._starting_epoch, online_lobby._lifecycle_generation)
	if not online_lobby._web_match_hud_registered:
		_publish({"phase": "failed", "error": "web_hud_bridge_registration_failed"})
		return
	_publish({"phase": "ready", "error": ""})


func _process(_delta: float) -> void:
	if _fake_coordinator == null or _last_published_pause_requests == _fake_coordinator.pause_requests:
		return
	_publish({"phase": "ready", "error": ""})


func _publish(extra: Dictionary) -> void:
	if not OS.has_feature("web"):
		return
	var report := {
		"active": online_lobby != null and online_lobby._match_started,
		"registered": online_lobby != null and online_lobby._web_match_hud_registered,
		"fallbackHudVisible": online_lobby != null and online_lobby._match_hud.visible,
		"pauseRequests": _fake_coordinator.pause_requests if _fake_coordinator != null else 0,
		"revision": online_lobby._web_match_hud_revision if online_lobby != null else -1,
	}
	report.merge(extra, true)
	_last_published_pause_requests = int(report.pauseRequests)
	JavaScriptBridge.eval("window.__onlineHudGodotSmoke = " + JSON.stringify(report))
	if str(report.get("phase", "")) == "ready":
		print("ONLINE_HUD_GODOT_BRIDGE_READY pause_requests=%d revision=%d" % [report.pauseRequests, report.revision])
	elif str(report.get("phase", "")) == "failed":
		push_error("ONLINE_HUD_GODOT_BRIDGE_FAILED " + str(report.get("error", "unknown")))
