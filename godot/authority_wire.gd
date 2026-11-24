extends RefCounted

const VERSION := 3
const MAX_WIRE_BYTES := 16_384
const MAX_RAW_BYTES := 262_144
const MAX_DEPTH := 24
const MAX_ITEMS := 24_000
const MAX_STRING := 256
var error := ""
var raw_bytes := 0
var wire_bytes := 0
var encode_us := 0
var decode_us := 0
var _items := 0

func _plain(value: Variant, depth: int = 0) -> bool:
	_items += 1
	if depth > MAX_DEPTH or _items > MAX_ITEMS: return false
	match typeof(value):
		TYPE_NIL, TYPE_BOOL, TYPE_INT: return true
		TYPE_FLOAT: return is_finite(value)
		TYPE_STRING: return value.length() <= MAX_STRING
		TYPE_ARRAY:
			for item in value:
				if not _plain(item, depth + 1): return false
			return true
		TYPE_DICTIONARY:
			for key in value:
				if not key is String or not _plain(key, depth + 1) or not _plain(value[key], depth + 1): return false
			return true
	return false

func encode(value: Dictionary) -> PackedByteArray:
	var started := Time.get_ticks_usec()
	error = ""
	_items = 0
	if not _plain(value):
		error = "invalid_authority_value"
		return PackedByteArray()
	var raw := var_to_bytes(value)
	raw_bytes = raw.size()
	if raw_bytes > MAX_RAW_BYTES:
		error = "authority_raw_limit"
		return PackedByteArray()
	var compressed := raw.size() + 5 > MAX_WIRE_BYTES
	var body := raw.compress(FileAccess.COMPRESSION_DEFLATE) if compressed else raw
	var packet := PackedByteArray([1 if compressed else 0])
	packet.resize(5)
	packet.encode_u32(1, raw.size())
	packet.append_array(body)
	if packet.size() > MAX_WIRE_BYTES:
		error = "authority_wire_limit"
		return PackedByteArray()
	wire_bytes = packet.size()
	encode_us = Time.get_ticks_usec() - started
	return packet

func decode(packet: PackedByteArray) -> Dictionary:
	var started := Time.get_ticks_usec()
	error = ""
	if packet.size() < 5 or packet.size() > MAX_WIRE_BYTES or packet[0] not in [0, 1]:
		error = "invalid_authority_packet"
		return {}
	var size := packet.decode_u32(1)
	if size <= 0 or size > MAX_RAW_BYTES:
		error = "authority_raw_limit"
		return {}
	var raw := packet.slice(5)
	if packet[0] == 1: raw = raw.decompress(size, FileAccess.COMPRESSION_DEFLATE)
	if raw.size() != size:
		error = "authority_length_mismatch"
		return {}
	# Objects are disabled; schema/resource validation still follows this boundary.
	var value: Variant = bytes_to_var(raw)
	_items = 0
	if not value is Dictionary or not _plain(value):
		error = "invalid_authority_value"
		return {}
	raw_bytes = size
	wire_bytes = packet.size()
	decode_us = Time.get_ticks_usec() - started
	return value

static func digest(value: Dictionary) -> String:
	var hashing := HashingContext.new()
	hashing.start(HashingContext.HASH_SHA256)
	hashing.update(var_to_bytes(value))
	return hashing.finish().hex_encode()
