extends RefCounted

static func allow_sound(node: Node, event: String) -> bool:
	var checkpoint: Variant = preload("res://rollback_lifetime.gd").owner(node)
	return checkpoint == null or checkpoint.allow_sound(node, event)
