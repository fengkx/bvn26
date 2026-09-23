extends SceneTree

const Coordinator = preload("res://online_match.gd")
const MATCH_EPOCH := "3fa85f64-5717-4562-b3fc-2c963f66afa6"
const HASH := "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"


func _initialize() -> void:
	var accepted := _coordinator()
	accepted._receive_result({"epoch": MATCH_EPOCH, "frame": 60.0, "winner": 1.0, "hash": HASH})
	assert(accepted.error.is_empty(), "Integral JSON float winner was rejected")
	assert(accepted._remote_result.get("winner") == 1 and accepted._remote_result.winner is int,
		"Integral JSON float winner was not normalized to an integer slot")

	var draw := _coordinator()
	draw._receive_result({"epoch": MATCH_EPOCH, "frame": 60, "winner": null, "hash": HASH})
	assert(draw.error.is_empty() and draw._remote_result.get("winner") == null,
		"Null draw winner was rejected or changed")

	for candidate in [true, 0.5, 2.0, -1.0]:
		var rejected := _coordinator()
		rejected._receive_result({"epoch": MATCH_EPOCH, "frame": 60, "winner": candidate, "hash": HASH})
		assert(rejected.error == "invalid_peer_result", "Invalid result winner was accepted: %s" % str(candidate))
	var missing := _coordinator()
	missing._receive_result({"epoch": MATCH_EPOCH, "frame": 60, "hash": HASH})
	assert(missing.error == "invalid_peer_result", "Missing winner was treated as a draw")
	var negative_frame := _coordinator()
	negative_frame._receive_result({"epoch": MATCH_EPOCH, "frame": -1, "winner": 0, "hash": HASH})
	assert(negative_frame.error == "invalid_peer_result", "Negative terminal frame was accepted")
	print("ONLINE_RESULT_WINNER_OK json_integral_float=true null=true missing_bool_fraction_range_and_negative_frame_rejected=true")
	quit()


func _coordinator() -> RefCounted:
	var coordinator: RefCounted = Coordinator.new()
	coordinator.epoch = MATCH_EPOCH
	return coordinator
