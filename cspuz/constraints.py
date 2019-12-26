from enum import Enum, auto


class Op(Enum):
    VAR = auto()
    ADD = auto()  # int + int : int
    SUB = auto()  # int - int : int
    EQ = auto()  # int == int : bool
    NE = auto()  # int != int : bool
    LE = auto()  # int <= int : bool
    LT = auto()  # int < int : bool
    GE = auto()  # int >= int : bool
    GT = auto()  # int > int : bool
    IFF = auto()  # bool == bool : bool
    XOR = auto()  # bool != bool : bool
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

    def __eq__(self, other):
        return BoolExpr(Op.IFF, [self, other])

    def __ne__(self, other):
        return BoolExpr(Op.XOR, [self, other])


class IntExpr(Expr):
    def __init__(self, op, operands):
        super(IntExpr, self).__init__(op, operands)

    def __add__(self, other):
        return IntExpr(Op.ADD, [self, other])

    def __sub__(self, other):
        return IntExpr(Op.SUB, [self, other])

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


class IntVar(IntExpr):
    def __init__(self, id, lo, hi):
        super(IntVar, self).__init__(Op.VAR, [])
        self.id = id
        self.lo = lo
        self.hi = hi
        self.sol = None
