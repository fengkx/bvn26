class_name OnlineMapSelectionAdapter
extends MapSelection

signal snapshot_changed(snapshot: Dictionary)
signal selection_confirmed(stage_id: String, session_id: String, revision: int)
signal selection_cancelled(session_id: String)

const SNAPSHOT_VERSION := 1
const MAX_REVISION := 9_007_199_254_740_991

var session_id := ""
var host_authority := false

var _selection_active := false
var _host_confirmed := false
var _revision := 0
var _remote_snapshot_received := false
var _remote_confirmed := false
var _cancel_held := false
var _generation := 0
var _confirmation_callback: Callable


func _ready() -> void:
	super._ready()
	mouse_filter = Control.MOUSE_FILTER_IGNORE
	visible = false
	cancelled.connect(_on_base_cancelled)
	# MapSelection's original timeout is kept for offline play. This adapter
	# replaces it with a callback bound to the active session generation.
	var offline_callback := Callable(self, "_finish_confirmation")
	if _confirm_timer.timeout.is_connected(offline_callback):
		_confirm_timer.timeout.disconnect(offline_callback)


func begin(new_session_id: String, is_host: bool, initial_stage_id: String) -> String:
	if new_session_id.is_empty() or new_session_id.length() > 128:
		return "invalid_selection_session"
	if spec.is_empty() or _confirm_timer == null:
		return "map_selection_not_ready"
	if _find_stage_index(initial_stage_id) < 0:
		return "unknown_stage"

	end_selection()
	_generation += 1
	session_id = new_session_id
	host_authority = is_host
	_selection_active = true
	_host_confirmed = false
	_revision = 0
	_remote_snapshot_received = false
	_remote_confirmed = false
	_cancel_held = false
	visible = true
	z_index = 200
	super.reset()
	_select_stage(initial_stage_id)
	if not host_authority:
		# A guest sees the host's choice but never operates the original picker.
		enabled = false
	_attach_confirmation_callback()
	if host_authority:
		_emit_snapshot(false)
	return ""


func tick_local(held: Dictionary) -> void:
	if not _selection_active:
		return
	if host_authority:
		var previous_stage := selected_stage()
		super.tick(held)
		if not _selection_active:
			return
		if selected_stage() != previous_stage:
			_advance_revision_and_emit(false)
		return

	# The guest advances the same source presentation clock without local game
	# input. Back is a request to the host; it does not alter the mirrored view.
	super.tick({})
	var back_pressed := bool(held.get("back", false))
	if back_pressed and not _cancel_held:
		_cancel_held = true
		selection_cancelled.emit(session_id)
	elif not back_pressed:
		_cancel_held = false


func apply_remote_snapshot(snapshot: Dictionary) -> bool:
	if not _selection_active or host_authority:
		return false
	if not _is_wire_integer(snapshot.get("version")) or int(snapshot.version) != SNAPSHOT_VERSION:
		return false
	if snapshot.get("sessionId") is not String or str(snapshot.sessionId) != session_id:
		return false
	var remote_revision: Variant = snapshot.get("revision")
	if not _is_wire_integer(remote_revision) or int(remote_revision) < 0 or int(remote_revision) > MAX_REVISION:
		return false
	if not snapshot.get("stageId") is String or _find_stage_index(str(snapshot.stageId)) < 0:
		return false
	if snapshot.get("confirmed") is not bool:
		return false
	if _remote_confirmed:
		return false
	if _remote_snapshot_received and int(remote_revision) <= _revision:
		return false
	if not _remote_snapshot_received and int(remote_revision) < 0:
		return false

	var remote_stage := str(snapshot.stageId)
	if selected_stage() != remote_stage:
		_select_stage(remote_stage)
	_revision = int(remote_revision)
	_remote_snapshot_received = true
	_remote_confirmed = bool(snapshot.confirmed)
	# A confirmed remote snapshot is display-only as well; only the host's
	# service-accepted map_committed message advances the room workflow.
	enabled = false
	return true


func end_selection() -> void:
	# Ending is local teardown, not a player cancellation. Invalidating the
	# generation first makes already-queued timer callbacks harmless.
	_generation += 1
	_selection_active = false
	if _confirm_timer != null:
		_confirm_timer.stop()
	if _confirmation_callback.is_valid() and _confirm_timer != null \
		and _confirm_timer.timeout.is_connected(_confirmation_callback):
		_confirm_timer.timeout.disconnect(_confirmation_callback)
	_confirmation_callback = Callable()
	if not spec.is_empty():
		super.leave()
	session_id = ""
	host_authority = false
	_host_confirmed = false
	_revision = 0
	_remote_snapshot_received = false
	_remote_confirmed = false
	_cancel_held = false


func _attach_confirmation_callback() -> void:
	if _confirmation_callback.is_valid() and _confirm_timer.timeout.is_connected(_confirmation_callback):
		_confirm_timer.timeout.disconnect(_confirmation_callback)
	_confirmation_callback = Callable(self, "_on_confirmation_timeout").bind(_generation, session_id)
	_confirm_timer.timeout.connect(_confirmation_callback)


func _on_confirmation_timeout(expected_generation: int, expected_session_id: String) -> void:
	if not _selection_active or not host_authority or _host_confirmed or not visible or enabled:
		return
	if expected_generation != _generation or expected_session_id != session_id:
		return
	_host_confirmed = true
	_advance_revision_and_emit(true)
	if not _selection_active:
		return
	var stage_id := selected_stage()
	selection_confirmed.emit(stage_id, session_id, _revision)


func _finish_confirmation() -> void:
	# Replaced in _ready(); retaining this override prevents the base-class
	# unbound callback from emitting a confirmation outside the session guard.
	pass


func _on_base_cancelled() -> void:
	if not _selection_active or not host_authority:
		return
	var cancelled_session_id := session_id
	end_selection()
	selection_cancelled.emit(cancelled_session_id)


func _advance_revision_and_emit(confirmed_state: bool) -> void:
	if _revision >= MAX_REVISION:
		var cancelled_session_id := session_id
		end_selection()
		selection_cancelled.emit(cancelled_session_id)
		return
	_revision += 1
	_emit_snapshot(confirmed_state)


func _emit_snapshot(confirmed_state: bool) -> void:
	if not _selection_active or not host_authority:
		return
	snapshot_changed.emit({
		"version": SNAPSHOT_VERSION,
		"sessionId": session_id,
		"revision": _revision,
		"stageId": selected_stage(),
		"confirmed": confirmed_state,
	})


func _find_stage_index(stage_id: String) -> int:
	var cards: Variant = spec.get("cards", [])
	if not cards is Array:
		return -1
	for index in cards.size():
		var card: Variant = cards[index]
		if card is Dictionary and card.get("id") is String and str(card.id) == stage_id:
			return index
	return -1


func _select_stage(stage_id: String) -> bool:
	var index := _find_stage_index(stage_id)
	if index < 0:
		return false
	var card: Dictionary = spec.cards[index]
	var grid: Array = card.get("grid", [])
	if grid.size() != 2:
		return false
	return _select_grid(Vector2i(int(grid[0]), int(grid[1])))


func _is_wire_integer(value: Variant) -> bool:
	if value is int:
		return true
	return value is float and is_finite(value) and value == floor(value)
