extends RefCounted

var spec: Dictionary
var last_requested_linkage: String = ""


func execute(state: AiSourceState, random: SourceRandom, probability: float, clock: RefCounted, dead: bool) -> void:
	last_requested_linkage = ""
	if dead:
		var death_checked: Variant = clock.read(spec["clock_sites"]["death_check"])
		if death_checked == null: return
		if int(death_checked) - int(state.read_field("_dievoicen")) < int(spec["death_cooldown_ms"]):
			return
		var death_written: Variant = clock.read(spec["clock_sites"]["death_write"])
		if death_written == null: return
		state.values["_dievoicen"] = death_written
		last_requested_linkage = spec["death_linkage"]
		return
	var draw := random.next_value(spec["probability_site"])
	if is_nan(draw) or draw > probability:
		return
	var checked: Variant = clock.read(spec["clock_sites"]["hurt_check"])
	if checked == null: return
	if int(checked) - int(state.read_field("_lastvoice")) < int(spec["hurt_cooldown_ms"]):
		return
	var selection := random.next_value(spec["selector_site"])
	if is_nan(selection):
		return
	last_requested_linkage = spec["hurt_linkages"][int(floor(selection * spec["hurt_linkages"].size()))]
	var written: Variant = clock.read(spec["clock_sites"]["hurt_write"])
	if written == null: return
	state.values["_lastvoice"] = written
	# Sound objects exist, but attachSound's three names have no exports in
	# the locked inputs. The compiler rejects newly present voice assets.
