extends RefCounted

const PROFILE := "naruto-ichigo-120-v1"
const SAMPLE_COUNT := 120

static func valid(report: Variant) -> bool:
	return report is Dictionary and report.size() == 5 \
		and report.get("profile") == PROFILE and report.get("samples") == SAMPLE_COUNT \
		and report.get("visible") == true \
		and report.get("p95_us") is int and report.p95_us > 0 \
		and report.get("long_stalls") is int and report.long_stalls >= 0

static func choose(p1: Variant, p2: Variant) -> int:
	var eligible := [valid(p1), valid(p2)]
	if not eligible[0] and not eligible[1]: return -1
	if not eligible[0]: return 1
	if not eligible[1]: return 0
	var high: int = maxi(p1.p95_us, p2.p95_us)
	# Integer arithmetic makes the strict 15% boundary identical on both peers.
	if absi(p1.p95_us - p2.p95_us) * 100 > high * 15:
		return 0 if p1.p95_us < p2.p95_us else 1
	if p1.long_stalls != p2.long_stalls:
		return 0 if p1.long_stalls < p2.long_stalls else 1
	return 0
