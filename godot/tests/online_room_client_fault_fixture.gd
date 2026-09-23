extends "res://online_room_client.gd"

var command_requests: Array[String] = []
var admission_requests: Array[String] = []
var fixture_state: Dictionary = {}


func _request_json(method: int, path: String, body_text: String, authenticated: bool) -> Dictionary:
	if path == "/v1/rooms/join-by-code" or path == "/v1/rooms":
		if method != HTTPClient.METHOD_POST or authenticated:
			return {"ok": false, "error": "unexpected_request", "uncertain": false}
		admission_requests.append(body_text)
		if admission_requests.size() == 1:
			return {"ok": false, "error": "http_transport_failed", "uncertain": true}
		var state := fixture_state.duplicate(true)
		var slot := 1 if path.ends_with("join-by-code") else 0
		return {
			"ok": true,
			"value": {
				"roomId": state["id"],
				"slot": slot,
				"state": state,
				"inviteCode": "calm-otter-abcdefgh" if slot == 0 else null,
			},
		}
	if not path.ends_with("/commands") or method != HTTPClient.METHOD_POST or not authenticated:
		return {"ok": false, "error": "unexpected_request", "uncertain": false}
	command_requests.append(body_text)
	if command_requests.size() == 1:
		return {"ok": false, "error": "http_transport_failed", "uncertain": true}
	var request: Dictionary = JSON.parse_string(body_text)
	var state := fixture_state.duplicate(true)
	state["revision"] += 1
	state["members"][_slot]["seq"] = request["seq"]
	var value := {"acceptedSeq": request["seq"], "state": state}
	if request["operation"].get("type") == "reinvite":
		value["inviteCode"] = "bright-wolf-234567ab"
	return {"ok": true, "value": value}
