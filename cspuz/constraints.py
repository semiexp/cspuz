from enum import Enum, auto
import functools


def check_dtype(obj, dtype):
    if dtype is int:
        return isinstance(obj, (int, IntVar, IntExpr))
    elif dtype is bool:
        return isinstance(obj, (bool, BoolVar, BoolExpr))


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

    if op in [Op.NEG, Op.ADD, Op.SUB, Op.IF]:
        return IntExpr(op, operands)
    else:
        return BoolExpr(op, operands)


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
