class_name CombatResolver
extends RefCounted


static func resolve_incoming(defender: FighterRuntime, attacker: FighterRuntime,
		helper: HelperRuntime, stages: StageHitRegistry, stage_order: Array) -> bool:
	# Sprite 2 checkHit: fighter, then that fighter's helper, then stage hit.
	# The caller determines which defender callback runs first.
	if not defender.allows_source_hit():
		return false
	var packet := attacker.attack_contact(defender, true)
	if not packet.is_empty():
		attacker.apply_attack_contact(packet, defender)
		return true
	if helper != null and helper.attacking:
		assert(helper.owner_fighter == attacker)
		packet = helper.attack_contact(defender)
		if not packet.is_empty():
			helper.apply_attack_contact(packet, defender)
			return true
	if stages != null:
		var contact := stages.first_contact(defender, stage_order)
		if not contact.is_empty():
			contact["effect"].apply_attack_contact(contact["packet"], defender)
			return true
	return false

# Source checkHit()/getHitObj() lives on the defender's body clip and looks up
# currently placed opponent clips named {key}atm. Sampling both sides first keeps
# simultaneous hits independent of player iteration order.


static func resolve_pair(first: FighterRuntime, second: FighterRuntime) -> void:
	# Source checkHit() returns null when !gameRunning() (root zhanting or
	# opponent.sw). Sample both sides first so simultaneous hits stay unordered.
	var first_contact := first.attack_contact(second) if second._game_running() else {}
	var second_contact := second.attack_contact(first) if first._game_running() else {}
	if not first_contact.is_empty():
		first.apply_attack_contact(first_contact, second)
	if not second_contact.is_empty():
		second.apply_attack_contact(second_contact, first)


static func resolve_body_pair(first: FighterRuntime, second: FighterRuntime) -> void:
	# Source on_enterframe returns before body pressure when `_root.zhanting`.
	if first.root_zhanting or second.root_zhanting:
		return
	# Each source player clip runs the same pressure routine. Preserve p1 then
	# p2 evaluation so the second fighter observes displacement from the first.
	first.resolve_body_collision(second)
	second.resolve_body_collision(first)


static func resolve_helpers(helpers: Array, fighters: Array) -> void:
	for helper in helpers:
		if helper == null or not helper.attacking:
			continue
		for fighter in fighters:
			if fighter == helper.owner_fighter:
				continue
			# Source defender.checkHit() returns before fighter, helper, and stage
			# lookup when gameRunning() is false. A stopped helper can retain an
			# active display-list hitbox, but it must not deal damage while paused.
			if not fighter._game_running():
				continue
			if not fighter.has_active_hit_receiver():
				continue
			var contact: Dictionary = helper.attack_contact(fighter)
			if not contact.is_empty():
				helper.apply_attack_contact(contact, fighter)
