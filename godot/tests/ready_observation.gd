extends RefCounted

const PHASE := "after_initial_frames_before_deferred_targets"
const STATE_FIELDS := ["hp", "ql", "action", "sw", "touch", "touchFloor", "hits", "paused", "hstm", "hurtSkling"]


static func non_admission() -> Dictionary:
	return {"original_parity_verified": false, "production_admitted": false,
		"native_parity_proven": false, "oracle_accepted": false,
		"certified_global_tick": false, "os_input_join_proven": false}


static func identity_refusal(identity: Dictionary) -> Dictionary:
	var report := {"status": "identity_refused", "report_identity": identity,
		"native_checkpoint": {}}
	report.merge(non_admission())
	return report


# Only one synchronous root-observer batch may supply a checkpoint. IDs refer
# to Godot objects within this run, not native Flash lifetime or global ticks.
static func bind_actors(rows: Array, identities: Dictionary, tick: int) -> Dictionary:
	if rows.size() != 2 or identities.size() != 2 or not identities.has_all(["p1", "p2"]):
		return {"error": "ready_actor_count_mismatch"}
	var by_slot := {}
	for value in rows:
		if not value is Dictionary:
			return {"error": "ready_observation_malformed"}
		var row: Dictionary = value
		var slot: String = row.get("slot", "")
		if not identities.has(slot) or by_slot.has(slot):
			return {"error": "ready_actor_duplicate_or_unknown"}
		if row.get("display_tick") != tick or row.get("observation_phase") != PHASE:
			return {"error": "ready_observation_tick_or_phase_mismatch"}
		if row.get("actor_identity") != identities[slot]:
			return {"error": "ready_actor_identity_mismatch"}
		if not row.get("actual") is Dictionary or not row.actual.has_all(STATE_FIELDS):
			return {"error": "ready_actual_state_missing"}
		if not row.has_all(["frame", "x", "y", "xscale", "pending_frame_actions"]):
			return {"error": "ready_observation_fields_missing"}
		by_slot[slot] = row
	var result := {"error": "", "actors": [], "pending_frame_actions": []}
	for slot in ["p1", "p2"]:
		var row: Dictionary = by_slot[slot]
		var actor: Dictionary = row.actual.duplicate(true)
		for key in ["frame", "x", "y", "xscale"]:
			actor[key] = row[key]
		actor["slot"] = slot
		result.actors.append(actor)
		result.pending_frame_actions.append(row.pending_frame_actions)
	return result
