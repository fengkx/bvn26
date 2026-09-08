class_name CombatResolver
extends RefCounted

# Source checkHit()/getHitObj() lives on the defender's body clip and looks up
# currently placed opponent clips named {key}atm. Sampling both sides first keeps
# simultaneous hits independent of player iteration order.


static func resolve_pair(first: FighterRuntime, second: FighterRuntime) -> void:
	var first_contact := first.attack_contact(second)
	var second_contact := second.attack_contact(first)
	if not first_contact.is_empty():
		first.apply_attack_contact(first_contact, second)
	if not second_contact.is_empty():
		second.apply_attack_contact(second_contact, first)


static func resolve_body_pair(first: FighterRuntime, second: FighterRuntime) -> void:
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
			var contact: Dictionary = helper.attack_contact(fighter)
			if not contact.is_empty():
				helper.apply_attack_contact(contact, fighter)
