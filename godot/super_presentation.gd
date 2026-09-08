class_name SuperPresentation
extends RefCounted

# Source: scripts/main.json frame_8 showFace / hideFace / blackStg / resumeBlackStg.
# Presentation only. Does not write hp/ql/hits.
# Interprets compiled super_presentation; imported timelines live under
# godot/generated/main/blackMu and ts_face.

var spec: Dictionary = {}
var black_mu_frame: int = 1
var bgmc_visible: bool = true
var fgmc_visible: bool = true
var face_label: String = ""
var active_slot: String = ""
var bg_frame: int = 1
var face_p1_frame: int = 1
var face_p2_frame: int = 1
var bg_playing: bool = false
var face_p1_playing: bool = false
var face_p2_playing: bool = false


func load_spec(path: String) -> void:
	var file := FileAccess.open(path, FileAccess.READ)
	if file == null:
		return
	var parsed: Variant = JSON.parse_string(file.get_as_text())
	if parsed is Dictionary:
		spec = parsed.get("super_presentation", {})
	reset()


func reset() -> void:
	black_mu_frame = int(_black_mu().get("idle_frame", 1))
	bgmc_visible = true
	fgmc_visible = true
	face_label = ""
	active_slot = ""
	bg_frame = int(_ts_face().get("idle_frame", 1))
	face_p1_frame = bg_frame
	face_p2_frame = bg_frame
	bg_playing = false
	face_p1_playing = false
	face_p2_playing = false


func black_stg(frame: int = -1) -> void:
	# Source blackStg(): hide game.bgmc/fgmc, blackMu.gotoAndStop(frame or 2).
	if frame < 1:
		frame = int(_black_mu().get("super_frame", 2))
	black_mu_frame = frame
	bgmc_visible = false
	fgmc_visible = false


func resume_black_stg() -> void:
	# Source resumeBlackStg(): show bgmc/fgmc, blackMu.gotoAndStop(1).
	black_mu_frame = int(_black_mu().get("idle_frame", 1))
	bgmc_visible = true
	fgmc_visible = true


func show_face(pn: int, label: String) -> void:
	# Source showFace(pn, frame): bg.gotoAndPlay("in") if on frame 1;
	# pn != 2 uses face_p2, pn == 2 uses face_p1.
	var slots: Dictionary = _ts_face().get("pn_face_slot", {})
	active_slot = str(slots.get(str(pn), "face_p1" if pn == 2 else "face_p2"))
	face_label = label
	var idle := int(_ts_face().get("idle_frame", 1))
	var in_frame := int(_ts_face().get("in_frame", 5))
	if bg_frame == idle:
		bg_frame = in_frame
		bg_playing = true
	if active_slot == "face_p1":
		face_p1_frame = in_frame
		face_p1_playing = true
	else:
		face_p2_frame = in_frame
		face_p2_playing = true


func hide_face() -> void:
	# Source hideFace: bg/face_p1/face_p2.gotoAndStop(1).
	var idle := int(_ts_face().get("idle_frame", 1))
	bg_frame = idle
	face_p1_frame = idle
	face_p2_frame = idle
	bg_playing = false
	face_p1_playing = false
	face_p2_playing = false
	face_label = ""
	active_slot = ""


func tick() -> void:
	# Source clips loop to frame 1 which stop()s. hideFace may cut this short.
	if bg_playing:
		bg_frame += 1
		if bg_frame > int(_ts_face().get("bg_frame_count", bg_frame)):
			bg_frame = int(_ts_face().get("idle_frame", 1))
			bg_playing = false
	if face_p1_playing:
		face_p1_frame += 1
		if face_p1_frame > int(_ts_face().get("face_frame_count", face_p1_frame)):
			face_p1_frame = int(_ts_face().get("idle_frame", 1))
			face_p1_playing = false
	if face_p2_playing:
		face_p2_frame += 1
		if face_p2_frame > int(_ts_face().get("face_frame_count", face_p2_frame)):
			face_p2_frame = int(_ts_face().get("idle_frame", 1))
			face_p2_playing = false


func portrait_frame(label: String) -> int:
	var labels: Dictionary = _ts_face().get("portrait_labels", {})
	return int(labels.get(label, 0))


func black_overlay_visible() -> bool:
	return black_mu_frame != int(_black_mu().get("idle_frame", 1))


func hide_stage_instances() -> PackedStringArray:
	var names: Array = spec.get("hide_stage_instances", ["bgmc", "fgmc"])
	var result: PackedStringArray = []
	for instance_name in names:
		result.append(str(instance_name))
	return result


func _black_mu() -> Dictionary:
	return spec.get("black_mu", {})


func _ts_face() -> Dictionary:
	return spec.get("ts_face", {})
