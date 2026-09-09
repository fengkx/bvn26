class_name StageHitRegistry
extends RefCounted

var counter: int
var _spec: Dictionary
var _latest: Dictionary = {}


func configure(spec: Dictionary) -> void:
	assert(_spec.is_empty(), "Stage registry belongs to one root lifetime")
	_spec = spec["registry"]
	counter = int(_spec["initial_counter"])


func register(effect: StageHitRuntime) -> String:
	assert(effect.caster.player_slot in ["p1", "p2"])
	counter += 1
	var slot := 3 - effect.caster.opponent_pn()
	var key := str(_spec["name_prefix"]) + str(counter) + str(_spec["owner_separator"]) + str(slot)
	effect.source_name = key
	_latest[key] = weakref(effect)
	# Source wraps only after attachMovie/name construction. In particular,
	# the counter can name 11 although the receiver's stgks stops at 10.
	if counter > int(_spec["wrap_after"]):
		counter = int(_spec["wrap_to"])
	return key


func first_contact(defender: FighterRuntime, ordered_prefixes: Array) -> Dictionary:
	assert(ordered_prefixes.size() == _spec["lookup_prefixes"].size())
	var seen := {}
	for prefix: String in ordered_prefixes:
		assert(prefix in _spec["lookup_prefixes"] and not seen.has(prefix))
		seen[prefix] = true
	if not defender.allows_source_hit():
		return {}
	for prefix: String in ordered_prefixes:
		var key := prefix + str(_spec["owner_separator"]) + str(defender.opponent_pn())
		if not _latest.has(key):
			continue
		var effect: StageHitRuntime = _latest[key].get_ref()
		if effect == null or effect.expired:
			continue
		var packet := effect.attack_contact(defender)
		if not packet.is_empty():
			return {"effect": effect, "packet": packet}
	return {}


func forget(effect: StageHitRuntime) -> void:
	var key := effect.source_name
	if _latest.has(key) and _latest[key].get_ref() == effect:
		_latest.erase(key)


func clear_effects() -> void:
	# Clearing a scene's effects does not re-execute root frame 8's stgi=0.
	_latest.clear()
