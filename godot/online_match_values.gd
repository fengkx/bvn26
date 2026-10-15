extends RefCounted


static func wire_integer(value: Variant, minimum: int, maximum: int) -> Variant:
	if value is bool:
		return null
	var normalized: int
	if value is int:
		normalized = value
	elif value is float and is_finite(value) and value == floor(value) \
		and absf(value) <= 9_007_199_254_740_991.0:
		normalized = int(value)
	else:
		return null
	if normalized < minimum or normalized > maximum:
		return null
	return normalized


static func is_digest(value: String) -> bool:
	if value.length() != 64 or value != value.to_lower():
		return false
	for index in range(value.length()):
		var codepoint := value.unicode_at(index)
		if not ((codepoint >= 48 and codepoint <= 57) or (codepoint >= 97 and codepoint <= 102)):
			return false
	return true
