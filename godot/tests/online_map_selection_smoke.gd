extends SceneTree

const OnlineMapSelectionAdapterScript := preload("res://online_map_selection.gd")


func _initialize() -> void:
	create_timer(20.0).timeout.connect(func() -> void: quit(1))
	call_deferred("_run")


func _run() -> void:
	var host = OnlineMapSelectionAdapterScript.new()
	root.add_child(host)
	await process_frame
	var stage_catalog: Dictionary = JSON.parse_string(
		FileAccess.get_file_as_string("res://generated/stages/catalog/catalog.json")
	)
	var catalog_ids: Array[String] = []
	for stage: Dictionary in stage_catalog["stages"]:
		catalog_ids.append(str(stage["id"]))
	var selector_ids: Array[String] = []
	for card: Dictionary in host.spec["cards"]:
		selector_ids.append(str(card["id"]))
	catalog_ids.sort()
	selector_ids.sort()
	assert(catalog_ids == selector_ids)
	for stage_id in catalog_ids:
		assert(host.begin("catalog-validation-" + stage_id, true, stage_id) == "")
		assert(host.selected_stage() == stage_id)
	host.end_selection()

	var host_snapshots: Array[Dictionary] = []
	var host_confirmations: Array[Dictionary] = []
	var host_cancellations: Array[String] = []
	host.snapshot_changed.connect(func(snapshot: Dictionary) -> void:
		host_snapshots.append(snapshot.duplicate(true))
	)
	host.selection_confirmed.connect(func(stage_id: String, session_id: String, revision: int) -> void:
		host_confirmations.append({"stageId": stage_id, "sessionId": session_id, "revision": revision})
	)
	host.selection_cancelled.connect(func(session_id: String) -> void:
		host_cancellations.append(session_id)
	)
	assert(host.begin("host-selection-1", true, "现世") == "")
	assert(host.selected_stage() == "现世")
	assert(host_snapshots.size() == 1)
	assert(host_snapshots[0] == {
		"version": 1,
		"sessionId": "host-selection-1",
		"revision": 0,
		"stageId": "现世",
		"confirmed": false,
	})
	assert(host.begin("bad-stage", true, "unknown") == "unknown_stage")
	assert(host.session_id == "host-selection-1")

	var guest = OnlineMapSelectionAdapterScript.new()
	root.add_child(guest)
	await process_frame
	var guest_confirmations: Array[bool] = []
	var guest_snapshots: Array[Dictionary] = []
	var guest_cancellations: Array[String] = []
	guest.selection_confirmed.connect(func(_stage_id: String, _session_id: String, _revision: int) -> void:
		guest_confirmations.append(true)
	)
	guest.snapshot_changed.connect(func(snapshot: Dictionary) -> void:
		guest_snapshots.append(snapshot.duplicate(true))
	)
	guest.selection_cancelled.connect(func(session_id: String) -> void:
		guest_cancellations.append(session_id)
	)
	assert(guest.begin("host-selection-1", false, "现世") == "")
	# map_open may carry the initial revision-zero snapshot.
	assert(guest.apply_remote_snapshot(host_snapshots[0]))
	assert(guest.apply_remote_snapshot({
		"version": 1,
		"sessionId": "host-selection-1",
		"revision": 1,
		"stageId": "流魂街",
		"confirmed": false,
	}))
	assert(guest.selected_stage() == "流魂街")
	assert(not guest.apply_remote_snapshot(host_snapshots[0]))
	assert(not guest.apply_remote_snapshot({
		"version": 1,
		"sessionId": "old-selection",
		"revision": 2,
		"stageId": "双极",
		"confirmed": false,
	}))
	assert(not guest.apply_remote_snapshot({
		"version": 1,
		"sessionId": "host-selection-1",
		"revision": 2,
		"stageId": "missing-stage",
		"confirmed": false,
	}))
	assert(not guest.apply_remote_snapshot({
		"version": 1,
		"sessionId": "host-selection-1",
		"revision": 1.5,
		"stageId": "双极",
		"confirmed": false,
	}))
	guest.tick_local({"left": true, "right": true, "up": true, "down": true, "confirm": true})
	assert(guest.selected_stage() == "流魂街")
	assert(guest_snapshots.is_empty() and guest_confirmations.is_empty())
	guest.tick_local({"back": true})
	guest.tick_local({"back": true})
	assert(guest_cancellations == ["host-selection-1"])
	assert(guest.visible and guest.selected_stage() == "流魂街")
	guest.tick_local({})
	guest.tick_local({"back": true})
	assert(guest_cancellations == ["host-selection-1", "host-selection-1"])

	# The base directional repeat and sparse grid remain the host's control source.
	host.tick_local({"down": true})
	assert(host.selected_stage() == "流魂街")
	assert(host_snapshots.size() == 2)
	assert(host_snapshots[1].revision == 1 and not host_snapshots[1].confirmed)
	guest.end_selection()
	assert(not guest.apply_remote_snapshot(host_snapshots[1]))
	assert(guest.begin("host-selection-1", false, "现世") == "")
	assert(guest.apply_remote_snapshot(host_snapshots[0]))
	assert(guest.apply_remote_snapshot(host_snapshots[1]))
	assert(guest.selected_stage() == "流魂街")

	# A host confirmation publishes once after the source 500 ms delay.
	var host_cancelled_before_confirm := host_cancellations.size()
	for _frame in 5:
		host.tick_local({"confirm": true})
	assert(host_confirmations.is_empty())
	await create_timer(0.15).timeout
	assert(host_confirmations.is_empty())
	await create_timer(0.40).timeout
	assert(host_confirmations.size() == 1)
	assert(host_snapshots.back().confirmed and host_snapshots.back().revision == 2)
	assert(host_confirmations[0] == {"stageId": "流魂街", "sessionId": "host-selection-1", "revision": 2})
	# Even an explicitly replayed current-session timeout cannot confirm twice.
	host._on_confirmation_timeout(host._generation, "host-selection-1")
	assert(host_confirmations.size() == 1)
	assert(host_cancellations.size() == host_cancelled_before_confirm)
	assert(guest.apply_remote_snapshot(host_snapshots.back()))
	assert(guest.selected_stage() == "流魂街")
	assert(not guest.apply_remote_snapshot({
		"version": 1,
		"sessionId": "host-selection-1",
		"revision": 3,
		"stageId": "双极",
		"confirmed": true,
	}))
	guest.tick_local({"down": true, "back": false})
	assert(guest.selected_stage() == "流魂街")
	assert(guest_confirmations.is_empty())

	# Ending and re-entering invalidates the old delayed callback and session.
	host.end_selection()
	assert(not host.apply_remote_snapshot(host_snapshots.back()))
	assert(host.begin("host-selection-3", true, "现世") == "")
	for _frame in 5:
		host.tick_local({"confirm": true})
	assert(host._confirm_timer.time_left > 0.0)
	host.end_selection()
	assert(host.begin("host-selection-4", true, "木叶村") == "")
	await create_timer(0.55).timeout
	assert(host_confirmations.size() == 1)
	assert(host.selected_stage() == "木叶村")

	# If Back is pressed with Confirm on the same source frame, cancellation wins.
	host.end_selection()
	assert(host.begin("host-selection-cancel", true, "现世") == "")
	host.tick_local({"confirm": true, "back": true})
	assert(host_cancellations == ["host-selection-cancel"])
	assert(host_confirmations.size() == 1)
	await create_timer(0.55).timeout
	assert(host_confirmations.size() == 1)
	guest.end_selection()
	host.end_selection()
	guest.queue_free()
	host.queue_free()
	await process_frame
	print("ONLINE_MAP_SELECTION_OK: host-only input, mirrored snapshots, confirmed/cancelled lifecycle, stale-session rejection")
	quit()
