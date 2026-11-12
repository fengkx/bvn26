extends RefCounted

const EVENTS_SHA256 := "ac14a0878757cf02b5ae88060db40f72382dcdc7be5cb10e2ba9536aa8d29d92"
const BUILD_SHA256 := "0e4d14c3d8758f60a536ad20423b5d421d628ab93fd127b223f51bc33cce6cfe"


# A deliberately narrow receipt profile, not roster inference from filenames.
static func qualify(events_path: String) -> Dictionary:
	var build_path := events_path.get_base_dir().path_join("build.json")
	if FileAccess.get_sha256(events_path) != EVENTS_SHA256:
		return {"error": "r13_event_identity_mismatch"}
	if FileAccess.get_sha256(build_path) != BUILD_SHA256:
		return {"error": "r13_build_identity_mismatch"}
	var build: Dictionary = JSON.parse_string(FileAccess.get_file_as_string(build_path))
	var root := ProjectSettings.globalize_path("res://").get_base_dir().get_base_dir()
	for path: String in build.sources_sha256:
		if FileAccess.get_sha256(root.path_join(path)) != build.sources_sha256[path]:
			return {"error": "locked_source_hash_mismatch", "path": path}
	return {"error": "", "events_sha256": EVENTS_SHA256, "build_sha256": BUILD_SHA256,
		"configuration": build.configuration, "sources_sha256": build.sources_sha256,
		"body_boundaries": build.body_boundaries, "native_binding_proven": false}


static func runtime_error(game, identity: Dictionary) -> String:
	if not identity.get("error", "missing_identity").is_empty():
		return "unqualified_receipt"
	var config: Dictionary = identity.configuration
	var fighters := [game.naruto, game.ichigo]
	for i in 2:
		var fighter = fighters[i]
		var model: Dictionary = JSON.parse_string(FileAccess.get_file_as_string(fighter.fighter_directory.path_join("fighter.json")))
		if model.fighter_id != config["p%d" % (i + 1)] or fighter.player_slot != "p%d" % (i + 1):
			return "runtime_fighter_identity_mismatch"
		for pair in [["swf_path", "swf_sha256"], ["script_bundle_path", "script_bundle_sha256"]]:
			if identity.sources_sha256.get(model.source[pair[0]], "") != model.source[pair[1]]:
				return "generated_source_identity_mismatch"
	if game.selected_stage != config.stage or game.session.modo != config.modo or game.session.ai_level != config.AI or game.session.p2cpu != config.p2cpu or game.session.p1cpu:
		return "runtime_configuration_mismatch"
	if game.naruto_helper.helper_id != config.p1sf or game.ichigo_helper.helper_id != config.p2sf:
		return "runtime_helper_identity_mismatch"
	for helper in [game.naruto_helper, game.ichigo_helper]:
		var model: Dictionary = JSON.parse_string(FileAccess.get_file_as_string(helper.helper_directory.path_join("combat.json")))
		if model.helper_id != helper.helper_id or identity.sources_sha256.get(model.source.swf, "") != model.source.swf_sha256:
			return "generated_helper_identity_mismatch"
	return ""
