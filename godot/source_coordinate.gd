class_name SourceCoordinate
extends RefCounted


static func store(value: float) -> float:
	# Native AS2 MovieClip setters store integer twips, truncating toward zero.
	return float(int(value * 20.0)) / 20.0


static func from_projection(value: float) -> float:
	# Recover authored twips from a float32 render vector; this is not an AS2 write.
	return roundf(value * 20.0) / 20.0
