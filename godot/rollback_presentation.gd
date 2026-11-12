extends RefCounted

static func allow_sound(node: Node, event: String) -> bool:
	var parent := node
	while parent != null:
		if parent.has_meta("authority_probe"): return false
		parent = parent.get_parent()
	var checkpoint: Variant = preload("res://rollback_lifetime.gd").owner(node)
	return checkpoint == null or checkpoint.allow_sound(node, event)


static func is_replaying(node: Node) -> bool:
	var checkpoint: Variant = preload("res://rollback_lifetime.gd").owner(node)
	if not checkpoint is Object:
		return false
	var value: Variant = checkpoint.get("replaying")
	return value if value is bool else false


static func should_emit_combat_console_event(node: Node) -> bool:
	return not is_replaying(node)
