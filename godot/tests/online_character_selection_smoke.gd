extends SceneTree

const Adapter = preload("res://online_character_selection.gd")

const SESSION := "selection-round-1"


class FakePeer extends RefCounted:
	var remote: OnlineCharacterSelectionAdapter
	var pending: Array[Dictionary] = []

	func send_snapshot(snapshot: Dictionary) -> void:
		if remote == null or not remote.apply_remote_snapshot(snapshot):
			pending.append(snapshot.duplicate(true))

	func flush() -> void:
		var queued := pending
		pending = []
		for snapshot in queued:
			var accepted := remote != null and remote.apply_remote_snapshot(snapshot)
			if not accepted:
				pending.append(snapshot)


func _initialize() -> void:
	call_deferred("_run")


func _run() -> void:
	var p1 := Adapter.new()
	var p2 := Adapter.new()
	root.add_child(p1)
	root.add_child(p2)
	await process_frame

	var p1_to_p2 := FakePeer.new()
	var p2_to_p1 := FakePeer.new()
	p1_to_p2.remote = p2
	p2_to_p1.remote = p1
	p1.snapshot_changed.connect(p1_to_p2.send_snapshot)
	p2.snapshot_changed.connect(p2_to_p1.send_snapshot)
	var p1_completed: Array[Dictionary] = []
	var p2_completed: Array[Dictionary] = []
	var offline_confirmed := [0, 0]
	p1.selection_completed.connect(func(choice: Dictionary) -> void: p1_completed.append(choice))
	p2.selection_completed.connect(func(choice: Dictionary) -> void: p2_completed.append(choice))
	p1.confirmed.connect(func(_fighters: Array, _helpers: Array) -> void: offline_confirmed[0] += 1)
	p2.confirmed.connect(func(_fighters: Array, _helpers: Array) -> void: offline_confirmed[1] += 1)

	assert(p1.begin(0, SESSION) == "")
	assert(p2.begin(1, SESSION) == "")
	assert(p1 is CharacterSelection and p2 is CharacterSelection,
		"Online adapter stopped reusing the source selector view")
	assert(p1.visible and p2.visible and p1._cards.size() == p1.cards.size()
		and p1._cursors.size() == 2 and p1._wipe != null,
		"Online entry did not construct the inherited character-selection view")
	p1_to_p2.flush()
	p2_to_p1.flush()
	var original_remote_fighter := p1._resource_id("fighters", str(p1.fighters[1]))
	var mismatched_fighter := ""
	for fighter_id in p1.available.fighters.values():
		if str(fighter_id) != original_remote_fighter:
			mismatched_fighter = str(fighter_id)
			break
	var helper_id := str(p1.available.helpers.values()[0])
	assert(not mismatched_fighter.is_empty() and not helper_id.is_empty())
	assert(p1.apply_remote_snapshot({
		"version": 1, "sessionId": SESSION, "revision": 0, "phase": "helper",
		"choice": {"fighter": mismatched_fighter, "helper": helper_id}, "confirmed": true,
	}), "A future helper snapshot should be buffered until fighter confirmation")
	assert(p1.enabled == [true, false], "P1 adapter exposed input for the remote slot")
	assert(p2.enabled == [false, true], "P2 adapter exposed input for the remote slot")
	assert(p1.phase == 0 and p2.phase == 0)

	var p1_fighter_before := str(p1.fighters[0])
	var p1_remote_before := str(p1.fighters[1])
	p1.repeats[0] = int(p1.spec.repeat_frames) - 1
	p1.tick_local({"right": true})
	p1_to_p2.flush()
	assert(str(p1.fighters[0]) != p1_fighter_before, "Local P1 menu input did not move its own fighter")
	assert(str(p1.fighters[1]) == p1_remote_before, "Local P1 menu input moved the remote fighter")
	assert(str(p2.fighters[0]) == str(p1.fighters[0]), "Fake peer did not apply the P1 snapshot")
	var p2_fighter_before := str(p2.fighters[1])
	var p2_remote_before := str(p2.fighters[0])
	p2.repeats[1] = int(p2.spec.repeat_frames) - 1
	p2.tick_local({"right": true})
	p2_to_p1.flush()
	assert(str(p2.fighters[1]) != p2_fighter_before, "Local P2 menu input did not map P1 keys to its own slot")
	assert(str(p2.fighters[0]) == p2_remote_before, "Local P2 menu input moved the remote fighter")
	assert(str(p1.fighters[1]) == str(p2.fighters[1]), "Fake peer did not apply the P2 snapshot")

	# Hold the P2 fighter confirmation so the faster P1 cannot enter the helper phase alone.
	_confirm(p1)
	await create_timer(float(p1.spec.confirm_delay_ms) / 1000.0 + 0.05).timeout
	p1_to_p2.flush()
	p2_to_p1.flush()
	assert(p1.phase == 0 and p2.phase == 0, "Fighter phase advanced before both confirmations")
	_confirm(p2)
	await create_timer(float(p2.spec.confirm_delay_ms) / 1000.0 + 0.05).timeout
	p1_to_p2.flush()
	p2_to_p1.flush()
	assert(p1.phase == 1 and p2.phase == 1, "Both fighter confirmations did not advance to helpers")
	assert(not str(p1.helpers[0]).is_empty() and not str(p2.helpers[1]).is_empty(), "Helper phase did not choose defaults")
	assert(p1.enabled == [true, false] and p2.enabled == [false, true])
	assert(str(p1.helpers[1]) == str(p2.helpers[1]), "Mismatched future helper snapshot overrode the confirmed fighter")
	var changed_fighter_snapshot := {
		"version": 1, "sessionId": SESSION, "revision": int(p1._remote_revisions["fighter"]) + 100,
		"phase": "fighter", "choice": {"fighter": mismatched_fighter, "helper": ""}, "confirmed": true,
	}
	assert(not p1.apply_remote_snapshot(changed_fighter_snapshot), "A remote peer changed its fighter after confirmation")
	var p1_helper_before_move := str(p1.helpers[0])
	var p2_helper_before_move := str(p2.helpers[1])
	p1.repeats[0] = int(p1.spec.repeat_frames) - 1
	p1.tick_local({"right": true})
	p1_to_p2.flush()
	assert(str(p1.helpers[0]) != p1_helper_before_move, "P1 could not reselect its helper")
	assert(str(p1.helpers[1]) == str(p2.helpers[1]), "P1 helper input changed the remote helper")
	p2.repeats[1] = int(p2.spec.repeat_frames) - 1
	p2.tick_local({"right": true})
	p2_to_p1.flush()
	assert(str(p2.helpers[1]) != p2_helper_before_move, "P2 could not reselect its helper")
	assert(str(p2.helpers[0]) == str(p1.helpers[0]), "P2 helper input changed the remote helper")

	_confirm(p2)
	await create_timer(float(p1.spec.confirm_delay_ms) / 1000.0 + 0.05).timeout
	p1_to_p2.flush()
	p2_to_p1.flush()
	assert(p1._remote_confirmed["helper"], "The faster peer's confirmed helper choice was not recorded")
	var confirmed_choice: Dictionary = p1._remote_snapshots["helper"]["choice"].duplicate()
	var previous_helper := p1._resource_id("helpers", p2_helper_before_move)
	assert(not previous_helper.is_empty() and previous_helper != confirmed_choice.helper)
	var changed_helper_snapshot := {
		"version": 1, "sessionId": SESSION, "revision": int(p1._remote_revisions["helper"]) + 1,
		"phase": "helper", "choice": {"fighter": confirmed_choice.fighter, "helper": previous_helper},
		"confirmed": true,
	}
	assert(not p1.apply_remote_snapshot(changed_helper_snapshot), "A remote peer changed its helper after confirmation")
	_confirm(p1)
	await create_timer(float(p1.spec.confirm_delay_ms) / 1000.0 + 0.05).timeout
	p1_to_p2.flush()
	p2_to_p1.flush()
	assert(p1_completed.size() == 1 and p2_completed.size() == 1, "Final choices were not emitted")
	assert(p1_completed[0].fighter == str(p1.available.fighters[p1.fighters[0]])
		and p1_completed[0].helper == str(p1.available.helpers[p1.helpers[0]]), "Completion did not use service resource IDs")
	assert(offline_confirmed == [0, 0], "Online selector emitted the offline confirmed signal")
	assert(not p1.visible and not p2.visible, "Completed selection should return to room controls")
	print("ONLINE_CHARACTER_SELECTION_SMOKE_OK local_slots=true phase_barrier=true helper_phase=true choice_freeze=true buffered_phase_validation=true service_ids=true offline_chain_isolated=true")

	# A reselect starts a distinct session; a stale message from the previous round is ignored.
	var stale: Dictionary = {
		"version": 1, "sessionId": SESSION, "revision": 999, "phase": "helper",
		"choice": p1_completed[0], "confirmed": true,
	}
	assert(p1.begin(0, "selection-round-2", [p1_completed[0], p2_completed[0]]) == "")
	assert(p2.begin(1, "selection-round-2", [p1_completed[0], p2_completed[0]]) == "")
	p1_to_p2.flush()
	p2_to_p1.flush()
	assert(not p2.apply_remote_snapshot(stale), "Previous selection session snapshot was accepted")
	var cancel_count := [0]
	p1.selection_cancelled.connect(func() -> void: cancel_count[0] += 1)
	p1.tick_local({"back": true})
	assert(cancel_count[0] == 1 and p1_completed.size() == 1, "Cancelling a reselect submitted another final choice")
	print("ONLINE_CHARACTER_SELECTION_RESELECT_SMOKE_OK stale_session_rejected=true cancel_keeps_choice=true")

	# Re-entry must stop the previous confirmation timer before assigning a new session.
	var next_session_snapshots: Array[Dictionary] = []
	p1.snapshot_changed.connect(func(snapshot: Dictionary) -> void:
		if str(snapshot.get("sessionId", "")) == "selection-round-4":
			next_session_snapshots.append(snapshot)
	)
	assert(p1.begin(0, "selection-round-3") == "")
	_confirm(p1)
	assert(p1._timers[0].time_left > 0.0, "Confirmation did not start its local delay")
	assert(p1.begin(0, "selection-round-4") == "")
	await create_timer(float(p1.spec.confirm_delay_ms) / 1000.0 + 0.05).timeout
	assert(p1.phase == 0 and not p1._local_confirmed.fighter,
		"A previous session's confirmation timer advanced a new selection")
	assert(next_session_snapshots.size() == 1 and not bool(next_session_snapshots[0].confirmed),
		"A previous confirmation timer published into the new session")

	# Explicit Lobby teardown is not player cancellation and closes the snapshot path.
	var late_remote_snapshot := {
		"version": 1, "sessionId": "selection-round-4", "revision": 100,
		"phase": "fighter", "choice": p2_completed[0], "confirmed": true,
	}
	p1.end_selection()
	assert(not p1.visible and not p1.apply_remote_snapshot(late_remote_snapshot),
		"A snapshot arriving after external teardown was accepted")
	assert(cancel_count[0] == 1, "External teardown emitted a player cancellation")
	assert(p1.begin(0, "selection-round-5") == "", "Adapter could not re-enter after external teardown")
	assert(p1.selection_session_id == "selection-round-5" and p1.phase == 0)
	print("ONLINE_CHARACTER_SELECTION_LIFECYCLE_SMOKE_OK pending_timer_stopped=true teardown_rejects_late_snapshot=true reentry=true")
	await _test_source_helper_exclusion()
	for adapter in [p1, p2]:
		adapter.end_selection()
		for sound in adapter._sounds:
			sound.stop()
		adapter.queue_free()
	await process_frame
	await process_frame
	quit(0)


func _confirm(adapter: OnlineCharacterSelectionAdapter) -> void:
	adapter.repeats[adapter.local_slot] = int(adapter.spec.repeat_frames) - 1
	adapter.tick_local({"confirm": true})


func _test_source_helper_exclusion() -> void:
	var adapter := Adapter.new()
	root.add_child(adapter)
	await process_frame
	var fighter_resource := str(adapter.available.fighters.values()[0])
	var fighter_display := adapter._display_id("fighters", fighter_resource)
	var helper_resource := str(adapter.available.helpers.values()[0])
	var helper_display := adapter._display_id("helpers", helper_resource)
	assert(not fighter_display.is_empty() and not helper_display.is_empty())
	# Build a temporary catalog collision to exercise the base selector's source
	# rule: a seat cannot choose its current fighter as its helper.
	adapter.available.helpers.erase(helper_display)
	adapter.available.helpers[fighter_display] = helper_resource
	var initial_choice := {"fighter": fighter_resource, "helper": helper_resource}
	assert(adapter.begin(0, "helper-exclusion", [initial_choice, initial_choice]) == "")
	adapter._advance_to_helper_phase()
	assert(adapter.phase == 1)
	assert(str(adapter.helpers[0]) != fighter_display,
		"Transition restored an old helper that equals the newly selected fighter")
	assert(adapter.apply_remote_snapshot({
		"version": 1,
		"sessionId": "helper-exclusion",
		"revision": 0,
		"phase": "helper",
		"choice": {"fighter": fighter_resource, "helper": helper_resource},
		"confirmed": false,
	}) == false, "A helper snapshot bypassed the original fighter/helper exclusion")
	adapter.end_selection()
	for sound in adapter._sounds:
		sound.stop()
	adapter.queue_free()
	await process_frame
	print("ONLINE_CHARACTER_SELECTION_SOURCE_RULE_SMOKE_OK same_fighter_helper_rejected=true invalid_old_helper_not_restored=true")
