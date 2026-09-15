extends SceneTree

const RETAINED_LIMIT := 4096

func _initialize() -> void:
	_run.call_deferred()


func _run() -> void:
	var random := SourceRandom.new()
	var random_records: Array[Dictionary] = []
	random.value_consumed.connect(func(record: Dictionary) -> void: random_records.append(record))
	random.use_live_random()
	for index in 5000:
		var value: float = random.next_value("live:%d" % index)
		assert(is_finite(value) and value >= 0.0 and value < 1.0)
	assert(random.absolute_index == 5000)
	assert(random.consumed.size() == RETAINED_LIMIT)
	assert(random.live_retained_dropped == 904)
	assert(random.consumed[0]["index"] == 1 and random.consumed[-1]["index"] == 4096)
	var random_replay: Array = [random_records[0].duplicate(true), random_records[1].duplicate(true)]
	random_replay[0]["index"] = 26
	random_replay[1]["index"] = 27
	assert(random.use_recorded_tape(random_replay, 25))
	assert(random.next_value("live:0") == random_replay[0]["value"])
	assert(random.next_value("live:1") == random_replay[1]["value"])
	assert(random.replay_complete())
	assert(random.absolute_index == 27)

	var clock: RefCounted = preload("res://source_clock.gd").new()
	var clock_records: Array[Dictionary] = []
	clock.value_consumed.connect(func(record: Dictionary) -> void: clock_records.append(record))
	for index in 5000:
		assert(clock.read("live:%d" % index) != null)
	assert(clock.absolute_index == 5000)
	assert(clock.consumed.size() == RETAINED_LIMIT)
	assert(clock.live_retained_dropped == 904)
	assert(clock.consumed[0]["index"] == 1 and clock.consumed[-1]["index"] == 4096)
	var clock_replay: Array = [clock_records[0].duplicate(true), clock_records[1].duplicate(true)]
	clock_replay[0]["index"] = 26
	clock_replay[1]["index"] = 27
	assert(clock.use_recorded_tape(clock_replay, 25))
	assert(clock.read("live:0") == clock_replay[0]["value"])
	assert(clock.read("live:1") == clock_replay[1]["value"])
	assert(clock.replay_complete())
	assert(clock.absolute_index == 27)
	print("DIAGNOSTIC_CONSUMER_BOUNDS_OK random=5000/4096+904 clock=5000/4096+904 replay=2")
	quit()
