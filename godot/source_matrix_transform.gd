extends RefCounted


static func matrix_transform(matrix: Dictionary, basis_scale: float) -> Transform2D:
	# Flash MATRIX / JPEXS Matrix.transform:
	# x' = scaleX * x + rotateSkew1 * y + translateX
	# y' = rotateSkew0 * x + scaleY * y + translateY
	# Godot columns are (a, b) then (c, d), so rotateSkew0 is the x-axis
	# y component and rotateSkew1 is the y-axis x component.
	return Transform2D(
		Vector2(
			float(matrix.get("scaleX", 1.0)) * basis_scale,
			float(matrix.get("rotateSkew0", 0.0)) * basis_scale
		),
		Vector2(
			float(matrix.get("rotateSkew1", 0.0)) * basis_scale,
			float(matrix.get("scaleY", 1.0)) * basis_scale
		),
		Vector2(
			float(matrix.get("translateX", 0)) / 20.0,
			float(matrix.get("translateY", 0)) / 20.0
		)
	)
