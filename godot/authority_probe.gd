extends RefCounted

const Selection = preload("res://authority_host_selection.gd")
const Battle = preload("res://rollback_battle.gd")
const Queue = preload("res://authority_input_queue.gd")
var cancelled := false

func run(game: Node, visible: Callable) -> Dictionary:
	var battle := Battle.new()
	var problem := battle.configure(game, false)
	if not problem.is_empty(): return {}
	game.set_meta("authority_probe", true)
	game.naruto.energy = 300.0
	game.ichigo.energy = 300.0
	var samples: Array[int] = []
	var stalls := 0
	var all_visible := true
	var last_wall := Time.get_ticks_msec()
	for frame in range(1, 241):
		if cancelled or not is_instance_valid(game):
			if is_instance_valid(game): battle.close()
			return {}
		var players := {"p1": Queue.neutral(), "p2": Queue.neutral()}
		if frame > 120:
			var phase := (frame - 121) % 60
			players.p1.right = phase < 15
			players.p2.left = phase < 15
			players.p1.attack = phase >= 20 and phase < 23
			players.p1.special = phase >= 35 and phase < 38
			players.p2.summon = phase >= 45 and phase < 48
		var skip := frame >= 30 and frame < 90
		var events := []
		if game.battle_intro.polling and frame % 15 == 0 and not (skip and game.battle_intro.step > 1 and game.battle_intro.step < 4):
			events.append({"kind": "intro_poll", "phase": "after_actor_advance", "sequence": frame, "time_ms": frame * 33})
		problem = battle.set_frame_events(frame, frame * 33, skip, events)
		if not problem.is_empty(): break
		var started := Time.get_ticks_usec()
		problem = battle.advance(frame, players)
		var elapsed := Time.get_ticks_usec() - started
		if not problem.is_empty(): break
		if frame > 120:
			samples.append(maxi(1, elapsed))
			all_visible = all_visible and bool(visible.call())
			var now := Time.get_ticks_msec()
			if now - last_wall > 100: stalls += 1
			last_wall = now
			await game.get_tree().physics_frame
		elif frame == 120:
			await game.get_tree().physics_frame
			last_wall = Time.get_ticks_msec()
	battle.close()
	if samples.size() != Selection.SAMPLE_COUNT: return {}
	samples.sort()
	return {"profile": Selection.PROFILE, "samples": samples.size(), "visible": all_visible,
		"p95_us": samples[ceili(samples.size() * 0.95) - 1], "long_stalls": stalls}
