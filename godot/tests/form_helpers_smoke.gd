extends SceneTree

var events: Array = []


class Context extends AiBodyContext:
	var observations: Array
	func goto_label(label: String, play: bool) -> void:
		observations.append(["goto", label, play])
	func play_body() -> void:
		observations.append(["play"])


func effect(operation: String, arguments: Array) -> Variant:
	events.append([operation, arguments])
	return false if operation == "_parent.nextFrame()" else null


func _initialize() -> void:
	_run.call_deferred()


func _run() -> void:
	var directory := "res://tests/fixtures/form_helpers"
	var fixtures: Array = JSON.parse_string(FileAccess.get_file_as_string(directory.path_join("sources.json")))
	var native_rows: Array = JSON.parse_string(FileAccess.get_file_as_string("res://../evidence/importer-loud-fail/r11/form-helpers/observations.json"))
	var checked := 0
	var native_compared := 0
	for fixture: Dictionary in fixtures:
		var native: Dictionary = {}
		for row: Dictionary in native_rows:
			if row.fighter == str(fixture.fighter).to_lower():
				for observation: Dictionary in row.events:
					native[observation.key] = observation.value
		assert(native.size() == 5)
		var fighter := FighterRuntime.new()
		fighter.max_health = 1000
		fighter.source_parent_values = {"万解": false}
		fighter.ai_source_state.values = {"wudi": true}
		fighter.health = 671
		fighter.energy = 234
		var intervals := SourceRootIntervals.new()
		intervals.recorded = true
		root.add_child(intervals)
		var root_values := {"root_y": 17, "maxhp": 1000, "difficulty": 3}
		var root_keys := ["w", "s", "a", "d", "j", "k", "l", "u", "i", "o", "上箭", "下箭", "左箭", "右箭", "N1", "N2", "N3", "N4", "N5", "N6"]
		for index in root_keys.size():
			root_values["key:" + root_keys[index]] = 91 + index
		var form := SourceFormContext.new(fighter, intervals, root_values, "p2", effect)
		var context := Context.new(fighter)
		context._scalar_fields = PackedStringArray(fixture.metadata.scalar_fields)
		context.form_context = form
		context.use_ai = null
		context.observations = events
		var body: RefCounted = load(directory.path_join(fixture.script)).new({})
		body.adapter = context
		fighter.source_body = body
		events.clear()
		body.wankai()
		assert(fighter.read_parent_field("万解") == true)
		assert(form.transfer == {"hp": 671.0, "ql": 234.0})
		assert(root_values.root_y == 17 and intervals.pending_count() == 0)
		assert(events == [["_parent.nextFrame()", []]])
		# Compare the helper-owned prefix; native's two following undefined body
		# fields require the full replacement consumer and are not fabricated here.
		var before: PackedStringArray = str(native.after_call).split(",")
		assert(Array(before.slice(0, 4)) == [str(fighter.read_parent_field("万解")), str(int(form.transfer.hp)), str(int(form.transfer.ql)), str(root_values.root_y)])
		native_compared += 1
		# This exercises actual transfer/init helpers, not a complete profile swap.
		# Boundary effects above are recorded and cannot publish a playable form.
		fighter.health = 1
		fighter.energy = 2
		body.doWanKai()
		assert(fighter.health == 671 and fighter.energy == 234)
		var after: PackedStringArray = str(native.after_replace).split(",")
		# minren/yihu target frame continuation additionally changes root_y to12;
		# that is recorded native evidence, outside this transfer helper fixture.
		assert([after[0], after[1], after[2], after[4], after[5]] == [str(fighter.read_parent_field("万解")), str(int(form.transfer.hp)), str(int(form.transfer.ql)), str(int(fighter.health)), str(int(fighter.energy))])
		native_compared += 1
		var body_keys := ["上", "下", "左", "右", "斩", "跳", "冲", "招", "必杀", "换"]
		var observed_keys := PackedStringArray()
		for index in body_keys.size():
			assert(fighter.ai_source_state.values[body_keys[index]] == 101 + index)
			observed_keys.append(str(fighter.ai_source_state.values[body_keys[index]]))
		assert(",".join(observed_keys) == native.keys)
		assert(native.interval == "undefined" and not intervals.handles.has("feiint"))
		native_compared += 2
		assert(events.slice(1) == [["trace", ["p2"]], ["goto", "开场", false], ["play"]])
		# A false transform flag still calls initCtrl; undefined useAI returns
		# before touching either controller or registering the AI interval.
		fighter.write_parent_field("万解", false)
		events.clear()
		body.doWanKai()
		assert(events.is_empty())
		context.use_ai = false
		body.initCtrl()
		assert(events == [["trace", ["initCtrl: false"]], ["_parent.updateGJL()", []],
			["_root.game[\"p\" + pn].updateGJL()", []], ["AImain.gotoAndStop(1)", []], ["AImain.unloadMovie()", []]])
		# Root handle assignment creates distinct registrations; initCtrl does not
		# clear the previous airanset registration when overwriting its field.
		context.use_ai = true
		events.clear()
		body.initCtrl()
		var first: int = intervals.handles.airanset
		body.initCtrl()
		var second: int = intervals.handles.airanset
		assert(first != second and intervals.pending_count() == 2)
		fighter.source_random = SourceRandom.new()
		var tape := []
		for index in 5:
			tape.append({"site": str(fixture.metadata.source_swf).trim_prefix("game/").trim_suffix(".swf") + "#" + fixture.metadata.path + ":" + str(index + 2), "value": (index + 1) * 0.1})
		assert(fighter.source_random.use_recorded_tape(tape))
		assert(intervals.fire_recorded(first))
		assert(fighter.source_random.failure.is_empty())
		for index in 5:
			assert(is_equal_approx(float(fighter.ai_source_state.values[["attran", "defran", "goran", "jumpran", "bisharan"][index]]), float((index + 1) * 30)))
		assert(intervals.clear_interval("airanset"))
		assert(intervals.pending_count() == 1 and intervals.handles.airanset == second)
		intervals.clear()
		# Clearing a feiint handle only cancels that ID, not another root slot.
		fighter.ai_source_state.values["wudi"] = false
		body.wankai()
		var old: int = intervals.handles.feiint
		var other := intervals.assign_interval("feiint2", Callable(body, "feixue"), 1000)
		body.wankai()
		assert(not intervals.fire_recorded(old))
		assert(intervals.pending_count() == 2)
		fighter.root_zhanting = false
		fighter.health = 671
		assert(intervals.fire_recorded(other) and fighter.health == 661)
		var snapshot := intervals.save_state(func(target: Object) -> String: return "body" if target == body else "")
		assert(not snapshot.has("error"))
		var broken := snapshot.duplicate(true)
		broken.root_handles.feiint = -1
		assert(not intervals.load_state(broken, func(_key: String) -> Object: return body).is_empty())
		assert(intervals.handles.feiint == snapshot.root_handles.feiint)
		intervals.clear()
		assert(intervals.load_state(snapshot, func(_key: String) -> Object: return body).is_empty())
		assert(intervals.pending_count() == 2)
		intervals.clear()
		fighter.source_body = null
		intervals.free()
		fighter.free()
		checked += 1
	print("FORM_HELPERS_SMOKE_OK ", checked, "/", fixtures.size(), " source helper sets; ", native_compared, "/28 native helper observations; full profile replacement not asserted")
	quit()
