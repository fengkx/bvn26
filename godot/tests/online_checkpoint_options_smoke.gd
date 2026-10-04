extends SceneTree

const Coordinator = preload("res://online_match.gd")

func _initialize() -> void:
	var coordinator := Coordinator.new()
	assert(coordinator.sparse_saves and coordinator.checkpoint_stride == 2)
	coordinator._apply_checkpoint_options("", "")
	assert(coordinator.sparse_saves and coordinator.checkpoint_stride == 2)
	coordinator._apply_checkpoint_options("0", "1")
	assert(not coordinator.sparse_saves and coordinator.checkpoint_stride == 1)
	coordinator._apply_checkpoint_options("invalid", "3")
	assert(not coordinator.sparse_saves and coordinator.checkpoint_stride == 1)
	coordinator._apply_checkpoint_options("1", "2")
	assert(coordinator.sparse_saves and coordinator.checkpoint_stride == 2)
	coordinator.close()
	print("ONLINE_CHECKPOINT_OPTIONS_SMOKE_OK default_stride_two=true explicit_fallback=true")
	quit()
