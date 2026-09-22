extends SceneTree

var result: Dictionary = {}
var game
var parity_rows: Array = []
var random_phase_log: Array = []
var random_phase: String = "bootstrap"
var input_by_fight_tick: Dictionary = {}
var fight_start_physics: int = -1
var sample_ticks: Dictionary = {}
var pre_ready_refresh_count: int = 0
var pre_ready_random_records: int = 0
var clock_tape: Array = []
var intro_polls: Array = []

func _initialize() -> void:
	_run.call_deferred()

func _run() -> void:
	var args := OS.get_cmdline_user_args()
	if args.size() < 2 or args.size() > 3:
		push_error("Pass random-tape.json, output JSON, and optional clean events.jsonl")
		quit(2)
		return
	var tape: Array = []
	var live := args[0] == "--live"
	var includes_main := false
	if not live:
		tape = JSON.parse_string(FileAccess.get_file_as_string(args[0]))
		includes_main = full_tape_has_main(tape)
	if args.size() == 3:
		_load_clean_events(args[2])
	game = load("res://main.tscn").instantiate()
	root.add_child(game)
	game.set_physics_process(false)
	await process_frame
	game._load_selected_stage("现世")
	game.character_selection.available.fighters["白哉"] = "byakuya"
	game.character_selection.available.helpers["魂"] = "kon"
	# Match the production Vs-Com slot contract: P1 is human and P2 is the
	# character under test.  main.gd binds the CPU driver to `ichigo` by slot.
	game._on_characters_confirmed(["一护", "白哉"], ["魂", "魂"])
	game.source_random.diverged.connect(func(message: String) -> void:
		print("RANDOM_DIVERGENCE phase=%s cursor=%d consumed=%d message=%s" % [random_phase, game.source_random.absolute_index, game.source_random.consumed.size(), message]))
	# The clean native tape begins with one main music consumer. This probe is
	# fighter-AI scoped; retain the original index while leaving that unrelated
	# consumer outside the replay stream rather than synthesizing a draw.
	if not live and includes_main:
		tape = tape.slice(1)
	if not live and not game.source_random.use_recorded_tape(tape, 1 if includes_main else 0):
		push_error("Could not load random tape: " + game.source_random.failure)
		quit(2)
		return
	if not live and not game.source_clock.use_recorded_tape(clock_tape, 0):
		push_error("Could not load clean clock tape: " + game.source_clock.failure)
		quit(2)
		return
	var full_global_tape := not live
	game._enter_current_fight(2)
	game.diagnostic_input_provider = Callable(self, "_input_tape")
	# Reinitialize the existing intro object through its recorded-poll contract,
	# matching intro_continuous_reference rather than toggling the flag after a
	# live begin.
	var intro_fighters: Array[FighterRuntime] = [game.naruto, game.ichigo]
	game.battle_intro.begin(intro_fighters, true)
	# Vs-Com's source random interval is started by _enter_current_fight.  The
	# native tape must be attached to that clock after driver setup, as the
	# existing vs_com_smoke harness does, or no draw can be observed.
	game.ichigo.ai_random_clock.cancel()
	game.ichigo.ai_random_clock.initialize(game.ichigo.ai_source_state, game.source_random, 5, true)
	print("AI_CLOCK_BINDING p1=%s p2=%s p1_sites=%s p2_sites=%s" % [game.naruto.fighter_name, game.ichigo.fighter_name, game.naruto.ai_source_state.spec["random_refresh"]["assignments"], game.ichigo.ai_source_state.spec["random_refresh"]["assignments"]])
	# Replay the source-observed pre-Ready randAI calls, with count derived from
	# the event stream rather than a role-specific constant.
	pre_ready_refresh_count = pre_ready_random_records / 5
	for refresh in pre_ready_refresh_count:
		random_phase = "pre_ready_byakuya_%d" % (refresh + 1)
		var before: int = game.source_random.consumed.size()
		if not game.ichigo.ai_random_clock.fire_recorded(500 + refresh * 500):
			push_error("Byakuya AI random refresh failed at %d" % (refresh + 1))
			quit(2)
			return
		random_phase_log.append({"phase": "pre_ready_byakuya", "refresh": refresh + 1,
			"cursor_before": before, "cursor_after": game.source_random.consumed.size(),
			"tick": -1})
	var intro_ticks := 0
	var states: Array = []
	var ready_poll_trace: Array = []
	while game.battle_intro.active and intro_ticks < 900:
		random_phase = "intro"
		var recorded_events: Array = []
		for poll: Dictionary in intro_polls:
			if int(poll["relative_tick"]) == intro_ticks + 1:
				recorded_events.append({"kind": "intro_poll", "phase": "after_actor_advance",
					"sequence": int(poll["sequence"]), "time_ms": int(poll["time_ms"])})
		if not recorded_events.is_empty():
			print("INTRO_POLL_DELIVER tick=%d events=%s active=%s polling=%s recorded=%s step=%d states=%s frames=[%d,%d] last=%d error=%s pending=%d" % [intro_ticks + 1, recorded_events, game.battle_intro.active, game.battle_intro.polling, game.battle_intro.recorded_polling, game.battle_intro.step, game.battle_intro.states, game.naruto.current_source_frame(), game.ichigo.current_source_frame(), game.battle_intro.last_poll_sequence, game.battle_intro.poll_replay_error, game.battle_intro._pending_frame_actions.size()])
		# Match mode_combat_reference.gd: observe Ready/tick0 from the callback
		# of the advance that closes intro, before any extra actor tick.
		game._advance_fight(recorded_events, func() -> bool:
			if not game.battle_intro.active and states.is_empty():
				_record_state(states, 0)
				ready_poll_trace.append({"intro_ticks": intro_ticks, "states": states.duplicate(true)})
			return false
		)
		intro_ticks += 1
	if game.battle_intro.active:
		push_error("AI tape probe did not reach Ready")
		quit(2)
		return
	fight_start_physics = game.physics_tick
	for tick in 180:
		random_phase = "advance_tick_%d" % (tick + 1)
		var tick_before: int = game.source_random.consumed.size()
		game._advance_fight()
		var tick_after_advance: int = game.source_random.consumed.size()
		_record_state(states, tick + 1)
		if sample_ticks.has(tick + 1):
			random_phase = "post_ready_byakuya_%d" % (tick + 1)
			var byakuya_before: int = game.source_random.consumed.size()
			if not game.ichigo.ai_random_clock.fire_recorded(500 + (tick + 1) * 33):
				push_error("Byakuya AI post-Ready random refresh failed at tick %d cursor %d (advance consumed %d): %s" % [tick + 1, game.source_random.consumed.size(), tick_after_advance - tick_before, game.source_random.failure])
				result = {"status": "random_order_diverged", "failure_tick": tick + 1,
					"intro_ticks": intro_ticks, "ticks_observed": tick + 1,
					"states": states, "parity_rows": parity_rows,
					"random": game.source_random.diagnostic_state(),
					"random_consumed": game.source_random.consumed,
					"random_phase_log": random_phase_log,
					"clock": game.source_clock.diagnostic_state()}
				FileAccess.open(args[1], FileAccess.WRITE).store_string(JSON.stringify(result, "  ") + "\n")
				quit(2)
				return
			random_phase_log.append({"phase": "post_ready_byakuya", "tick": tick + 1,
				"cursor_before": byakuya_before, "cursor_after": game.source_random.consumed.size(),
				"advance_consumed": tick_after_advance - tick_before})
	result = {"status": "completed", "intro_ticks": intro_ticks, "ticks": 180,
		"p1_name": game.naruto.fighter_name, "p2_name": game.ichigo.fighter_name,
		"p2_cpu": game.session.p2cpu, "states": states, "ready_poll_trace": ready_poll_trace,
		"parity_rows": parity_rows,
		"random": game.source_random.diagnostic_state(),
		"random_consumed": game.source_random.consumed,
		"clock": game.source_clock.diagnostic_state()}
	FileAccess.open(args[1], FileAccess.WRITE).store_string(JSON.stringify(result, "  ") + "\n")
	print("BYAKUYA_AI_TAPE_PROBE " + JSON.stringify(result))
	game._goto_menu()
	game.queue_free()
	await process_frame
	quit()

func _load_clean_events(path: String) -> void:
	var poll_events: Array = []
	for line in FileAccess.get_file_as_string(path).split("\n", false):
		var event: Dictionary = JSON.parse_string(line)
		if event.get("kind") == "intro_poll":
			var display_tick := int(event.get("display_tick", -1))
			poll_events.append({"sequence": int(event.get("sequence", -1)),
				"time_ms": int(event.get("time_ms", -1)), "display_tick": display_tick})
		if event.get("kind") == "sample":
			sample_ticks[int(event.get("fight_tick", -1))] = true
		if event.get("kind") == "random" and int(event.get("fight_tick", -1)) < 0 and str(event.get("value", "")).contains("fighter/Byakuya#"):
			pre_ready_random_records += 1
		if event.get("kind") == "clock":
			var values := str(event.get("value", "")).split(",")
			if values.size() == 3:
				clock_tape.append({"index": int(values[0]), "site": values[1], "value": int(values[2])})
		if event.get("kind") != "input_next_display":
			continue
		var tick := int(event.get("fight_tick", -1))
		if tick >= 0:
			input_by_fight_tick[tick] = str(event.get("value", ""))
	for poll: Dictionary in poll_events:
		# Native display tick zero is the fresh intro start in this capture.
		# _advance_fight's first call observes tick one, so display_tick N is
		# delivered on the Nth advance, matching the source callback cadence.
		poll["relative_tick"] = int(poll["display_tick"])
		intro_polls.append(poll)

func full_tape_has_main(tape: Array) -> bool:
	return not tape.is_empty() and str(tape[0].get("site", "")).begins_with("main#")

func _input_tape(slot: String, physics_tick: int) -> Dictionary:
	if slot != "p1" or fight_start_physics < 0:
		return {}
	var fight_tick := physics_tick - fight_start_physics
	var value := str(input_by_fight_tick.get(fight_tick, ""))
	var result := {}
	for item in value.split(",", false):
		var pair := item.split("=")
		if pair.size() == 2 and pair[1] in ["true", "false"]:
			result[pair[0]] = pair[1] == "true"
	return result

func _record_state(states: Array, tick: int) -> void:
	for actor in [game.naruto, game.ichigo]:
		var ai_values := {}
		if actor == game.ichigo:
			for field in ["attran", "defran", "goran", "jumpran", "bisharan"]:
				ai_values[field] = actor.ai_source_state.read_field(field)
		parity_rows.append({"tick": tick, "slot": actor.player_slot, "frame": actor.current_source_frame(),
			"x": actor.source_x, "y": actor.source_y, "xscale": actor.scale.x * 100,
			"action": actor.ai_source_state.read_field("动作"), "hp": actor.health,
			"ql": actor.energy, "sw": actor.sw, "touch": actor.ai_source_state.read_field("touch"),
			"touchFloor": actor.ai_source_state.read_field("touchFloor"), "hits": actor.hits,
			"paused": actor.root_zhanting, "hstm": actor.ai_source_state.read_field("hstm"),
			"hurtSkling": actor.ai_source_state.read_field("hurtSkling"), "ai_values": ai_values})
	states.append({
		"tick": tick,
		"p1_name": game.naruto.fighter_name,
		"p2_name": game.ichigo.fighter_name,
		"p1_frame": game.naruto.current_source_frame(),
		"p2_frame": game.ichigo.current_source_frame(),
		"p1_action": game.naruto.ai_source_state.read_field("动作"),
		"p2_action": game.ichigo.ai_source_state.read_field("动作"),
		"p1_energy": game.naruto.energy,
		"p2_energy": game.ichigo.energy,
		"p1_x": game.naruto.source_x,
		"p2_x": game.ichigo.source_x,
		"p1_y": game.naruto.source_y,
		"p2_y": game.ichigo.source_y,
		"p2_cpu": game.session.p2cpu,
	})
