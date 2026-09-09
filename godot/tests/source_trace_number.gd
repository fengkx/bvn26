extends RefCounted


static func decode(value: String) -> Variant:
	if value == "undefined": return null
	if value == "true": return true
	if value == "false": return false
	if not value.begins_with("f:"):
		assert(value.is_valid_float(), "Unsupported source state value")
		return float(value)
	var parts := value.split(":")
	assert(parts.size() == 5)
	for index in range(1, 5):
		assert(parts[index].is_valid_int())
	var sign_value := int(parts[1])
	var exponent := int(parts[2])
	var high := int(parts[3])
	var low := int(parts[4])
	assert(sign_value in [-1, 1] and exponent >= -1074 and exponent <= 1023)
	assert(low >= 0 and low < 67108864)
	if high == 0:
		assert(low == 0 and exponent == 0)
	else:
		assert(high >= 67108864 and high < 134217728)
	var mantissa := float(high * 67108864 + low) / 4503599627370496.0
	return float(sign_value) * mantissa * pow(2.0, exponent)
