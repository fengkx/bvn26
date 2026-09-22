extends Control

const MAIN_SCENE := "res://main.tscn"
const FIXTURE := {
	"mode": 3,
	"players": {
		"p1": {
			"resourcePath": "res://generated/fighters/byakuya",
			"helper": {"resourcePath": "res://generated/helpers/kon"},
		},
		"p2": {
			"resourcePath": "res://generated/fighters/lee",
			"helper": {"resourcePath": "res://generated/helpers/woailuo"},
		},
	},
}

var game: Node
var _energy_seeded := false

func _ready() -> void:
	set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	game = load(MAIN_SCENE).instantiate()
	add_child(game)
	await get_tree().process_frame
	game.session.modo = int(FIXTURE.mode)
	game.session.p1cpu = false
	game.session.p2cpu = false
	var setup_error: String = game.configure_diagnostic_roster(FIXTURE.players)
	if not setup_error.is_empty():
		push_error("QA_WEB_FIXTURE_SETUP_FAILED " + setup_error)
		return
	game._goto_map_selection(int(FIXTURE.mode))
	print("QA_WEB_FIXTURE_MAP ", JSON.stringify({
		"mode": game.session.modo,
		"p1cpu": game.session.p1cpu,
		"p2cpu": game.session.p2cpu,
		"p1": game.naruto.fighter_directory,
		"p1_helper": game.naruto_helper.helper_directory,
		"p2": game.ichigo.fighter_directory,
		"p2_helper": game.ichigo_helper.helper_directory,
		"map_screen": game.session.root_label,
		"initial_map": game.map_selection.selected_stage(),
	}))

func _process(_delta: float) -> void:
	if _energy_seeded or game == null:
		return
	if game.session.root_label != "游戏场景" or game.battle_intro.active:
		return
	game.naruto.energy = 300.0
	game.ichigo.energy = 300.0
	_energy_seeded = true
	print("QA_WEB_READY ", JSON.stringify({
		"mode": game.session.modo,
		"p1cpu": game.session.p1cpu,
		"p2cpu": game.session.p2cpu,
		"p1": game.naruto.fighter_directory,
		"p1_action": game.naruto.action,
		"p1_frame": game.naruto.current_source_frame(),
		"p1_energy": game.naruto.energy,
		"p1_helper": game.naruto_helper.helper_directory,
		"p2": game.ichigo.fighter_directory,
		"p2_action": game.ichigo.action,
		"p2_frame": game.ichigo.current_source_frame(),
		"p2_energy": game.ichigo.energy,
		"p2_helper": game.ichigo_helper.helper_directory,
		"root_label": game.session.root_label,
		"intro_active": game.battle_intro.active,
		"countdown_visible": game.health_hud.visible,
	}))
