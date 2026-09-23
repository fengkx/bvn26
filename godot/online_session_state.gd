extends RefCounted

# Keep local device/render preferences on the existing GameSession instance,
# while retaining every value that can affect an online battle in the graph.
const State = preload("res://simulation_state.gd")
const CAUSAL_FIELDS := ["modo", "maxhp", "maxtime", "p1cpu", "p2cpu", "root_label"]
const LOCAL_FIELDS := ["codes", "render_quality", "source_quality", "keyboard", "store_path", "write_success", "ai_level"]
const IMMUTABLE_FIELDS := ["training_spec"]


static func capture(session: Object) -> Dictionary:
	var known := CAUSAL_FIELDS + LOCAL_FIELDS + IMMUTABLE_FIELDS
	for property in session.get_property_list():
		if property.usage & PROPERTY_USAGE_SCRIPT_VARIABLE and property.name not in known:
			return {"error": "Unaudited GameSession field: " + str(property.name)}
	var causal := {}
	for field in CAUSAL_FIELDS:
		causal[field] = session.get(field)
	var problem := State.validate_value(causal)
	return {"error": problem} if not problem.is_empty() else {"version": 1, "causal": State.canonical(causal)}


static func validate(snapshot: Variant) -> String:
	if not snapshot is Dictionary or snapshot.get("version") != 1 or not snapshot.get("causal") is Dictionary:
		return "Invalid online GameSession state"
	if snapshot.causal.size() != CAUSAL_FIELDS.size():
		return "Incomplete online GameSession state"
	for field in CAUSAL_FIELDS:
		if not snapshot.causal.has(field):
			return "Missing online GameSession field: " + field
	return State.validate_value(snapshot.causal)


static func restore(session: Object, snapshot: Variant) -> String:
	var problem := validate(snapshot)
	if not problem.is_empty():
		return problem
	for field in CAUSAL_FIELDS:
		session.set(field, snapshot.causal[field])
	return ""
