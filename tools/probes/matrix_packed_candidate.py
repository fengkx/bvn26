"""Bounded diagnostic translation of independently pinned matrix byte operations."""
from tools.probes.analyze_matrix_coefficient_pairs import f32


def coefficients(matrix):
    if len(matrix) != 20 or list(matrix[15:]) != [0, 0, 0, 1, 0]:
        raise ValueError('Diagnostic only proves identity alpha row')
    rows = []
    for start in range(0, 20, 5):
        row = [f32(x) for x in matrix[start:start+5]]
        positive = sum(max(0, x)*2048 for x in row[:4])+max(0, row[4])*4
        negative = sum(min(0, x)*2048 for x in row[:4])+min(0, row[4])*4
        if positive > 32000 or negative < -32000:
            raise ValueError('Outside inspected packed-coefficient range')
        rows.append([round(f32(x*2048)) for x in row[:4]]+[round(f32(row[4]*4))+2])
    return rows


def pixel(source, rows, mode):
    if mode not in ('opaque_pair', 'alpha_pair', 'remainder'):
        raise ValueError('Unknown independently selected span mode')
    alpha = source[3]
    if any(not 0 <= c <= alpha for c in source[:3]) or not 0 <= alpha <= 255:
        raise ValueError('Expected premultiplied source bytes')
    factor = 65280//alpha if alpha else 0
    if mode == 'opaque_pair':
        if alpha != 255:
            raise ValueError('Opaque pair contains transparent source')
        inputs = [c*128 for c in source]
    elif mode == 'alpha_pair':
        inputs = [(c*(256 if channel == 3 else factor)+127)//2
                  for channel, c in enumerate(source)]
    else:
        straight = source[:3] if alpha == 255 else [(c*factor+127)//256 for c in source[:3]]
        inputs = [c*128 for c in [*straight, alpha]]
    transformed = [max(0, min(255, (sum(c*v//65536 for c, v in zip(row[:4], inputs))+row[4])//4))
                   for row in rows]
    # Native word arithmetic divides by255 with a floor, not nearest conversion.
    products = [c*transformed[3] for c in transformed[:3]]
    return [(p+(p>>8)+1)>>8 for p in products]+[transformed[3]]


def render(source, width, matrix):
    if width <= 0 or len(source) % width:
        raise ValueError('Incomplete source rows')
    rows = coefficients(matrix)
    result = []
    prefix = width//4*4
    for i, value in enumerate(source):
        x = i % width
        if x >= prefix:
            mode = 'remainder'
        else:
            mate = source[i+(1 if x%2 == 0 else -1)]
            mode = 'opaque_pair' if value[3] == mate[3] == 255 else 'alpha_pair'
        result.append(pixel(value, rows, mode))
    return result
