extends RefCounted

# The device adapter is also used by selection/settings, outside match playback.
const BUTTONS := ["up", "down", "left", "right", "attack", "jump", "dash", "ranged", "special", "summon"]


func is_slot_down(session: RefCounted, slot: String) -> bool:
	var key: Key = session.flash_to_key(int(session.codes[slot]))
	return Input.is_physical_key_pressed(key) or Input.is_key_pressed(key)


func fighter_input(session: RefCounted, player: String) -> Dictionary:
	var slots: PackedStringArray = session.P1_SLOTS if player == "p1" else session.P2_SLOTS
	var held := {}
	for index in BUTTONS.size():
		held[BUTTONS[index]] = is_slot_down(session, slots[index])
	return held
