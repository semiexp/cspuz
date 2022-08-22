from typing import Any, List, Union, overload

from .array import BoolArray1D, BoolArray2D, IntArray1D, IntArray2D, _elementwise
from .expr import BoolExpr, BoolExprLike, IntExpr, IntExprLike, Op


def flatten_iterator(*args: Any) -> Any:
    for arg in args:
        if hasattr(arg, "__iter__"):
            for xs in arg:
                for x in flatten_iterator(xs):
                    yield x
        else:
            yield arg


def alldifferent(*args: Any) -> BoolExpr:
    operands: List[Union[IntExpr, int]] = []

    for x in flatten_iterator(*args):
        if isinstance(x, int):
            operands.append(x)
        elif isinstance(x, IntExpr):
            operands.append(x)
        else:
            raise TypeError()

    return BoolExpr(Op.ALLDIFF, operands)


def count_true(*args: Any) -> IntExpr:
    operands: List[Union[IntExpr, int]] = []
    constant = 0

    for x in flatten_iterator(*args):
        if isinstance(x, bool):
            if x is True:
                constant += 1
        elif isinstance(x, BoolExpr):
            operands.append(x.cond(1, 0))
        else:
            raise TypeError()

    if constant > 0:
        operands.append(constant)
    if len(operands) == 0:
        return IntExpr(Op.INT_CONSTANT, [0])

    return IntExpr(Op.ADD, operands)  # type: ignore


def fold_or(*args: Any) -> BoolExpr:
    operands: List[BoolExpr] = []

    for x in flatten_iterator(*args):
        if isinstance(x, bool):
            if x is True:
                return BoolExpr(Op.BOOL_CONSTANT, [True])
        elif isinstance(x, BoolExpr):
            operands.append(x)
        else:
            raise TypeError()

    if len(operands) == 0:
        return BoolExpr(Op.BOOL_CONSTANT, [False])
    return BoolExpr(Op.OR, operands)  # type: ignore


def fold_and(*args: Any) -> BoolExpr:
    operands: List[BoolExpr] = []

    for x in flatten_iterator(*args):
        if isinstance(x, bool):
            if x is False:
                return BoolExpr(Op.BOOL_CONSTANT, [False])
        elif isinstance(x, BoolExpr):
            operands.append(x)
        else:
            raise TypeError()

    if len(operands) == 0:
        return BoolExpr(Op.BOOL_CONSTANT, [True])
    return BoolExpr(Op.AND, operands)  # type: ignore


@overload
def cond(c: BoolExprLike, t: IntExprLike, f: IntExprLike) -> IntExpr:
    ...


@overload
def cond(c: BoolExprLike, t: IntExprLike, f: IntArray1D) -> IntArray1D:
    ...


@overload
def cond(c: BoolExprLike, t: IntArray2D, f: IntArray2D) -> IntArray2D:
    ...


@overload
def cond(c: BoolExprLike, t: IntArray1D, f: Union[IntExprLike, IntArray1D]) -> IntArray1D:
    ...


@overload
def cond(c: BoolExprLike, t: IntArray2D, f: Union[IntExprLike, IntArray2D]) -> IntArray2D:
    ...


@overload
def cond(
    c: BoolArray1D, t: Union[IntExprLike, IntArray1D], f: Union[IntExprLike, IntArray1D]
) -> IntExpr:
    ...


@overload
def cond(
    c: BoolArray2D, t: Union[IntExprLike, IntArray2D], f: Union[IntExprLike, IntArray2D]
) -> IntExpr:
    ...


def cond(
    c: Union[BoolExprLike, BoolArray1D, BoolArray2D],
    t: Union[IntExprLike, IntArray1D, IntArray2D],
    f: Union[IntExprLike, IntArray1D, IntArray2D],
) -> Union[IntExpr, IntArray1D, IntArray2D]:
    if isinstance(c, (BoolArray1D, BoolArray2D)):
        shape = c.shape
    elif isinstance(t, (IntArray1D, IntArray2D)):
        shape = t.shape
    elif isinstance(f, (IntArray1D, IntArray2D)):
        shape = f.shape
    else:
        return IntExpr(Op.IF, [c, t, f])

    return _elementwise(Op.IF, shape, [c, t, f])  # type: ignore


@overload
def then(x: BoolExprLike, y: BoolExprLike) -> BoolExpr:
    ...


@overload
def then(x: BoolExprLike, y: BoolArray1D) -> BoolArray1D:
    ...


@overload
def then(x: BoolExprLike, y: BoolArray2D) -> BoolArray2D:
    ...


@overload
def then(x: BoolArray1D, y: Union[BoolExprLike, BoolArray1D]) -> BoolArray1D:
    ...


@overload
def then(x: BoolArray2D, y: Union[BoolExprLike, BoolArray2D]) -> BoolArray2D:
    ...


def then(
    x: Union[BoolExprLike, BoolArray1D, BoolArray2D],
    y: Union[BoolExprLike, BoolArray1D, BoolArray2D],
) -> Union[BoolExpr, BoolArray1D, BoolArray2D]:
    if isinstance(x, (BoolArray1D, BoolArray2D)):
        shape = x.shape
    elif isinstance(y, (BoolArray1D, BoolArray2D)):
        shape = y.shape
    else:
        return BoolExpr(Op.IMP, [x, y])

    return _elementwise(Op.IMP, shape, [x, y])  # type: ignore
