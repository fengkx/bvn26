class_name SourceFormProfile
extends RefCounted


static func prepare(directory: String, source_sha256: String, loaded_timeline: Dictionary = {}) -> Dictionary:
	var result := {"directory": directory}
	for key in ["timeline", "fighter", "assets", "combat", "ai", "hurt_voice", "sound_segments"]:
		var path := directory.path_join(str(key) + ".json")
		if not FileAccess.file_exists(path):
			return {"error": "Missing form profile: " + path}
		var data: Variant
		if key == "timeline" and not loaded_timeline.is_empty():
			data = loaded_timeline
		else:
			data = JSON.parse_string(FileAccess.get_file_as_string(path))
		if not data is Dictionary:
			return {"error": "Malformed form profile: " + path}
		result[key] = data
	if result.timeline.get("source_swf", {}).get("sha256") != source_sha256 or result.ai.get("source_swf", {}).get("sha256") != source_sha256:
		return {"error": "Replacement profile source hash mismatch: " + directory}
	if not result.timeline.has("frames") or not result.timeline.has("definitions") or not result.ai.has("frame_writes") or not result.sound_segments.has("frames"):
		return {"error": "Incomplete replacement timeline/state: " + directory}
	var initialization: Dictionary = result.ai.get("form_initialization", {})
	for field in ["wrapper_scale_from_xscale", "wrapper_visible", "body_visible", "bind_opponent_slot", "call_doWanKai", "update_direct_unless_transformed"]:
		if initialization.get(field) != true:
			return {"error": "Unsupported replacement initialization " + field + ": " + directory}
	for asset: Dictionary in result.assets.get("assets", []):
		# Exported textures and scripts are remapped resources, not loose files.
		if not ResourceLoader.exists(directory.path_join(str(asset.get("path", "")))):
			return {"error": "Missing replacement asset: " + str(asset.get("path", ""))}
	var controller := directory.path_join("player_controller")
	for name in ["body.gd", "body.json", "controller.gd", "controller.json", "predicates.gd"]:
		var path := controller.path_join(name)
		var exists := ResourceLoader.exists(path) if name.ends_with(".gd") else FileAccess.file_exists(path)
		if not exists:
			return {"error": "Missing replacement controller: " + controller.path_join(name)}
	var hit_path := directory.path_join("ai_hit_state.gd")
	if not ResourceLoader.exists(hit_path):
		return {"error": "Missing replacement hit consumer: " + hit_path}
	result["controller_directory"] = controller
	result["hit_state_script"] = load(hit_path)
	result["body_script"] = load(controller.path_join("body.gd"))
	result["body_metadata"] = JSON.parse_string(FileAccess.get_file_as_string(controller.path_join("body.json")))
	for method in ["wankai", "doWanKai", "initCtrl", "randAI", "feixue", "loseHp"]:
		if method not in result.body_metadata.get("functions", []):
			return {"error": "Uncompiled replacement BODY method: " + method + " in " + directory}
	if result.body_metadata.get("swf_sha256") != source_sha256:
		return {"error": "Replacement BODY source mismatch: " + directory}
	return result
