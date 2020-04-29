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


_BASE36 = '0123456789abcdefghijklmnopqrstuvwxyz'


def _encode_int_or_str(v):
    if isinstance(v, str):
        return v
    else:
        if v <= 15:
            prefix = ''
        elif v <= 255:
            prefix = '-'
        elif v <= 4095:
            prefix = '+'
        else:
            raise ValueError('too large value: {}'.format(v))
        return prefix + hex(v)[2:]


def map2d(func, it):
    return list(map(lambda x: list(map(func, x)), it))


def encode_array(array, single_empty_marker='g', empty=None, dim=None):
    """
    Encode a 1-D or 2-D array into a serialized string in the pzpr format.
    :param array: a 1-D or 2-D array to be serialized.
    Each element of `array` should be one of:
    - `empty` representing the empty cell,
    - a str to be serialized as-is,
    - an int to be serialized in base-16, or
    - a `list` or 'tuple' of `str`s or `int`s.
    :param single_empty_marker: the number (in base-36) representing single empty cell in the serialization.
    :param empty: the value to represent empty cells.
    :param dim: the number of dimensions (1 or 2) of `array`. If `None` is specified, it is automatically inferred.
    :return: a str representing the serialization of `array`.
    """
    single_empty_index = _BASE36.index(single_empty_marker)

    if dim is None:
        is_two_dim = True
        for v in array:
            if not isinstance(v, list):
                is_two_dim = False
        if is_two_dim:
            dim = 2
        else:
            dim = 1
    else:
        if dim not in (1, 2):
            raise ValueError('invalid value of dim')
    if dim == 2:
        # flatten
        array = sum(array, [])
    res = []
    contiguous_empty_cells = 0
    for v in array:
        if v == empty:
            contiguous_empty_cells += 1
            if contiguous_empty_cells - 1 + single_empty_index >= 36:
                res.append(_BASE36[-1])
                contiguous_empty_cells = 1
        else:
            if contiguous_empty_cells > 0:
                res.append(_BASE36[contiguous_empty_cells - 1 + single_empty_index])
                contiguous_empty_cells = 0
            if isinstance(v, (str, int)):
                res.append(_encode_int_or_str(v))
            elif isinstance(v, (list, tuple)):
                for w in v:
                    res.append(_encode_int_or_str(w))
            else:
                raise TypeError('unsupported type for serialization')
    if contiguous_empty_cells > 0:
        res.append(_BASE36[contiguous_empty_cells - 1 + single_empty_index])
    return ''.join(res)


def encode_grid_segmentation(height, width, block_id):
    def convert_binary_seq(s):
        ret = ''
        for i in range((len(s) + 4) // 5):
            v = 0
            for j in range(5):
                if i * 5 + j < len(s) and s[i * 5 + j] == 1:
                    v += (2 ** (4 - j))
            ret += _BASE36[v]
        return ret
    s = []
    for y in range(height):
        for x in range(width - 1):
            s.append(1 if block_id[y][x] != block_id[y][x + 1] else 0)
    ret = convert_binary_seq(s)
    s = []
    for y in range(height - 1):
        for x in range(width):
            s.append(1 if block_id[y][x] != block_id[y + 1][x] else 0)
    ret += convert_binary_seq(s)
    return ret
