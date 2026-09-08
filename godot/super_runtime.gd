class_name SuperRuntime
extends RefCounted

# Source: scripts/main.json frame_8 bsd / cbsd / bsw / cbsw / stopMc / playMc.
# Interprets compiled super_events only. Does not invent cut-in art.

signal shine_requested(color_rgb24: int)
signal xg_requested(clip_name: String, source_position: Vector2, source_facing: int)

var zhanting: bool = false
var game_paused: bool = false
var presentation
var last_xg: String = ""
var last_focus: String = "all"


func apply(event: Dictionary, caster: FighterRuntime, opponent: FighterRuntime, helpers: Array = []) -> void:
	var op := str(event.get("op", ""))
	if op == "super_start":
		_bsd(event, caster, opponent, helpers)
	elif op == "show_face":
		if presentation != null and caster != null:
			presentation.show_face(caster.opponent_pn(), str(event.get("face_label", "")))
	elif op == "super_end":
		_bsw(event, caster, opponent, helpers)


func reset(caster: FighterRuntime = null, opponent: FighterRuntime = null, helpers: Array = []) -> void:
	zhanting = false
	last_xg = ""
	last_focus = "all"
	if presentation != null:
		presentation.reset()
	_set_root_zhanting(caster, opponent, false)
	if caster != null:
		caster.bs = 0
		caster.zhanting = false
	if opponent != null:
		opponent.bs = 0
		opponent.zhanting = false
		play_mc(opponent)
	for helper in helpers:
		play_mc(helper)


func game_running(fighter: FighterRuntime) -> bool:
	# Source gameRunning(): _root.zhanting == false && opponent.sw == false.
	if zhanting:
		return false
	if fighter == null or not is_instance_valid(fighter):
		return false
	return fighter.opponent == null or not fighter.opponent.sw


func stop_mc(mc: Object) -> void:
	# Source stopMc: stop if hited==0 && bs==0 && sw===false.
	if mc == null or not is_instance_valid(mc):
		return
	if int(mc.get("hited")) != 0:
		return
	if int(mc.get("bs")) != 0:
		return
	if bool(mc.get("sw")):
		return
	mc.set("timeline_playing", false)


func play_mc(mc: Object) -> void:
	# Source playMc: skip if gamePaused or attacking===false;
	# play if hited==0 && sw===false.
	if mc == null or not is_instance_valid(mc):
		return
	if game_paused:
		return
	if mc.get("attacking") == false:
		return
	if int(mc.get("hited")) != 0:
		return
	if bool(mc.get("sw")):
		return
	mc.set("timeline_playing", true)


func _bsd(event: Dictionary, caster: FighterRuntime, opponent: FighterRuntime, helpers: Array) -> void:
	# Source bsd(pn): zhanting=true, shine(), blackStg(), caster.mc.bs=1,
	# stopMc(caster helper), addChildXG(caster, xg), stopMc(opponent.mc),
	# stopMc(opponent helper). cbsd also sets 焦点 to the caster.
	zhanting = true
	_set_root_zhanting(caster, opponent, true)
	var active_helper: HelperRuntime = null
	if bool(event.get("helper", false)):
		for helper in helpers:
			if helper.owner_fighter == caster:
				active_helper = helper
				break
	if active_helper != null:
		active_helper.bs = 1
		stop_mc(caster)
	elif caster != null:
		caster.bs = 1
		caster.zhanting = true
	shine_requested.emit(0xFFFFFF)
	if presentation != null:
		presentation.black_stg()
		var face := str(event.get("face_label", ""))
		if face != "" and caster != null:
			presentation.show_face(caster.opponent_pn(), face)
	if opponent != null:
		stop_mc(opponent)
	for helper in helpers:
		stop_mc(helper)
	var kind := str(event.get("kind", "bsd"))
	last_xg = str(event.get("xg", "XG_cbs" if kind == "cbsd" else "XG_bs"))
	if active_helper != null:
		xg_requested.emit(last_xg, active_helper.position, active_helper.facing)
	elif caster != null:
		xg_requested.emit(last_xg, caster.position, caster.facing)
	if kind == "cbsd" and caster != null:
		last_focus = caster.player_slot
	else:
		last_focus = "all"


func _bsw(event: Dictionary, caster: FighterRuntime, opponent: FighterRuntime, helpers: Array) -> void:
	# Source bsw(pn): caster.bs=0; if gamePaused or opponent.bs==1, stopMc(caster) and return
	# without restoring the stage. Else playMc helpers/opponent, hideFace, resumeBlackStg,
	# zhanting=false. cbsw also restores 焦点="all".
	if caster != null:
		caster.bs = 0
	if game_paused or (opponent != null and opponent.bs == 1):
		stop_mc(caster)
		return
	play_mc(opponent)
	for helper in helpers:
		play_mc(helper)
	if presentation != null:
		presentation.hide_face()
		presentation.resume_black_stg()
	zhanting = false
	_set_root_zhanting(caster, opponent, false)
	if caster != null:
		caster.zhanting = false
	if str(event.get("kind", "")) == "cbsw":
		last_focus = "all"


func _set_root_zhanting(caster: FighterRuntime, opponent: FighterRuntime, value: bool) -> void:
	if caster != null:
		caster.root_zhanting = value
	if opponent != null:
		opponent.root_zhanting = value
