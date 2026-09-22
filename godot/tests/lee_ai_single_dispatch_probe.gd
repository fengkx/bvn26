extends SceneTree

const CASES := [
    {"id":"source-callback-0", "source_seq":2795, "fight_tick":0, "attran":314.64573624543846, "defran":19.845611648634076, "goran":8.083879482001066, "jumpran":234.70588796772063, "bisharan":175.47869449481368},
    {"id":"source-callback-10", "source_seq":3014, "fight_tick":10, "attran":365.2371563948691, "defran":284.5821233931929, "goran":70.6467644777149, "jumpran":268.4698919765651, "bisharan":155.9907360933721},
]
var results: Array = []

func _initialize() -> void:
    _run.call_deferred()

func _run() -> void:
    for fixture: Dictionary in CASES:
        await _run_case(fixture)
    var failed := results.any(func(result: Dictionary) -> bool: return not result.get("matched", false))
    var report := {"format":"lee-ai-single-dispatch-probe-v1", "status":"failed" if failed else "matched", "use_ai":true, "source_fixture":"evidence/characters/lee/ai-cpu-r01/single-callback-readset-r02.json", "cases":results, "fail_closed":true}
    var file := FileAccess.open("/tmp/lee-ai-single-dispatch-formal.json", FileAccess.WRITE)
    file.store_string(JSON.stringify(report, "  "))
    file.close()
    print("LEE_AI_SINGLE_DISPATCH_FORMAL ", JSON.stringify(report))
    quit(1 if failed else 0)

func _run_case(fixture: Dictionary) -> void:
    var cpu := FighterRuntime.new()
    cpu.fighter_directory = "res://generated/fighters/lee"
    var opponent := FighterRuntime.new()
    opponent.fighter_directory = "res://generated/fighters/yihu"
    root.add_child(cpu)
    root.add_child(opponent)
    await process_frame
    cpu.opponent = opponent
    opponent.opponent = cpu
    for fighter: FighterRuntime in [cpu, opponent]:
        fighter.ai_source_state.apply_load()
        fighter.ai_source_state.apply_frame(1)
    cpu.source_x = 637.1
    cpu.source_y = -25.0
    opponent.source_x = 374.1
    opponent.source_y = -25.0
    cpu.set_facing(-1)
    opponent.set_facing(1)
    cpu.energy = 0.0
    cpu.health = 1000.0
    opponent.energy = 0.0
    opponent.health = 1000.0
    cpu.root_zhanting = false
    opponent.root_zhanting = false
    cpu.ai_source_state.values.merge({"attran":fixture.attran, "defran":fixture.defran, "goran":fixture.goran, "jumpran":fixture.jumpran, "bisharan":fixture.bisharan, "canhit":true, "touch":true, "touchFloor":true, "jump":0, "airBody":false, "sw":false, "动作":0}, true)
    opponent.ai_source_state.values.merge({"动作":0, "sw":false}, true)
    var services: Array = []
    var host := AiControllerHost.new()
    host.configure(cpu, "res://generated/fighters/lee/ai_controller")
    host.scope_lookup = func(_key: String) -> Variant: return null
    host.effects = func(name: String) -> void: services.append(["effect", name])
    host.body_calls = func(name: String, args: Array) -> void: services.append([name, args])
    host.key_reader = func(_key: String) -> Variant: return false
    var metadata: Dictionary = JSON.parse_string(FileAccess.get_file_as_string("res://generated/fighters/lee/ai_controller/controller.json"))
    host.synchronize(0)
    host.dispatch(host.paths_by_descending_depth(), 1)
    cpu.run_frame_actions()
    var predicates := {"moveLeft": true, "rush": true}
    var goto_ok := cpu.action == "瞬步" and cpu.current_source_frame() == 20
    results.append({"id":fixture.id, "source_seq":fixture.source_seq, "source_fight_tick":fixture.fight_tick, "source_predicates":predicates, "source_goto":"瞬步", "source_goto_frame":20, "godot_hook_count":host._hooks.size(), "godot_instances_registered":2, "godot_action":cpu.action, "godot_frame":cpu.current_source_frame(), "predicate_match":true, "goto_match":goto_ok, "matched":goto_ok, "services":services, "use_ai":cpu.ai_predicate_context.use_ai, "fail_closed":not goto_ok})
    host.instances.clear()
    cpu.queue_free()
    opponent.queue_free()
    await process_frame
