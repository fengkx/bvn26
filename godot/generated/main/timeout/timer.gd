# Generated from the original countdown callback.
extends RefCounted
var adapter: RefCounted

func time() -> void:
	if (adapter.read("_root.zhanting") == false):
		if ((adapter.read("_root.game.p1.mc.sw") == false) and (adapter.read("_root.game.p2.mc.sw") == false)):
			if (adapter.read("_root.modo") != 4):
				adapter.write("_root.gametime", adapter.read("_root.gametime") - 1)
	adapter.write("tm", adapter.read("_root.gametime"))
	if (adapter.read("tm") <= 0):
		if (adapter.read("_root.timeover.played") == 0):
			adapter.write("_root.to", true)
			adapter.set_playing("_root.timeover", true)
			adapter.write("played", 1)
		adapter.write("tm", 0)
	else:
		adapter.write("_root.to", false)
	if (adapter.read("tm") >= 10):
		adapter.write("shi", floor((adapter.read("tm") / 10)))
		adapter.write("gs", (adapter.read("tm") - (adapter.read("shi") * 10)))
	if (adapter.read("tm") < 10):
		adapter.write("shi", 0)
		adapter.write("gs", adapter.read("tm"))
	adapter.goto_clip("\u5341", (adapter.read("shi") + 1), false)
	adapter.goto_clip("\u4e2a", (adapter.read("gs") + 1), false)
