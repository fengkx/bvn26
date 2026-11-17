class_name FighterSelection
extends RefCounted

const CATALOG_PATH := "res://generated/main/character_selection/available.json"


static func directory(resource_id: String) -> String:
	var catalog: Dictionary = JSON.parse_string(FileAccess.get_file_as_string(CATALOG_PATH))
	assert(resource_id in catalog.fighters.values(), "Unavailable selected fighter: " + resource_id)
	var category := "forms" if catalog.get("forms", {}).has(resource_id) else "fighters"
	return "res://generated/%s/%s" % [category, resource_id]


static func form(resource_id: String) -> Dictionary:
	var catalog: Dictionary = JSON.parse_string(FileAccess.get_file_as_string(CATALOG_PATH))
	return catalog.get("forms", {}).get(resource_id, {})
