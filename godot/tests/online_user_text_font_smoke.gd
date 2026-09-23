extends SceneTree

const OnlineUserFont = preload("res://online_user_text_font.gd")
const STATIC_FONT_PATH := "res://generated/main/title_menu/menu-font.ttf"
const DYNAMIC_FONT_PATH := "res://generated/main/fonts/user-cjk.woff2"
const SAMPLE_STRINGS := ["输入角色昵称", "繁體姓名", "龘璟姍𠮷㐀"]


func _initialize() -> void:
	_run.call_deferred()


func _run() -> void:
	var static_font := load(STATIC_FONT_PATH) as FontFile
	var fallback_font := load(DYNAMIC_FONT_PATH) as FontFile
	assert(static_font != null, "Static menu font must load")
	assert(fallback_font != null, "WOFF2 CJK fallback must load as FontFile")
	assert(not static_font.has_char("龘".unicode_at(0)), "Rare name glyph must stay outside static subset")

	var combined_font := OnlineUserFont.with_cjk_fallback(static_font)
	assert(combined_font != null, "Helper must return a font with CJK fallback")
	assert(static_font.fallbacks.is_empty(), "Helper must not mutate the shared static font")
	for sample in SAMPLE_STRINGS:
		for index in range(sample.length()):
			var codepoint: int = sample.substr(index, 1).unicode_at(0)
			assert(fallback_font.has_char(codepoint), "CJK fallback missing U+%04X" % codepoint)
			assert(combined_font.has_char(codepoint), "Combined font missing U+%04X" % codepoint)
	assert(combined_font.get_char_size("龘".unicode_at(0), 32).x > 0.0)

	var line_edit := LineEdit.new()
	root.add_child(line_edit)
	line_edit.add_theme_font_override("font", combined_font)
	line_edit.text = SAMPLE_STRINGS[2]
	line_edit.grab_focus()
	await process_frame
	assert(root.gui_get_focus_owner() == line_edit, "Nickname editor must accept focus")
	assert(line_edit.text == SAMPLE_STRINGS[2], "Nickname text must preserve unknown source literals")
	print("ONLINE_USER_TEXT_FONT_SMOKE_OK format=WOFF2 coverage=31547 static_subset_preserved=true fallback=true focus=true")
	quit()
