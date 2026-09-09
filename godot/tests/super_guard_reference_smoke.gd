extends SceneTree
var game
var tick := 0
var records: Array = []
var names = ["ichigo_bs", "ichigo_sbs", "ichigo_cbs", "naruto_bs", "naruto_sbs", "naruto_cbs"]
var labels = ["必杀", "上必杀", "超必杀", "必杀", "上必杀", "超必杀"]
func _initialize():
	run.call_deferred()
func observe():
	var ci := tick / 300
	var t := tick % 300
	var a = game.ichigo if ci < 3 else game.naruto
	var b = game.naruto if ci < 3 else game.ichigo
	var key := InputEventKey.new()
	key.keycode = game.session.flash_to_key(int(game.session.codes["s"]))
	key.physical_keycode = key.keycode
	key.pressed = ci < 3
	Input.parse_input_event(key)
	Input.flush_buffered_events()
	if t == 0:
		game.ichigo.ai_random_clock.cancel()
		for field in ["attran", "goran", "jumpran", "bisharan"]: game.ichigo.ai_source_state.values[field] = 500
		game.ichigo.ai_source_state.values["defran"] = 0
		for f in [game.naruto, game.ichigo]:
			f.health = 1000
			f.energy = 300
			f.sw = false
			f.hits = 0
			f.hited = 0
			f.beida = 0
			for field in ["hits", "hited", "beida", "动作"]: f.ai_source_state.values[field] = 0
			f.ai_source_state.values["canhit"] = true
			f.goto_ai_label("站立", true)
		a.position.x = 400
		b.position.x = 450
		a.set_facing(1)
		b.set_facing(-1)
		b.position.y = a.position.y
		b.goto_ai_label("防御2", true)
	if t == 10:
		b.goto_ai_label("防御2", true)
		a.goto_ai_label(labels[ci], true)
	records.append([names[ci], t, a.current_source_frame(), b.current_source_frame(), b.health, b.hits, b.ai_source_state.read_field("动作"), a.position.x, a.position.y, b.position.x, b.position.y, b.root_zhanting])
	tick += 1
	return false
func run():
	game = load("res://main.tscn").instantiate()
	root.add_child(game)
	game.set_physics_process(false)
	game._on_menu_confirmed("vs_com")
	game._on_characters_confirmed(["鸣人", "一护"], ["我爱罗", "魂"])
	game._on_map_confirmed("现世")
	game.ichigo.ai_random_clock.cancel()
	for n in 600:
		game._advance_fight()
		if not game.battle_intro.active: break
	assert(not game.battle_intro.active)
	while tick < 1800:
		game._advance_fight([], observe)
	var passed := compare_reference()
	var args := OS.get_cmdline_user_args()
	if not args.is_empty():
		FileAccess.open(args[0], FileAccess.WRITE).store_string(JSON.stringify(records))
	game._goto_menu()
	game.queue_free()
	await process_frame
	if passed: print("SUPER_GUARD_REFERENCE_SMOKE_OK snapshots=", records.size())
	quit(0 if passed else 1)

func compare_reference() -> bool:
	var path := ProjectSettings.globalize_path("res://../evidence/combat/super-guard-observation/original.log")
	var expected: Array = []
	for line in FileAccess.get_file_as_string(path).split("\n"):
		if not line.begins_with("SG2|"): continue
		var fields = line.split("|")
		var row: Array = [fields[1]]
		for index in range(2, 12): row.append(float(fields[index]))
		row.append(fields[12] == "true")
		expected.append(row)
	if expected.size() != 1800 or records.size() != expected.size():
		push_error("Incomplete original/native guard trace")
		return false
	for index in expected.size():
		for field in expected[index].size():
			if records[index][field] != expected[index][field]:
				push_error("Guard trace first difference: row %s field %s expected=%s actual=%s" % [index, field, expected[index], records[index]])
				return false
	return true
