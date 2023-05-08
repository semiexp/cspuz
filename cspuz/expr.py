from enum import Enum, auto
from typing import (
    Any,
    Iterable,
    List,
    Literal,
    Optional,
    TYPE_CHECKING,
    Union,
    cast,
    overload,
)

if TYPE_CHECKING:
    from .array import BoolArray1D, BoolArray2D, IntArray1D, IntArray2D


class Op(Enum):
    VAR = auto()
    BOOL_CONSTANT = auto()
    INT_CONSTANT = auto()
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
    GRAPH_ACTIVE_VERTICES_CONNECTED = auto()
    GRAPH_DIVISION = auto()


BoolOp = Literal[
    Op.BOOL_CONSTANT,
    Op.EQ,
    Op.NE,
    Op.LE,
    Op.LT,
    Op.GE,
    Op.GT,
    Op.NOT,
    Op.AND,
    Op.OR,
    Op.IFF,
    Op.XOR,
    Op.IMP,
    Op.ALLDIFF,
]
IntOp = Literal[Op.INT_CONSTANT, Op.NEG, Op.ADD, Op.SUB, Op.IF]

ExprLike = Union["Expr", int, bool]
BoolExprLike = Union["BoolExpr", bool]
IntExprLike = Union["IntExpr", int]


def is_bool_op(op: Op) -> bool:
    return op in [
        Op.BOOL_CONSTANT,
        Op.EQ,
        Op.NE,
        Op.LE,
        Op.LT,
        Op.GE,
        Op.GT,
        Op.NOT,
        Op.AND,
        Op.OR,
        Op.IFF,
        Op.XOR,
        Op.IMP,
        Op.ALLDIFF,
    ]


def is_int_op(op: Op) -> bool:
    return op in [Op.INT_CONSTANT, Op.NEG, Op.ADD, Op.SUB, Op.IF]


def _is_bool_expr_like(value: Any) -> bool:
    return isinstance(value, (BoolExpr, bool))


def _is_int_expr_like(value: Any) -> bool:
    return isinstance(value, (IntExpr, int)) and not isinstance(value, bool)


def _make_bool_expr(op: BoolOp, operands: List[ExprLike]) -> "BoolExpr":
    # type checking
    if op in [Op.EQ, Op.NE, Op.LE, Op.LT, Op.GE, Op.GT]:
        if len(operands) != 2 or not all(map(_is_int_expr_like, operands)):
            return NotImplemented
    elif op in [Op.AND, Op.OR, Op.IFF, Op.XOR, Op.IMP]:
        if len(operands) != 2 or not all(map(_is_bool_expr_like, operands)):
            return NotImplemented
    elif op == Op.BOOL_CONSTANT:
        if len(operands) != 1 or not isinstance(operands[0], bool):
            return NotImplemented
    elif op == Op.NOT:
        if len(operands) != 1 or not _is_bool_expr_like(operands[0]):
            return NotImplemented
    elif op == Op.ALLDIFF:
        if not all(map(_is_int_expr_like, operands)):
            return NotImplemented
    else:
        raise ValueError(f"Operator {op} does not return a bool value")

    return BoolExpr(op, operands)


def _make_int_expr(op: IntOp, operands: List[ExprLike]) -> "IntExpr":
    # type checking
    if op in [Op.ADD, Op.SUB]:
        if len(operands) != 2 or not all(map(_is_int_expr_like, operands)):
            return NotImplemented
    elif op == Op.INT_CONSTANT:
        if len(operands) != 1 or not isinstance(operands[0], int):
            return NotImplemented
    elif op == Op.NEG:
        if len(operands) != 1 or not _is_int_expr_like(operands[0]):
            return NotImplemented
    elif op == Op.IF:
        if len(operands) != 3 or not (
            _is_bool_expr_like(operands[0])
            and _is_int_expr_like(operands[1])
            and _is_int_expr_like(operands[2])
        ):
            return NotImplemented
    else:
        raise ValueError(f"operator {op} does not return an int value")

    return IntExpr(op, operands)


class Expr:
    def __init__(self, op: Op, operands: Iterable[ExprLike]):
        self.op: Op = op
        self.operands: List[ExprLike] = list(operands)

    def is_variable(self) -> bool:
        return False

    def __bool__(self):
        raise ValueError(
            "CSP values cannot be converted to a bool value. "
            "Perhaps you are using 'and', 'or' or 'not' on CSP values. "
            "For logical operations, use '&', '|' or '~' instead, respectively."
        )


class BoolExpr(Expr):
    def __init__(self, op: Op, operands: Iterable[ExprLike]):
        super().__init__(op, operands)

    @overload
    def cond(self, t: IntExprLike, f: IntExprLike) -> "IntExpr":
        ...

    @overload
    def cond(self, t: "IntArray1D", f: Union[IntExprLike, "IntArray1D"]) -> "IntArray1D":
        ...

    @overload
    def cond(self, t: "IntArray2D", f: Union[IntExprLike, "IntArray2D"]) -> "IntArray2D":
        ...

    @overload
    def cond(self, t: IntExprLike, f: "IntArray1D") -> "IntArray1D":
        ...

    @overload
    def cond(self, t: IntExprLike, f: "IntArray2D") -> "IntArray2D":
        ...

    def cond(
        self,
        t: Union[IntExprLike, "IntArray1D", "IntArray2D"],
        f: Union[IntExprLike, "IntArray1D", "IntArray2D"],
    ) -> Union["IntExpr", "IntArray1D", "IntArray2D"]:
        if _is_int_expr_like(t) and _is_int_expr_like(f):
            res = _make_int_expr(Op.IF, [self, cast(IntExprLike, t), cast(IntExprLike, f)])
            if res is not NotImplemented:
                return res
        else:
            from .constraints import cond

            res = cond(self, t, f)  # type: ignore

            if res is not NotImplemented:
                return res

        raise TypeError(
            "unsupported argument type(s) for operator 'cond': "
            "'{}' and '{}'".format(type(t).__name__, type(f).__name__)
        )

    @overload
    def then(self, other: BoolExprLike) -> "BoolExpr":
        ...

    @overload
    def then(self, other: "BoolArray1D") -> "BoolArray1D":
        ...

    @overload
    def then(self, other: "BoolArray2D") -> "BoolArray2D":
        ...

    def then(
        self, other: Union[BoolExprLike, "BoolArray1D", "BoolArray2D"]
    ) -> Union["BoolExpr", "BoolArray1D", "BoolArray2D"]:
        if _is_bool_expr_like(other):
            res = _make_bool_expr(Op.IMP, [self, cast(BoolExprLike, other)])
            if res is not NotImplemented:
                return res
        else:
            from .constraints import then

            res2 = then(self, other)
            if res2 is not NotImplemented:
                return res2

        raise TypeError(
            "unsupported argument type(s) for operator `then`: '{}'".format(type(other).__name__)
        )

    def __invert__(self) -> "BoolExpr":
        return _make_bool_expr(Op.NOT, [self])

    def __and__(self, other: BoolExprLike) -> "BoolExpr":
        return _make_bool_expr(Op.AND, [self, other])

    def __rand__(self, other: BoolExprLike) -> "BoolExpr":
        return _make_bool_expr(Op.AND, [other, self])

    def __or__(self, other: BoolExprLike) -> "BoolExpr":
        return _make_bool_expr(Op.OR, [self, other])

    def __ror__(self, other: BoolExprLike) -> "BoolExpr":
        return _make_bool_expr(Op.OR, [other, self])

    def __eq__(self, other: BoolExprLike) -> "BoolExpr":  # type: ignore
        return _make_bool_expr(Op.IFF, [self, other])

    def __ne__(self, other: BoolExprLike) -> "BoolExpr":  # type: ignore
        return _make_bool_expr(Op.XOR, [self, other])

    def __xor__(self, other: BoolExprLike) -> "BoolExpr":
        return _make_bool_expr(Op.XOR, [self, other])

    def __rxor__(self, other: BoolExprLike) -> "BoolExpr":
        return _make_bool_expr(Op.XOR, [other, self])

    def fold_or(self) -> "BoolExpr":
        return self

    def fold_and(self) -> "BoolExpr":
        return self

    def count_true(self) -> "IntExpr":
        return self.cond(1, 0)

    @property
    def sol(self) -> Optional[bool]:
        raise ValueError("sol property is available only for variables")

    @sol.setter
    def sol(self, value: Optional[bool]):
        raise ValueError("sol property is available only for variables")


class IntExpr(Expr):
    def __init__(self, op: Op, operands: Iterable[ExprLike]):
        super().__init__(op, operands)

    def __neg__(self) -> "IntExpr":
        return _make_int_expr(Op.NEG, [self])

    def __add__(self, other: IntExprLike) -> "IntExpr":
        return _make_int_expr(Op.ADD, [self, other])

    def __radd__(self, other: IntExprLike) -> "IntExpr":
        return _make_int_expr(Op.ADD, [other, self])

    def __sub__(self, other: IntExprLike) -> "IntExpr":
        return _make_int_expr(Op.SUB, [self, other])

    def __rsub__(self, other: IntExprLike) -> "IntExpr":
        return _make_int_expr(Op.SUB, [other, self])

    def __eq__(self, other: IntExprLike) -> "BoolExpr":  # type: ignore
        return _make_bool_expr(Op.EQ, [self, other])

    def __ne__(self, other: IntExprLike) -> "BoolExpr":  # type: ignore
        return _make_bool_expr(Op.NE, [self, other])

    def __ge__(self, other: IntExprLike) -> "BoolExpr":
        return _make_bool_expr(Op.GE, [self, other])

    def __gt__(self, other: IntExprLike) -> "BoolExpr":
        return _make_bool_expr(Op.GT, [self, other])

    def __le__(self, other: IntExprLike) -> "BoolExpr":
        return _make_bool_expr(Op.LE, [self, other])

    def __lt__(self, other: IntExprLike) -> "BoolExpr":
        return _make_bool_expr(Op.LT, [self, other])

    @property
    def sol(self) -> Optional[int]:
        raise ValueError("sol property is available only for variables")

    @sol.setter
    def sol(self, value: Optional[int]):
        raise ValueError("sol property is available only for variables")


class BoolVar(BoolExpr):
    def __init__(self, var_id: int):
        super().__init__(Op.VAR, [])
        self.id: int = var_id
        self.__sol: Optional[bool] = None

    def is_variable(self) -> bool:
        return True

    @property
    def sol(self) -> Optional[bool]:
        return self.__sol

    @sol.setter
    def sol(self, value: Optional[bool]):
        self.__sol = value


class IntVar(IntExpr):
    def __init__(self, var_id: int, lo: int, hi: int):
        super().__init__(Op.VAR, [])
        self.id: int = var_id
        self.lo: int = lo
        self.hi: int = hi
        self.__sol: Optional[int] = None

    def is_variable(self) -> bool:
        return True

    @property
    def sol(self) -> Optional[int]:
        return self.__sol

    @sol.setter
    def sol(self, value: Optional[int]):
        self.__sol = value
