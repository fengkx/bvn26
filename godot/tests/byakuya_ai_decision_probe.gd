extends SceneTree

var cases := [
	{"id":"standing_attack","source_tick":12,"expected_predicate":"nornalhit","expected":true,"attran":75.0,"defran":200.0,"opponent_action":0,"canhit":true},
	{"id":"standing_defence","source_tick":149,"expected_predicate":"defence","expected":true,"attran":200.0,"defran":50.0,"opponent_action":1,"canhit":true}
]
var report := []

func _initialize() -> void:
	_run.call_deferred()

func _run() -> void:
	for fixture in cases:
		await _run_case(fixture)
	var out := {"status":"completed","scope":"single controller decision; no full scene restore","cases":report,
		"read_set": ["x","y","scale_X","xscale","ql","root_paused","opponent_x","opponent_y","opponent_hp","opponent_action","opponent_sw","opponent_helper_action","attran","defran","goran","jumpran","bisharan","canhit","sw","speed","jumpPower","jumped","fall","khit","touch","touchFloor","sensors.kanmian"]}
	var path := "/tmp/byakuya-ai-decision-probe.json"
	var f := FileAccess.open(path, FileAccess.WRITE); f.store_string(JSON.stringify(out,"  ")); f.close()
	print("BYAKUYA_AI_DECISION_PROBE ", JSON.stringify(out))
	quit()

func _run_case(fixture: Dictionary) -> void:
	var cpu := FighterRuntime.new(); cpu.fighter_directory = "res://generated/fighters/byakuya"
	var opp := FighterRuntime.new(); opp.fighter_directory = "res://generated/fighters/yihu"
	root.add_child(cpu); root.add_child(opp); await process_frame
	cpu.opponent = opp; opp.opponent = cpu
	for fighter: FighterRuntime in [cpu,opp]:
		fighter.ai_source_state.apply_load(); fighter.ai_source_state.apply_frame(1)
	cpu.source_x = (421.1 if fixture.id == "standing_attack" else 301.1); cpu.source_y = -25; cpu.set_facing(-1)
	opp.source_x = (374.1 if fixture.id == "standing_attack" else 164.1); opp.source_y = -25; opp.set_facing(1)
	cpu.energy = 0; cpu.health = 1000; opp.health = 1000
	cpu.root_zhanting = false
	cpu.ai_source_state.values.merge({"attran":fixture.attran,"defran":fixture.defran,"goran": (398.28 if fixture.id == "standing_attack" else 264.14),"jumpran":200.0,"bisharan":200.0,"canhit":fixture.canhit,"touchFloor":true,"touch":true,"jumped":0,"fall":0,"khit":0,"speed":5.0,"jumpPower":15.0,"sw":false,"_lastX":637.1},true)
	opp.ai_source_state.values["动作"] = fixture.opponent_action
	opp.ai_source_state.values["sw"] = false
	var services := []
	var host := AiControllerHost.new()
	host.configure(cpu, "res://generated/fighters/byakuya/ai_controller")
	host.scope_lookup = func(key: String) -> Variant: return cpu.ai_source_state.read_field(key) if cpu.ai_source_state.values.has(key) else null
	host.effects = func(name: String) -> void: services.append(["effect", name])
	host.body_calls = func(name: String, args: Array) -> void: services.append([name, args])
	host.key_reader = func(_key: String) -> Variant: return false
	host.synchronize(0)
	host.dispatch(host.paths_by_descending_depth(), 1)
	cpu.run_frame_actions()
	var predicate_script = load("res://generated/fighters/byakuya/ai_controller/predicates.gd")
	var context := {"x":cpu.source_x,"y":cpu.source_y,"scale_X":cpu.facing,"xscale":cpu.scale.x*100.0,"ql":cpu.energy,"root_paused":false,"opponent_x":opp.source_x,"opponent_y":opp.source_y,"opponent_hp":opp.health,"opponent_action":fixture.opponent_action,"opponent_sw":false,"opponent_helper_action":null,"attran":fixture.attran,"defran":fixture.defran,"goran": (398.28 if fixture.id == "standing_attack" else 264.14),"jumpran":200.0,"bisharan":200.0,"canhit":fixture.canhit,"sw":false,"speed":5.0,"jumpPower":15.0,"jumped":0,"fall":0,"khit":0,"touch":true,"touchFloor":true,"sensors":{"kanmian":true},"body_hits":{},"power":{}}
	var predicates = predicate_script.new(context)
	var actual_predicate := bool(predicates.call(fixture.expected_predicate))
	var actual_action := cpu.action
	report.append({"id":fixture.id,"source_tick":fixture.source_tick,"expected_predicate":fixture.expected_predicate,"expected":fixture.expected,"actual_predicate":actual_predicate,"actual_action":actual_action,"actual_frame":cpu.current_source_frame(),"last_event":cpu.last_event,"goto_expected":("砍1" if fixture.id == "standing_attack" else "防御"),"goto_matched":(actual_action == ("砍1" if fixture.id == "standing_attack" else "防御")),"services":services,"matched":actual_predicate == fixture.expected,"source_read_set":"DefineSprite_631/frame_1/DoAction.as#controller predicates"})
	cpu.queue_free(); opp.queue_free(); await process_frame
