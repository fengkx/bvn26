extends RefCounted

const TTL_TICKS := 8
const MAX_EVENTS := 64
var resources: Array[String] = []
var _events := {}
var _players := {}
var _next_id := 0
var _played := {}
var _guest_players := {}
var error := ""

func _init() -> void:
	_catalog("res://generated")
	resources.sort()

func _catalog(directory: String) -> void:
	# ResourceLoader preserves original names after import/remapping in Web PCKs.
	for name in ResourceLoader.list_directory(directory):
		if name.ends_with("/"): _catalog(directory.path_join(name.trim_suffix("/")))
		elif name.get_extension() in ["wav", "mp3", "ogg"]: resources.append(directory.path_join(name))

static func accepted(source: Node, player: AudioStreamPlayer, offset: float = 0.0, end: float = -1.0) -> void:
	var owner := source
	while owner != null and not owner.has_meta("authority_audio"): owner = owner.get_parent()
	if owner != null: owner.get_meta("authority_audio").record(player, owner.physics_tick, offset, end)

func record(player: AudioStreamPlayer, tick: int, offset: float, end: float) -> void:
	var resource := resources.find(player.stream.resource_path)
	if resource < 0:
		error = "unregistered_authority_sound:" + player.stream.resource_path
		return
	_next_id += 1
	var looped: bool = player.stream is AudioStreamMP3 and player.stream.loop
	_events[_next_id] = {"id": _next_id, "resource": resource, "tick": tick, "offset": offset,
		"end": end, "volume": player.volume_db, "pitch": player.pitch_scale, "loop": looped}
	_players[_next_id] = weakref(player)

func capture(tick: int) -> Dictionary:
	var active := []
	var events := []
	for id in _events.keys():
		var player: Variant = _players[id].get_ref()
		var playing: bool = player != null and not player.is_queued_for_deletion() and player.playing
		if playing: active.append(id)
		if playing or tick - int(_events[id].tick) <= TTL_TICKS: events.append(_events[id].duplicate())
		else:
			_events.erase(id)
			_players.erase(id)
	if events.size() > MAX_EVENTS: error = "authority_sound_limit"
	return {"events": events, "active": active}

func validate(value: Variant, tick: int) -> String:
	if not value is Dictionary or value.size() != 2 or not value.get("events") is Array or not value.get("active") is Array or value.events.size() > MAX_EVENTS or value.active.size() > MAX_EVENTS: return "invalid_authority_audio"
	var ids := {}
	for event in value.events:
		if not event is Dictionary or event.size() != 8 or not event.get("id") is int or event.id < 1 or ids.has(event.id) or not event.get("resource") is int or event.resource < 0 or event.resource >= resources.size() or not event.get("tick") is int or event.tick < 0 or event.tick > tick or not event.get("loop") is bool: return "invalid_authority_sound"
		for key in ["offset", "end", "volume", "pitch"]:
			var number: Variant = event.get(key)
			if typeof(number) not in [TYPE_INT, TYPE_FLOAT] or not is_finite(float(number)): return "invalid_authority_sound_scalar"
		if event.offset < 0 or event.offset > 3600 or event.end < -1 or event.end > 3600 or event.volume < -100 or event.volume > 6 or event.pitch <= 0 or event.pitch > 4: return "invalid_authority_sound_range"
		ids[event.id] = true
	for id in value.active:
		if not id is int or not ids.has(id): return "invalid_authority_active_sound"
	return ""

func apply(value: Dictionary, tick: int, root: Node) -> void:
	for id in _guest_players.keys():
		var player: AudioStreamPlayer = _guest_players[id]
		if id not in value.active or not player.playing:
			player.queue_free()
			_guest_players.erase(id)
	for event: Dictionary in value.events:
		if _played.has(event.id): continue
		_played[event.id] = tick
		# Events outlive skipped snapshots briefly, but never replay old effects.
		if not event.loop and tick - event.tick > TTL_TICKS: continue
		var stream: AudioStream = load(resources[event.resource])
		var elapsed: float = float(tick - event.tick) / 30.0
		var offset: float = event.offset + elapsed * event.pitch
		var end: float = stream.get_length() if event.end < 0 else minf(event.end, stream.get_length())
		if not event.loop and offset >= end: continue
		var player := AudioStreamPlayer.new()
		if stream is AudioStreamMP3:
			stream = stream.duplicate()
			stream.loop = event.loop
		player.stream = stream
		player.volume_db = event.volume
		player.pitch_scale = event.pitch
		root.add_child(player)
		player.play(fmod(offset, stream.get_length()) if event.loop and stream.get_length() > 0 else offset)
		_guest_players[event.id] = player
	for id in _played.keys():
		if tick - int(_played[id]) > 300 and not _guest_players.has(id): _played.erase(id)
