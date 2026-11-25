extends RefCounted
class_name OnlineUserTextFont

const CJK_FALLBACK_PATH := "res://generated/main/fonts/user-cjk.woff2"

static var _cjk_fallback: Font


static func with_cjk_fallback(base_font: Font) -> Font:
	if base_font == null:
		return null
	var configured_font := base_font.duplicate() as Font
	if configured_font == null:
		return null
	var fallback_font := get_cjk_fallback()
	if fallback_font == null:
		return null
	var fallbacks: Array[Font] = []
	for font in configured_font.fallbacks:
		fallbacks.append(font)
	if not fallbacks.has(fallback_font):
		fallbacks.append(fallback_font)
	configured_font.fallbacks = fallbacks
	return configured_font


static func get_cjk_fallback() -> Font:
	if _cjk_fallback == null:
		_cjk_fallback = load(CJK_FALLBACK_PATH) as Font
	return _cjk_fallback
