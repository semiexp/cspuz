def stringify_array(array, symbol_map):
    height, width = array.shape
    rows = []

    for y in range(height):
        row = [symbol_map[v.sol] for v in array[y, :]]
        rows.append(' '.join(row))

    return '\n'.join(rows)
