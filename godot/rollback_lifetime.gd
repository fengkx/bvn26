extends RefCounted

static func owner(node: Node) -> Variant:
	var current := node
	while current != null:
		if current.has_meta("rollback_owner"):
			return current.get_meta("rollback_owner")
		current = current.get_parent()
	return null

static func retire(node: Node) -> void:
	var checkpoint: Variant = owner(node)
	if checkpoint == null:
		node.queue_free()
	else:
		checkpoint.retire(node)
