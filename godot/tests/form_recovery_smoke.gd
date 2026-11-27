extends SceneTree

const Fixture = preload("res://tests/rollback_fixture.gd")
const Inputs = preload("res://authority_input_queue.gd")


func _initialize() -> void:
	_run.call_deferred()


func _run() -> void:
	var catalog: Dictionary = JSON.parse_string(FileAccess.get_file_as_string(FighterSelection.CATALOG_PATH))
	var passed := 0
	var failed := 0
	for fighter_name: String in catalog.fighters:
		var directory := FighterSelection.directory(catalog.fighters[fighter_name])
		var manifest_path := directory.path_join("form_profiles.json")
		if not FileAccess.file_exists(manifest_path):
			continue
		var manifest: Dictionary = JSON.parse_string(FileAccess.get_file_as_string(manifest_path))
		for slot in ["p1", "p2"]:
			var names := [fighter_name, "迪达拉"] if slot == "p1" else ["迪达拉", fighter_name]
			var fixture := Fixture.create(self, names, ["松本", "夜一"], "流魂街")
			for parent_frame in range(2, manifest.profiles.size() + 2):
				var target: String = manifest.profiles[str(parent_frame)].directory
				if not _transform_and_attack(fixture, slot, target):
					failed += 1
					break
				passed += 1
				print("FORM_RECOVERED ", target.get_file(), " ", slot)
			Fixture.dispose(fixture.game, fixture.battle)
			await process_frame
	assert(await preload("res://tests/audio_shutdown.gd").drain(self))
	print("FORM_RECOVERY_RESULT passed=%d failed=%d" % [passed, failed])
	quit(0 if failed == 0 and passed > 0 else 1)


func _transform_and_attack(fixture: Dictionary, slot: String, target: String) -> bool:
	var game: Node = fixture.game
	var fighter: FighterRuntime = game.naruto if slot == "p1" else game.ichigo
	var transform_step := -1
	var saw_pause := false
	var attack_sent := false
	var attacked := {"p1": false, "p2": false}
	for step in 900:
		var players := {"p1": Inputs.neutral(), "p2": Inputs.neutral()}
		if transform_step < 0 and not game.battle_intro.active and fighter.action == "站立":
			fighter.energy = 300
			transform_step = step
		if transform_step >= 0 and step < transform_step + 4:
			players[slot].attack = true
			players[slot].jump = true
		elif fighter.source_body_available and fighter.fighter_directory == target and fighter.action == "站立" \
				and saw_pause and not game.super_runtime.zhanting and not game.super_presentation.black_overlay_visible():
			players.p1.attack = true
			players.p2.attack = true
			attack_sent = true
		var tick: int = game.physics_tick + 1
		var callbacks := []
		if game.battle_intro.polling and tick % 15 == 0:
			callbacks.append({"kind": "intro_poll", "phase": "after_actor_advance", "sequence": tick, "time_ms": tick * 33})
		assert(fixture.battle.set_frame_events(tick, tick * 33, false, callbacks).is_empty())
		assert(fixture.battle.advance(tick, players).is_empty())
		if transform_step >= 0 and game.super_runtime.zhanting and game.super_presentation.black_overlay_visible():
			saw_pause = true
		if attack_sent:
			attacked.p1 = attacked.p1 or game.naruto.action == "砍1"
			attacked.p2 = attacked.p2 or game.ichigo.action == "砍1"
			if attacked.p1 and attacked.p2:
				return true
	push_error("Form recovery failed for %s %s: directory=%s action=%s frame=%d paused=%s attacks=%s" % [
		target, slot, fighter.fighter_directory, fighter.action, fighter.current_source_frame(), game.super_runtime.zhanting, attacked])
	return false
