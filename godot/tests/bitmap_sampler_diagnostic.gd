extends RefCounted
# Positive axis transforms, identity bitmap fill matrix and fully covered pixels.
# This diagnostic has no production placement binding.

static func axis(scale: float, translation: float, pixel: int, size: int, repeat: bool) -> float:
	var inverse := int(floor(65536.0 / scale + 0.5))
	var half := inverse / 2
	if inverse % 2 == 1 and (not repeat or half % 2 == 1):
		half += 1
	var quarter := float(int(translation * 4.0)) / 4.0
	var fixed := pixel * inverse + int(floor(-quarter / scale * 65536.0 + 0.5)) + half - 32768
	if not repeat:
		return float(fixed) / 65536.0
	var numerator := fixed * size * 256
	var byte := absi(numerator) / (size * 65536 - 1)
	if numerator < 0:
		byte = -byte - 1
	return float(byte) / 256.0

static func row(c: Dictionary) -> Dictionary:
	var repeat: bool = c.repeat
	var width := int(c.width)
	var height := int(c.height)
	var left := maxi(int(c.left), int(ceil(float(c.shape_left) * float(c.sx) + float(int(float(c.tx) * 4.0)) / 4.0)))
	var right := int(c.right)
	var y := axis(c.sy, c.ty, int(c.y), height, repeat)
	var xs: Array[float] = []
	var modes: Array[int] = []
	for x in range(left, right):
		xs.append(axis(c.sx, c.tx, x, width, repeat))
		modes.append(0)
	for chunk in range(0, xs.size(), 256):
		var end := mini(chunk + 256, xs.size())
		if repeat:
			var start := chunk
			while start < end:
				var period := floori(xs[start] / width)
				var stop := start + 1
				while stop < end and floori(xs[stop] / width) == period:
					stop += 1
				var bulk := start + ((stop - start) / 4) * 4
				if bulk > start:
					var safe := fposmod(xs[bulk - 1], width) < width - 1 and fposmod(y, height) < height - 1
					for i in range(start, bulk):
						modes[i] = 1 if safe else 2
				start = stop
		elif y >= 1 and y < height - 1:
			var start := chunk
			var stop := end
			while start < stop and xs[start] < 1:
				start += 1
			while stop > start and xs[stop - 1] >= width - 1:
				stop -= 1
			for i in range(start, start + ((stop - start) / 4) * 4):
				modes[i] = 1
	return {"left": left, "xs": xs, "y": y, "modes": modes}

static func texel(c: Dictionary, x: int, y: int) -> Color:
	if c.repeat:
		x = posmod(x, int(c.width))
		y = posmod(y, int(c.height))
	else:
		x = clampi(x, 0, int(c.width) - 1)
		y = clampi(y, 0, int(c.height) - 1)
	var alpha := int(c.alpha)
	if bool(c.get("varying_alpha", false)):
		alpha = [0, 64, 128, 255][posmod(y, 2) * 2 + posmod(x, 2)]
	var r := 0
	var g := 0
	var b := 0
	if c.pattern == "basis":
		var colors := [[1, 0, 0], [0, 1, 0], [0, 0, 1], [1, 1, 1]]
		var color: Array = colors[posmod(y, 2) * 2 + posmod(x, 2)]
		r = color[0] * alpha
		g = color[1] * alpha
		b = color[2] * alpha
	elif c.pattern == "unique":
		r = 255 if posmod(y, 2) * 2 + posmod(x, 2) == int(c.corner) else 0
		g = (x * 37 + 17) % 256
		b = 113
	else:
		var corner := int(c.corner)
		if corner < 4:
			r = 255 if posmod(y, 2) * 2 + posmod(x, 2) == corner else 0
		else:
			r = 255 * posmod(x if corner == 4 else y, 2)
		g = 113
		b = 113
	return Color(float(r) / 255, float(g) / 255, float(b) / 255, float(alpha) / 255)
