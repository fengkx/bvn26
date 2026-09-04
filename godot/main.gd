extends Control

@onready var tick_label: Label = %TickLabel
@onready var naruto: TimelinePreview = %Naruto
@onready var ichigo: TimelinePreview = %Ichigo

var physics_tick: int = 0


func _ready() -> void:
	print(
		"M0_BOOT_OK ",
		JSON.stringify(
			{
				"godot": Engine.get_version_info()["string"],
				"physics_hz": Engine.physics_ticks_per_second,
				"display_server": DisplayServer.get_name(),
			}
		)
	)


func _physics_process(_delta: float) -> void:
	physics_tick += 1
	tick_label.text = "Fixed simulation tick: %d" % physics_tick


func _unhandled_key_input(event: InputEvent) -> void:
	if not event.pressed or event.echo:
		return
	match event.keycode:
		KEY_1:
			naruto.play_action("砍1")
			ichigo.play_action("砍1")
		KEY_2:
			naruto.play_action("砍2")
			ichigo.play_action("砍2")
		KEY_3:
			naruto.play_action("砍3")
			ichigo.play_action("砍3")
		KEY_4:
			naruto.play_action("被打")
			ichigo.play_action("被打")
		KEY_5:
			naruto.play_action("必杀")
			ichigo.play_action("必杀")
