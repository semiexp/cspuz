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
