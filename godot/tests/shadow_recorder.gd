extends RefCounted

var rows: Array = []
var tick: int = 0
var ids: Dictionary = {}

func attach(world: Node) -> void:
	world.child_entered_tree.connect(_child_entered)

func _child_entered(child: Node) -> void:
	if child is ShadowSnapshot:
		ids[child.get_instance_id()] = ids.size()
		child.source_event.connect(_record.bind(child.get_instance_id()))

func _record(kind: String, values: Array, id: int) -> void:
	var row: Array = [tick, kind, ids[id]]
	row.append_array(values.slice(0, 7) if kind == "spawn" else values)
	rows.append(row)

func compare(path: String, output: String) -> void:
	FileAccess.open(output, FileAccess.WRITE).store_string(JSON.stringify(rows))
	var expected: Array = JSON.parse_string(FileAccess.get_file_as_string(path))
	assert(rows.size() == expected.size(), "Shadow event count differs")
	for index in expected.size():
		assert(rows[index].size() == expected[index].size())
		for field in expected[index].size():
			assert(rows[index][field] == expected[index][field], "Shadow event %d field %d differs: %s != %s" % [index, field, rows[index][field], expected[index][field]])
	print("SHADOW_REFERENCE_OK ", rows.size(), " events")
