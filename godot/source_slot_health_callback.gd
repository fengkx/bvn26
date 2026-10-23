extends RefCounted

# A real script resource gives rollback a stable identity for captured functions.
var target: WeakRef
var root_values: Dictionary


func deliver() -> void:
	var current: FighterRuntime = target.get_ref()
	if current != null and current.source_body_available and current.source_health_defined and not current.root_zhanting and current.health > float(root_values["maxhp"]) / 5.0:
		current.health -= 10.0
