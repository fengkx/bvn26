extends RefCounted


static func normalized_impact_strength(strength: int) -> int:
	# beida()/fangyu() remove the >10 guard-break marker before bdxg().
	return strength - 10 if strength > 10 else strength


static func hit_fx_table(hit_fx: Dictionary, name: String) -> Dictionary:
	if hit_fx.has(name):
		return hit_fx[name]
	return {}


static func clip_for_strength(table: Dictionary, strength: int) -> String:
	return str(table.get(str(normalized_impact_strength(strength)), ""))
