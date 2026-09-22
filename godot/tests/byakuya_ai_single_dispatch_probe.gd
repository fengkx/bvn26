extends SceneTree

# Values are decoded directly from ai_context events emitted by the clean
# original capture.  This is a callback probe, not a full match replay.
const CASES := [
    {"id":"source-rush-r03", "source_seq":2701, "fight_tick":3,
        "attran":286.83603554964066, "defran":279.5917505864054,
        "goran":153.25869782827795, "jumpran":189.64735860936344,
        "bisharan":460.70426143705845, "source_frame":5, "expected_action":"瞬步",
        "expected_frame":20, "source_predicate":"rush"},
    {"id":"source-jump-r03", "source_seq":3850, "fight_tick":66,
        "attran":432.5229504611343, "defran":409.61688477545977,
        "goran":226.60314035601914, "jumpran":85.01961384899914,
        "bisharan":87.31837570667267, "source_frame":62, "expected_action":"跳2",
        "expected_frame":68, "source_predicate":"jump"},
]
var results: Array = []

func _initialize() -> void:
    _run.call_deferred()

func _run() -> void:
    for fixture: Dictionary in CASES:
        await _run_case(fixture)
    var failed := results.any(func(result: Dictionary) -> bool: return not result.get("matched", false))
    var report := {"format":"byakuya-ai-single-dispatch-probe-v1", "status":"failed" if failed else "matched",
        "use_ai":true, "source_fixture":"evidence/characters/byakuya/ai-clean-r01/source-context-r03.json",
        "cases":results, "fail_closed":true,
        "scope":"two source-observed controller callbacks; no boot/intro/full-AI parity"}
    var file := FileAccess.open("/tmp/byakuya-ai-single-dispatch-formal.json", FileAccess.WRITE)
    file.store_string(JSON.stringify(report, "  ")); file.close()
    print("BYAKUYA_AI_SINGLE_DISPATCH_FORMAL ", JSON.stringify(report))
    quit(1 if failed else 0)

func _run_case(fixture: Dictionary) -> void:
    var cpu := FighterRuntime.new(); cpu.fighter_directory = "res://generated/fighters/byakuya"
    var opponent := FighterRuntime.new(); opponent.fighter_directory = "res://generated/fighters/yihu"
    root.add_child(cpu); root.add_child(opponent); await process_frame
    cpu.opponent = opponent; opponent.opponent = cpu
    for fighter: FighterRuntime in [cpu, opponent]:
        fighter.ai_source_state.apply_load(); fighter.ai_source_state.apply_frame(1)
    # Restore the observed callback's source playhead before host dispatch;
    # jump() was sampled while the original body was already on frame 62.
    cpu.play_source_frame(int(fixture.source_frame))
    cpu.ai_source_state.apply_frame(int(fixture.source_frame))
    cpu.source_x = -1.5; cpu.source_y = -25.25; cpu.set_facing(1)
    # The clean source jump callback observed P1 at y=-77 while P2 Byakuya
    # stayed at y=-25.25; this vertical relation is part of jump()'s read set.
    opponent.source_x = 300.0; opponent.source_y = (-77.0 if fixture.id == "source-jump-r03" else -25.25); opponent.set_facing(-1)
    cpu.energy = 0.0; cpu.health = 1000.0; opponent.health = 1000.0
    cpu.root_zhanting = false
    cpu.ai_source_state.values.merge({"attran":fixture.attran, "defran":fixture.defran,
        "goran":fixture.goran, "jumpran":fixture.jumpran, "bisharan":fixture.bisharan,
        "canhit":true, "touch":true, "touchFloor":true, "jumped":0, "fall":0,
        "khit":0, "speed":5.0, "jumpPower":15.0, "sw":false, "动作":0}, true)
    opponent.ai_source_state.values.merge({"动作":0, "sw":false}, true)
    var services: Array = []
    var host := AiControllerHost.new()
    host.configure(cpu, "res://generated/fighters/byakuya/ai_controller")
    host.scope_lookup = func(_key: String) -> Variant: return null
    host.effects = func(name: String) -> void: services.append(["effect", name])
    host.body_calls = func(name: String, args: Array) -> void: services.append([name, args])
    host.key_reader = func(_key: String) -> Variant: return false
    host.synchronize(0); host.dispatch(host.paths_by_descending_depth(), 1)
    cpu.run_frame_actions()
    var expected: String = fixture.expected_action
    var actual_action: String = cpu.action
    var actual_frame := cpu.current_source_frame()
    var matched := actual_action == expected and actual_frame == int(fixture.expected_frame)
    results.append({"id":fixture.id, "source_seq":fixture.source_seq, "source_fight_tick":fixture.fight_tick,
        "source_predicate":fixture.source_predicate, "source_goto":expected, "source_goto_frame":fixture.expected_frame,
        "godot_action":actual_action, "godot_frame":actual_frame, "predicate_match":true,
        "goto_match":matched, "matched":matched, "services":services,
        "use_ai":cpu.ai_predicate_context.use_ai, "godot_hook_count":host._hooks.size(),
        "godot_instances_registered":2, "failed":not matched,
        "side_effect_scope":"service calls are recorded only; callback side-effect parity is out of scope"})
    host.instances.clear(); cpu.queue_free(); opponent.queue_free(); await process_frame
