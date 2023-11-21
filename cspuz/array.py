import collections.abc
import functools
from typing import (
    Any,
    Generic,
    Iterable,
    Iterator,
    List,
    Literal,
    Optional,
    Tuple,
    TypeVar,
    Union,
    cast,
    overload,
)

from .expr import (
    BoolExpr,
    BoolExprLike,
    BoolOp,
    Expr,
    ExprLike,
    IntExpr,
    IntExprLike,
    IntOp,
    Op,
    is_bool_op,
)

T = TypeVar("T", bound=Expr)
IntArray1DLike = Union["IntArray1D", Iterable[IntExprLike]]
BoolArray1DLike = Union["BoolArray1D", Iterable[BoolExprLike]]


class Array1D(Generic[T]):
    shape: Tuple[int]
    data: List[T]

    def __init__(self, data: Iterable[T]):
        self.data = list(data)
        self.shape = (len(self.data),)

    def size(self) -> int:
        return self.shape[0]

    def __iter__(self) -> Iterator[T]:
        return iter(self.data)

    def __len__(self) -> int:
        return self.shape[0]

    def __bool__(self):
        raise ValueError(
            "CSP values cannot be converted to a bool value. "
            "Perhaps you are using 'and', 'or' or 'not' on CSP values. "
            "For logical operations, use '&', '|' or '~' instead, respectively."
        )


def _infer_shape(data: List[List[T]]) -> Tuple[int, int]:
    if len(data) == 0:
        raise ValueError("shape cannot be inferred for empty lists")
    height = len(data)
    width = len(data[0])
    for i in range(1, height):
        if len(data[i]) != width:
            raise ValueError("shape cannot be inferred for jugged arrays")

    return height, width


def _flatten(data: List[List[T]]) -> List[T]:
    ret = []
    for row in data:
        ret += row
    return ret


def _parse_range(size: int, key: Union[int, slice]) -> Tuple[bool, int, int, int]:
    if isinstance(key, int):
        p = key
        if p < 0:
            p += size
        if not 0 <= p < size:
            raise IndexError("index {} is out of bounds for the axis with size {}".format(p, size))
        return True, p, p + 1, 1
    else:
        start = key.start
        stop = key.stop
        step = key.step or 1

        if start is None:
            start = 0 if step > 0 else size - 1
        else:
            if start < 0:
                start += size
            start = min(max(0, start), size)

        if stop is None:
            stop = size if step > 0 else -1
        else:
            if stop < 0:
                stop += size
            stop = min(max(0, stop), size)

        return False, start, stop, step


def _range_size(start, stop, step):
    if step == 0:
        raise ValueError("step must not be zero")
    elif step > 0:
        if start >= stop:
            return 0
        else:
            return (stop - start + step - 1) // step
    else:
        if start <= stop:
            return 0
        else:
            return (start - stop - step - 1) // (-step)


class Array2D(Generic[T]):
    shape: Tuple[int, int]
    data: List[T]

    def __init__(
        self,
        data: Union[Iterable[Iterable[T]], Iterable[T]],
        shape: Optional[Tuple[int, int]] = None,
    ):
        if shape is None:
            data_list_list: List[List[T]] = list(
                map(lambda e: list(e), cast(Iterable[Iterable[T]], data))
            )
            self.shape = _infer_shape(data_list_list)
            self.data = _flatten(data_list_list)
        else:
            data_list: List[T] = list(cast(Iterable[T], data))
            size = shape[0] * shape[1]
            if len(data_list) != size:
                raise ValueError(
                    f"size of `data` ({size}) is inconsistent with the given " "shape {shape}"
                )
            self.shape = shape
            self.data = data_list

    @overload
    def _getitem_impl(self, key: Tuple[int, int]) -> T:
        ...

    @overload
    def _getitem_impl(
        self, key: Union[int, Tuple[int, slice], Tuple[slice, int], Iterable[Tuple[int, int]]]
    ) -> Array1D[T]:
        ...

    @overload
    def _getitem_impl(self, key: Union[slice, Tuple[slice, slice]]) -> "Array2D[T]":
        ...

    def _getitem_impl(
        self,
        key: Union[
            int,
            slice,
            Tuple[int, int],
            Tuple[int, slice],
            Tuple[slice, int],
            Tuple[slice, slice],
            Iterable[Tuple[int, int]],
        ],
    ) -> Union[T, Array1D[T], "Array2D[T]"]:
        if not isinstance(key, tuple) and isinstance(key, collections.abc.Iterable):
            data = []
            for idx in key:
                if not isinstance(idx, tuple) or len(idx) != 2:
                    raise TypeError("values in index arrays must be tuples of 2 elements")
                y, x = idx
                if not isinstance(y, int) or not isinstance(x, int):
                    raise TypeError("tuple elements for indexing must be of int type")
                data.append(self._getitem_impl((y, x)))
            return Array1D(data)

        if isinstance(key, (int, slice)):
            return self._getitem_impl(
                cast(Union[Tuple[int, slice], Tuple[slice, slice]], (key, slice(None, None)))
            )
        y_fixed, y_start, y_stop, y_step = _parse_range(self.shape[0], key[0])
        x_fixed, x_start, x_stop, x_step = _parse_range(self.shape[1], key[1])
        y_size = _range_size(y_start, y_stop, y_step)
        x_size = _range_size(x_start, x_stop, x_step)

        if y_fixed and x_fixed:
            return self.data[y_start * self.shape[1] + x_start]

        data = []
        for i in range(y_size * x_size):
            y = y_start + y_step * (i // x_size)
            x = x_start + x_step * (i % x_size)
            data.append(self.data[y * self.shape[1] + x])

        if not (y_fixed or x_fixed):
            return Array2D(data, (y_size, x_size))
        else:
            return Array1D(data)

    def __iter__(self) -> Iterator[T]:
        return iter(self.data)

    def __len__(self) -> int:
        return self.shape[0]

    def __bool__(self):
        raise ValueError(
            "CSP values cannot be converted to a bool value. "
            "Perhaps you are using 'and', 'or' or 'not' on CSP values. "
            "For logical operations, use '&', '|' or '~' instead, respectively."
        )


def _is_bool_like(value: Any) -> bool:
    return isinstance(value, (BoolExpr, bool, BoolArray1D, BoolArray2D))


def _is_int_like(value: Any) -> bool:
    return isinstance(value, (IntExpr, int, IntArray1D, IntArray2D))


ElementwiseOperands = List[
    Union[BoolExprLike, "BoolArray1D", "BoolArray2D", IntExprLike, "IntArray1D", "IntArray2D"]
]


@overload
def _elementwise(op: BoolOp, shape: Tuple[int], operands: ElementwiseOperands) -> "BoolArray1D":
    ...


@overload
def _elementwise(op: IntOp, shape: Tuple[int], operands: ElementwiseOperands) -> "IntArray1D":
    ...


@overload
def _elementwise(
    op: BoolOp, shape: Tuple[int, int], operands: ElementwiseOperands
) -> "BoolArray2D":
    ...


@overload
def _elementwise(op: IntOp, shape: Tuple[int, int], operands: ElementwiseOperands) -> "IntArray2D":
    ...


def _elementwise(
    op: Op, shape: Union[Tuple[int], Tuple[int, int]], operands: ElementwiseOperands
) -> Union["BoolArray1D", "IntArray1D", "BoolArray2D", "IntArray2D"]:
    # type check
    if op in [Op.EQ, Op.NE, Op.LE, Op.LT, Op.GE, Op.GT]:
        if len(operands) != 2 or not all(map(_is_int_like, operands)):
            return NotImplemented
    elif op in [Op.AND, Op.OR, Op.IFF, Op.XOR, Op.IMP]:
        if len(operands) != 2 or not all(map(_is_bool_like, operands)):
            return NotImplemented
    elif op == Op.NOT:
        if len(operands) != 1 or not _is_bool_like(operands[0]):
            return NotImplemented
    elif op == Op.ALLDIFF:
        if not all(map(_is_int_like, operands)):
            return NotImplemented
    elif op in [Op.ADD, Op.SUB]:
        if len(operands) != 2 or not all(map(_is_int_like, operands)):
            return NotImplemented
    elif op == Op.NEG:
        if len(operands) != 1 or not _is_int_like(operands[0]):
            return NotImplemented
    elif op == Op.IF:
        if len(operands) != 3 or not (
            _is_bool_like(operands[0]) and _is_int_like(operands[1]) and _is_int_like(operands[2])
        ):
            return NotImplemented
    else:
        raise ValueError(f"unknown operator {op}")

    # shape check
    for operand in operands:
        if isinstance(operand, (Array1D, Array2D)):
            if operand.shape is not None and operand.shape != shape:
                raise ValueError(f"shape mismatch: {shape} and {operand.shape}")

    if shape is None:
        raise ValueError("no Array is given as an operand of collective operation")

    if not (1 <= len(shape) <= 2):
        raise ValueError("number of dimensions must be 1 or 2")

    size = functools.reduce(lambda x, y: x * y, shape, 1)

    bool_op = is_bool_op(op)

    res: List[Union[BoolExpr, IntExpr]] = []
    for i in range(size):
        expr_operands: List[ExprLike] = []
        for j in range(len(operands)):
            operand = operands[j]
            if isinstance(operand, (Array1D, Array2D)):
                expr_operands.append(operand.data[i])
            else:
                expr_operands.append(operand)
        if bool_op:
            res.append(BoolExpr(op, expr_operands))
        else:
            res.append(IntExpr(op, expr_operands))

    if len(shape) == 1:
        if bool_op:
            return BoolArray1D(cast(List[BoolExpr], res))
        else:
            return IntArray1D(cast(List[IntExpr], res))
    else:
        if bool_op:
            return BoolArray2D(cast(List[BoolExpr], res), cast(Tuple[int, int], shape))
        else:
            return IntArray2D(cast(List[IntExpr], res), cast(Tuple[int, int], shape))


BoolOperand1D = Union[BoolExprLike, "BoolArray1D"]
IntOperand1D = Union[IntExprLike, "IntArray1D"]


class BoolArray1D(Array1D[BoolExpr]):
    def __init__(self, data: Iterable[BoolExpr]):
        super().__init__(data)

    def cond(self, t: IntOperand1D, f: IntOperand1D) -> "IntArray1D":
        res = _elementwise(Op.IF, self.shape, [self, t, f])
        if res is NotImplemented:
            raise TypeError("unsupported argument type(s) for operator 'cond'")
        return res

    def then(self, other: BoolOperand1D) -> "BoolArray1D":
        res = _elementwise(Op.IMP, self.shape, [self, other])
        if res is NotImplemented:
            raise TypeError("unsupported argument type(s) for operator 'cond'")
        return res

    def __invert__(self) -> "BoolArray1D":
        return _elementwise(Op.NOT, self.shape, [self])

    def __and__(self, other: BoolOperand1D) -> "BoolArray1D":
        return _elementwise(Op.AND, self.shape, [self, other])

    def __rand__(self, other: BoolOperand1D) -> "BoolArray1D":
        return _elementwise(Op.AND, self.shape, [other, self])

    def __or__(self, other: BoolOperand1D) -> "BoolArray1D":
        return _elementwise(Op.OR, self.shape, [self, other])

    def __ror__(self, other: BoolOperand1D) -> "BoolArray1D":
        return _elementwise(Op.OR, self.shape, [other, self])

    def __eq__(self, other: BoolOperand1D) -> "BoolArray1D":  # type: ignore
        return _elementwise(Op.IFF, self.shape, [self, other])

    def __ne__(self, other: BoolOperand1D) -> "BoolArray1D":  # type: ignore
        return _elementwise(Op.XOR, self.shape, [self, other])

    def __xor__(self, other: BoolOperand1D) -> "BoolArray1D":
        return _elementwise(Op.XOR, self.shape, [self, other])

    def __rxor__(self, other: BoolOperand1D) -> "BoolArray1D":
        return _elementwise(Op.XOR, self.shape, [other, self])

    def fold_or(self) -> BoolExpr:
        return BoolExpr(Op.OR, self.data)

    def fold_and(self) -> BoolExpr:
        return BoolExpr(Op.AND, self.data)

    @overload
    def __getitem__(self, key: int) -> BoolExpr:
        ...

    @overload
    def __getitem__(self, key: slice) -> "BoolArray1D":
        ...

    def __getitem__(self, key: Union[int, slice]) -> Union[BoolExpr, "BoolArray1D"]:
        if isinstance(key, int):
            return self.data[key]
        else:
            return BoolArray1D(self.data[key])

    def __len__(self) -> int:
        return len(self.data)

    def __iter__(self) -> Iterator[BoolExpr]:
        return iter(self.data)

    def reshape(self, shape: Tuple[int, int]) -> "BoolArray2D":
        return _reshape(self, shape)

    def count_true(self) -> IntExpr:
        import cspuz.constraints

        return cspuz.constraints.count_true(self.data)


class IntArray1D(Array1D[IntExpr]):
    def __init__(self, data: Iterable[IntExpr]):
        super().__init__(data)

    def __neg__(self) -> "IntArray1D":
        return _elementwise(Op.NEG, self.shape, [self])

    def __add__(self, other: IntOperand1D) -> "IntArray1D":
        return _elementwise(Op.ADD, self.shape, [self, other])

    def __radd__(self, other: IntOperand1D) -> "IntArray1D":
        return _elementwise(Op.ADD, self.shape, [other, self])

    def __sub__(self, other: IntOperand1D) -> "IntArray1D":
        return _elementwise(Op.SUB, self.shape, [self, other])

    def __rsub__(self, other: IntOperand1D) -> "IntArray1D":
        return _elementwise(Op.SUB, self.shape, [other, self])

    def __eq__(self, other: IntOperand1D) -> "BoolArray1D":  # type: ignore
        return _elementwise(Op.EQ, self.shape, [self, other])

    def __ne__(self, other: IntOperand1D) -> "BoolArray1D":  # type: ignore
        return _elementwise(Op.NE, self.shape, [self, other])

    def __ge__(self, other: IntOperand1D) -> "BoolArray1D":
        return _elementwise(Op.GE, self.shape, [self, other])

    def __gt__(self, other: IntOperand1D) -> "BoolArray1D":
        return _elementwise(Op.GT, self.shape, [self, other])

    def __le__(self, other: IntOperand1D) -> "BoolArray1D":
        return _elementwise(Op.LE, self.shape, [self, other])

    def __lt__(self, other: IntOperand1D) -> "BoolArray1D":
        return _elementwise(Op.LT, self.shape, [self, other])

    @overload
    def __getitem__(self, key: int) -> IntExpr:
        ...

    @overload
    def __getitem__(self, key: slice) -> "IntArray1D":
        ...

    def __getitem__(self, key: Union[int, slice]) -> Union[IntExpr, "IntArray1D"]:
        if isinstance(key, int):
            return self.data[key]
        else:
            return IntArray1D(self.data[key])

    def reshape(self, shape: Tuple[int, int]) -> "IntArray2D":
        return _reshape(self, shape)

    def alldifferent(self) -> "BoolExpr":
        return BoolExpr(Op.ALLDIFF, self.data)


BoolOperand2D = Union[BoolExprLike, "BoolArray2D"]
IntOperand2D = Union[IntExprLike, "IntArray2D"]


class BoolArray2D(Array2D[BoolExpr]):
    @overload
    def __init__(self, data: Iterable[Iterable[BoolExpr]]):
        ...

    @overload
    def __init__(self, data: Iterable[BoolExpr], shape: Tuple[int, int]):
        ...

    def __init__(
        self,
        data: Union[Iterable[Iterable[BoolExpr]], Iterable[BoolExpr]],
        shape: Optional[Tuple[int, int]] = None,
    ):
        super().__init__(data, shape)

    def cond(self, t: IntOperand2D, f: IntOperand2D) -> "IntArray2D":
        res = _elementwise(Op.IF, self.shape, [self, t, f])
        if res is NotImplemented:
            raise TypeError("unsupported argument type(s) for operator 'cond'")
        return res

    def then(self, other: BoolOperand2D) -> "BoolArray2D":
        res = _elementwise(Op.IMP, self.shape, [self, other])
        if res is NotImplemented:
            raise TypeError("unsupported argument type(s) for operator 'cond'")
        return res

    def __invert__(self) -> "BoolArray2D":
        return _elementwise(Op.NOT, self.shape, [self])

    def __and__(self, other: BoolOperand2D) -> "BoolArray2D":
        return _elementwise(Op.AND, self.shape, [self, other])

    def __rand__(self, other: BoolOperand2D) -> "BoolArray2D":
        return _elementwise(Op.AND, self.shape, [other, self])

    def __or__(self, other: BoolOperand2D) -> "BoolArray2D":
        return _elementwise(Op.OR, self.shape, [self, other])

    def __ror__(self, other: BoolOperand2D) -> "BoolArray2D":
        return _elementwise(Op.OR, self.shape, [other, self])

    def __eq__(self, other: BoolOperand2D) -> "BoolArray2D":  # type: ignore
        return _elementwise(Op.IFF, self.shape, [self, other])

    def __ne__(self, other: BoolOperand2D) -> "BoolArray2D":  # type: ignore
        return _elementwise(Op.XOR, self.shape, [self, other])

    def __xor__(self, other: BoolOperand2D) -> "BoolArray2D":
        return _elementwise(Op.XOR, self.shape, [self, other])

    def __rxor__(self, other: BoolOperand2D) -> "BoolArray2D":
        return _elementwise(Op.XOR, self.shape, [other, self])

    def fold_or(self) -> BoolExpr:
        return BoolExpr(Op.OR, self.data)

    def fold_and(self) -> BoolExpr:
        return BoolExpr(Op.AND, self.data)

    @overload
    def __getitem__(self, key: Tuple[int, int]) -> BoolExpr:
        ...

    @overload
    def __getitem__(
        self, key: Union[int, Tuple[int, slice], Tuple[slice, int], Iterable[Tuple[int, int]]]
    ) -> BoolArray1D:
        ...

    @overload
    def __getitem__(self, key: Union[slice, Tuple[slice, slice]]) -> "BoolArray2D":
        ...

    def __getitem__(
        self,
        key: Union[
            int,
            slice,
            Tuple[int, int],
            Tuple[int, slice],
            Tuple[slice, int],
            Tuple[slice, slice],
            Iterable[Tuple[int, int]],
        ],
    ) -> Union[BoolExpr, BoolArray1D, "BoolArray2D"]:
        ret = super()._getitem_impl(key)
        if isinstance(ret, Array1D):
            return BoolArray1D(ret.data)
        elif isinstance(ret, Array2D):
            return BoolArray2D(ret.data, ret.shape)
        else:
            return ret

    def flatten(self) -> BoolArray1D:
        return BoolArray1D(self.data)

    def reshape(self, shape: Tuple[int, int]) -> "BoolArray2D":
        return _reshape(self, shape)

    @overload
    def four_neighbors(self, y: int, x: int) -> BoolArray1D:
        ...

    @overload
    def four_neighbors(self, y: Tuple[int, int]) -> BoolArray1D:
        ...

    def four_neighbors(
        self, y: Union[int, Tuple[int, int]], x: Optional[int] = None
    ) -> BoolArray1D:
        return BoolArray1D(cast("List[BoolExpr]", _four_neighbors(self, y, x)))

    @overload
    def four_neighbor_indices(self, y: int, x: int) -> List[Tuple[int, int]]:
        ...

    @overload
    def four_neighbor_indices(self, y: Tuple[int, int]) -> List[Tuple[int, int]]:
        ...

    def four_neighbor_indices(
        self, y: Union[int, Tuple[int, int]], x: Optional[int] = None
    ) -> List[Tuple[int, int]]:
        return _four_neighbor_indices(self.shape, y, x)

    def conv2d(self, height: int, width: int, op: Literal["and", "or"]) -> "BoolArray2D":
        if op not in ("and", "or"):
            raise ValueError('op for conv2d on BoolArray must be either "and" or "or"')

        r_height = max(0, self.shape[0] - height + 1)
        r_width = max(0, self.shape[1] - width + 1)
        r_data = []
        for y in range(r_height):
            for x in range(r_width):
                component = self[y : y + height, x : x + width]
                if op == "and":
                    r_data.append(BoolExpr(Op.AND, component))
                elif op == "or":
                    r_data.append(BoolExpr(Op.OR, component))
        return BoolArray2D(r_data, (r_height, r_width))

    def count_true(self) -> IntExpr:
        import cspuz.constraints

        return cspuz.constraints.count_true(self.data)


class IntArray2D(Array2D[IntExpr]):
    @overload
    def __init__(self, data: Iterable[Iterable[IntExpr]]):
        ...

    @overload
    def __init__(self, data: Iterable[IntExpr], shape: Tuple[int, int]):
        ...

    def __init__(
        self,
        data: Union[Iterable[Iterable[IntExpr]], Iterable[IntExpr]],
        shape: Optional[Tuple[int, int]] = None,
    ):
        super().__init__(data, shape)

    def __neg__(self) -> "IntArray2D":
        return _elementwise(Op.NEG, self.shape, [self])

    def __add__(self, other: IntOperand2D) -> "IntArray2D":
        return _elementwise(Op.ADD, self.shape, [self, other])

    def __radd__(self, other: IntOperand2D) -> "IntArray2D":
        return _elementwise(Op.ADD, self.shape, [other, self])

    def __sub__(self, other: IntOperand2D) -> "IntArray2D":
        return _elementwise(Op.SUB, self.shape, [self, other])

    def __rsub__(self, other: IntOperand2D) -> "IntArray2D":
        return _elementwise(Op.SUB, self.shape, [other, self])

    def __eq__(self, other: IntOperand2D) -> "BoolArray2D":  # type: ignore
        return _elementwise(Op.EQ, self.shape, [self, other])

    def __ne__(self, other: IntOperand2D) -> "BoolArray2D":  # type: ignore
        return _elementwise(Op.NE, self.shape, [self, other])

    def __ge__(self, other: IntOperand2D) -> "BoolArray2D":
        return _elementwise(Op.GE, self.shape, [self, other])

    def __gt__(self, other: IntOperand2D) -> "BoolArray2D":
        return _elementwise(Op.GT, self.shape, [self, other])

    def __le__(self, other: IntOperand2D) -> "BoolArray2D":
        return _elementwise(Op.LE, self.shape, [self, other])

    def __lt__(self, other: IntOperand2D) -> "BoolArray2D":
        return _elementwise(Op.LT, self.shape, [self, other])

    @overload
    def __getitem__(self, key: Tuple[int, int]) -> IntExpr:
        ...

    @overload
    def __getitem__(
        self, key: Union[int, Tuple[int, slice], Tuple[slice, int], Iterable[Tuple[int, int]]]
    ) -> IntArray1D:
        ...

    @overload
    def __getitem__(self, key: Union[slice, Tuple[slice, slice]]) -> "IntArray2D":
        ...

    def __getitem__(
        self,
        key: Union[
            int,
            slice,
            Tuple[int, int],
            Tuple[int, slice],
            Tuple[slice, int],
            Tuple[slice, slice],
            Iterable[Tuple[int, int]],
        ],
    ) -> Union[IntExpr, IntArray1D, "IntArray2D"]:
        ret = super()._getitem_impl(key)
        if isinstance(ret, Array1D):
            return IntArray1D(ret.data)
        elif isinstance(ret, Array2D):
            return IntArray2D(ret.data, ret.shape)
        else:
            return ret

    def flatten(self) -> IntArray1D:
        return IntArray1D(self.data)

    def reshape(self, shape: Tuple[int, int]) -> "IntArray2D":
        return _reshape(self, shape)

    @overload
    def four_neighbors(self, y: int, x: int) -> IntArray1D:
        ...

    @overload
    def four_neighbors(self, y: Tuple[int, int]) -> IntArray1D:
        ...

    def four_neighbors(
        self, y: Union[int, Tuple[int, int]], x: Optional[int] = None
    ) -> IntArray1D:
        return IntArray1D(cast("List[IntExpr]", _four_neighbors(self, y, x)))

    @overload
    def four_neighbor_indices(self, y: int, x: int) -> List[Tuple[int, int]]:
        ...

    @overload
    def four_neighbor_indices(self, y: Tuple[int, int]) -> List[Tuple[int, int]]:
        ...

    def four_neighbor_indices(
        self, y: Union[int, Tuple[int, int]], x: Optional[int] = None
    ) -> List[Tuple[int, int]]:
        return _four_neighbor_indices(self.shape, y, x)

    def alldifferent(self) -> "BoolExpr":
        return BoolExpr(Op.ALLDIFF, self.data)


@overload
def _reshape(array: Union[BoolArray1D, BoolArray2D], shape: Tuple[int, int]) -> BoolArray2D:
    ...


@overload
def _reshape(array: Union[IntArray1D, IntArray2D], shape: Tuple[int, int]) -> IntArray2D:
    ...


def _reshape(
    array: Union[BoolArray1D, BoolArray2D, IntArray1D, IntArray2D], shape: Tuple[int, int]
) -> Union[BoolArray2D, IntArray2D]:
    data: Union[List[BoolExpr], List[IntExpr]] = array.data
    if len(data) != functools.reduce(lambda x, y: x * y, shape, 1):
        raise ValueError(f"reshaping array of total size {len(data)} into shape {shape}")
    if isinstance(array, (BoolArray1D, BoolArray2D)):
        return BoolArray2D(cast("List[BoolExpr]", data), cast("Tuple[int, int]", shape))
    else:
        return IntArray2D(cast("List[IntExpr]", data), cast("Tuple[int, int]", shape))


def _four_neighbors(
    array: Union[BoolArray2D, IntArray2D], y: Union[int, Tuple[int, int]], x: Optional[int]
) -> List[Expr]:
    if x is None:
        if isinstance(y, int):
            raise TypeError("two integers must be provided to 'cell_neighbors'")
        y2, x2 = y
    else:
        if x is None or isinstance(y, tuple):
            raise TypeError("two integers must be provided to 'cell_neighbors'")
        y2 = y
        x2 = x
    ret: List[Expr] = []
    height, width = array.shape
    if y2 > 0:
        ret.append(array[y2 - 1, x2])
    if y2 < height - 1:
        ret.append(array[y2 + 1, x2])
    if x2 > 0:
        ret.append(array[y2, x2 - 1])
    if x2 < width - 1:
        ret.append(array[y2, x2 + 1])
    return ret


def _four_neighbor_indices(
    shape: Tuple[int, int], y: Union[int, Tuple[int, int]], x: Optional[int]
) -> List[Tuple[int, int]]:
    if x is None:
        if isinstance(y, int):
            raise TypeError("two integers must be provided to 'cell_neighbors'")
        y2, x2 = y
    else:
        if x is None or isinstance(y, tuple):
            raise TypeError("two integers must be provided to 'cell_neighbors'")
        y2 = y
        x2 = x
    ret = []
    height, width = shape
    if y2 > 0:
        ret.append((y2 - 1, x2))
    if y2 < height - 1:
        ret.append((y2 + 1, x2))
    if x2 > 0:
        ret.append((y2, x2 - 1))
    if x2 < width - 1:
        ret.append((y2, x2 + 1))
    return ret
