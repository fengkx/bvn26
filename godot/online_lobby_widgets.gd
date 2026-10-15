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
