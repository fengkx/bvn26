extends RefCounted

static var enabled := false
static var stack: Array[Dictionary] = []
static var totals := {}
static var display_spans: Array = []
static var advance_total_us := 0
static var materialize_in_advance_us := 0

static func begin(kind: String, now: int = -1) -> void:
	if not enabled: return
	stack.append({"kind": kind, "start": Time.get_ticks_usec() if now < 0 else now, "children": 0})

static func end(now: int = -1) -> void:
	if not enabled: return
	assert(not stack.is_empty())
	var entry: Dictionary = stack.pop_back()
	var elapsed: int = (Time.get_ticks_usec() if now < 0 else now) - int(entry.start)
	var exclusive: int = elapsed - int(entry.children)
	if entry.kind in ["materialize", "draw"]:
		display_spans.append([entry.start, int(entry.start) + elapsed])
	totals[entry.kind] = int(totals.get(entry.kind, 0)) + exclusive
	if entry.kind == "advance": advance_total_us += elapsed
	if entry.kind == "materialize":
		for ancestor in stack:
			if ancestor.kind == "advance":
				materialize_in_advance_us += exclusive
				break
	if not stack.is_empty(): stack[-1].children += elapsed

static func take() -> Dictionary:
	assert(stack.is_empty())
	var result := {"display_spans_us": display_spans.duplicate(true), "exclusive_us": totals.duplicate(), "advance_total_us": advance_total_us,
		"materialize_in_advance_us": materialize_in_advance_us,
		"simulation_excluding_materialize_us": advance_total_us - materialize_in_advance_us}
	totals.clear()
	display_spans.clear()
	advance_total_us = 0
	materialize_in_advance_us = 0
	return result
