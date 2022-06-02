import re
from typing import Any, List, Optional, Tuple


def _as_list(x):
    if isinstance(x, list):
        return x
    elif isinstance(x, set):
        return list(x)
    else:
        return [x]


_BASE36_CHARS = "0123456789abcdefghijklmnopqrstuvwxyz"


def _to_base16(n: int) -> str:
    return hex(n)[2:]


def _from_base16(s: str) -> int:
    return int(s, 16)


def _to_base36(n: int) -> str:
    if n < 0:
        raise ValueError("`n` must be non-negative")
    if n == 0:
        return "0"
    ret_rev: List[str] = []
    while n > 0:
        ret_rev += _BASE36_CHARS[n % 36]
        n //= 36
    return "".join(reversed(ret_rev))


def _from_base36(s: str) -> int:
    return int(s, 36)


def _is_alnum_lower(s: str) -> bool:
    for c in s:
        i = ord(c)
        if not (48 <= i <= 57 or 97 <= i <= 122):
            return False
    return True


def _is_hex(s: str) -> bool:
    for c in s:
        i = ord(c)
        if not (48 <= i <= 57 or 97 <= i <= 102):
            return False
    return True


class CombinatorEnv:
    height: int
    width: int

    def __init__(self, height: int, width: int):
        self.height = height
        self.width = width


class Combinator:
    def __init__(self):
        pass

    def serialize(
        self, env: CombinatorEnv, data: List[Any], idx: int
    ) -> Optional[Tuple[int, str]]:
        raise NotImplementedError()

    def deserialize(
        self, env: CombinatorEnv, data: str, idx: int
    ) -> Optional[Tuple[int, List[Any]]]:
        raise NotImplementedError()


class FixStr(Combinator):
    def __init__(self, s):
        super().__init__()
        self._s = s

    def serialize(self, env, data, idx):
        return 0, self._s

    def deserialize(self, env, data, idx):
        if idx + len(self._s) > len(data):
            return None
        if data[idx : idx + len(self._s)] == self._s:
            return len(self._s), []
        else:
            return None


class Dict(Combinator):
    def __init__(self, before, after):
        super(Dict, self).__init__()
        self._before = _as_list(before)
        self._after = _as_list(after)

        if len(self._before) != len(self._after):
            raise ValueError("`before` and `after` should have the same number of elements")

    def serialize(self, env, data, idx):
        if idx == len(data):
            return None
        for i in range(len(self._before)):
            if data[idx] == self._before[i]:
                return 1, self._after[i]
        return None

    def deserialize(self, env, data, idx):
        if idx == len(data):
            return None
        for i in range(len(self._before)):
            if (
                idx + len(self._after[i]) <= len(data)
                and data[idx : idx + len(self._after[i])] == self._after[i]
            ):
                return len(self._after[i]), [self._before[i]]
        return None


class Spaces(Combinator):
    def __init__(self, space, smallest):
        super(Spaces, self).__init__()
        self._space = space
        self._smallest = smallest

        if not isinstance(smallest, str) or len(smallest) != 1:
            raise ValueError("`smallest` must be a 1-digit base-36 number")
        self._offset = _from_base36(smallest) - 1
        self._max_consecutive = 35 - self._offset

    def serialize(self, env, data, idx):
        if idx == len(data):
            return None
        if data[idx] != self._space:
            return None
        i = 1
        while i < self._max_consecutive and idx + i < len(data) and data[idx + i] == self._space:
            i += 1
        return i, _to_base36(self._offset + i)

    def deserialize(self, env, data, idx):
        if idx == len(data):
            return None
        if not _is_alnum_lower(data[idx]):
            return None
        i = _from_base36(data[idx])
        if i > self._offset:
            return 1, [self._space for _ in range(i - self._offset)]
        return None


class DecInt(Combinator):
    def __init__(self):
        super().__init__()

    def serialize(self, env, data, idx):
        if idx == len(data):
            return None
        if not isinstance(data[idx], int):
            return None
        if data[idx] < 0:
            return None
        return 1, str(data[idx])

    def deserialize(self, env, data, idx):
        if idx == len(data):
            return None
        n_digits = 0
        while idx + n_digits < len(data) and data[idx + n_digits].isdigit():
            n_digits += 1
        if n_digits == 0:
            return None
        return n_digits, [int(data[idx : idx + n_digits])]


class HexInt(Combinator):
    def __init__(self):
        super(HexInt, self).__init__()

    def serialize(self, env, data, idx):
        if idx == len(data):
            return None
        if not isinstance(data[idx], int):
            return None
        v = data[idx]
        if not 0 <= v <= 4095:
            return None
        prefix = ""
        if 16 <= v < 256:
            prefix = "-"
        elif 256 <= v:
            prefix = "+"
        return 1, prefix + _to_base16(v)

    def deserialize(self, env, data, idx):
        if idx == len(data):
            return None
        c = data[idx]
        if c == "-":
            if idx + 3 > len(data):
                return None
            return 3, [_from_base16(data[idx + 1 : idx + 3])]
        elif c == "+":
            if idx + 4 > len(data):
                return None
            return 4, [_from_base16(data[idx + 1 : idx + 4])]
        elif _is_hex(c):
            return 1, [_from_base16(c)]
        else:
            return None


class IntSpaces(Combinator):
    def __init__(self, space, max_int, max_num_spaces):
        super().__init__()

        if (max_int + 1) * (max_num_spaces + 1) > 36:
            raise ValueError("(max_int + 1) * (max_num_spaces + 1) must be at most 36")
        self._space = space
        self._max_int = max_int
        self._max_num_spaces = max_num_spaces

    def serialize(self, env, data, idx):
        if idx == len(data):
            return None
        if not isinstance(data[idx], int):
            return None
        v = data[idx]
        if not 0 <= v <= self._max_int:
            return None
        num_spaces = 0
        while idx + num_spaces + 1 < len(data) and num_spaces < self._max_num_spaces:
            if data[idx + num_spaces + 1] != self._space:
                break
            num_spaces += 1
        return (1 + num_spaces), _to_base36(num_spaces * (self._max_int + 1) + v)

    def deserialize(self, env, data, idx):
        if idx == len(data):
            return None
        v = data[idx]
        if not _is_alnum_lower(v):
            return None
        n = _from_base36(v)
        if not 0 <= n < (self._max_int + 1) * (self._max_num_spaces + 1):
            return None
        num = n % (self._max_int + 1)
        num_spaces = n // (self._max_int + 1)
        return 1, ([num] + [self._space for _ in range(num_spaces)])


class MultiDigit(Combinator):
    def __init__(self, base, digits):
        super(MultiDigit, self).__init__()

        if base**digits > 36:
            raise ValueError("base ** digits must be at most 36")
        self._base = base
        self._digits = digits

    def serialize(self, env, data, idx):
        if idx == len(data):
            return None

        value = 0
        for i in range(self._digits):
            value *= self._base
            if idx + i < len(data):
                if not 0 <= data[idx + i] < self._base:
                    return None
                value += data[idx + i]
        return min(len(data) - idx, self._digits), _to_base36(value)

    def deserialize(self, env, data, idx):
        if idx == len(data):
            return None

        if not _is_alnum_lower(data[idx]):
            return None

        value = _from_base36(data[idx])
        if not 0 <= value < self._base**self._digits:
            return None
        unpacked = []
        for i in range(self._digits):
            unpacked.append(value % self._base)
            value //= self._base
        unpacked.reverse()
        return 1, unpacked


class OneOf(Combinator):
    def __init__(self, *choices):
        super(OneOf, self).__init__()
        self._choices = []
        for choice in choices:
            if isinstance(choice, list):
                self._choices += choice
            else:
                self._choices.append(choice)

    def serialize(self, env, data, idx):
        for choice in self._choices:
            res = choice.serialize(env, data, idx)
            if res is not None:
                return res
        return None

    def deserialize(self, env, data, idx):
        for choice in self._choices:
            res = choice.deserialize(env, data, idx)
            if res is not None:
                return res
        return None


class Tupl(Combinator):
    def __init__(self, *elements):
        super().__init__()
        self._elements = []
        for element in elements:
            if isinstance(element, list):
                self._elements += element
            else:
                self._elements.append(element)

    def serialize(self, env, data, idx):
        if idx == len(data):
            return None
        d = data[idx]
        if not isinstance(d, tuple):
            return None
        if len(d) != len(self._elements):
            return None
        parts = []
        for i in range(len(self._elements)):
            res = self._elements[i].serialize(env, d[i], 0)
            if res is None:
                return None
            parts.append(res[1])

        return 1, "".join(parts)

    def deserialize(self, env, data, idx):
        if idx == len(data):
            return None
        parts = []
        ofs = 0
        for element in self._elements:
            res = element.deserialize(env, data, idx + ofs)
            if res is None:
                return None
            n_read, val = res
            ofs += n_read
            parts.append(val)

        return ofs, [tuple(parts)]


class Seq(Combinator):
    def __init__(self, base, n):
        super(Seq, self).__init__()
        self._base = base
        self._n = n

    def serialize(self, env, data, idx):
        if idx == len(data):
            return None
        if not isinstance(data[idx], list):
            return None
        d = data[idx]

        ret = []
        n_read = 0
        while n_read < self._n:
            tmp = self._base.serialize(env, d, n_read)
            if tmp is None:
                return None
            ofs, d2 = tmp
            n_read += ofs
            ret.append(d2)
        assert n_read == self._n
        return 1, "".join(ret)

    def deserialize(self, env, data, idx):
        ret = []
        n_read = 0
        while len(ret) < self._n:
            tmp = self._base.deserialize(env, data, idx + n_read)
            if tmp is None:
                return None
            ofs, d = tmp
            n_read += ofs
            ret += d
        return n_read, [ret[: self._n]]


class Grid(Combinator):
    def __init__(self, base, height=None, width=None):
        super(Grid, self).__init__()
        self._base = base
        if (height is None) != (width is None):
            raise ValueError("`height` and `width` must be specified at the same time")
        self._height = height
        self._width = width

    def serialize(self, env, data, idx):
        if idx == len(data):
            return None
        if not isinstance(data[idx], list):
            return None

        d = data[idx]
        height = self._height or env.height
        width = self._width or env.width
        seq_combinator = Seq(self._base, height * width)

        d_flat = []
        for y in range(height):
            d_flat += d[y]

        tmp = seq_combinator.serialize(env, [d_flat], idx)
        return tmp

    def deserialize(self, env, data, idx):
        height = self._height or env.height
        width = self._width or env.width
        seq_combinator = Seq(self._base, height * width)

        tmp = seq_combinator.deserialize(env, data, idx)
        if tmp is None:
            return None
        ofs, d = tmp
        assert len(d) == 1
        d = d[0]
        assert len(d) == height * width
        ret = []
        for i in range(height):
            row = []
            for j in range(width):
                row.append(d[i * width + j])
            ret.append(row)
        return ofs, [ret]


class Rooms(Combinator):
    def __init__(self, skip_on_error=False, allow_redundant_border=False):
        super().__init__()

        self._skip_on_error = skip_on_error
        self._allow_redundant_border = allow_redundant_border

    def _serialize(self, env, data, idx):
        if idx == len(data):
            raise ValueError("index out of bounds")
        d = data[idx]
        if not isinstance(d, list):
            raise ValueError("Rooms can serialize only List[List[Tuple[int, int]]]")
        height = env.height
        width = env.width
        room_id = [[-1 for _ in range(width)] for _ in range(height)]
        for i, room in enumerate(d):
            if not isinstance(room, list):
                raise ValueError("Rooms can serialize only List[List[Tuple[int, int]]]")
            for p in room:
                if not isinstance(p, tuple) or len(p) != 2:
                    raise ValueError("Rooms can serialize only List[List[Tuple[int, int]]]")
                y, x = p
                if not 0 <= y < height and 0 <= x < width:
                    raise ValueError(f"Cell position out of bounds: ({y}, {x})")
                if room_id[y][x] != -1:
                    raise ValueError(f"Cell ({y}, {x}) belongs to multiple rooms")
                room_id[y][x] = i
        for y in range(height):
            for x in range(width):
                if room_id[y][x] == -1:
                    raise ValueError(f"Cell ({y}, {x}) does not belong to any room")
        vertical = [
            [1 if room_id[y][x] != room_id[y][x + 1] else 0 for x in range(width - 1)]
            for y in range(height)
        ]
        horizontal = [
            [1 if room_id[y][x] != room_id[y + 1][x] else 0 for x in range(width)]
            for y in range(height - 1)
        ]

        combinator = Tupl(
            Grid(MultiDigit(base=2, digits=5), height=height, width=width - 1),
            Grid(MultiDigit(base=2, digits=5), height=height - 1, width=width),
        )
        return combinator.serialize(env, [([vertical], [horizontal])], 0)

    def serialize(self, env, data, idx):
        if self._skip_on_error:
            try:
                res = self._serialize(env, data, idx)
                return res
            except ValueError:
                return None
        else:
            return self._serialize(env, data, idx)

    def _deserialize(self, env, data, idx):
        if idx == len(data):
            raise ValueError("index out of bounds")
        height = env.height
        width = env.width

        combinator = Tupl(
            Grid(MultiDigit(base=2, digits=5), height=height, width=width - 1),
            Grid(MultiDigit(base=2, digits=5), height=height - 1, width=width),
        )
        res = combinator.deserialize(env, data, idx)
        if res is None:
            raise ValueError("border data could not be deserialized")
        n_read, [([vertical], [horizontal])] = res
        room_id = [[-1 for _ in range(width)] for _ in range(height)]

        def dfs(y: int, x: int, id: int):
            nonlocal room_id
            nonlocal vertical
            nonlocal horizontal
            nonlocal height
            nonlocal width

            if room_id[y][x] != -1:
                return
            room_id[y][x] = id
            if y > 0 and not horizontal[y - 1][x]:
                dfs(y - 1, x, id)
            if y < height - 1 and not horizontal[y][x]:
                dfs(y + 1, x, id)
            if x > 0 and not vertical[y][x - 1]:
                dfs(y, x - 1, id)
            if x < width - 1 and not vertical[y][x]:
                dfs(y, x + 1, id)

        last_id = 0
        for y in range(height):
            for x in range(width):
                if room_id[y][x] == -1:
                    dfs(y, x, last_id)
                    last_id += 1

        if not self._allow_redundant_border:
            for y in range(height):
                for x in range(width):
                    if y < height - 1 and horizontal[y][x] and room_id[y][x] == room_id[y + 1][x]:
                        raise ValueError("redundant horizontal border found")
                    if x < width - 1 and vertical[y][x] and room_id[y][x] == room_id[y][x + 1]:
                        raise ValueError("redundant vertical border found")

        rooms = [[] for _ in range(last_id)]
        for y in range(height):
            for x in range(width):
                assert room_id[y][x] != -1
                rooms[room_id[y][x]].append((y, x))

        return n_read, [rooms]

    def deserialize(self, env, data, idx):
        if self._skip_on_error:
            try:
                res = self._deserialize(env, data, idx)
                return res
            except ValueError:
                return None
        else:
            return self._deserialize(env, data, idx)


class ValuedRooms(Combinator):
    def __init__(self, value_combinator, **kwargs):
        super().__init__()

        self._value_combinator = value_combinator
        self._room_combinator = Rooms(**kwargs)

    def serialize(self, env, data, idx):
        if idx == len(data):
            return None
        d = data[idx]
        if not isinstance(d, tuple) or len(d) != 2:
            return None
        rooms, values = list(map(list, zip(*sorted(zip(*d)))))

        combinator = Tupl(self._room_combinator, Seq(self._value_combinator, len(rooms)))
        res = combinator.serialize(env, [([rooms], [values])], 0)
        return res or (1, res[1])

    def deserialize(self, env, data, idx):
        rooms_res = self._room_combinator.deserialize(env, data, idx)
        if rooms_res is None:
            return None
        ofs, rooms = rooms_res
        rooms = rooms[0]
        value_combinator = Seq(self._value_combinator, len(rooms))
        values_res = value_combinator.deserialize(env, data, idx + ofs)
        if values_res is None:
            return None
        ofs2, values = values_res
        values = values[0]

        return ofs + ofs2, [(rooms, values)]


def serialize_problem(combinator, problem, **kwargs):
    env = CombinatorEnv(**kwargs)
    tmp = combinator.serialize(env, [problem], 0)
    assert tmp is not None
    return tmp[1]


def deserialize_problem(combinator, serialized, **kwargs):
    env = CombinatorEnv(**kwargs)
    tmp = combinator.deserialize(env, serialized, 0)
    if tmp is None:
        return None
    assert tmp is not None
    problem = tmp[1]
    assert len(problem) == 1
    return problem[0]


def serialize_problem_as_url(
    combinator, puzzle, height, width, problem, prefix="https://puzz.link/p?"
):
    serialized = serialize_problem(combinator, problem, height=height, width=width)
    return f"{prefix}{puzzle}/{width}/{height}/{serialized}"


_DESERIALIZE_URL_REG = re.compile("https?://[^/]+/p(?:\\.html)?\\?([^/]+)/(\\d+)/(\\d+)/(.*)")


def get_puzzle_info_from_url(url: str) -> Optional[Tuple[str, int, int]]:
    m = _DESERIALIZE_URL_REG.match(url)
    if m is None:
        return None
    else:
        return (m[1], int(m[3]), int(m[2]))


def deserialize_problem_as_url(
    combinator, url, allowed_puzzles=None, allow_failure=False, return_size=False
):
    m = _DESERIALIZE_URL_REG.match(url)
    if allow_failure and m is None:
        return None
    assert m is not None

    puzzle = m[1]
    width = int(m[2])
    height = int(m[3])
    body = m[4]

    if allowed_puzzles is not None:
        if isinstance(allowed_puzzles, list):
            if puzzle not in allowed_puzzles:
                raise ValueError(f"unexpected puzzle name: {puzzle}")
        else:
            if puzzle != allowed_puzzles:
                raise ValueError(f"unexpected puzzle name: {puzzle}")

    problem = deserialize_problem(combinator, body, height=height, width=width)
    if problem is None:
        return None
    if return_size:
        return height, width, problem
    else:
        return problem
