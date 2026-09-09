class_name SourceHealthRules
extends RefCounted

var spec: Dictionary
var fighters: Array[FighterRuntime]
var max_health: Callable
var pending := false


func configure(actors: Array[FighterRuntime], maximum: Callable) -> void:
	spec = JSON.parse_string(FileAccess.get_file_as_string("res://generated/main/health/rules.json"))
	assert(spec.format == "bvn26-health-rules-v1" and actors.size() == 2)
	fighters = actors
	max_health = maximum


func enter_frame() -> void:
	var percentages: Array[float] = []
	for fighter in fighters:
		percentages.append(fighter.health / float(max_health.call()) * float(spec.percent_scale))
	for percent in percentages:
		if percent <= float(spec.return_if_any_percent_at_most):
			return
	for rule: Dictionary in spec.rules:
		var index := int(rule.slot) - 1
		if percentages[index] < float(rule.percent_below):
			# The HUD writes ql directly. BODY clamps it on its own callback;
			# pausing or clamping here would change the original ordering.
			fighters[index].energy += float(rule.energy_delta)


func queue_frame() -> void:
	pending = true


func run_pending_frame() -> void:
	if pending:
		pending = false
		enter_frame()
