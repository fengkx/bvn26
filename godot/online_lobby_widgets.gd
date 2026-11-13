extends RefCounted


static func label(value: String) -> Label:
	var label := Label.new()
	label.text = value
	label.vertical_alignment = VERTICAL_ALIGNMENT_CENTER
	return label


static func line_edit(value: String, placeholder: String, focus_entered: Callable, focus_exited: Callable) -> LineEdit:
	var edit := LineEdit.new()
	edit.text = value
	edit.placeholder_text = placeholder
	edit.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	edit.focus_entered.connect(focus_entered.bind(edit))
	edit.focus_exited.connect(focus_exited.bind(edit))
	return edit


static func row(label: String, input: Control, label_factory: Callable) -> HBoxContainer:
	var row := HBoxContainer.new()
	row.add_child(label_factory.call(label))
	row.add_child(input)
	return row


static func button(text: String, callback: Callable) -> Button:
	var button := Button.new()
	button.text = text
	button.pressed.connect(callback)
	return button


static func style_theme(theme: Theme) -> void:
	theme.default_font_size = 14
	for kind in ["Label", "Button", "LineEdit", "OptionButton", "CheckButton"]:
		theme.set_color("font_color", kind, Color("f4efe7"))
	for kind in ["Button", "OptionButton", "LineEdit", "Panel", "PanelContainer"]:
		for state in ["normal", "hover", "pressed", "disabled", "focus", "panel"]:
			var style := StyleBoxFlat.new()
			style.bg_color = Color("242023") if kind in ["Panel", "PanelContainer"] else Color("30292c")
			if state == "hover": style.bg_color = Color("494246")
			if state == "pressed": style.bg_color = Color("c4412e")
			style.set_corner_radius_all(3)
			style.content_margin_left = 8
			style.content_margin_right = 8
			style.content_margin_top = 5
			style.content_margin_bottom = 5
			if state == "focus":
				style.set_border_width_all(2)
				style.border_color = Color("ffc68c")
			theme.set_stylebox(state, kind, style)


static func player_card(slot: int) -> PanelContainer:
	var panel := PanelContainer.new()
	panel.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	var surface := StyleBoxFlat.new()
	surface.bg_color = Color("30292c")
	surface.border_width_top = 2
	surface.border_color = Color("73a3ba") if slot == 1 else Color("c4412e")
	surface.content_margin_left = 7
	surface.content_margin_right = 7
	surface.content_margin_top = 7
	panel.add_theme_stylebox_override("panel", surface)
	var box := VBoxContainer.new()
	panel.add_child(box)
	var text := Label.new()
	text.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	text.custom_minimum_size.x = 145
	text.add_theme_font_size_override("font_size", 12)
	text.add_theme_color_override("font_color", Color("73a3ba") if slot == 1 else Color("f4efe7"))
	box.add_child(text)
	var portrait := TextureRect.new()
	portrait.custom_minimum_size = Vector2(145, 100)
	portrait.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
	portrait.stretch_mode = TextureRect.STRETCH_KEEP_ASPECT_CENTERED
	box.add_child(portrait)
	return panel


static func primary(button: Button) -> void:
	var style := StyleBoxFlat.new()
	style.bg_color = Color("c4412e")
	style.set_corner_radius_all(3)
	style.content_margin_left = 10
	style.content_margin_right = 10
	style.content_margin_top = 7
	style.content_margin_bottom = 7
	button.add_theme_stylebox_override("normal", style)
