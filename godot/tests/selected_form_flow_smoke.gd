extends SceneTree

const Fixture = preload("res://tests/rollback_fixture.gd")
const Inputs = preload("res://rollback_test_session.gd")
const State = preload("res://simulation_state.gd")


func _initialize() -> void:
	_run.call_deferred()


func _inputs(attack: bool) -> Dictionary:
	var players := {"p1": {}, "p2": {}}
	for slot in players:
		for button in Inputs.BUTTONS:
			players[slot][button] = button == "attack" and attack
	return players


func _run() -> void:
	var available: Dictionary = JSON.parse_string(FileAccess.get_file_as_string(FighterSelection.CATALOG_PATH))
	var checked := 0
	for name in available.fighters:
		var resource_id: String = available.fighters[name]
		if not available.forms.has(resource_id):
			continue
		for selected_slot in [0, 1]:
			var names := ["一护", "日番谷"]
			names[selected_slot] = name
			var fixture := Fixture.create(self, names, ["我爱罗", "魂"], "现世")
			var game: Node = fixture.game
			var battle: RefCounted = fixture.battle
			var actor = game.naruto if selected_slot == 0 else game.ichigo
			assert(actor.fighter_directory == FighterSelection.directory(resource_id))
			assert(actor.source_parent_frame == 2 and not actor.read_parent_field("万解"))
			assert(actor.health == game.session.maxhp and actor.energy == 0)
			assert(not game.source_root_intervals.handles.has("feiint"))
			assert(not game.source_root_intervals.handles.has("feiint2"))
			var ready_tick := -1
			var checkpoint := {}
			var checkpoint_tick := -1
			var final_tick := -1
			var attack_seen := false
			for tick in range(1, 901):
				if not game.battle_intro.active and ready_tick < 0:
					ready_tick = tick
				var callbacks := []
				if game.battle_intro.polling and tick % 15 == 0:
					callbacks.append({"kind": "intro_poll", "phase": "after_actor_advance", "sequence": tick, "time_ms": tick * 33})
				assert(battle.set_frame_events(tick, tick * 33, false, callbacks).is_empty())
				assert(battle.advance(tick, _inputs(ready_tick > 0 and tick < ready_tick + 4)).is_empty())
				attack_seen = attack_seen or actor.action == "砍1"
				if ready_tick > 0 and tick == ready_tick + 5:
					checkpoint = battle.save_state()
					checkpoint_tick = tick
				if ready_tick > 0 and tick == ready_tick + 50:
					final_tick = tick
					break
				if tick % 60 == 0:
					await process_frame
			assert(ready_tick > 0 and attack_seen and not checkpoint.is_empty())
			var expected: Dictionary = battle.save_state()
			assert(battle.load_state(checkpoint).is_empty())
			battle.begin_replay()
			for tick in range(checkpoint_tick + 1, final_tick + 1):
				assert(battle.advance(tick, _inputs(false)).is_empty())
			battle.end_replay()
			assert(State.first_difference(expected, battle.save_state()).is_empty())
			actor.health = 0
			actor.sw = true
			game.ko_timeline.controller.nextfight()
			assert(actor.health == game.session.maxhp and not actor.sw)
			assert(actor.source_parent_frame == 2 and actor.current_source_frame() == 1)
			Fixture.dispose(game, battle)
			await process_frame
			checked += 1
		# VS Com must have only the selected BODY's authored random interval.
		var cpu_fixture := Fixture.create(self, ["一护", name], ["我爱罗", "魂"], "现世")
		cpu_fixture.battle.close()
		cpu_fixture.game._enter_current_fight(2)
		assert(cpu_fixture.game.source_root_intervals.handles.has("airanset"))
		assert(cpu_fixture.game.ichigo.ai_random_clock.registered_ms == -1)
		Fixture.dispose(cpu_fixture.game, cpu_fixture.battle)
		await process_frame
	print("SELECTED_FORM_FLOW_OK slots=%d natural_intro=true attack=true rollback=true next_round=true cpu_interval=true" % checked)
	quit()
