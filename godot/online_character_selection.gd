class_name OnlineCharacterSelectionAdapter
extends CharacterSelection

signal snapshot_changed(snapshot: Dictionary)
signal selection_completed(choice: Dictionary)
signal selection_cancelled

const SNAPSHOT_VERSION := 1
const FIGHTER_PHASE := "fighter"
const HELPER_PHASE := "helper"
const MAX_REVISION := 9_007_199_254_740_991

var independent_selection := false
var local_slot := -1
var selection_session_id := ""

var _selection_active := false
var _next_revision := 0
var _remote_revisions := {FIGHTER_PHASE: -1, HELPER_PHASE: -1}
var _remote_snapshots: Dictionary = {}
var _local_confirmed := {FIGHTER_PHASE: false, HELPER_PHASE: false}
var _remote_confirmed := {FIGHTER_PHASE: false, HELPER_PHASE: false}


func _ready() -> void:
	super._ready()
	# CharacterSelection binds its confirmation timers directly to its offline
	# transition method. Replace only those callbacks on this adapter instance so
	# the source view remains untouched for local play.
	for player in 2:
		var timer := _timers[player]
		var offline_handler := Callable(self, "_finish_confirmation").bind(player)
		if timer.timeout.is_connected(offline_handler):
			timer.timeout.disconnect(offline_handler)
		timer.timeout.connect(_on_local_confirmation_timeout.bind(player))
	mouse_filter = Control.MOUSE_FILTER_IGNORE
	visible = false
	cancelled.connect(_on_view_cancelled)


func begin(slot: int, session_id: String, initial_choices: Array = []) -> String:
	if slot not in [0, 1]:
		return "invalid_local_slot"
	if session_id.is_empty() or session_id.length() > 128:
		return "invalid_selection_session"
	if not initial_choices.is_empty() and initial_choices.size() != 2:
		return "invalid_initial_choices"
	# Stop any prior round before publishing the new session identity so a late
	# confirmation timeout cannot be attributed to the next selection round.
	end_selection()
	local_slot = slot
	selection_session_id = session_id
	_next_revision = 0
	_remote_revisions = {FIGHTER_PHASE: -1, HELPER_PHASE: -1}
	_remote_snapshots.clear()
	_local_confirmed = {FIGHTER_PHASE: false, HELPER_PHASE: false}
	_remote_confirmed = {FIGHTER_PHASE: false, HELPER_PHASE: false}
	mode = 3
	reset(3)
	_selection_active = true
	_set_control_slot()
	if not initial_choices.is_empty():
		for player in 2:
			var choice: Variant = initial_choices[player]
			if not choice is Dictionary:
				continue
			_apply_choice_resource_ids(player, choice)
	_update_view()
	_publish_snapshot(false)
	return ""


func end_selection() -> void:
	# Lobby teardown is not a player cancellation and must reject delayed peer
	# snapshots without emitting selection_cancelled.
	_selection_active = false
	leave()


func tick_local(menu_held: Dictionary) -> void:
	if not _selection_active or not _active:
		return
	var before := _local_choice_resource_ids()
	var p1: Dictionary = menu_held if local_slot == 0 else {}
	var p2: Dictionary = menu_held if local_slot == 1 else {}
	super.tick(p1, p2)
	if not _selection_active:
		return
	if before != _local_choice_resource_ids():
		_publish_snapshot(false)


func apply_remote_snapshot(snapshot: Dictionary) -> bool:
	if not _selection_active or not _active or snapshot.get("version") != SNAPSHOT_VERSION:
		return false
	if str(snapshot.get("sessionId", "")) != selection_session_id:
		return false
	var phase_name := str(snapshot.get("phase", ""))
	if phase_name not in [FIGHTER_PHASE, HELPER_PHASE]:
		return false
	var revision: Variant = snapshot.get("revision")
	if not _is_wire_integer(revision) or int(revision) < 0 or int(revision) > MAX_REVISION:
		return false
	if int(revision) <= int(_remote_revisions[phase_name]):
		return false
	if not snapshot.get("confirmed") is bool:
		return false
	var choice := _normalize_choice(snapshot.get("choice"), phase_name)
	if choice.is_empty():
		return false
	var prior_snapshot: Variant = _remote_snapshots.get(phase_name)
	if bool(_remote_confirmed[phase_name]):
		if not bool(snapshot.confirmed) or not prior_snapshot is Dictionary \
			or choice != _as_dictionary(prior_snapshot.get("choice")):
			return false
	if phase_name == HELPER_PHASE:
		var fighter_snapshot: Variant = _remote_snapshots.get(FIGHTER_PHASE)
		if fighter_snapshot is Dictionary and bool(fighter_snapshot.get("confirmed", false)):
			var fighter_choice := _as_dictionary(fighter_snapshot.get("choice"))
			if str(choice.get("fighter", "")) != str(fighter_choice.get("fighter", "")):
				return false
	_remote_revisions[phase_name] = int(revision)
	_remote_snapshots[phase_name] = {
		"choice": choice,
		"confirmed": bool(snapshot.confirmed),
	}
	if bool(snapshot.confirmed):
		_remote_confirmed[phase_name] = true
		if phase_name == FIGHTER_PHASE:
			_invalidate_mismatched_future_helper(choice)
	if phase_name == _phase_name():
		_apply_remote_choice(choice)
	_maybe_advance_phase()
	return true


func _on_local_confirmation_timeout(player: int) -> void:
	if not _selection_active or not _active or player != local_slot:
		return
	var phase_name := _phase_name()
	_local_confirmed[phase_name] = true
	_publish_snapshot(true)
	_maybe_advance_phase()


func _set_control_slot() -> void:
	enabled = [false, false]
	enabled[local_slot] = true
	var remote_snapshot: Variant = _remote_snapshots.get(_phase_name())
	if remote_snapshot is Dictionary:
		_apply_remote_choice(_as_dictionary(remote_snapshot.get("choice")))


func _maybe_advance_phase() -> void:
	if not _selection_active or not _active:
		return
	var phase_name := _phase_name()
	if not bool(_local_confirmed[phase_name]) or (not independent_selection and not bool(_remote_confirmed[phase_name])):
		return
	if phase == 0:
		_advance_to_helper_phase()
		return
	var choice := _local_choice_resource_ids()
	end_selection()
	selection_completed.emit(choice)


func _advance_to_helper_phase() -> void:
	var local_choice := _local_choice_resource_ids()
	var remote_snapshot: Dictionary = _as_dictionary(_remote_snapshots.get(HELPER_PHASE, {}))
	var remote_fighter: Dictionary = _as_dictionary(_remote_snapshots.get(FIGHTER_PHASE, {}))
	var confirmed_remote_choice := _as_dictionary(remote_fighter.get("choice"))
	_enter_phase(1)
	_local_confirmed[HELPER_PHASE] = false
	if _helper_pair_is_legal(str(local_choice.get("fighter", "")), str(local_choice.get("helper", ""))):
		_apply_choice_resource_ids(local_slot, local_choice)
	var remote_choice := _as_dictionary(remote_snapshot.get("choice"))
	if not remote_snapshot.is_empty() \
		and str(remote_choice.get("fighter", "")) == str(confirmed_remote_choice.get("fighter", "")) \
		and _helper_pair_is_legal(str(remote_choice.get("fighter", "")), str(remote_choice.get("helper", ""))):
		_apply_remote_choice(remote_choice)
	elif not remote_snapshot.is_empty():
		_remote_snapshots.erase(HELPER_PHASE)
		_remote_confirmed[HELPER_PHASE] = false
	_set_control_slot()
	_publish_snapshot(false)


func _invalidate_mismatched_future_helper(fighter_choice: Dictionary) -> void:
	var helper_snapshot: Variant = _remote_snapshots.get(HELPER_PHASE)
	if not helper_snapshot is Dictionary:
		return
	var helper_choice := _as_dictionary(helper_snapshot.get("choice"))
	if str(helper_choice.get("fighter", "")) == str(fighter_choice.get("fighter", "")):
		return
	_remote_snapshots.erase(HELPER_PHASE)
	_remote_confirmed[HELPER_PHASE] = false


func _publish_snapshot(confirmed: bool) -> void:
	if not _selection_active or not _active or local_slot not in [0, 1] or selection_session_id.is_empty():
		return
	if _next_revision > MAX_REVISION:
		_selection_active = false
		selection_cancelled.emit()
		return
	var snapshot := {
		"version": SNAPSHOT_VERSION,
		"sessionId": selection_session_id,
		"revision": _next_revision,
		"phase": _phase_name(),
		"choice": _local_choice_resource_ids(),
		"confirmed": confirmed,
	}
	_next_revision += 1
	snapshot_changed.emit(snapshot)


func _apply_remote_choice(choice: Dictionary) -> void:
	if choice.is_empty():
		return
	var player := 1 - local_slot
	_apply_choice_resource_ids(player, choice)
	var id := str(fighters[player] if phase == 0 else helpers[player])
	for index in cards.size():
		if str(cards[index].get("id", "")) == id:
			selected[player] = index
			break
	enabled[player] = false
	_update_view()


func _apply_choice_resource_ids(player: int, choice: Dictionary) -> void:
	var fighter_id := _display_id("fighters", str(choice.get("fighter", "")))
	var helper_id := _display_id("helpers", str(choice.get("helper", "")))
	if not fighter_id.is_empty():
		fighters[player] = fighter_id
	if not helper_id.is_empty():
		helpers[player] = helper_id
	if phase == 0 and not fighter_id.is_empty():
		_select_display_card(player, fighter_id)
	elif phase == 1 and not helper_id.is_empty():
		_select_display_card(player, helper_id)


func _select_display_card(player: int, display_id: String) -> void:
	for index in cards.size():
		if str(cards[index].get("id", "")) == display_id:
			selected[player] = index
			return


func _local_choice_resource_ids() -> Dictionary:
	return {
		"fighter": _resource_id("fighters", str(fighters[local_slot])) if local_slot in [0, 1] else "",
		"helper": _resource_id("helpers", str(helpers[local_slot])) if local_slot in [0, 1] else "",
	}


func _normalize_choice(value: Variant, phase_name: String) -> Dictionary:
	if not value is Dictionary or not value.get("fighter") is String:
		return {}
	var fighter_display := _display_id("fighters", str(value.fighter))
	if fighter_display.is_empty():
		return {}
	var helper_id := ""
	if phase_name == HELPER_PHASE:
		if not value.get("helper") is String:
			return {}
		helper_id = str(value.helper)
		if _display_id("helpers", helper_id).is_empty():
			return {}
		if not _helper_pair_is_legal(str(value.fighter), helper_id):
			return {}
	elif value.has("helper") and not value.get("helper") is String:
		return {}
	elif value.get("helper", "") != "":
		helper_id = str(value.helper)
		if _display_id("helpers", helper_id).is_empty():
			return {}
	return {"fighter": str(value.fighter), "helper": helper_id}


func _resource_id(kind: String, display_id: String) -> String:
	var roster: Variant = available.get(kind)
	if not roster is Dictionary:
		return ""
	return str(roster.get(display_id, ""))


func _helper_pair_is_legal(fighter_resource_id: String, helper_resource_id: String) -> bool:
	var fighter_display_id := _display_id("fighters", fighter_resource_id)
	var helper_display_id := _display_id("helpers", helper_resource_id)
	return not fighter_display_id.is_empty() and not helper_display_id.is_empty() \
		and fighter_display_id != helper_display_id


func _display_id(kind: String, resource_id: String) -> String:
	var roster: Variant = available.get(kind)
	if not roster is Dictionary or resource_id.is_empty():
		return ""
	for display_id in roster:
		if str(roster[display_id]) == resource_id:
			return str(display_id)
	return ""


func _phase_name() -> String:
	return FIGHTER_PHASE if phase == 0 else HELPER_PHASE


func _is_wire_integer(value: Variant) -> bool:
	if value is int:
		return true
	return value is float and is_finite(value) and value == floor(value)


func _on_view_cancelled() -> void:
	if not _selection_active:
		return
	_selection_active = false
	selection_cancelled.emit()


func _as_dictionary(value: Variant) -> Dictionary:
	return value if value is Dictionary else {}
