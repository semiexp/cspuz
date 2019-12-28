from enum import Enum, auto
import functools


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


class Expr(object):
    def __init__(self, op, operands):
        self.op = op
        self.operands = operands


class BoolExpr(Expr):
    def __init__(self, op, operands):
        super(BoolExpr, self).__init__(op, operands)

    def cond(self, t, f):
        return IntExpr(Op.IF, [self, t, f])

    def then(self, other):
        return BoolExpr(Op.IMP, [self, other])

    def __invert__(self):
        return BoolExpr(Op.NOT, [self])

    def __and__(self, other):
        return BoolExpr(Op.AND, [self, other])

    def __rand__(self, other):
        return BoolExpr(Op.AND, [other, self])

    def __or__(self, other):
        return BoolExpr(Op.OR, [self, other])

    def __ror__(self, other):
        return BoolExpr(Op.OR, [other, self])

    def __eq__(self, other):
        return BoolExpr(Op.IFF, [self, other])

    def __ne__(self, other):
        return BoolExpr(Op.XOR, [self, other])

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
        return IntExpr(Op.NEG, [self])

    def __add__(self, other):
        return IntExpr(Op.ADD, [self, other])

    def __radd__(self, other):
        return IntExpr(Op.ADD, [other, self])

    def __sub__(self, other):
        return IntExpr(Op.SUB, [self, other])

    def __rsub__(self, other):
        return IntExpr(Op.ADD, [other, self])

    def __eq__(self, other):
        return BoolExpr(Op.EQ, [self, other])

    def __ne__(self, other):
        return BoolExpr(Op.NE, [self, other])

    def __ge__(self, other):
        return BoolExpr(Op.GE, [self, other])

    def __gt__(self, other):
        return BoolExpr(Op.GT, [self, other])

    def __le__(self, other):
        return BoolExpr(Op.LE, [self, other])

    def __lt__(self, other):
        return BoolExpr(Op.LT, [self, other])


class BoolVar(BoolExpr):
    def __init__(self, id):
        super(BoolVar, self).__init__(Op.VAR, [])
        self.id = id
        self.sol = None


class BoolVars(object):
    def __init__(self, vars):
        self.vars = vars

    def fold_or(self):
        return functools.reduce(lambda x, y: x | y, self.vars)

    def fold_and(self):
        return functools.reduce(lambda x, y: x & y, self.vars)

    def count_true(self):
        if len(self.vars) == 0:
            return 0
        else:
            return functools.reduce(lambda x, y: x + y, map(lambda x: x.cond(1, 0), self.vars))

    def __iter__(self):
        return iter(self.vars)


class IntVar(IntExpr):
    def __init__(self, id, lo, hi):
        super(IntVar, self).__init__(Op.VAR, [])
        self.id = id
        self.lo = lo
        self.hi = hi
        self.sol = None
