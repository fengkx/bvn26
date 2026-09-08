class_name GameSession
extends RefCounted

# Source: scripts/main.json frame_7/DoAction.as defaults and SharedObject("bvn_5d").
# showKeyName: scripts/main.json frame_8/DoAction.as `_root.showKeyName`.

const STORE_PATH := "user://bvn_5d.cfg"
const STORE_SECTION := "bvn_5d"

const P1_SLOTS: PackedStringArray = ["w", "s", "a", "d", "j", "k", "l", "u", "i", "o"]
const P2_SLOTS: PackedStringArray = ["上箭", "下箭", "左箭", "右箭", "N1", "N2", "N3", "N4", "N5", "N6"]
# Source key-setting labels are 上/下/左/右/斩/跳/冲/招/必杀/换.
# Display English so the default Godot font can render them.
const SLOT_ACTIONS := {
	"w": "Up",
	"s": "Down",
	"a": "Left",
	"d": "Right",
	"j": "Attack",
	"k": "Jump",
	"l": "Dash",
	"u": "Skill",
	"i": "Super",
	"o": "Assist",
	"上箭": "Up",
	"下箭": "Down",
	"左箭": "Left",
	"右箭": "Right",
	"N1": "Attack",
	"N2": "Jump",
	"N3": "Dash",
	"N4": "Skill",
	"N5": "Super",
	"N6": "Assist",
}
const DEFAULT_CODES := {
	"w": 87,
	"s": 83,
	"a": 65,
	"d": 68,
	"j": 74,
	"k": 75,
	"l": 76,
	"u": 85,
	"i": 73,
	"o": 79,
	"上箭": 38,
	"下箭": 40,
	"左箭": 37,
	"右箭": 39,
	"N1": 97,
	"N2": 98,
	"N3": 99,
	"N4": 100,
	"N5": 101,
	"N6": 102,
}
const FLASH_TO_KEY := {
	8: KEY_BACKSPACE,
	13: KEY_ENTER,
	27: KEY_ESCAPE,
	32: KEY_SPACE,
	33: KEY_PAGEUP,
	34: KEY_PAGEDOWN,
	35: KEY_END,
	36: KEY_HOME,
	37: KEY_LEFT,
	38: KEY_UP,
	39: KEY_RIGHT,
	40: KEY_DOWN,
	45: KEY_INSERT,
	46: KEY_DELETE,
	96: KEY_KP_0,
	97: KEY_KP_1,
	98: KEY_KP_2,
	99: KEY_KP_3,
	100: KEY_KP_4,
	101: KEY_KP_5,
	102: KEY_KP_6,
	103: KEY_KP_7,
	104: KEY_KP_8,
	105: KEY_KP_9,
	106: KEY_KP_MULTIPLY,
	107: KEY_KP_ADD,
	109: KEY_KP_SUBTRACT,
	110: KEY_KP_PERIOD,
	111: KEY_KP_DIVIDE,
	186: KEY_SEMICOLON,
	219: KEY_BRACKETLEFT,
	221: KEY_BRACKETRIGHT,
	222: KEY_APOSTROPHE,
}
const SHOW_KEY_NAME := {
	49: "1",
	50: "2",
	51: "3",
	52: "4",
	53: "5",
	54: "6",
	55: "7",
	56: "8",
	57: "9",
	48: "0",
	81: "Q",
	87: "W",
	69: "E",
	82: "R",
	84: "T",
	89: "Y",
	85: "U",
	73: "I",
	79: "O",
	80: "P",
	219: "[",
	221: "]",
	65: "A",
	83: "S",
	68: "D",
	70: "F",
	71: "G",
	72: "H",
	74: "J",
	75: "K",
	76: "L",
	186: ";",
	222: "'",
	90: "Z",
	88: "X",
	67: "C",
	86: "V",
	66: "B",
	78: "N",
	77: "M",
	32: "Space",
	38: "↑",
	40: "↓",
	37: "←",
	39: "→",
	45: "Ins",
	36: "Hom",
	33: "PaU",
	46: "Del",
	35: "End",
	34: "PaD",
	96: "Num0",
	110: "Num.",
	97: "Num1",
	98: "Num2",
	99: "Num3",
	100: "Num4",
	101: "Num5",
	102: "Num6",
	103: "Num7",
	104: "Num8",
	105: "Num9",
	106: "Num*",
	111: "Num/",
	107: "Num+",
	109: "Num-",
}

var codes: Dictionary = DEFAULT_CODES.duplicate()
var modo: int = 1
var maxhp: float = 1000.0
var p1cpu: bool = false
var p2cpu: bool = false
var root_label: String = "MENU"
var write_success: bool = true


func load_store() -> void:
	var store := ConfigFile.new()
	if store.load(STORE_PATH) != OK:
		return
	if store.get_value(STORE_SECTION, "w", null) == null:
		return
	for slot in DEFAULT_CODES.keys():
		codes[slot] = int(store.get_value(STORE_SECTION, slot, DEFAULT_CODES[slot]))
	maxhp = float(store.get_value(STORE_SECTION, "maxhp", maxhp))


func save_store() -> bool:
	# Source cselect==6 / K: write the same fields to SharedObject("bvn_5d").
	var store := ConfigFile.new()
	store.set_value(STORE_SECTION, "name", "bleachvsnaruto")
	for slot in DEFAULT_CODES.keys():
		store.set_value(STORE_SECTION, slot, int(codes[slot]))
	store.set_value(STORE_SECTION, "maxhp", maxhp)
	write_success = store.save(STORE_PATH) == OK
	return write_success


func flash_to_key(flash_code: int) -> Key:
	if FLASH_TO_KEY.has(flash_code):
		return FLASH_TO_KEY[flash_code]
	return flash_code as Key


func key_to_flash(keycode: Key) -> int:
	for flash_code in FLASH_TO_KEY.keys():
		if FLASH_TO_KEY[flash_code] == keycode:
			return int(flash_code)
	return int(keycode)


func show_key_name(flash_code: int) -> String:
	if SHOW_KEY_NAME.has(flash_code):
		return str(SHOW_KEY_NAME[flash_code])
	return ""


func slot_action(slot: String) -> String:
	return str(SLOT_ACTIONS.get(slot, slot))


func is_slot_down(slot: String) -> bool:
	var key := flash_to_key(int(codes[slot]))
	return Input.is_physical_key_pressed(key) or Input.is_key_pressed(key)


func bind_slot(slot: String, flash_code: int) -> void:
	if not DEFAULT_CODES.has(slot):
		return
	codes[slot] = flash_code


func apply_zdbx(fighters: Array, p2loaded: bool = true) -> void:
	# Source DefineSprite_1991 zdbx + setInterval(zdbx, 1000) when modo==4.
	if modo != 4 or not p2loaded:
		return
	for fighter in fighters:
		if int(fighter.beida) != 0:
			continue
		fighter.health = maxhp
		fighter.energy = 300.0


func fighter_input(player: String) -> Dictionary:
	var slots := P1_SLOTS if player == "p1" else P2_SLOTS
	return {
		"up": is_slot_down(slots[0]),
		"down": is_slot_down(slots[1]),
		"left": is_slot_down(slots[2]),
		"right": is_slot_down(slots[3]),
		"attack": is_slot_down(slots[4]),
		"jump": is_slot_down(slots[5]),
		"dash": is_slot_down(slots[6]),
		"ranged": is_slot_down(slots[7]),
		"special": is_slot_down(slots[8]),
		"summon": is_slot_down(slots[9]),
	}


func menu_held() -> Dictionary:
	# MENU / 游戏设置 read `_root.w` / `_root.s` / `_root.j` / `_root.k`.
	return {
		"up": is_slot_down("w"),
		"down": is_slot_down("s"),
		"confirm": is_slot_down("j"),
		"back": is_slot_down("k"),
		"left": is_slot_down("a"),
		"right": is_slot_down("d"),
	}
