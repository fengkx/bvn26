extends SceneTree


func _initialize() -> void:
	var voice = preload("res://hurt_voice.gd").new()
	voice.spec = JSON.parse_string(FileAccess.get_file_as_string("res://generated/fighters/minren/hurt_voice.json"))
	var state := AiSourceState.new()
	state.values = {"_lastvoice": 0, "_dievoicen": 0}
	var random := SourceRandom.new()
	var tape: Array = []
	for value in [0.5, 0.6, 0.5]:
		tape.append({"site": voice.spec["probability_site"], "value": value})
	tape.append({"site": voice.spec["selector_site"], "value": 0.99})
	assert(random.use_recorded_tape(tape))
	var clock = preload("res://source_clock.gd").new()
	var sites: Dictionary = voice.spec["clock_sites"]
	assert(clock.use_recorded_tape([
		{"site": sites["death_check"], "value": 999},
		{"site": sites["death_check"], "value": 1000},
		{"site": sites["death_write"], "value": 1001},
		{"site": sites["hurt_check"], "value": 1999},
		{"site": sites["hurt_check"], "value": 2000},
		{"site": sites["hurt_write"], "value": 2003},
	]))
	voice.execute(state, random, 0.5, clock, true)
	assert(voice.last_requested_linkage == "" and random.consumed.is_empty())
	voice.execute(state, random, 0.5, clock, true)
	assert(voice.last_requested_linkage == "voice_die")
	assert(state.read_field("_dievoicen") == 1001 and random.consumed.is_empty())
	voice.execute(state, random, 0.5, clock, false)
	assert(random.consumed.size() == 1 and voice.last_requested_linkage == "")
	voice.execute(state, random, 0.5, clock, false)
	assert(random.consumed.size() == 2 and clock.consumed.size() == 4)
	voice.execute(state, random, 0.5, clock, false)
	assert(random.replay_complete() and voice.last_requested_linkage == "voice_hurt2")
	assert(state.read_field("_lastvoice") == 2003 and clock.replay_complete())
	assert(clock.use_recorded_tape([{"site": "check", "value": 3}]))
	assert(clock.read("wrong") == null and clock.consumed.is_empty())
	assert(clock.read("check") == null)
	assert(not clock.use_recorded_tape([{"site": "check", "value": 0.5}]))
	assert(not clock.use_recorded_tape([{"site": "check", "value": 2}, {"site": "check", "value": 1}]))
	print("HURT_VOICE_SMOKE_OK")
	quit()
