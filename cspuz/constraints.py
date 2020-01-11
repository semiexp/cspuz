from enum import Enum, auto
import functools


def check_dtype(obj, dtype):
    if dtype is int:
        return isinstance(obj, (int, IntVar, IntExpr)) or (isinstance(obj, Array) and obj.dtype is int)
    elif dtype is bool:
        return isinstance(obj, (bool, BoolVar, BoolExpr)) or (isinstance(obj, Array) and obj.dtype is bool)


class Op(Enum):
    VAR = auto()
    NEG = auto()  # -int : int
    ADD = auto()  # int + int : int
    SUB = auto()  # int - int : int
    EQ = auto()  # int == int : bool
    NE = auto()  # int != int : bool
    LE = auto()  # int <= int : bool
    LT = auto()  # int < int : bool
    GE = auto()  # int >= int : bool
    GT = auto()  # int > int : bool
    NOT = auto()  # !bool : bool
    AND = auto()  # bool & bool : bool
    OR = auto()  # bool | bool : bool
    IFF = auto()  # bool == bool : bool
    XOR = auto()  # bool != bool : bool
    IMP = auto()  # bool (=>) bool : bool
    IF = auto()  # if (bool) { int } else { int } : int
    ALLDIFF = auto()  # alldifferent(int*) : bool


def _make_expr(op, operands):
    # array shape checking
    shapes = []
    for o in operands:
        if isinstance(o, Array):
            shapes.append(o.shape)
    if len(shapes) >= 2:
        for i in range(1, len(shapes)):
            if shapes[0] != shapes[i]:
                raise TypeError('operands have non-uniform shapes')
    # type checking
    if op in [Op.NEG, Op.ADD, Op.SUB, Op.EQ, Op.NE, Op.LE, Op.LT, Op.GE, Op.GT, Op.ALLDIFF]:
        # operand type: int
        if not all(map(lambda o: check_dtype(o, int), operands)):
            return NotImplemented
    elif op in [Op.NOT, Op.AND, Op.OR, Op.IFF, Op.XOR, Op.IMP]:
        # operand type: bool
        if not all(map(lambda o: check_dtype(o, bool), operands)):
            return NotImplemented
    elif op == Op.IF:
        if not (check_dtype(operands[0], bool) and check_dtype(operands[1], int) and check_dtype(operands[2], int)):
            return NotImplemented

    if len(shapes) == 0:
        if op in [Op.NEG, Op.ADD, Op.SUB, Op.IF]:
            return IntExpr(op, operands)
        else:
            return BoolExpr(op, operands)
    else:
        if len(shapes[0]) == 1:
            size, = shapes[0]
        else:
            h, w = shapes[0]
            size = h * w
        if op in [Op.NEG, Op.ADD, Op.SUB, Op.IF]:
            dtype = int
        else:
            dtype = bool
        data = []
        for i in range(size):
            ops = []
            for o in operands:
                if isinstance(o, Array):
                    ops.append(o.data[i])
                else:
                    ops.append(o)
            if dtype is int:
                data.append(IntExpr(op, ops))
            else:
                data.append(BoolExpr(op, ops))

        return Array(data, shape=shapes[0], dtype=dtype)


class Expr(object):
    def __init__(self, op, operands):
        self.op = op
        self.operands = operands


class BoolExpr(Expr):
    def __init__(self, op, operands):
        super(BoolExpr, self).__init__(op, operands)

    def cond(self, t, f):
        res = _make_expr(Op.IF, [self, t, f])
        if res is NotImplemented:
            raise TypeError('unsupported argument type(s) for operator `cond`: \'{}\' and \'{}\''.format(
                type(t).__name__, type(f).__name__))
        return res

    def then(self, other):
        res = _make_expr(Op.IMP, [self, other])
        if res is NotImplemented:
            raise TypeError('unsupported argument type(s) for operator `then`: \'{}\''.format(type(other).__name__))
        return res

    def __invert__(self):
        return _make_expr(Op.NOT, [self])

    def __and__(self, other):
        return _make_expr(Op.AND, [self, other])

    def __rand__(self, other):
        return _make_expr(Op.AND, [other, self])

    def __or__(self, other):
        return _make_expr(Op.OR, [self, other])

    def __ror__(self, other):
        return _make_expr(Op.OR, [other, self])

    def __eq__(self, other):
        return _make_expr(Op.IFF, [self, other])

    def __ne__(self, other):
        return _make_expr(Op.XOR, [self, other])

    def fold_or(self):
        return self

    def fold_and(self):
        return self

    def count_true(self):
        return self.cond(1, 0)


class IntExpr(Expr):
    def __init__(self, op, operands):
        super(IntExpr, self).__init__(op, operands)

    def __neg__(self):
        return _make_expr(Op.NEG, [self])

    def __add__(self, other):
        return _make_expr(Op.ADD, [self, other])

    def __radd__(self, other):
        return _make_expr(Op.ADD, [other, self])

    def __sub__(self, other):
        return _make_expr(Op.SUB, [self, other])

    def __rsub__(self, other):
        return _make_expr(Op.ADD, [other, self])

    def __eq__(self, other):
        return _make_expr(Op.EQ, [self, other])

    def __ne__(self, other):
        return _make_expr(Op.NE, [self, other])

    def __ge__(self, other):
        return _make_expr(Op.GE, [self, other])

    def __gt__(self, other):
        return _make_expr(Op.GT, [self, other])

    def __le__(self, other):
        return _make_expr(Op.LE, [self, other])

    def __lt__(self, other):
        return _make_expr(Op.LT, [self, other])


class BoolVar(BoolExpr):
    def __init__(self, id):
        super(BoolVar, self).__init__(Op.VAR, [])
        self.id = id
        self.sol = None


class BoolVars(object):
    def __init__(self, vars):
        self.vars = vars

    def fold_or(self):
        if len(self.vars) == 0:
            return False
        else:
            return functools.reduce(lambda x, y: x | y, self.vars)

    def fold_and(self):
        if len(self.vars) == 0:
            return True
        else:
            return functools.reduce(lambda x, y: x & y, self.vars)

    def count_true(self):
        if len(self.vars) == 0:
            return 0
        else:
            return functools.reduce(lambda x, y: x + y, map(lambda x: x.cond(1, 0), self.vars))

    def __iter__(self):
        return iter(self.vars)


class IntVars(object):
    def __init__(self, vars):
        self.vars = vars

    def __iter__(self):
        return iter(self.vars)

    def alldifferent(self):
        return alldifferent(self.vars)


class IntVar(IntExpr):
    def __init__(self, id, lo, hi):
        super(IntVar, self).__init__(Op.VAR, [])
        self.id = id
        self.lo = lo
        self.hi = hi
        self.sol = None


def alldifferent(*args):
    if len(args) >= 2:
        return _make_expr(Op.ALLDIFF, args)
    arg, = args
    if hasattr(arg, '__iter__'):
        return _make_expr(Op.ALLDIFF, list(arg))
    else:
        return True


def count_true(*args):
    res = None
    for arg in args:
        if hasattr(arg, '__iter__'):
            for x in arg:
                if res is None:
                    res = x.cond(1, 0)
                else:
                    res = res + x.cond(1, 0)
        else:
            if res is None:
                res = arg.cond(1, 0)
            else:
                res = res + arg.cond(1, 0)
    return res


def fold_or(*args):
    res = None
    for arg in args:
        if hasattr(arg, '__iter__'):
            for x in arg:
                if res is None:
                    res = x
                else:
                    res = res | x
        else:
            if res is None:
                res = arg
            else:
                res = res | arg
    if res is None:
        return False
    else:
        return res


def fold_and(*args):
    res = None
    for arg in args:
        if hasattr(arg, '__iter__'):
            for x in arg:
                if res is None:
                    res = x
                else:
                    res = res & x
        else:
            if res is None:
                res = arg
            else:
                res = res & arg
    if res is None:
        return True
    else:
        return res


def _compute_shape(data):
    if hasattr(data, '__len__') and hasattr(data, '__iter__') and hasattr(data, '__getitem__'):
        h = len(data)
        if h == 0:
            return 0,
        row = data[0]
        if hasattr(row, '__len__') and hasattr(row, '__iter__') and hasattr(data, '__getitem__'):
            w = len(row)
            for i in range(1, h):
                if len(data[i]) != w:
                    raise ValueError('jugged arrays are not supported')
            return h, w
        else:
            return h,
    else:
        return ()


def _parse_range(r, size):
    if isinstance(r, slice):
        lo = r.start
        hi = r.stop
        if lo is None:
            lo = 0
        elif lo < 0:
            lo = lo + size
        if hi is None:
            hi = size
        elif hi < 0:
            hi = hi + size
        point = False
    else:
        if r < 0:
            r2 = r + size
        else:
            r2 = r
        if not 0 <= r2 < size:
            raise IndexError('index {} is out of bounds for the axis with size {}'.format(r, size))
        lo = r2
        hi = r2 + 1
        point = True
    return min(max(0, lo), size), min(max(0, hi), size), point


class Array(object):
    def __init__(self, data, shape=None, dtype=None):
        if shape is not None:
            self.data = data
            self.shape = shape
        else:
            shape = _compute_shape(data)
            if len(shape) == 0:
                raise ValueError('0-dim arrays are not supported')
            if len(shape) == 1:
                self.data = [x for x in data]
            if len(shape) == 2:
                h, w = shape
                self.data = []
                for y in range(h):
                    for x in range(w):
                        self.data.append(data[y][x])
            self.shape = shape
        if dtype is None:
            if len(self.data) == 0:
                raise TypeError('dtype cannot be inferred from empty data')
            if check_dtype(self.data[0], int):
                self.dtype = int
            elif check_dtype(self.data[0], bool):
                self.dtype = bool
            else:
                raise TypeError('unsupported dtype')
            if not all(map(lambda o: check_dtype(o, self.dtype), self.data)):
                raise TypeError('inconsistent dtype')
        else:
            self.dtype = dtype

    def flatten(self):
        return Array(self.data, shape=(len(self.data),), dtype=self.dtype)

    def __getitem__(self, item):
        if len(self.shape) == 1:
            sz, = self.shape
            lo, hi, pt = _parse_range(item, sz)
            if pt:
                return self.data[lo]
            else:
                ret_data = []
                for i in range(lo, hi):
                    ret_data.append(self.data[i])
                return Array(ret_data, shape=(max(0, hi - lo),), dtype=self.dtype)
        else:
            h, w = self.shape
            if isinstance(item, tuple) and len(item) == 2:
                y, x = item
            else:
                y = item
                x = slice(None, None)
            ylo, yhi, ypt = _parse_range(y, h)
            xlo, xhi, xpt = _parse_range(x, w)

            if ypt and xpt:
                return self.data[ylo * w + xlo]
            else:
                ret_data = []
                for i in range(ylo, yhi):
                    for j in range(xlo, xhi):
                        ret_data.append(self.data[i * w + j])
                if ypt and not xpt:
                    return Array(ret_data, shape=(max(0, xhi - xlo), ), dtype=self.dtype)
                elif not ypt and xpt:
                    return Array(ret_data, shape=(max(0, yhi - ylo), ), dtype=self.dtype)
                else:
                    return Array(ret_data, shape=(max(0, yhi - ylo), max(0, xhi - xlo)), dtype=self.dtype)

    def __iter__(self):
        return iter(self.data)

    def cond(self, t, f):
        res = _make_expr(Op.IF, [self, t, f])
        if res is NotImplemented:
            raise TypeError('unsupported argument type(s) for operator `cond`: \'{}\' and \'{}\''.format(
                type(t).__name__, type(f).__name__))
        return res

    def then(self, other):
        res = _make_expr(Op.IMP, [self, other])
        if res is NotImplemented:
            raise TypeError('unsupported argument type(s) for operator `then`: \'{}\''.format(type(other).__name__))
        return res

    def __invert__(self):
        return _make_expr(Op.NOT, [self])

    def __and__(self, other):
        return _make_expr(Op.AND, [self, other])

    def __rand__(self, other):
        return _make_expr(Op.AND, [other, self])

    def __or__(self, other):
        return _make_expr(Op.OR, [self, other])

    def __ror__(self, other):
        return _make_expr(Op.OR, [other, self])

    def __eq__(self, other):
        if self.dtype == int:
            return _make_expr(Op.EQ, [self, other])
        else:
            return _make_expr(Op.IFF, [self, other])

    def __ne__(self, other):
        if self.dtype == int:
            return _make_expr(Op.NE, [self, other])
        else:
            return _make_expr(Op.XOR, [self, other])

    def __neg__(self):
        return _make_expr(Op.NEG, [self])

    def __add__(self, other):
        return _make_expr(Op.ADD, [self, other])

    def __radd__(self, other):
        return _make_expr(Op.ADD, [other, self])

    def __sub__(self, other):
        return _make_expr(Op.SUB, [self, other])

    def __rsub__(self, other):
        return _make_expr(Op.ADD, [other, self])

    def __ge__(self, other):
        return _make_expr(Op.GE, [self, other])

    def __gt__(self, other):
        return _make_expr(Op.GT, [self, other])

    def __le__(self, other):
        return _make_expr(Op.LE, [self, other])

    def __lt__(self, other):
        return _make_expr(Op.LT, [self, other])
