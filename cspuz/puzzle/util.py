from cspuz import Array


def stringify_array(array, symbol_map=None):
    if isinstance(array, Array):
        height, width = array.shape
    else:
        height = len(array)
        width = len(array[0])
    rows = []

    for y in range(height):
        if isinstance(symbol_map, dict):
            row = [symbol_map[v.sol if hasattr(v, 'sol') else v] for v in array[y]]
        elif symbol_map is not None:
            row = [symbol_map(v.sol if hasattr(v, 'sol') else v) for v in array[y]]
        else:
            row = [v.sol if hasattr(v, 'sol') else v for v in array[y]]
        rows.append(' '.join(row))

    return '\n'.join(rows)


_VERTICAL_EDGE = {
    None: ' ',
    True: '|',
    False: 'x'
}

_HORIZONTAL_EDGE = {
    None: ' ',
    True: '-',
    False: 'x'
}


def stringify_grid_frame(grid_frame):
    res = []
    for y in range(2 * grid_frame.height + 1):
        for x in range(2 * grid_frame.width + 1):
            if y % 2 == 0 and x % 2 == 0:
                res.append('+')
            elif y % 2 == 1 and x % 2 == 0:
                res.append(_VERTICAL_EDGE[grid_frame[y, x].sol])
            elif y % 2 == 0 and x % 2 == 1:
                res.append(_HORIZONTAL_EDGE[grid_frame[y, x].sol])
            else:
                res.append(' ')
        res.append('\n')
    return ''.join(res)
