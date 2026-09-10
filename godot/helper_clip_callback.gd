class_name HelperClipCallback
extends RefCounted

var owner
var event: Dictionary


func enter_frame() -> void:
	if owner != null and is_instance_valid(owner):
		owner.run_nested_clip_callback(event)
