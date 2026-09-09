# Generated from the locked Sprite 620 controller; do not edit.
extends RefCounted
var select: int = 1
var spd: float = 5
var an: int = 0
var anj: int = 0
var i: int = 0
var positions: Dictionary = {}
var hint: String = ""
var hint_reset: bool = false
var sounds: Array = []
var confirmed_index: int = 0

func reset(held: Dictionary = {}) -> void:
	select = 1
	spd = 5
	an = 0
	anj = 0
	positions[1] = 0.1
	positions[2] = 56
	positions[3] = 111.9
	positions[4] = 167.8
	positions[5] = 229.7
	positions[6] = 291.6
	positions[7] = 347.5
	positions[8] = 403.4
	positions[9] = -58.8
	positions[10] = -114.7
	positions[11] = 459.7
	positions[12] = 515.6

func tick(held: Dictionary = {}) -> void:
	if an == 0:
		if anj == 0:
			if bool(held.get("up", false)):
				sounds.append(1)
				if select == 1:
					select = 9
				else:
					select -= 1
				an = 1
			if bool(held.get("down", false)):
				sounds.append(1)
				if select == 8:
					select = 11
				else:
					select += 1
				an = 1
			if bool(held.get("confirm", false)):
				sounds.append(2)
				confirmed_index = select
				anj = 1
	if positions[select] < -5:
		i = 1
		while i < 15:
			positions[i] += spd
			i += 1
	if positions[select] > 5:
		i = 1
		while i < 15:
			positions[i] -= spd
			i += 1
	if positions[select] > -6 and positions[select] < 6:
		if select == 9:
			positions[1] = -403.5
			positions[2] = -347.6
			positions[3] = -291.7
			positions[4] = -235.8
			positions[5] = -173.9
			positions[6] = -112
			positions[7] = -56.1
			positions[8] = -0.2
			positions[9] = -460.3
			positions[10] = -516.2
			positions[11] = 56.1
			positions[12] = 112
			select = 8
		if select == 11:
			positions[1] = 0.1
			positions[2] = 56
			positions[3] = 111.9
			positions[4] = 167.8
			positions[5] = 229.7
			positions[6] = 291.6
			positions[7] = 347.5
			positions[8] = 403.4
			positions[9] = -58.8
			positions[10] = -114.7
			positions[11] = 459.7
			positions[12] = 515.6
			select = 1
		if an == 1:
			hint_reset = true
		an = 0
		if select == 1 or select == 11:
			hint = "普通单人模式"
		if select == 2 or select == 12:
			hint = "与电脑对战"
		if select == 3:
			hint = "双人对战"
		if select == 4:
			hint = "格斗练习"
		if select == 5:
			hint = "游戏设置|按键设置"
		if select == 6:
			hint = "游戏相关信息说明"
		if select == 7 or select == 10:
			hint = "更多精彩游戏"
		if select == 8 or select == 9:
			hint = "退出游戏"
