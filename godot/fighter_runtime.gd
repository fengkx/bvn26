class_name FighterRuntime
extends TimelinePreview

# Development availability policy; isolated source probes keep the full timeline.
var disabled_actions: PackedStringArray = []

const FighterHitEffectLookup = preload("res://fighter_hit_effect_lookup.gd")
const SourceCoordinateStore = preload("res://source_coordinate.gd")
const SourceSweepGeometry = preload("res://source_sweep_geometry.gd")
const RollbackPresentation = preload("res://rollback_presentation.gd")

var ai_timeline_controlled: bool = false
var _source_goto_pending_frames: Array[int] = []
var _source_goto_defer_advance_once := false

# Keep source arithmetic out of Node2D's float32 render projection.
var _source_x: float = 0.0
var _source_y: float = 0.0
var _source_projection := Vector2.INF
var source_x: float:
	get:
		_sync_source_position()
		return _source_x
	set(value):
		# Flash ignores NaN transform assignments (for example an undefined
		# authored hit impulse); converting to twips would turn them into zero.
		if is_nan(value):
			return
		_sync_source_position()
		_source_x = SourceCoordinateStore.store(value)
		position.x = _source_x
		_source_projection = position
var source_y: float:
	get:
		_sync_source_position()
		return _source_y
	set(value):
		if is_nan(value):
			return
		_sync_source_position()
		_source_y = SourceCoordinateStore.store(value)
		position.y = _source_y
		_source_projection = position


func _sync_source_position() -> void:
	# Scene setup and retained legacy callers can still set Node2D.position.
	if position.x != _source_projection.x:
		_source_x = SourceCoordinateStore.from_projection(float(position.x))
	if position.y != _source_projection.y:
		_source_y = SourceCoordinateStore.from_projection(float(position.y))
	_source_projection = position

var ai_color_state := AiColorState.new()
var ai_color_operations: Dictionary = JSON.parse_string(FileAccess.get_file_as_string("res://generated/main/hit_receive.json"))["hit_fx"]["color_effects"]
signal ai_frame_service_requested(event: Dictionary)

signal hit_effect_requested(effect_name: String, source_position: Vector2, source_facing: int)
signal screen_flash_requested(color_rgb24: int)
signal combo_hud_requested(board_pn: int, hit_count: int)
signal super_event_applied(event: Dictionary)
signal ko_requested(opponent_number: int)
signal helper_spawn_requested
signal source_frame_changed(frame: int)
signal source_frame_script_boundary(frame: int, entering: bool)
signal source_child_frame_requested(operation: Callable)

# Wrapper fields survive body-state replacement and belong in rollback snapshots.
var source_parent_values: Dictionary = {}
var source_body: RefCounted
var source_body_epoch: int = 0
var source_body_available: bool = true
var source_health_defined: bool = true
var source_parent_frame: int = 1
var source_power_fields: Dictionary = {}
var source_projectiles: Dictionary = {}

@export var facing: int = 1

var fighter_name: String
var action: String = "站立"
var health: float = 1000.0
var displayed_health: float = 1000.0
var max_health: float = 1000.0
var energy: float = 0.0
# Source mc.hits. Incremented in onBeHit; HUD only if hits > 1.
var hits: int = 0
var last_combo_board: int = 0
var zhanting: bool = false
# Source _root.zhanting. gameRunning() is false for both fighters while set.
var root_zhanting: bool = false
var root_to: bool = false
var source_random: SourceRandom
var source_clock = preload("res://source_clock.gd").new()
var hurt_voice = preload("res://hurt_voice.gd").new()
# Source mc.bs. Caster sets 1 in bsd(); stopMc skips clips with bs != 0.
var bs: int = 0
# Source mc.hited. stopMc/playMc skip when hited != 0.
var hited: int = 0
var last_super: Dictionary = {}
var super_runtime
var super_helpers: Array = []
var hitstun_ticks: int = 0
var timeline_playing: bool = true
var last_event: String = "ready"
var airborne: bool = false
var guarding: bool = false
# Source player wrapper values used by mc.on_enterframe body pressure.
var body_heavy: float = 2.0
var body_forward_velocity: float = 0.0
# Source mc.sw from checkDead(); locks input and blocks 起身 / 站立.
var sw: bool = false
var player_slot: String = ""
# Source `_root.modo`. Default matches frame_7; 4 is 格斗练习.
var modo: int = 1
# Source mc.beida: onBeHit0 sets 1; 站立 is frame 1 and re-runs `var beida = 0`.
var beida: int = 0
var ai_source_state := AiSourceState.new()
var ai_senses := AiSenses.new()
var ai_random_clock: AiRandomClock
var ai_predicate_context: AiPredicateContext
var _ai_hit_transfer: RefCounted
var _ai_state_frame_applied: int = -1
var _ai_pending_frames: Array[Dictionary] = []
var _nested_stage_actions: Array[Dictionary] = []
var frame_script_sequence: Callable
# Root timeline names are source identities, while TimelinePreview keeps the
# authored display-list name for rendering.  Keys include depth and the
# PlaceObject generation so a reused depth cannot inherit an old alias.
var _source_name_bindings: Dictionary = {}

var _combat: Dictionary
var _commands: CommandCatalog = CommandCatalog.new()
var _hit_instances: Dictionary = {}
var _ground_y: float
var _vertical_velocity: float = 0.0
var _double_jump_used: bool = false
var _guard_held: bool = false
var _dash_ticks: int = 0
var _dash_velocity: Vector2 = Vector2.ZERO
var _hurt_stop_applied: bool = false
var _hurt_motion_ticks: int = 0
var _hurt_horizontal_step: float = 0.0
var _hurt_vertical_step: float = 0.0
var _guard_horizontal_step: float = 0.0
var _body_last_x: float = 0.0
var _jump_was_held: bool = false
var _jump_pressed: bool = false
var _stage_platforms: Array[Rect2] = []
var _wall_min: float = 20.0
var source_hit_wall: bool = false
var _wall_max: float = 970.0
var _hurt_falling: bool = false
var _launched: bool = false
var _zhongli_fall: bool = false
var _js: float = 0.0
var _jumpinggg: bool = false
var _energy_event_applied: bool = false
var _health_events_applied: Dictionary = {}
var _summon_applied: bool = false
var _presentation_events_applied: Dictionary = {}
var _super_events_applied: Dictionary = {}
var _clip_placements_applied: Dictionary = {}
var _body_warps_applied: Dictionary = {}
var _source_frame_execution_serial: int = 0
var _scripted_jump: bool = false
var _placement_owned: Dictionary = {}
var helper_spawn: Dictionary = {}
var opponent: FighterRuntime
var last_hit_effect: String = ""
var diagnostic_runtime: Node
var diagnostic_slot: String = ""
var diagnostic_role: String = "unknown"
var diagnostic_tick: int = -1
var diagnostic_helper: HelperRuntime
var pending_hit_diagnostic: Dictionary = {}
# Same-tick cancel must not drop a sourced hit: start_action clears
# _hit_instances and the display list before the defender checkHit callback.
# Production resolve_incoming polls with source_receiver=true; stash must serve
# that path. Unused stash is discarded after source_callbacks.dispatch.
var _stashed_attack: Dictionary = {}


func _ready() -> void:
	autoplay = false
	super._ready()
	_combat = _read_json("%s/combat.json" % fighter_directory)
	hurt_voice.spec = _read_json("%s/hurt_voice.json" % fighter_directory)
	var ai_model := _read_json("%s/ai.json" % fighter_directory)
	source_parent_values = ai_model.get("parent_initial_values", {}).duplicate(true)
	ai_source_state.configure(ai_model)
	if ai_model.get("placement_filter_initialization", ai_model.get("form_initialization", {})).get("clear_placement_filters", false):
		reset_ai_colors()
	_ai_hit_transfer = load("%s/ai_hit_state.gd" % fighter_directory).new(ai_source_state.values)
	ai_senses.configure(self, ai_model)
	ai_predicate_context = AiPredicateContext.new(self)
	ai_random_clock = AiRandomClock.new()
	runtime_services().add_child(ai_random_clock)
	_commands.load_combat(_combat)
	fighter_name = str(_combat.get("fighter_id", "fighter"))
	displayed_health = health
	max_health = health
	_ground_y = position.y
	set_facing(facing)
	start_action("站立")
	# configure() already ran the new timeline's initial declarations.
	_ai_pending_frames.clear()
	_ai_state_frame_applied = 1


func _physics_process(_delta: float) -> void:
	pass


func advance_timeline() -> void:
	if not timeline_playing:
		return
	if _should_stop_dead_knockdown():
		timeline_playing = false
		last_event = "death_stop"
		return
	if current_source_frame() >= int(action_range(action).get("end_frame", 0)):
		if action == "防御":
			start_action("防御2")
			return
		if action == "防住":
			start_action("防御2" if _guard_held else "站立")
			return
		if action in ["被打", "击飞"]:
			return
		if _is_one_shot_action(action):
			_finish_action()
			return
	advance_source_frame(true)
	_queue_source_frame(current_source_frame())
	_expire_absent_hit_instances()


func advance_ai_timeline() -> void:
	if not _source_goto_pending_frames.is_empty():
		# A controller goto places the destination frame during the previous
		# display tick. Its frame script enters on this tick. A playing clip then
		# advances to the following frame in the same display pass; a stopped clip
		# remains on the destination. Preserve source order when a controller
		# emits multiple gotos during one callback.
		for pending_frame: int in _source_goto_pending_frames:
			_queue_source_frame(pending_frame, _source_goto_defer_advance_once)
		_source_goto_pending_frames.clear()
		# A goto issued while a source MovieClip is being re-placed enters its
		# destination frame on this dispatch, but its first timeline advance is
		# the following display tick. This preserves the placed-instance lifetime
		# without suppressing the whole actor from the runner.
		if _source_goto_defer_advance_once:
			_source_goto_defer_advance_once = false
			return
		if not timeline_playing:
			return
	if not timeline_playing:
		return
	var frame := current_source_frame() + 1
	if frame > int(_timeline["frame_count"]):
		frame = 1
	assert(_frames.has(frame), "CPU timeline requires the complete source frame")
	for label: String in _frames[frame]["labels"]:
		_set_ai_action_label(label)
	# Crossing a label is sequential playback: do not clear retained child
	# state or run start_action's synthesized stand/guard/hurt transitions.
	play_source_frame(frame)
	_queue_source_frame(frame)
	_expire_absent_hit_instances()


func goto_ai_label(label: String, play: bool) -> void:
	if label in disabled_actions:
		return
	var target := action_range(label)
	assert(not target.is_empty(), "Uncompiled source label: " + label)
	if current_source_frame() == int(target["start_frame"]):
		timeline_playing = play
		return
	_set_ai_action_label(label, "controller_goto")
	_source_goto_pending_frames.clear()
	timeline_playing = play
	play_source_frame(_action_start)
	_queue_source_frame(_action_start)
	_expire_absent_hit_instances()
	last_event = "action_%s" % label


func read_parent_field(key: String) -> Variant:
	assert(source_parent_values.has(key), "Uncompiled parent field: " + key)
	return source_parent_values[key]


func write_parent_field(key: String, value: Variant) -> void:
	assert(source_parent_values.has(key) and value is bool, "Uncompiled parent field write: " + key)
	source_parent_values[key] = value


func source_goto_frame(frame: int, play: bool) -> void:
	assert(_frames.has(frame), "Uncompiled numeric source frame: %d" % frame)
	timeline_playing = play
	if current_source_frame() == frame:
		return
	# Numeric jumps enter the exact source frame, without replaying the label
	# prefix or resetting gameplay fields owned by skipped frame scripts.
	play_source_frame(frame)
	_queue_source_frame(frame)
	_expire_absent_hit_instances()


func source_goto_label(label: String, play: bool, defer_frame_script: bool = false) -> void:
	# Controller MovieClip.gotoAndStop/gotoAndPlay changes the playhead and
	# queues the destination frame script. It does not synthesize a fighter
	# action transition; that state is owned by the destination frame script.
	if label in disabled_actions:
		return
	var frames := action_range(label)
	assert(not frames.is_empty(), "Uncompiled source label: " + label)
	_action_start = int(frames["start_frame"])
	_action_end = int(frames["end_frame"])
	_current_frame = _action_start
	_source_entry_serial += 1
	_render_frame()
	timeline_playing = play
	if defer_frame_script:
		_source_goto_defer_advance_once = true
		if _source_goto_pending_frames.is_empty() or _source_goto_pending_frames[-1] != _current_frame:
			_source_goto_pending_frames.append(_current_frame)
	else:
		# Only coalesce an identical consecutive goto. A -> B -> A is a real
		# re-entry and must retain both A entries, including a fresh source
		# entry serial and child placement lifetime.
		var last_pending_frame := -1
		if not _ai_pending_frames.is_empty():
			last_pending_frame = int(_ai_pending_frames[-1].get("frame", -1))
		if last_pending_frame != _current_frame:
			_queue_source_frame(_current_frame)

func _set_ai_action_label(label: String, reason: String = "timeline_label") -> void:
	var frames := action_range(label)
	assert(not frames.is_empty(), "Uncompiled CPU frame label: " + label)
	var before := _diagnostic_state()
	var previous_action := action
	action = label
	_action_start = int(frames["start_frame"])
	_action_end = int(frames["end_frame"])
	# Native event bookkeeping resets without pre-executing source writes.
	_energy_event_applied = false
	_health_events_applied.clear()
	_summon_applied = false
	_hurt_stop_applied = false
	_presentation_events_applied.clear()
	_super_events_applied.clear()
	# Re-entered source frame scripts execute again on the next cast. Keep
	# live clip offsets until their PlaceObject lifetime actually ends.
	_clip_placements_applied.clear()
	_body_warps_applied.clear()
	if previous_action != action:
		var event_type := "ai_action" if diagnostic_role == "cpu" and reason == "controller_goto" else "action_transition"
		_emit_diagnostic(event_type, {"slot": diagnostic_slot,
			"source": diagnostic_role, "reason": reason, "phase": "source_timeline",
			"before": before, "after": _diagnostic_state()})


func enter_frame(input_state: Dictionary) -> void:
	if _combat_input_locked():
		input_state = {}
	var jump_held := bool(input_state.get("jump", false))
	_jump_pressed = jump_held and not _jump_was_held
	_jump_was_held = jump_held
	if health > 0.0 and health < 200.0:
		change_energy(0.2)
	_guard_held = bool(input_state.get("down", false))
	guarding = action in ["防御", "防御2", "防住"] and _guard_held
	# Source frame DoAction (gotoAndStop) runs when the playhead enters the
	# frame, before that frame's clip enterFrame motion / cancel.
	if source_body == null:
		_apply_action_exit()
	_apply_super_events()
	_apply_clip_placements()
	_apply_body_warps()
	# Motion clips wrap `_x/_y` in `if(_root.zhanting == false)`.
	if not root_zhanting:
		_run_source_motion(input_state)
	if _update_dash_motion():
		if _game_running():
			_dispatch_cancels(input_state)
		return
	# Clip enterFrame cancels run on the current action before the
	# stand/walk early return that used to swallow 落地/砍3/瞬步.
	# Source: those clips wrap the body in if(gameRunning()).
	if _game_running() and _dispatch_cancels(input_state):
		return
	# 击飞/被打/击落地 run beidax(), not on_enterframe zhongli. Checking
	# this before air motion keeps a grounded self-goto 击飞 on that clip
	# instead of snapping to 落地.
	if _is_hurt_action(action):
		# Source beidax() returns before movement and time++ while the root is
		# paused. stopMc intentionally leaves hited clips playing, so this gate
		# must freeze the callback without freezing their playhead.
		if root_zhanting:
			return
		if action == "被打" and current_source_frame() < int(_combat["hurt"]["callback_start_frame"]):
			return
		_update_hurt_motion()
		# on_enterframe() is a clip action on the wrapper's PlaceObject of the
		# body mc, so it keeps resolving the floor during 被打/击飞. Its
		# jump == 1 early return sits inside the `_y < floorY` branch only, so a
		# downward yup is pulled back by `if(_y > floorY - 10) _y = floorY`.
		if position.y >= _ground_y:
			position.y = _ground_y
		if action == "被打":
			hitstun_ticks = maxi(0, hitstun_ticks - 1)
			if hitstun_ticks == 0:
				timeline_playing = true
		return
	# Source on_enterframe returns here when `_root.zhanting`. Dash already ran.
	if root_zhanting:
		return
	if not _uses_scripted_flight() and _update_air_motion(input_state):
		return
	if source_body == null and _update_hurt_fall():
		return
	# DefineSprite_16 enterFrame keeps calling doDropDown() while that clip
	# stays on the display list, including 防御2. jumpDown() is only blocked
	# when touchFloor is true (main floor), not while standing on a ban.
	if _jump_pressed and _guard_held:
		if _start_drop_through():
			return
	if not airborne:
		var stand_y := _hit_ban_y(position)
		if not is_nan(stand_y):
			position.y = stand_y
	if (
		not _uses_scripted_flight()
		and position.y < _ground_y
		and not _has_support_at(position)
	):
		airborne = true
		_vertical_velocity = 0.0
		_zhongli_fall = true
		start_action("落")
		_update_air_motion(input_state)
		return

	# Guard and stand buttons come from the shared command catalog
	# (doAllAction / onDefence). Stand takes the first leaving goto;
	# guard later-wins because onDefence pins 防御2 then keeps going.
	# Source DefineSprite_16 enterFrame: if(gameRunning()) doAllAction().
	if not _game_running():
		return
	if action in ["防御", "防御2"]:
		if _dispatch_catalog("guard", input_state):
			return
		if action == "防御2":
			if not _guard_held:
				start_action("站立")
			else:
				# The source clip calls gotoAndPlay("防御2") every enterFrame,
				# pinning a held guard to its first frame instead of looping it.
				play_action("防御2")
		return
	if action not in ["站立", "走"]:
		return
	if _dispatch_catalog("stand", input_state):
		return

	var direction := int(input_state.get("right", false)) - int(input_state.get("left", false))
	if direction == 0:
		if action != "站立":
			start_action("站立")
		return
	_move_world_x(direction * float(_combat["movement"]["speed_per_tick"]))
	set_facing(direction)
	if action != "走":
		start_action("走")


func _queue_visual_frame(frame: int, sprite: int) -> void:
	var record: Dictionary = ai_source_state.spec.get("nested_stage_frames", {}).get(str(sprite), {}).get(str(frame), {})
	for event: Dictionary in record.get("events", []):
		_nested_stage_actions.append(event)


func _run_nested_stage_actions() -> void:
	while not _nested_stage_actions.is_empty():
		var event: Dictionary = _nested_stage_actions.pop_front()
		if event.op == "screen_flash":
			screen_flash_requested.emit(int(event.color_rgb24))
		else:
			assert(event.op == "root_position" and not ai_frame_service_requested.get_connections().is_empty())
			ai_frame_service_requested.emit(event)


func run_frame_actions(drain_nested: bool = true, initial_limit: int = -1) -> void:
	_run_nested_stage_actions()
	_apply_ai_source_frame(drain_nested, initial_limit)
	_run_nested_stage_actions()
	_run_frame_actions()
	# A goto made by a frame script queues another target script in this
	# display tick. Retained-then-removed targets must not lose their writes.
	if drain_nested:
		_apply_ai_source_frame()
		_run_nested_stage_actions()

func flush_queued_frame_scripts(limit: int = -1) -> void:
	_apply_ai_source_frame(false, limit)
	_run_nested_stage_actions()


func _run_frame_actions() -> void:
	_apply_source_energy_event()
	_apply_source_health_event()
	_apply_summon_event()
	_apply_presentation_events()
	_apply_clip_placements()
	if not ai_timeline_controlled and source_body == null:
		_apply_body_warps()
	_chase_displayed_health()
	if not _hurt_stop_applied and current_source_frame() == _action_stop_frame():
		timeline_playing = false
		_hurt_stop_applied = true
		last_event = "launch_stop" if action == _death_launch_label() else "hurt_stop"
		return
	if _should_stop_dead_knockdown():
		timeline_playing = false
		last_event = "death_stop"
		return
	if _apply_action_exit():
		return
	# Source-controlled timelines already evaluated the authored branch. A
	# blocked contact must not override that decision through the legacy cache.
	if action == "必杀" and not ai_timeline_controlled and source_body == null:
		for transition: Dictionary in _combat["special"]["transitions"]:
			if transition["from"] != action:
				continue
			if int(transition.get("frame", -1)) != current_source_frame():
				continue
			if (
				transition.get("condition") == "always"
				or (
					transition.get("condition") == "source_condition"
					and not _hit_instances.is_empty()
				)
			):
				start_action(str(transition["to"]))
				return


func receive_attack(attack: Dictionary, attacker_facing: int, source_context: Dictionary = {}) -> void:
	var before := _diagnostic_state()
	pending_hit_diagnostic = source_context.duplicate(true)
	# Source fangyu() treats zl > 10 as a guard break, then removes the
	# encoding offset before choosing the normal hit presentation.
	# Sprite 2 writes the received packet before entering its chosen reaction.
	# Keep hdtime fractional here; BODY compares its integer time against tdtime.
	var target: Dictionary = _ai_hit_transfer.transfer({
		"pw": attack.get("damage"),
		"zl": attack.get("impact_strength"),
		"yup": attack.get("vertical_impulse"),
		"hitx": attack.get("horizontal_impulse"),
		"hdtime": attack.get("hitstun_ms"),
		"htype": attack.get("reaction_label"),
	}, guarding)
	_hurt_motion_ticks = 0
	_hurt_horizontal_step = attacker_facing * _ai_hit_transfer.number(attack.get("horizontal_impulse"))
	_hurt_vertical_step = -_ai_hit_transfer.number(attack.get("vertical_impulse"))
	_guard_horizontal_step = _hurt_horizontal_step
	hitstun_ticks = ceili(float(ai_source_state.read_field("tdtime")))
	# getHitObj reads authored fields verbatim, including undefined operands.
	# An absent reaction target must not synthesize another hit animation.
	if target["label"] == null:
		return
	var reaction := str(target["label"])
	var guard_branch := ("blocked" if reaction == "防住" else "break") if guarding else "hit"
	_launched = reaction == _death_launch_label()
	_hurt_falling = _launched or _hurt_vertical_step != 0.0 or position.y < _ground_y
	_clear_interrupted_super_preparation()
	if ai_timeline_controlled:
		goto_ai_label(reaction, bool(target["play"]))
	else:
		start_action(reaction, "received_hit")
	_emit_diagnostic("hit_received", {"slot": diagnostic_slot,
		"before": before, "after": _diagnostic_state(), "guardBranch": guard_branch, "attack": source_context})


func _clear_interrupted_super_preparation(mark_pending: bool = true) -> void:
	if guarding:
		return
	var shared_super: SuperRuntime = _ensure_super_runtime()
	if shared_super.zhanting or shared_super.game_paused or not _game_running():
		return
	# A receiver can interrupt before this entry's queued DoAction sets bs.
	# Preserve its other writes (including energy), then clear the orphaned lock.
	if mark_pending:
		for pending: Dictionary in _ai_pending_frames:
			if int(pending.get("serial", 0)) != _source_frame_execution_serial:
				continue
			for write: Dictionary in ai_source_state.spec["frame_writes"].get(str(pending["frame"]), []):
				if write.get("field") == "bs" and write.get("value") == 1:
					pending["interrupted_super_preparation"] = true
	if bs != 1:
		return
	# Intentional Flash deviation: source sets bs before entering bsd.
	# If a real hit replaces that preparation action, it may not reach the
	# frame-1 initializer before the next super pause; retaining bs can strand
	# that later bsw behind an orphaned lock.
	bs = 0
	ai_source_state.values["bs"] = 0


func _apply_hit_settlement_frame(frame: int) -> void:
	var sprite := int(_combat.get("source", {}).get("timeline_symbol_id", 0))
	for event: Dictionary in _combat.get("on_be_hit_frames", []):
		if int(event["sprite_id"]) == sprite and int(event["frame"]) == frame:
			_settle_source_hit(false, bool(event["flying"]), 1)
	for event: Dictionary in _combat.get("on_defence_frames", []):
		if int(event["sprite_id"]) == sprite and int(event["frame"]) == frame:
			_settle_source_hit(true, false, int(event["xgtype"]))


func swap_opponent_depths() -> void:
	var depth := z_index
	z_index = opponent.z_index
	opponent.z_index = depth


func _settle_receiver_depth() -> void:
	if is_instance_valid(opponent) and z_index > opponent.z_index:
		swap_opponent_depths()


func _settle_source_hit(defended: bool, flying: bool, xgtype: int) -> void:
	# Read mutable receiver fields when the source DoAction executes.
	var damage := float(ai_source_state.read_field("jhp"))
	var previous_health := health
	var strength := int(ai_source_state.read_field("bdzl"))
	if not defended:
		ai_source_state.apply_function("onBeHit0")
		beida = 1
		hited = 1
		timeline_playing = true
	last_hit_effect = _guard_effect_for_strength(strength, xgtype) if defended else _hit_effect_for_strength(strength)
	if not defended and ai_timeline_controlled:
		var color_operation: Dictionary = ai_color_operations.get(str(strength), {})
		ai_color_state.receive(color_operation)
		if color_operation.get("op") == "set_color_matrix":
			set_source_color(ai_color_state.transform, ai_color_state.matrix)
	if last_hit_effect != "":
		hit_effect_requested.emit(last_hit_effect, position, facing)
	if not defended:
		hits += 1
		ai_source_state.values["hits"] = hits
		last_combo_board = 0
		if hits > 1:
			last_combo_board = opponent_pn()
			combo_hud_requested.emit(last_combo_board, hits)
	if defended and source_body != null:
		source_body.updateDirect(true)
	if not root_to:
		health -= damage / (10.0 if defended else 1.0)
		energy += damage / (15.0 if defended else 10.0)
		if is_instance_valid(opponent) and opponent.ai_source_state.read_field("动作") != 3:
			opponent.energy += damage / (10.0 if defended else 5.0)
	if not defended and source_body != null:
		source_body.updateDirect(true)
	if defended:
		_settle_receiver_depth()
	_check_dead(flying)
	_emit_diagnostic("hit_settled", {
		"slot": diagnostic_slot,
		"source": pending_hit_diagnostic,
		"defender": diagnostic_slot,
		"damage": damage,
		"defended": defended,
		"healthBefore": previous_health,
		"healthAfter": health,
		"reaction": action,
		"position": {"x": source_x, "y": source_y},
		"bounds": pending_hit_diagnostic.get("defenderBounds", {}),
	})
	pending_hit_diagnostic.clear()
	if not defended and source_random != null:
		var voice_spec: Dictionary = hurt_voice.spec
		var probability := float(voice_spec["flying_probability"] if flying else voice_spec["low_damage_probability"] if damage <= float(voice_spec["damage_threshold"]) else voice_spec["high_damage_probability"])
		hurt_voice.execute(ai_source_state, source_random, probability, source_clock, sw)
	if not defended and source_hit_wall:
		var wall_rule: Dictionary = _combat["wall_hit_near"]
		var near := absf(source_x - opponent.source_x) < float(wall_rule["distance"])
		if near:
			near = source_x > float(wall_rule["side_split_x"]) if facing != 1 else source_x < float(wall_rule["side_split_x"])
		ai_source_state.values["hitNear"] = near
	if not defended:
		_settle_receiver_depth()
	last_event = "guard_settlement" if defended else "hit_settlement"
	if RollbackPresentation.should_emit_combat_console_event(self):
		print("COMBAT_EVENT ", JSON.stringify(snapshot()))


func _normalized_impact_strength(strength: int) -> int:
	return FighterHitEffectLookup.normalized_impact_strength(strength)


func _hit_fx_table(name: String) -> Dictionary:
	var hit_fx: Dictionary = _combat.get("hit_fx", {})
	return FighterHitEffectLookup.hit_fx_table(hit_fx, name)


func _clip_for_strength(table_name: String, strength: int) -> String:
	var table := _hit_fx_table(table_name)
	return FighterHitEffectLookup.clip_for_strength(table, strength)


func _hit_effect_for_strength(strength: int) -> String:
	return _clip_for_strength("bdxg", strength)


func apply_ai_colors() -> void:
	if ai_color_state.apply_colors():
		set_source_color(ai_color_state.transform, ai_color_state.matrix)


func reset_ai_colors() -> void:
	_source_placement_filters_cleared = true
	ai_color_state.reset_color()
	set_source_color(ai_color_state.transform, ai_color_state.matrix)


func _guard_effect_for_strength(strength: int, xgtype: int) -> String:
	return _clip_for_strength("bdfyxg2" if xgtype == 2 else "bdfyxg", strength)


func emit_source_guard_effect(xgtype: int = 1) -> void:
	# Source bdfyxg()/bdfyxg2() callbacks run on the placed guard clip after
	# receiver state has written bdzl. Reuse the same compiled strength table
	# used by settlement so the callback cannot invent a role-specific effect.
	var strength := int(ai_source_state.read_field("bdzl"))
	var effect := _guard_effect_for_strength(strength, xgtype)
	if effect != "":
		hit_effect_requested.emit(effect, position, facing)


func _defence_xgtype() -> int:
	var sprite := int(_combat.get("source", {}).get("timeline_symbol_id", 0))
	for item: Dictionary in _combat.get("on_defence_frames", []):
		if int(item.get("sprite_id", 0)) != sprite:
			continue
		if int(item.get("frame", -1)) != current_source_frame():
			continue
		return int(item.get("xgtype", 1))
	return 1


func instance_global_bounds(instance_name: String) -> Rect2:
	if not _source_name_is_live(instance_name):
		return Rect2()
	var bounds := super.instance_global_bounds(instance_name)
	if bounds.has_area():
		return bounds
	var placed := _placed_name_for_hitbox(instance_name)
	if placed != "" and placed != instance_name:
		return super.instance_global_bounds(placed)
	return Rect2()


func incoming_attack_hits(attacker: FighterRuntime) -> bool:
	var contact := attacker.attack_contact(self)
	if contact.is_empty():
		return false
	attacker.apply_attack_contact(contact, self)
	return true


func sync_body_collision_position() -> void:
	_body_last_x = position.x
	body_forward_velocity = 0.0


func resolve_body_collision(other: FighterRuntime) -> void:
	# Source on_enterframe skips body pressure while doDashX owns movement.
	if _dash_ticks > 0:
		sync_body_collision_position()
		return
	var movement := clampf(position.x - _body_last_x, -30.0, 30.0)
	var forward_pressure := movement * float(facing)
	if forward_pressure > 0.0:
		forward_pressure += other.body_forward_velocity / 2.0
		body_forward_velocity = forward_pressure
	else:
		body_forward_velocity = 0.0
	var body := instance_global_bounds("bdmn")
	var other_body := other.instance_global_bounds("bdmn")
	if (
		forward_pressure >= 0.0
		and body.has_area()
		and other_body.has_area()
		and SourceHitTest.intersects(body, other_body)
	):
		# The original injects ten pixels of pressure when two idle bodies are
		# already touching, so accidental overlap resolves instead of persisting.
		if forward_pressure == 0.0 and other.body_forward_velocity == 0.0:
			forward_pressure = 10.0
		var heavy_delta := maxf(0.0, other.body_heavy - body_heavy)
		var other_push := maxf(0.0, forward_pressure / 2.0 - heavy_delta)
		var self_push := forward_pressure - other_push
		other.position.x += other_push * float(facing)
		position.x -= self_push * float(facing)
	_body_last_x = position.x
	# BODY's exact main-floor branch follows body pressure and is skipped by
	# the earlier root-pause/dashing returns. Other floor branches stay separate.
	if not root_zhanting and position.y == _ground_y:
		for event: Dictionary in ai_source_state.spec["main_floor_contact"]["writes"]:
			ai_source_state.apply_write(event)


func attack_contact(defender: FighterRuntime, source_receiver: bool = false) -> Dictionary:
	if not defender.allows_source_hit():
		return {}
	if not _stashed_attack.is_empty() and defender == opponent:
		return _stashed_attack.duplicate()
	_expire_absent_hit_instances()
	var body := defender.instance_global_bounds("bdmn")
	if not body.has_area():
		return {}
	for instance_name in _ordered_attack_instances():
		# Source getHitObj has no per-attack hit cache. Receiver clip lifetime
		# and canhit determine when it can query the same retained attack again.
		if not instance_name.ends_with("atm") or (not source_receiver and _hit_instances.has(instance_name)):
			continue
		var attack := _attack_from_instance(instance_name)
		if attack.is_empty():
			continue
		var attack_bounds := source_projectile_target_bounds(instance_name) if source_receiver else instance_global_bounds(instance_name)
		if attack_bounds.has_area() and SourceHitTest.intersects(body, attack_bounds):
			return attack
	return {}


func allows_source_hit() -> bool:
	return _ai_hit_transfer.truth(_ai_hit_transfer.allows_hit(_game_running()))


func has_active_hit_receiver() -> bool:
	# Legacy polling must honor the receiver's PlaceObject callback lifetime.
	# The source-controlled path invokes resolve_incoming from that callback itself.
	for placement: Dictionary in _frames[current_source_frame()]["display_list"]:
		if placement.get("name", "") != "bdmn":
			continue
		if current_source_frame() <= int(placement["placed_frame"]):
			return false
		for callback: Dictionary in placement.get("clip_actions", []):
			if "EnterFrame" in callback.get("events", []):
				return true
	return false


func _ordered_attack_instances() -> PackedStringArray:
	var visible: Dictionary = {}
	for instance_name in current_named_instances():
		if str(instance_name).ends_with("atm"):
			visible[str(instance_name)] = true
	for instance_name in _aliased_hitbox_names():
		visible[instance_name] = true
	for reference: WeakRef in source_projectiles.values():
		var clip: RefCounted = reference.get_ref()
		if clip != null:
			var current_name: Variant = clip.current_source_name()
			if current_name != null and str(current_name).ends_with("atm"):
				visible[str(current_name)] = true
	var ordered := PackedStringArray()
	# Native AVM1 enumerates this dense source Array from the last key to the
	# first. Overlapping later suffixes (e.g. zh32) must win over zh3/zh31.
	var source_priority: Array = _combat.get("hit_priority", {}).get("instances", []).duplicate()
	source_priority.reverse()
	for instance_name in source_priority:
		var name := str(instance_name)
		if visible.erase(name):
			ordered.append(name)
	# Unknown source names remain usable, but never displace a sourced priority.
	var remaining := PackedStringArray(visible.keys())
	remaining.sort()
	ordered.append_array(remaining)
	return ordered


func apply_attack_contact(attack: Dictionary, defender: FighterRuntime) -> void:
	_stashed_attack = {}
	var attack_bounds := source_projectile_target_bounds(str(attack["instance_name"]))
	if not attack_bounds.has_area():
		attack_bounds = instance_global_bounds(str(attack["instance_name"]))
	var defender_bounds := defender.instance_global_bounds("bdmn")
	var hit_source := {"kind": "fighter", "slot": diagnostic_slot,
		"fighter": fighter_name, "resourcePath": fighter_directory,
		"action": action, "sourceFrame": current_source_frame(),
		"instanceName": str(attack["instance_name"]),
		"attack": attack.duplicate(true), "attackBounds": _diagnostic_rect(attack_bounds),
		"defenderBounds": _diagnostic_rect(defender_bounds),
		"attackerPosition": {"x": source_x, "y": source_y}}
	_emit_diagnostic("hit_contact", hit_source)
	defender.receive_attack(attack, facing, hit_source)
	mark_attack_hit(str(attack["instance_name"]))


func active_attack() -> Dictionary:
	_expire_absent_hit_instances()
	for instance_name in current_named_instances():
		if not instance_name.ends_with("atm") or _hit_instances.has(instance_name):
			continue
		var attack := _attack_from_instance(instance_name)
		if not attack.is_empty() and instance_global_bounds(instance_name).has_area():
			return attack
	return {}


func _aliased_hitbox_names() -> PackedStringArray:
	var result := PackedStringArray()
	var frame := current_source_frame()
	for window: Dictionary in _combat.get("hitbox_windows", {}).get(action, []):
		if source_projectiles.has(str(window.get("placed_name", ""))):
			continue
		var name := str(window.get("instance_name", ""))
		if not name.ends_with("atm"):
			continue
		if frame < int(window.get("start_frame", 0)) or frame > int(window.get("end_frame", 0)):
			continue
		if str(window.get("placed_name", "")) != "":
			if window.has("depth") and not _source_alias_matches(window):
				continue
			result.append(name)
	return result


func _placed_name_for_hitbox(instance_name: String) -> String:
	var frame := current_source_frame()
	for window: Dictionary in _combat.get("hitbox_windows", {}).get(action, []):
		if str(window.get("instance_name", "")) != instance_name:
			continue
		if frame < int(window.get("start_frame", 0)) or frame > int(window.get("end_frame", 0)):
			continue
		if window.has("depth") and not _source_alias_matches(window):
			continue
		return str(window.get("placed_name", ""))
	return ""


func _source_instance_key(depth: int, character_id: int, placed_frame: int) -> String:
	return "%d:%d:%d" % [depth, character_id, placed_frame]


func _source_event_key(event: Dictionary) -> String:
	return _source_instance_key(
		int(event.get("depth", -1)),
		int(event.get("character_id", 0)),
		int(event.get("placed_frame", -1))
	)


func _reconcile_source_name_bindings() -> void:
	if _source_name_bindings.is_empty() or not _frames.has(_current_frame):
		return
	var live: Dictionary = {}
	for placement: Dictionary in _frames[_current_frame].get("display_list", []):
		var authored := str(placement.get("name", ""))
		if authored == "":
			continue
		live[_source_instance_key(
			int(placement.get("depth", -1)),
			int(placement.get("character_id", 0)),
			int(placement.get("placed_frame", _current_frame))
		)] = true
	for key in _source_name_bindings.keys().duplicate():
		if not live.has(key):
			_source_name_bindings.erase(key)


func _source_display_instance_matches(event: Dictionary, source_name: String) -> bool:
	var source_frame := int(event.get("frame", _current_frame))
	if not _frames.has(source_frame):
		return false
	var key := _source_event_key(event)
	for placement: Dictionary in _frames[source_frame].get("display_list", []):
		var placement_key := _source_instance_key(
			int(placement.get("depth", -1)),
			int(placement.get("character_id", 0)),
			int(placement.get("placed_frame", _current_frame))
		)
		if placement_key == key and str(placement.get("name", "")) == source_name:
			return true
	return false


func _apply_root_clip_rename(event: Dictionary) -> void:
	var source_name := str(event.get("source_name", ""))
	var instance_name := str(event.get("instance_name", ""))
	var key := _source_event_key(event)
	if source_name == "" or instance_name == "" or key.begins_with("-1:"):
		return
	var binding: Dictionary = _source_name_bindings.get(key, {})
	if binding.is_empty():
		if not _source_display_instance_matches(event, source_name):
			return
		binding = {
			"visual_name": source_name,
			"current_name": source_name,
			"depth": int(event.get("depth", -1)),
			"character_id": int(event.get("character_id", 0)),
			"placed_frame": int(event.get("placed_frame", -1)),
		}
	if str(binding.get("current_name", "")) != source_name:
		# AS2 lookup of an old name returns undefined after _name replacement.
		return
	binding["current_name"] = instance_name
	_source_name_bindings[key] = binding
	for reference: WeakRef in source_projectiles.values():
		var projectile: RefCounted = reference.get_ref()
		if projectile != null:
			projectile.rename_from_root(source_name, instance_name)


func _source_alias_matches(window: Dictionary) -> bool:
	var key := _source_event_key(window)
	var binding: Dictionary = _source_name_bindings.get(key, {})
	return (
		not binding.is_empty()
		and str(binding.get("current_name", "")) == str(window.get("instance_name", ""))
		and str(binding.get("visual_name", "")) == str(window.get("placed_name", ""))
	)


func _source_name_is_live(instance_name: String) -> bool:
	var stale := false
	for binding: Dictionary in _source_name_bindings.values():
		if str(binding.get("visual_name", "")) == instance_name:
			if str(binding.get("current_name", "")) == instance_name:
				return true
			stale = true
	return not stale


func _attack_from_instance(instance_name: String) -> Dictionary:
	var attack_key := instance_name.trim_suffix("atm")
	if not _combat["attacks"].has(attack_key):
		return {}
	var result: Dictionary = _combat["attacks"][attack_key].duplicate(true)
	result["instance_name"] = instance_name
	return result


func mark_attack_hit(instance_name: String) -> void:
	_hit_instances[instance_name] = true


func _expire_absent_hit_instances() -> void:
	# Source getHitObj() has no already-hit flag. A removed clip is gone;
	# a later PlaceObject with the same name is a new instance and can hit.
	var live: Dictionary = {}
	for instance_name in current_named_instances():
		if str(instance_name).ends_with("atm"):
			live[str(instance_name)] = true
	for instance_name in _aliased_hitbox_names():
		live[instance_name] = true
	for instance_name in _hit_instances.keys().duplicate():
		if not live.has(instance_name):
			_hit_instances.erase(instance_name)


func _apply_action_exit() -> bool:
	if not _combat["action_exits"].has(action):
		return false
	var exit: Dictionary = _combat["action_exits"][action]
	if current_source_frame() != int(exit["frame"]):
		return false
	var target := str(exit["target"])
	var leave_scripted_flight := _uses_scripted_flight()
	if target == _death_launch_label():
		# Source 超必杀2@942: yup/htx then gotoAndStop("击飞"); play().
		# beidax(true) keeps applying those until touch → 击落地.
		_begin_self_launch(exit)
	start_action(target)
	# 招3 sets jump=1 so on_enterframe skips zhongli; goto "落" then
	# 落 frame 56 does jump=0 and gravity is _root.zhongli.
	if leave_scripted_flight and target in ["落", "落2"]:
		airborne = true
		_zhongli_fall = true
		_vertical_velocity = 0.0
	return true


func _begin_self_launch(exit: Dictionary) -> void:
	# Player wrapper: moveX(-htx) => _x += -htx * scale_X; moveY(-yup) goes up.
	_hurt_motion_ticks = 0
	_hurt_horizontal_step = -float(facing) * float(exit.get("htx", 0.0))
	_hurt_vertical_step = -float(exit.get("yup", 0.0))
	_launched = true
	_hurt_falling = true


func start_action(label: String, reason: String = "runtime_transition") -> void:
	if label in disabled_actions:
		return
	if sw and not _is_death_sequence_action(label):
		return
	var frames := action_range(label)
	if frames.is_empty():
		push_error("Missing source action for %s: %s" % [fighter_name, label])
		return
	var before := _diagnostic_state()
	_source_goto_pending_frames.clear()
	_source_goto_defer_advance_once = false
	var previous_action := action
	action = label
	if label == "站立":
		beida = 0
		hited = 0
	if label == _death_launch_label():
		# Source 击飞 first frame: hited = 0; play();
		hited = 0
	guarding = label in ["防御", "防御2", "防住"] and _guard_held
	if label != "防住":
		_guard_horizontal_step = 0.0
	if label == "被打" or label == _death_launch_label():
		_hurt_stop_applied = false
	_energy_event_applied = false
	_health_events_applied.clear()
	_summon_applied = false
	_presentation_events_applied.clear()
	_super_events_applied.clear()
	_clear_clip_placements()
	_body_warps_applied.clear()
	_scripted_jump = false
	# Keep helper_spawn until GameWorld consumes yfgj(). start_action("站立")
	# on the same tick must not drop doZhaoHuan's placement.
	timeline_playing = true
	_hit_instances.clear()
	play_action(label)
	_queue_source_frame(current_source_frame())
	last_event = "action_%s" % label
	if previous_action != action:
		_emit_diagnostic("action_transition", {"slot": diagnostic_slot,
			"source": diagnostic_role, "reason": reason, "phase": "start_action",
			"before": before, "after": _diagnostic_state()})
	if RollbackPresentation.should_emit_combat_console_event(self):
		print("COMBAT_EVENT ", JSON.stringify(snapshot()))


func _queue_source_frame(frame: int, defer_until_next_tick: bool = false) -> void:
	assert(source_body_available, "Cannot queue a frame on a retired body")
	_reconcile_source_name_bindings()
	_source_frame_execution_serial += 1
	var entry := {"frame": frame,
		"order": frame_script_sequence.call() if frame_script_sequence.is_valid() else 0,
		"serial": _source_frame_execution_serial}
	if defer_until_next_tick:
		entry["defer_until_tick"] = diagnostic_tick + 1
	_ai_pending_frames.append(entry)
	source_frame_changed.emit(frame)


func _apply_ai_source_frame(drain_nested: bool = true, initial_limit: int = -1) -> void:
	if not source_body_available:
		return
	var body_epoch := source_body_epoch
	var frame := current_source_frame()
	if _ai_pending_frames.is_empty() and frame != _ai_state_frame_applied:
		_queue_source_frame(frame)
	var initial_count := _ai_pending_frames.size()
	if initial_limit >= 0:
		initial_count = mini(initial_count, initial_limit)
	var applied := 0
	while not _ai_pending_frames.is_empty() and (drain_nested or applied < initial_count):
		if int(_ai_pending_frames[0].get("defer_until_tick", -1)) > diagnostic_tick:
			break
		applied += 1
		var pending_entry: Dictionary = _ai_pending_frames.pop_front()
		var pending: int = int(pending_entry["frame"])
		var pending_serial: int = int(pending_entry.get("serial", 0))
		_apply_body_warps(pending, pending_serial)
		source_frame_script_boundary.emit(pending, true)
		if ai_timeline_controlled or source_body != null:
			var events: Array = ai_source_state.spec["frame_writes"].get(str(pending), []).duplicate()
			events.append_array(ai_source_state.spec["frame_calls"].get(str(pending), []))
			for placement: Dictionary in _combat.get("clip_placements", []):
				if str(placement.get("action", "")) != action:
					continue
				if int(placement.get("frame", -1)) != pending:
					continue
				var placement_event := placement.duplicate(true)
				placement_event["op"] = "clip_placement"
				events.append(placement_event)
			events.sort_custom(func(left: Dictionary, right: Dictionary) -> bool:
				return int(left["line"]) < int(right["line"]))
			for event: Dictionary in events:
				if body_epoch != source_body_epoch:
					return
				if event.has("field"):
					ai_source_state.apply_write(event)
					var field := str(event["field"])
					if field in ["hited", "beida", "bs", "sw"]:
						set(field, ai_source_state.read_field(field))
					elif field == "hits":
						hits = int(ai_source_state.read_field(field))
						if hits == 0:
							last_combo_board = 0
				elif event.get("op") == "energy_delta":
					energy += float(event["delta"])
					_energy_event_applied = true
				elif event.get("op") == "body_warp":
					_apply_body_warp_event(event, pending_serial)
				elif event.get("op") == "root_opponent_warp":
					_apply_root_opponent_warp(event, pending_serial)
				elif event.get("op") == "root_clip_rename":
					_apply_root_clip_rename(event)
				elif event.get("op") == "clip_placement":
					_apply_clip_placement(event)
				elif event.get("op") == "screen_flash":
					screen_flash_requested.emit(int(event.get("color_rgb24", 0xFFFFFF)))
				else:
					assert(not ai_frame_service_requested.get_connections().is_empty(), "Unconnected CPU frame service")
					ai_frame_service_requested.emit(event)
		else:
			ai_source_state.apply_frame(pending)
			_apply_hits_reset(pending)
			for write: Dictionary in ai_source_state.spec["frame_writes"].get(str(pending), []):
				if write["field"] == "hits":
					hits = int(ai_source_state.read_field("hits"))
					if hits == 0:
						last_combo_board = 0
		if body_epoch != source_body_epoch:
			return
		_apply_hit_settlement_frame(pending)
		# A retained DoAction still runs when a newer callback has changed the
		# playhead. Source doZhaoHuan frames contain only this call.
		for summon: Dictionary in _combat.get("summon_events", []):
			if int(summon["frame"]) == pending and str(summon.get("call_kind", "doZhaoHuan")) == "doZhaoHuan":
				_summon_applied = true
				_execute_summon_event(summon)
		if pending_entry.get("interrupted_super_preparation", false):
			_clear_interrupted_super_preparation(false)
		_ai_state_frame_applied = pending
		source_frame_script_boundary.emit(pending, false)


func _try_start_action(label: String) -> bool:
	if label in disabled_actions:
		return false
	if _combat_input_locked() and not _is_death_sequence_action(label):
		return false
	if action_range(label).is_empty():
		return false
	start_action(label, "command_input_or_cancel")
	return true


func _dispatch_cancels(input_state: Dictionary) -> bool:
	var window := _commands.match_cancel(
		action, current_source_frame(), input_state, energy
	)
	if window.is_empty():
		return false
	var label := str(window.get("to", ""))
	if label == "" or label == action:
		return false
	# Sample the current display list before start_action swaps it.
	_stash_current_attack()
	var entry := _commands.entry(label)
	var handler := str(entry.get("handler", "start_action"))
	if handler == "start_jump":
		_start_jump(false)
		return true
	if handler == "start_dash":
		_start_dash(false, false)
		return true
	return _try_start_action(label)


func _stash_current_attack() -> void:
	# Clear first so attack_contact samples the live display list, not an older stash.
	_stashed_attack = {}
	if opponent == null or not is_instance_valid(opponent):
		return
	var contact := attack_contact(opponent)
	if not contact.is_empty():
		_stashed_attack = contact


func discard_unused_stashed_attack() -> void:
	_stashed_attack = {}


func _dispatch_catalog(context: String, input_state: Dictionary) -> bool:
	var entry := _commands.match_context(context, input_state, energy, true)
	if entry.is_empty():
		return false
	var handler := str(entry.get("handler", "start_action"))
	var label := str(entry.get("label", ""))
	if handler == "start_jump":
		_start_jump(false)
		return true
	if handler == "start_dash":
		# rush() is 冲 and not 上/下; vertical L dashes were not sourced here.
		_start_dash(false, false)
		return true
	return _try_start_action(label)


func has_command(label: String) -> bool:
	return _commands.has_label(label)


func command_is_wired(label: String) -> bool:
	return _commands.is_wired(label)


func command_gaps() -> Array:
	return _commands.gaps()


func start_command(label: String) -> bool:
	# Public hook for later move work and extra fighters. Labels are the
	# original timeline IDs; catalog_only still plays if the span exists.
	return _try_start_action(label)


func _start_jump(second_jump: bool) -> void:
	if airborne and (not second_jump or _double_jump_used):
		return
	if airborne:
		_double_jump_used = true
	else:
		airborne = true
		_double_jump_used = false
	_zhongli_fall = false
	_jumpinggg = false
	_js = 0.0
	_vertical_velocity = 0.0
	start_action("跳2" if second_jump else "跳")


func _start_drop_through() -> bool:
	# jumpDown() returns false only when touchFloor; doDropDown() then does
	# _y += _root.zhongli and gotoAndPlay("落2"). The +10 leaves the isHitBan
	# window (ban._y - 10, ban._y], so the next surface below is used.
	if _touch_floor():
		return false
	position.y += _zhongli()
	airborne = true
	_zhongli_fall = true
	_vertical_velocity = 0.0
	start_action("落2")
	return true


func _update_air_motion(input_state: Dictionary) -> bool:
	if not airborne:
		return false
	var step := _on_jumping_step()
	if step != 0:
		var direction := int(input_state.get("right", false)) - int(input_state.get("left", false))
		if direction != 0:
			_move_world_x(direction * float(_combat["movement"]["speed_per_tick"]))
			set_facing(direction)
	if (
		_jump_pressed
		and not _double_jump_used
		and step in [2, 3]
	):
		_start_jump(true)
		return true
	if action in ["跳", "跳2", "落", "落2"]:
		if bool(input_state.get("special", false)) and energy >= 100.0:
			var air_special := "空中必杀"
			_try_start_action(air_special)
		elif bool(input_state.get("ranged", false)):
			_try_start_action("跳招")
		elif bool(input_state.get("attack", false)):
			_try_start_action("跳砍")
	var previous_y := position.y
	var window := _current_jump_window()
	if not window.is_empty() and current_source_frame() == int(window["start_frame"]):
		# New PlaceObject instance. clip_lifecycle probe: enterFrame starts
		# on the next root frame, and `js` does not carry to the new clip.
		_js = 0.0
		_jumpinggg = false
	if step == 1 or step == 4:
		if not _jumpinggg:
			_jumpinggg = true
			_js = float(_fighter["movement_constants"]["jump_power"])
		_js -= 1.0
		position.y -= _js
	elif step == 2 or step == 5:
		_jumpinggg = false
		position.y -= _js
	elif not _jump_flag_locked():
		# on_enterframe: floor equality and isHitBan() return before zhongli.
		# jump=1 (steps 1/2/4/5) already skipped above. doDropDown has left
		# the ban window and sets `_zhongli_fall`.
		var ban_y := _hit_ban_y(Vector2(position.x, previous_y))
		if not is_nan(ban_y) and not _zhongli_fall:
			position.y = ban_y
		elif not is_equal_approx(previous_y, _ground_y):
			position.y += _zhongli()
	var landing_y := _landing_surface_y(previous_y, position.y)
	var falling := position.y > previous_y
	if not is_nan(landing_y) and falling:
		position.y = landing_y
		_vertical_velocity = 0.0
		_js = 0.0
		_jumpinggg = false
		airborne = false
		_zhongli_fall = false
		start_action("落地")
		return true
	return true


func _start_dash(up: bool, down: bool) -> void:
	if up or down:
		if energy < 100.0:
			return
		change_energy(-100.0)
		_dash_ticks = 9
		_dash_velocity = Vector2(0.0, -14.0 if up else 12.0)
		airborne = true
		start_action("落")
		return
	# Horizontal 瞬步 motion comes from the clip enterFrame
	# (`speed * 2.5 * scale_X`). Do not also run _dash_ticks or the
	# compiled cancel windows on that clip never fire.
	_dash_ticks = 0
	_dash_velocity = Vector2.ZERO
	start_action("瞬步")


func _update_dash_motion() -> bool:
	if _dash_ticks <= 0:
		return false
	position += _dash_velocity
	position.x = clampf(position.x, _wall_min, _wall_max)
	_dash_ticks -= 1
	if _dash_ticks == 0:
		if _dash_velocity.y != 0.0:
			_vertical_velocity = -_dash_velocity.y
			start_action("落2")
		else:
			start_action("站立")
	return true


func _finish_action() -> void:
	if sw:
		# Source standup() and 击落地 sw-stop never leave death for 起身/站立.
		if action == _death_down_label():
			timeline_playing = false
			last_event = "death_stop"
		return
	var fallthrough := _timeline_fallthrough_target()
	if fallthrough != "":
		# Adjacent labels with no stop/goto keep playing. 砍技1 has no
		# terminal script, so a whiff still reaches 砍技12 and explodes.
		start_action(fallthrough)
		return
	if airborne or (source_body == null and _hurt_falling):
		start_action("落2" if _double_jump_used else "落")
	else:
		start_action("站立")


func _timeline_fallthrough_target() -> String:
	for item: Dictionary in _combat.get("timeline_fallthroughs", []):
		if str(item.get("from", "")) == action:
			return str(item.get("to", ""))
	return ""


func _run_source_motion(input_state: Dictionary = {}) -> void:
	var frame := current_source_frame()
	var speed := float(_combat["movement"]["speed_per_tick"])
	for window: Dictionary in _combat.get("motion_windows", []):
		if str(window.get("action", "")) != action:
			continue
		if frame < int(window["start_frame"]) or frame > int(window["end_frame"]):
			continue
		if window.has("contact_cancel_to") and _motion_contact_hit(window):
			_try_start_action(str(window["contact_cancel_to"]))
			return
		if window.has("forward_speed_factor"):
			var distance := speed * float(window["forward_speed_factor"])
			if bool(window.get("round_forward", false)):
				distance = roundf(distance)
			if window.has("contact_cancel_to") and _sweep_motion_contact(window, distance):
				return
			_move_forward(distance)
		if window.has("steer_speed_factor"):
			var steer := (
				int(input_state.get("right", false))
				- int(input_state.get("left", false))
			)
			if steer != 0:
				_move_world_x(steer * speed * float(window["steer_speed_factor"]))
				set_facing(steer)
		if window.has("forward_pixels"):
			_move_forward(float(window["forward_pixels"]))
		if window.has("vertical_pixels"):
			position.y += float(window["vertical_pixels"])
		if window.has("vertical_speed_factor"):
			var previous_y := position.y
			var rise := speed * float(window["vertical_speed_factor"])
			if bool(window.get("round_vertical", false)):
				rise = roundf(rise)
			position.y += rise
			if window.has("land_cancel_to"):
				var landing_y := _landing_surface_y(previous_y, position.y)
				if not is_nan(landing_y):
					position.y = landing_y
					airborne = false
					_vertical_velocity = 0.0
					_try_start_action(str(window["land_cancel_to"]))
					return
		elif window.has("land_cancel_to") and _has_support_at(position):
			airborne = false
			_vertical_velocity = 0.0
			_try_start_action(str(window["land_cancel_to"]))
			return
	if action == "防住" and _guard_horizontal_step != 0.0:
		_move_world_x(_guard_horizontal_step)
	_update_projectiles()


func _uses_scripted_flight() -> bool:
	# Source `jump = 1` on the player wrapper skips on_enterframe zhongli
	# until the next start_action. 超必杀@884 sets this before fallthrough.
	if _scripted_jump:
		return true
	for window: Dictionary in _combat.get("motion_windows", []):
		if str(window.get("action", "")) != action:
			continue
		if (
			window.has("vertical_speed_factor")
			or window.has("vertical_pixels")
			or window.has("land_cancel_to")
		):
			return true
	return false


func _motion_contact_hit(window: Dictionary) -> bool:
	var instance_name := str(window.get("contact_instance", ""))
	if opponent != null and is_instance_valid(opponent):
		var body := opponent.instance_global_bounds("bdmn")
		if not body.has_area():
			return false
		if instance_name != "":
			var attack_bounds := instance_global_bounds(instance_name)
			return attack_bounds.has_area() and SourceHitTest.intersects(body, attack_bounds)
		return not attack_contact(opponent).is_empty()
	return instance_name != "" and _hit_instances.has(instance_name)


func _sweep_motion_contact(window: Dictionary, forward_distance: float) -> bool:
	if opponent == null or not is_instance_valid(opponent):
		return false
	var instance_name := str(window.get("contact_instance", ""))
	if instance_name == "":
		return false
	var attack_bounds := instance_global_bounds(instance_name)
	var body := opponent.instance_global_bounds("bdmn")
	if not attack_bounds.has_area() or not body.has_area():
		return false
	var delta_x := forward_distance * float(facing)
	var fraction := _horizontal_sweep_fraction(attack_bounds, body, delta_x)
	if fraction < 0.0:
		return false
	# The Flash clip tests before each speed*2 step. The swept fallback preserves
	# the first crossed contact when converted AABBs would otherwise tunnel.
	var contact_distance := absf(delta_x) * fraction
	_move_world_x(float(signf(delta_x)) * minf(absf(delta_x), contact_distance + 0.01))
	_try_start_action(str(window["contact_cancel_to"]))
	return true


func _horizontal_sweep_fraction(moving: Rect2, target: Rect2, delta_x: float) -> float:
	return SourceSweepGeometry.horizontal_sweep_fraction(moving, target, delta_x)


func _update_projectiles() -> void:
	var frame := current_source_frame()
	var live: Dictionary = {}
	var moved := false
	for projectile: Dictionary in _combat.get("projectiles", []):
		if str(projectile.get("action", "")) != action:
			continue
		if frame < int(projectile["start_frame"]) or frame > int(projectile["end_frame"]):
			continue
		var instance_name := str(projectile["instance_name"])
		live[instance_name] = true
		var existed := _instance_local_frames.has(instance_name)
		if not existed:
			_start_clip_playhead(instance_name, projectile)
			moved = true
		var jumped_hit := run_projectile_callback(projectile)
		moved = true
		if existed and not jumped_hit:
			_advance_clip_playhead(instance_name, projectile)
	for instance_name in _instance_local_offsets.keys():
		if live.has(instance_name) or _placement_owned.has(instance_name):
			continue
		_instance_local_offsets.erase(instance_name)
		_instance_local_frames.erase(instance_name)
		moved = true
	if moved:
		refresh_display()


func run_projectile_callback(projectile: Dictionary) -> bool:
	var instance_name := str(projectile["instance_name"])
	var speed := float(_combat["movement"]["speed_per_tick"])
	var jumped_hit := false
	var blocked := _projectile_blocked(instance_name, projectile)
	if blocked:
		var hit_variables := instance_source_variables(instance_name)
		var goto_conditions: Array = projectile.get("on_hit_goto_conditions", [])
		# Child ClipActions run in source order after their collision query. Their
		# writes target the owning fighter timeline, while an authored opponent
		# goto is conditional on the opponent's source action field.
		for event: Dictionary in projectile.get("on_hit_events", []):
			match str(event.get("op", "")):
				"write":
					ai_source_state.apply_write(event)
				"local_write_group":
					jumped_hit = _apply_projectile_local_write(instance_name, event) or jumped_hit
				"goto":
					if opponent != null and is_instance_valid(opponent):
						if opponent.ai_source_state.read_field("动作") == int(event["action"]):
							opponent.goto_ai_label(str(event["label"]), bool(event["play"]))
				_: assert(false, "Uncompiled projectile hit event")
		var goto_allowed := _projectile_conditions_match(hit_variables, goto_conditions)
		if not projectile.get("on_hit_goto_grouped", false) and goto_allowed and projectile.has("on_hit_goto_frame") and not _clip_past_hit(
			instance_name, projectile
		):
			set_instance_clip_frame(
				instance_name, int(projectile["on_hit_goto_frame"]), true
			)
			jumped_hit = true
		# A hit write or opponent goto does not block this child clip's natural
		# advance. Only a source-authored child goto is a child timeline jump.
		if not projectile.get("motion_after_collision", false):
			return jumped_hit
	if not blocked or projectile.get("motion_after_collision", false):
		var offset := instance_local_offset(instance_name)
		var source_variables := instance_source_variables(instance_name)
		var motion_conditions: Array = projectile.get("local_motion_conditions", [])
		if not _projectile_conditions_match(source_variables, motion_conditions):
			return jumped_hit
		var step := float(source_variables.get("movspeed", projectile.get("initial_speed",
			speed * float(projectile.get("speed_factor", 1.0)))))
		# The source sets movspeed=0 on impact; losing contact cannot restart it.
		if projectile.has("initial_speed") and _clip_past_hit(instance_name, projectile):
			step = 0.0
		if projectile.has("local_x_delta"):
			offset.x += float(projectile["local_x_delta"])
		else:
			offset.x += step * float(projectile.get("local_x_factor", 0.0))
		if projectile.has("local_y_delta"):
			offset.y += float(projectile["local_y_delta"])
		else:
			offset.y += step * float(projectile.get("local_y_factor", 0.0))
		set_instance_local_offset(instance_name, offset)
	return jumped_hit


func _start_clip_playhead(instance_name: String, projectile: Dictionary) -> void:
	set_instance_clip_frame(instance_name, 1, not _is_stop_frame(projectile, 1), 0)
	var record: Dictionary = _instance_local_frames[instance_name]
	var variables: Dictionary = projectile.get("initial_variables", {}).duplicate(true)
	if projectile.has("initial_speed_field"):
		variables["movspeed"] = float(ai_source_state.read_field(str(projectile["initial_speed_field"]))) * float(projectile.get("initial_speed_factor", 1.0))
	record["source_variables"] = variables
	record["child_stop_frames"] = projectile.get("child_stop_frames", {}).duplicate(true)
	_instance_local_frames[instance_name] = record


func _apply_projectile_local_write(instance_name: String, event: Dictionary) -> bool:
	var variables := instance_source_variables(instance_name)
	var conditions: Array = event.get("conditions", [])
	if not _projectile_conditions_match(variables, conditions):
		return false
	for write: Dictionary in event.get("writes", []):
		# A source assignment can create a property on the clip; a preceding
		# `var` declaration is not required. Reads still require compiled state.
		variables[str(write["field"])] = write["value"]
	var record: Dictionary = _instance_local_frames.get(instance_name, {})
	record["source_variables"] = variables
	_instance_local_frames[instance_name] = record
	if event.has("goto_frame") and not _clip_past_hit(instance_name, {"on_hit_goto_frame": event["goto_frame"]}):
		set_instance_clip_frame(instance_name, int(event["goto_frame"]), true)
		return true
	return false


func _projectile_conditions_match(variables: Dictionary, conditions: Array) -> bool:
	for condition: Dictionary in conditions:
		assert(variables.has(condition["field"]), "Projectile guard reads an undeclared local")
		var actual: Variant = variables[condition["field"]]
		var expected: Variant = condition["value"]
		match str(condition["operator"]):
			"==":
				if actual != expected:
					return false
			"!=":
				if actual == expected:
					return false
			_:
				assert(false, "Unsupported projectile local guard")
	return true


func instance_source_variables(instance_name: String) -> Dictionary:
	var record: Dictionary = _instance_local_frames.get(instance_name, {})
	return record.get("source_variables", {}).duplicate(true)


func _advance_clip_playhead(instance_name: String, projectile: Dictionary) -> void:
	if not _instance_local_frames.has(instance_name):
		return
	var record: Dictionary = _instance_local_frames[instance_name]
	var current := int(record.get("local_start", 1))
	var age := int(record.get("age", 0)) + 1
	if not bool(record.get("playing", true)) or _is_stop_frame(projectile, current):
		set_instance_clip_frame(instance_name, current, false, age)
		return
	var next_frame := current + 1
	if projectile.has("frame_count"):
		next_frame = posmod(current, int(projectile["frame_count"])) + 1
	set_instance_clip_frame(
		instance_name, next_frame, not _is_stop_frame(projectile, next_frame), age
	)


func _is_stop_frame(projectile: Dictionary, frame: int) -> bool:
	for item in projectile.get("stop_frames", []):
		if int(item) == frame:
			return true
	return false


func _clip_past_hit(instance_name: String, projectile: Dictionary) -> bool:
	if not projectile.has("on_hit_goto_frame"):
		return false
	return instance_clip_frame(instance_name) >= int(projectile["on_hit_goto_frame"])


func _projectile_blocked(instance_name: String, projectile: Dictionary = {}) -> bool:
	# getHitObj runs in the receiver, independently of this child's hitTest.
	# Its settled-hit cache cannot stand in for the callback's current geometry
	# (including a temporarily absent bdmn or a new same-name placement).
	if projectile.has("collision_queries"):
		if opponent == null or not is_instance_valid(opponent):
			return false
		for query: Dictionary in projectile["collision_queries"]:
			var bounds := instance_global_bounds(instance_name) if query["receiver"] == "self" else child_instance_global_bounds(instance_name, query["receiver"])
			var target := opponent.source_projectile_target_bounds(query["target"])
			if bounds.has_area() and target.has_area() and SourceHitTest.intersects(bounds, target):
				return true
		return false
	if _hit_instances.has(instance_name):
		return true
	if opponent == null or not is_instance_valid(opponent):
		return false
	var body := opponent.instance_global_bounds("bdmn")
	var attack_bounds := instance_global_bounds(instance_name)
	return body.has_area() and attack_bounds.has_area() and SourceHitTest.intersects(body, attack_bounds)


func source_projectile_target_bounds(source_name: String) -> Rect2:
	# A source rename replaces the property used by the other fighter's query.
	var hidden_authored_name := false
	var newest_generation := -1
	var bound_key := ""
	for key: String in source_projectiles:
		var projectile: RefCounted = source_projectiles[key].get_ref()
		if projectile == null:
			continue
		var current_name: Variant = projectile.current_source_name()
		if current_name == null:
			continue
		if current_name == source_name and projectile.generation > newest_generation:
			newest_generation = projectile.generation
			bound_key = key
		if projectile.model.get("authored_name", key) == source_name:
			hidden_authored_name = true
	if bound_key != "":
		return super.instance_global_bounds(bound_key)
	if hidden_authored_name:
		return Rect2()
	for projectile: Dictionary in _combat.get("projectiles", []):
		var authored := str(projectile["instance_name"])
		if source_projectiles.has(authored):
			continue
		if not _instance_local_frames.has(authored):
			continue
		if current_source_frame() < int(projectile["start_frame"]) or current_source_frame() > int(projectile["end_frame"]):
			continue
		var current_name := authored
		for rename: Dictionary in projectile.get("rename_frames", []):
			if instance_clip_frame(authored) >= int(rename["frame"]):
				current_name = rename["instance_name"]
				if rename.has("name_field"):
					var variables := instance_source_variables(authored)
					assert(variables.has(rename["name_field"]), "Undeclared projectile rename local")
					current_name = str(variables[rename["name_field"]])
		if current_name == source_name:
			return super.instance_global_bounds(authored)
		if authored == source_name:
			hidden_authored_name = true
	return Rect2() if hidden_authored_name else instance_global_bounds(source_name)


func _update_hurt_motion() -> void:
	# Source beidax(): moveX/moveY for time<=13; then yup=0 and non-flying
	# htx=0. No zhongli. 被打 stays at the yup height until tdtime/play().
	# 击飞 keeps falling via the flying branch after time>15.
	if _hurt_motion_ticks <= 13:
		_move_world_x(_hurt_horizontal_step)
		position.y += _hurt_vertical_step
	_hurt_motion_ticks += 1
	if _hurt_motion_ticks == 16 and not _launched and position.y < _ground_y:
		airborne = true
	if _hurt_motion_ticks > 15 and _launched:
		_update_hurt_fall()


func _update_hurt_fall() -> bool:
	if not _hurt_falling:
		return false
	# beidax() non-flying never applies zhongli. Hover until 被打 ends.
	if not _launched and action == "被打":
		return false
	if _hurt_motion_ticks <= 15:
		_hurt_motion_ticks += 1
		return true
	var previous_y := position.y
	var next_y := position.y + 10.0
	var landing_y := _landing_surface_y(previous_y, next_y)
	if is_nan(landing_y):
		position.y = next_y
		if action == "击飞":
			return true
		if action != "被打" and action not in ["落", "落2"]:
			start_action("落")
		return true
	position.y = landing_y
	_hurt_falling = false
	airborne = false
	if _launched or action in ["击飞", "击落地"]:
		_launched = false
		if action != "击落地":
			start_action("击落地")
		return false
	if action != "被打":
		start_action("落地")
	return false


func configure_stage(
	ground_y: float,
	platforms: Array[Rect2],
	wall_min: float = 20.0,
	wall_max: float = 970.0
) -> void:
	_ground_y = ground_y
	_stage_platforms = platforms.duplicate()
	_wall_min = wall_min
	_wall_max = wall_max


func change_energy(amount: float) -> void:
	energy = clampf(energy + amount, 0.0, 300.0)


func _apply_source_energy_event() -> void:
	# Source-controlled timelines execute energy writes from their compiled
	# frame statement. The metadata event list is a legacy fallback only; using
	# both paths replays the same source write after a queued frame transition.
	if ai_timeline_controlled or source_body != null:
		return
	if _energy_event_applied:
		return
	for event: Dictionary in _combat.get("energy_events", []):
		if event["action"] == action and int(event["frame"]) == current_source_frame():
			change_energy(float(event["delta"]))
			_energy_event_applied = true


func _apply_source_health_event() -> void:
	var health_events: Array = _combat.get("health_events", [])
	for event_index in health_events.size():
		var event: Dictionary = health_events[event_index]
		if event["action"] != action or int(event["frame"]) != current_source_frame():
			continue
		var event_key := "%s:%d:%d:%s" % [action, int(event["frame"]), event_index, str(event.get("source_sha256", ""))]
		if _health_events_applied.has(event_key):
			continue
		_health_events_applied[event_key] = true
		if ai_source_state.read_field("wudi") == true:
			continue
		var loss := float(event["above_damage"]) if health > float(event["threshold"]) else health * float(event["below_ratio"])
		health -= loss


func _apply_summon_event() -> void:
	if _summon_applied:
		return
	for event: Dictionary in _combat.get("summon_events", []):
		if str(event.get("call_kind", "doZhaoHuan")) == "doZhaoHuan":
			continue
		if event["action"] != action or int(event["frame"]) != current_source_frame():
			continue
		_summon_applied = true
		_execute_summon_event(event)
		return


func _execute_summon_event(event: Dictionary) -> void:
	if event.has("skip_if_truthy") and _ai_hit_transfer.truth(
		ai_source_state.read_field(str(event["skip_if_truthy"]))
	):
		return
	if event.get("set_bs") != null:
		bs = int(event["set_bs"])
	if event.has("energy_delta"):
		change_energy(float(event["energy_delta"]))
	helper_spawn = _yfgj_spawn(event)
	helper_spawn_requested.emit()
	last_event = "summon_%s" % event.get("helper_id", "helper")
	if RollbackPresentation.should_emit_combat_console_event(self):
		print("COMBAT_EVENT ", JSON.stringify(snapshot()))


func _apply_presentation_events() -> void:
	for index in range(_combat.get("presentation_events", []).size()):
		var event: Dictionary = _combat["presentation_events"][index]
		if event["action"] != action or int(event["frame"]) != current_source_frame():
			continue
		# AI/source-body timelines execute root DoAction calls from frame_calls.
		# The combat presentation index contains the same authored root shine for
		# visual lookup, so consume it only once while retaining child-clip shines
		# whose source path is not present in the root frame call list.
		if event.get("op") == "screen_flash" and (ai_timeline_controlled or source_body != null):
			var duplicate_root_flash := false
			for call: Dictionary in ai_source_state.spec.get("frame_calls", {}).get(str(current_source_frame()), []):
				if call.get("op") != "screen_flash":
					continue
				if (str(call.get("path", "")) == str(event.get("source_path", ""))
					and int(call.get("line", -1)) == int(event.get("source_line", -2))
					and int(call.get("color_rgb24", 0xFFFFFF)) == int(event.get("color_rgb24", 0xFFFFFF))):
					duplicate_root_flash = true
					break
			if duplicate_root_flash:
				continue
		var event_key := "%s:%d:%d" % [action, current_source_frame(), index]
		if _presentation_events_applied.has(event_key):
			continue
		_presentation_events_applied[event_key] = true
		if event.get("op") == "screen_flash":
			screen_flash_requested.emit(int(event.get("color_rgb24", 0xFFFFFF)))


func _apply_body_warps(frame: int = -1, invocation_serial: int = -1) -> void:
	# Source `_parent._x/_y = _root.game["p"+pn]._x/_y` writes the player
	# container, not a named clip. 832 copies X only, so a jump-height
	# defender stays outside later *atm AABBs.
	var invocation_serials: Array[int] = []
	var source_frame := current_source_frame() if frame < 0 else frame
	if invocation_serial >= 0:
		invocation_serials.append(invocation_serial)
	else:
		for pending: Dictionary in _ai_pending_frames:
			if int(pending.get("frame", -1)) == source_frame:
				invocation_serials.append(int(pending.get("serial", 0)))
	if invocation_serials.is_empty():
		invocation_serials.append(_source_frame_execution_serial)
	for event: Dictionary in _combat.get("body_warps", []):
		if str(event.get("action", "")) != action:
			continue
		if int(event.get("frame", -1)) != source_frame:
			continue
		if str(event.get("op", "")) not in ["warp_to_opponent", "offset_parent_x_by_xscale"]:
			continue
		for serial_item: int in invocation_serials:
			_apply_body_warp_event(event, serial_item)


func _body_warp_event_key(event: Dictionary, invocation_serial: int) -> String:
	var source_path := str(event.get("path", event.get("source_path", "")))
	if source_path.is_empty():
		source_path = str(event.get("action", action))
	var source_frame := int(event.get("frame", current_source_frame()))
	var warp: Dictionary = event.get("warp", event)
	var operation := str(warp.get("op", event.get("op", "")))
	var serial := invocation_serial if invocation_serial >= 0 else _source_frame_execution_serial
	return "%s:%d:%s:%d" % [source_path, source_frame, operation, serial]


func _apply_body_warp_event(event: Dictionary, invocation_serial: int = -1) -> void:
	var warp: Dictionary = event.get("warp", event)
	var operation := str(warp.get("op", ""))
	if operation not in ["offset_parent_x_by_xscale", "warp_to_opponent"]:
		return
	if operation == "warp_to_opponent" and (opponent == null or not is_instance_valid(opponent)):
		return
	var event_key := _body_warp_event_key(event, invocation_serial)
	if _body_warps_applied.has(event_key):
		return
	if operation == "offset_parent_x_by_xscale":
		# Flash _xscale is expressed in percent; scale.x retains that local sign and magnitude.
		source_x += scale.x * 100.0 * float(warp.get("xscale_factor", 0.0))
		_body_warps_applied[event_key] = true
		return
	var branch: Dictionary = warp
	if warp.has("xscale_gt_0"):
		branch = warp["xscale_gt_0"] if scale.x > 0 else warp["xscale_lt_0"]
	if branch.has("set_xscale"):
		# A container _xscale write does not assign the source scale_X variable.
		# BODY pressure keeps using scale_X until updateDirect explicitly changes it.
		scale.x = float(branch["set_xscale"]) / 100.0
	# Source `_x = opponent._x - opponent.mc.bdmn._width * 1.7`
	# reads the clip's local width. Global bounds include the scene scale and
	# would shrink the source-authored container warp before applying it to
	# source_x coordinates.
	# AS2 keeps a missing `bdmn` as undefined.  The authored arithmetic then
	# does not produce a usable coordinate write; a present zero-area clip is a
	# different case and must still contribute width/height zero.
	var body_exists := "bdmn" in opponent.current_named_instances()
	var body := opponent.instance_local_bounds("bdmn")
	# Width and height are independent Flash properties.  Do not collapse a
	# thin (zero-area) but present clip to (0, 0): one axis may still be valid.
	var body_size := body.size
	# Only an authored dimension read is poisoned by a missing clip.  A plain
	# opponent._x/_y assignment remains a valid source write on its own axis;
	# this matters for mixed scripts such as x-width + plain y.
	var x_reads_body_width := branch.has("x_bdmn_width")
	var y_reads_body_height := warp.has("y_bdmn_height")
	# Flash MovieClip._width/_height round transformed bounds to the nearest twip.
	# Lee/Yihu: 26.63017 -> 26.65 and 44.71463 -> 44.7; Lee/Naruto:
	# 26.610... -> 26.6. This quantizes only source dimension reads.
	# Keep dimension reads in double precision. Vector2 would turn 26.65 into
	# 26.649999..., losing a twip at the subsequent AS2 coordinate setter.
	var source_body_width := roundf(body_size.x * 20.0) / 20.0
	var source_body_height := roundf(body_size.y * 20.0) / 20.0
	if (not x_reads_body_width or body_exists) and bool(warp.get("place_x", true)):
		source_x = (
			opponent.source_x
			+ float(branch.get("x_pixels", 0.0))
			+ source_body_width * float(branch.get("x_bdmn_width", 0.0))
		)
	if branch.has("set_scale_x"):
		facing = int(branch["set_scale_x"])
	if (not y_reads_body_height or body_exists) and bool(warp.get("place_y", false)):
		source_y = (
			opponent.source_y
			+ float(warp.get("y_pixels", 0.0))
			+ source_body_height * float(warp.get("y_bdmn_height", 0.0))
		)
	if bool(warp.get("set_jump", false)):
		_scripted_jump = true
		airborne = true
	_body_warps_applied[event_key] = true


func _apply_root_opponent_warp(event: Dictionary, invocation_serial: int = -1) -> void:
	"""Apply a source `_root.game["p" + pn]` container assignment."""
	if opponent == null or not is_instance_valid(opponent):
		return
	var source_path := str(event.get("path", ""))
	var source_frame := int(event.get("frame", current_source_frame()))
	var serial := invocation_serial if invocation_serial >= 0 else _source_frame_execution_serial
	var event_key := "%s:%d:root_opponent_warp:%d" % [source_path, source_frame, serial]
	if _body_warps_applied.has(event_key):
		return
	if bool(event.get("copy_x", false)):
		opponent.source_x = source_x
	if bool(event.get("copy_y", false)):
		opponent.source_y = source_y
	if bool(event.get("visible", false)):
		opponent.visible = true
	_body_warps_applied[event_key] = true


func _apply_clip_placements() -> void:
	_expire_clip_placements()
	for event: Dictionary in _combat.get("clip_placements", []):
		if str(event.get("action", "")) != action:
			continue
		if int(event.get("frame", -1)) != current_source_frame():
			continue
		_apply_clip_placement(event)


func _apply_clip_placement(event: Dictionary) -> void:
	if str(event.get("op", "")) not in ["place_at_opponent", "clip_placement"]:
		return
	var instance_name := str(event.get("instance_name", ""))
	if instance_name == "":
		return
	var placement_frame := int(event.get("frame", current_source_frame()))
	var event_key := "%s:%d:%s" % [str(event.get("action", action)), placement_frame, instance_name]
	if _clip_placements_applied.has(event_key):
		return
	# DoAction/load runs once even when a referenced MovieClip is undefined.
	# Record the attempt before lookup so a stopped frame cannot retry later.
	# This dictionary is captured by BattleCheckpoint and reset on action entry.
	_clip_placements_applied[event_key] = true
	if opponent == null or not is_instance_valid(opponent):
		return
	# A root _name replacement makes the old AS2 variable undefined.  Keep
	# the authored display object for rendering, but do not replay a later
	# source write through its stale name.
	if not _source_name_is_live(instance_name):
		return
	var origin := named_instance_origin(instance_name)
	if origin == Vector2.INF:
		return
	# Source overwrites clip._x/_y. PlaceObject translate is replaced,
	# so the Godot offset subtracts the remaining matrix origin.
	# xscale > 0: _x = opponent._x - parent._x
	# else:       _x = parent._x - opponent._x
	if bool(event.get("front_only", false)) and (opponent.source_x - source_x) * facing < 0:
		return
	var reference_position := Vector2((opponent.source_x - source_x) * facing,
		opponent.source_y - source_y)
	var parent_transform := _wrapper_transform()
	if bool(event.get("divide_parent_scale_x", false)):
		reference_position.x /= parent_transform.x.length()
	if bool(event.get("divide_parent_scale_y", false)):
		reference_position.y /= parent_transform.y.length()
	var reference_name := str(event.get("reference_instance", ""))
	if not reference_name.is_empty():
		reference_position = named_instance_origin(reference_name)
		if reference_position == Vector2.INF:
			return
		reference_position += instance_local_offset(reference_name)
	var offset := instance_local_offset(instance_name)
	if bool(event.get("place_x", true)):
		var local_x := reference_position.x + float(event.get("x_facing_pixels", 0.0)) * facing
		offset.x = local_x - origin.x
	if bool(event.get("place_y", false)):
		var local_y := reference_position.y
		local_y += float(event.get("y_pixels", 0.0))
		offset.y = local_y - origin.y
	set_instance_local_offset(instance_name, offset)
	_placement_owned[instance_name] = true
	refresh_display()


func _expire_clip_placements() -> void:
	var live: Dictionary = {}
	for instance_name in current_named_instances():
		live[str(instance_name)] = true
	for instance_name in _placement_owned.keys().duplicate():
		if live.has(instance_name):
			continue
		_instance_local_offsets.erase(instance_name)
		_placement_owned.erase(instance_name)


func _clear_clip_placements() -> void:
	for instance_name in _placement_owned.keys():
		_instance_local_offsets.erase(instance_name)
	_placement_owned.clear()
	_clip_placements_applied.clear()


func opponent_pn() -> int:
	# Source: pn = _parent._name != "p1" ? 1 : 2
	return 1 if player_slot == "p2" else 2


func _apply_hits_reset(source_frame: int) -> void:
	var sprite := int(_combat.get("source", {}).get("timeline_symbol_id", 0))
	for item: Dictionary in _combat.get("hits_reset_frames", []):
		if int(item.get("sprite_id", 0)) != sprite:
			continue
		if int(item.get("frame", -1)) != source_frame:
			continue
		hits = 0
		last_combo_board = 0
		return


func _apply_super_events() -> void:
	for event: Dictionary in _combat.get("super_events", []):
		if str(event.get("action", "")) != action:
			continue
		if int(event.get("frame", -1)) != current_source_frame():
			continue
		var event_key := "%s:%d:%s" % [action, current_source_frame(), event.get("op", "")]
		if _super_events_applied.has(event_key):
			continue
		_super_events_applied[event_key] = true
		last_super = event.duplicate()
		_ensure_super_runtime().apply(event, self, opponent, super_helpers)
		super_event_applied.emit(last_super)


func _chase_displayed_health() -> void:
	# Source DefineSprite_1814: bar2 only chases when hits == 0, at maxhp/500.
	if hits != 0:
		return
	var step := max_health / 500.0
	if displayed_health > health:
		displayed_health = maxf(health, displayed_health - step)
	elif displayed_health < health:
		displayed_health = minf(health, displayed_health + step)


func _yfgj_spawn(event: Dictionary) -> Dictionary:
	# Source yfgj(): helper._x = caster._x - 20 * (xscale <= 0 ? -1 : 1)
	# and helper faces the opponent, then gotoAndPlay(2).
	var behind := float(event.get("behind_pixels", 20.0))
	var spawn_x := source_x - behind * facing
	var helper_facing := facing
	if opponent != null and is_instance_valid(opponent):
		helper_facing = -1 if source_x >= opponent.source_x else 1
	return {
		"helper_id": str(event.get("helper_id", "")),
		"helper_swf": str(event.get("helper_swf", "")),
		"x": spawn_x,
		"y": source_y,
		"facing": helper_facing,
		"start_frame": int(event.get("start_frame", 2)),
	}


func _zhongli() -> float:
	# _root.zhongli from scripts/main.json frame_7/DoAction.as
	return 10.0


func _touch_floor() -> bool:
	# on_enterframe: _y == floorY or (_y > floorY - 10 after no ban hit)
	if not is_nan(_hit_ban_y(position)):
		return false
	return is_equal_approx(position.y, _ground_y) or position.y > _ground_y - _zhongli()


func _hit_ban_y(point: Vector2) -> float:
	# isHitBan(): _y <= ban._y && _y > ban._y - 10 && _x in [ban._x, ban._x + _width]
	for platform in _stage_platforms:
		var ban_y := platform.position.y
		if point.y <= ban_y and point.y > ban_y - _zhongli():
			if point.x >= platform.position.x and point.x <= platform.end.x:
				return ban_y
	return NAN


func _landing_surface_y(previous_y: float, next_y: float) -> float:
	var result := NAN
	if previous_y <= _ground_y and next_y >= _ground_y:
		result = _ground_y
	elif next_y > _ground_y - _zhongli() and next_y >= previous_y:
		result = _ground_y
	for platform in _stage_platforms:
		if position.x < platform.position.x or position.x > platform.end.x:
			continue
		var ban_y := platform.position.y
		var crossed := previous_y <= ban_y and next_y >= ban_y
		var in_window := next_y <= ban_y and next_y > ban_y - _zhongli()
		if (crossed or in_window) and (is_nan(result) or ban_y < result):
			result = ban_y
	return result


func _has_support_at(point: Vector2) -> bool:
	if is_equal_approx(point.y, _ground_y):
		return true
	return not is_nan(_hit_ban_y(point))


func _move_world_x(distance: float) -> void:
	position.x = clampf(position.x + distance, _wall_min, _wall_max)


func _move_forward(distance: float) -> void:
	_move_world_x(distance * facing)


func _is_special_action(label: String) -> bool:
	return label in ["必杀", "必杀1", "必杀0", "上必杀", "超必杀", "空中必杀"]


func _death_data() -> Dictionary:
	var death = _combat.get("death")
	if typeof(death) == TYPE_DICTIONARY and not death.is_empty():
		return death
	return {}


func _death_launch_label() -> String:
	var label := str(_death_data().get("launch_label", "击飞"))
	return label if not action_range(label).is_empty() else "击飞"


func _action_stop_frame() -> int:
	# 被打 stop(); and 击飞 stop() (鸣人 1035 / 一护 759). Playhead stays
	# while beidax keeps running. Label end_frame is not this stop.
	if action == str(_combat.get("hurt", {}).get("label", "被打")):
		return int(_combat.get("hurt", {}).get("stop_frame", 0))
	if action == _death_launch_label():
		return int(_combat.get("hurt", {}).get("launch_stop_frame", 0))
	return 0


func _death_down_label() -> String:
	var label := str(_death_data().get("down_label", "击落地"))
	return label if not action_range(label).is_empty() else "击落地"


func _is_death_sequence_action(label: String) -> bool:
	return label == _death_launch_label() or label == _death_down_label()


func _ensure_super_runtime():
	if super_runtime == null:
		super_runtime = load("res://super_runtime.gd").new()
		super_runtime.shine_requested.connect(
			func(color_rgb24: int) -> void:
				screen_flash_requested.emit(color_rgb24)
		)
	return super_runtime


func _game_running() -> bool:
	# Source: return _root.zhanting == false && opponent.mc.sw == false.
	if root_zhanting or (opponent != null and is_instance_valid(opponent) and opponent.root_zhanting):
		return false
	return opponent == null or not is_instance_valid(opponent) or not opponent.sw


func _combat_input_locked() -> bool:
	# Source gameRunning() is false when the opponent's mc.sw is true;
	# own dash/hurtSkill/standup also fail when this.sw or hp <= 0.
	if sw:
		return true
	return opponent != null and is_instance_valid(opponent) and opponent.sw


func _should_stop_dead_knockdown() -> bool:
	if not sw or action != _death_down_label():
		return false
	var stop_frame := int(_death_data().get("knockdown_stop_frame", 0))
	return stop_frame > 0 and current_source_frame() == stop_frame


func _check_dead(flying: bool) -> bool:
	# Source checkDead(fly): if sw, return; if hp <= 0 and modo != 4,
	# set sw, KOplay, and if !fly gotoAndStop("击飞").
	if sw:
		return false
	if health > 0.0:
		return false
	if modo == 4:
		return false
	if _death_data().is_empty() and action_range("击飞").is_empty():
		return false
	var death := _death_data()
	for write: Dictionary in death.get("ko_writes", []):
		ai_source_state.values[write.field] = write.value
	sw = bool(ai_source_state.read_field("sw")) if death.has("ko_writes") else true
	last_event = "ko"
	if death.has("ko_number_binding"):
		var binding: Dictionary = death.ko_number_binding
		ko_requested.emit(int(binding.equal if player_slot == binding.name else binding.different))
	if not flying:
		if ai_timeline_controlled:
			goto_ai_label(_death_launch_label(), false)
			timeline_playing = true
		else:
			_launched = true
			_hurt_falling = true
			start_action(_death_launch_label())
	return true


func _is_hurt_action(label: String) -> bool:
	return label in ["被打", "击飞", "击落地"]


func _current_jump_window() -> Dictionary:
	var frame := current_source_frame()
	for window: Dictionary in _combat.get("jump_windows", []):
		if str(window.get("action", "")) != action:
			continue
		if frame < int(window["start_frame"]) or frame > int(window["end_frame"]):
			continue
		return window
	return {}


func _on_jumping_step() -> int:
	var window := _current_jump_window()
	if window.is_empty():
		return 0
	# evidence/probes/schedule/clip_lifecycle.log: child enterFrame starts
	# on the root frame after PlaceObject, not the placement frame.
	if current_source_frame() == int(window["start_frame"]):
		return 0
	return int(window["step"])


func _jump_flag_locked() -> bool:
	# Frame DoAction sets jump=1 for onJumping 1/2/4/5, including the
	# placement frame where enterFrame has not started yet.
	var window := _current_jump_window()
	if window.is_empty():
		return false
	return int(window["step"]) in [1, 2, 4, 5]


func _is_one_shot_action(label: String) -> bool:
	return label not in [
		"站立", "走", "落", "落2", "防御", "防御2", "被打", "击飞"
	]


func set_facing(value: int) -> void:
	if value == 0:
		return
	facing = signi(value)
	scale.x = absf(scale.x) * facing


func snapshot() -> Dictionary:
	return {
		"fighter": fighter_name,
		"action": action,
		"frame": current_source_frame(),
		"x": position.x,
		"facing": facing,
		"health": health,
		"displayed_health": displayed_health,
		"hits": hits,
		"energy": energy,
		"hitstun_ticks": hitstun_ticks,
		"timeline_playing": timeline_playing,
		"airborne": airborne,
		"guarding": guarding,
		"sw": sw,
		"beida": beida,
		"zhanting": zhanting,
		"bs": bs,
		"hited": hited,
		"event": last_event,
		"helper_spawn": helper_spawn,
	}


func _diagnostic_state() -> Dictionary:
	return {
		"action": action,
		"sourceFrame": current_source_frame(),
		"x": source_x,
		"y": source_y,
		"facing": facing,
		"hp": health,
		"energy": energy,
		"bs": bs,
		"hited": hited,
		"zhanting": zhanting,
		"rootZhanting": root_zhanting,
		"timelinePlaying": timeline_playing,
	}


func _diagnostic_rect(bounds: Rect2) -> Dictionary:
	return {"x": bounds.position.x, "y": bounds.position.y,
		"width": bounds.size.x, "height": bounds.size.y}


func _emit_diagnostic(event_type: String, payload: Dictionary) -> void:
	if diagnostic_runtime == null or not is_instance_valid(diagnostic_runtime):
		return
	var event_payload := payload
	if RollbackPresentation.is_replaying(self):
		event_payload = payload.duplicate(true)
		event_payload["replay"] = true
	diagnostic_runtime.call("push_event", event_type, event_payload, diagnostic_tick)


func retire_source_body() -> void:
	# The wrapper survives, but its mc path is vacant until the load/frame phase.
	# Epoch checks also retire a currently executing old frame's remaining calls.
	source_body_epoch += 1
	source_body_available = false
	source_health_defined = false
	source_body = null
	_ai_pending_frames.clear()
	_source_goto_pending_frames.clear()
	_source_goto_defer_advance_once = false
	_ai_state_frame_applied = -1
	_hit_instances.clear()
	_stashed_attack.clear()
	source_projectiles.clear()
	_source_name_bindings.clear()
	_instance_local_frames.clear()
	_instance_local_offsets.clear()
	_retained_visual_clips.clear()
	_nested_stage_actions.clear()
	_frames = {}
	materialize_display()


func install_source_profile(profile: Dictionary, load_declarations: Array) -> void:
	assert(not source_body_available and source_body == null)
	_wrapper_visual_clips.clear()
	fighter_directory = profile.directory
	_timeline = profile.timeline
	_fighter = profile.fighter
	_combat = profile.combat
	_definitions = {}
	_assets = {}
	_frames = {}
	for definition: Dictionary in _timeline.definitions:
		_definitions[int(definition.character_id)] = definition
	for asset: Dictionary in profile.assets.assets:
		_assets[int(asset.character_id)] = asset.path
	for frame: Dictionary in _timeline.frames:
		_frames[int(frame.frame)] = frame
	_sound_segments = profile.sound_segments.frames
	_nested_sound_segments = profile.sound_segments.get("nested_frames", {})
	_sound_played_frame = -1
	_nested_sound_observation_frame = -1
	_nested_sound_instance_frames.clear()
	_nested_sound_container_states.clear()
	_nested_sound_placement_generations.clear()
	last_sound_ids.clear()
	last_nested_sound_ids.clear()
	last_nested_sound_events.clear()
	hidden_instance_names.clear()
	_health_events_applied.clear()
	_presentation_events_applied.clear()
	_super_events_applied.clear()
	_clip_placements_applied.clear()
	_body_warps_applied.clear()
	_placement_owned.clear()
	ai_source_state = AiSourceState.new()
	ai_source_state.spec = profile.ai
	for field: String in profile.ai.undefined_declarations:
		ai_source_state.values[field] = null
	# New PlaceObject load declarations precede this instance's initial frame.
	for declaration: Dictionary in load_declarations:
		if declaration.has("binding"):
			assert(declaration.binding == "Key.isDown" and declaration.field == "kis")
		else:
			ai_source_state.values[declaration.field] = declaration.value
			if declaration.field == "ql":
				energy = float(declaration.value)
	ai_source_state.apply_frame(1)
	# The compiled initial frame assigns scale_X without changing _xscale.
	assert(profile.ai.form_initialization.wrapper_scale_from_xscale)
	facing = -1 if scale.x <= 0 else 1
	assert(profile.ai.form_initialization.wrapper_visible and profile.ai.form_initialization.body_visible)
	visible = true
	ai_source_state.values["pn"] = 2 if player_slot == "p1" else 1
	_ai_hit_transfer = profile.hit_state_script.new(ai_source_state.values)
	hurt_voice.spec = profile.hurt_voice
	ai_senses = AiSenses.new()
	ai_senses.configure(self, profile.ai)
	_commands = CommandCatalog.new()
	_commands.load_combat(_combat)
	source_power_fields = profile.ai.base_power_fields
	_source_placement_filters_cleared = bool(profile.ai.form_initialization.get("clear_placement_filters", false))
	ai_color_state = AiColorState.new()
	ai_color_state.reset_color()
	_source_color_mul = Color(1, 1, 1, 1)
	_source_color_add = Color(0, 0, 0, 0)
	_source_color_matrix.clear()
	for field in ["bs", "hited", "beida", "sw", "hits"]:
		if ai_source_state.values.get(field) != null:
			set(field, ai_source_state.values[field])
	source_body_available = true
	timeline_playing = true
	_current_frame = 1
	_ai_state_frame_applied = 1
	for label: String in _frames[1].labels:
		_set_ai_action_label(label)
	play_source_frame(1)
