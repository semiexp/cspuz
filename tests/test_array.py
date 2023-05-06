import pytest

import cspuz
from cspuz.array import BoolArray1D, BoolArray2D, IntArray1D, IntArray2D

from tests.util import check_equality_expr


def apply_binary_operator(left, op, right):
    if op == "+":
        return left + right
    elif op == "-":
        return left - right
    elif op == "&":
        return left & right
    elif op == "|":
        return left | right
    elif op == "then":
        return left.then(right)
    elif op == "==":
        return left == right
    elif op == "!=":
        return left != right
    elif op == "^":
        return left ^ right
    elif op == ">=":
        return left >= right
    elif op == ">":
        return left > right
    elif op == "<=":
        return left <= right
    elif op == "<":
        return left < right
    else:
        raise ValueError(f"unexpected operator: {op}")


ARRAY_INDEX_TEST_PATTERN = [
    (slice(None, None, None), [0, 1, 2, 3, 4, 5, 6, 7, 8, 9]),
    (slice(None, None, 1), [0, 1, 2, 3, 4, 5, 6, 7, 8, 9]),
    (slice(None, None, 2), [0, 2, 4, 6, 8]),
    (slice(None, None, -1), [9, 8, 7, 6, 5, 4, 3, 2, 1, 0]),
    (slice(None, None, -2), [9, 7, 5, 3, 1]),
    (slice(0, 10, None), [0, 1, 2, 3, 4, 5, 6, 7, 8, 9]),
    (slice(4, 7, None), [4, 5, 6]),
    (slice(4, 2, None), []),
    (slice(2, -2, None), [2, 3, 4, 5, 6, 7]),
    (slice(8, 0, -2), [8, 6, 4, 2]),
    (slice(2, 11, 1), [2, 3, 4, 5, 6, 7, 8, 9]),
    (slice(-5, None, 1), [5, 6, 7, 8, 9]),
    (slice(4, 8, -1), []),
]

FOUR_NEIGHBOR_TEST_PATTERN = [
    (3, 4, 1, 2, [(0, 2), (2, 2), (1, 1), (1, 3)]),
    (3, 4, 2, 2, [(1, 2), (2, 1), (2, 3)]),
    (3, 4, 0, 0, [(0, 1), (1, 0)]),
    (1, 5, 0, 4, [(0, 3)]),
    (6, 1, 3, 0, [(2, 0), (4, 0)]),
    (1, 1, 0, 0, []),
]


class TestArray:
    @pytest.fixture
    def solver(self):
        return cspuz.Solver()

    def test_bool_array2d_constructor(self, solver):
        vars = []
        for i in range(6):
            vars.append(solver.bool_var())
        array = BoolArray2D([[vars[0], vars[1], vars[2]], [vars[3], vars[4], vars[5]]])
        for i in range(2):
            for j in range(3):
                assert check_equality_expr(array[i, j], vars[i * 3 + j])

    def test_int_array2d_constructor(self, solver):
        vars = []
        for i in range(6):
            vars.append(solver.int_var(0, 3))
        array = IntArray2D([[vars[0], vars[1], vars[2]], [vars[3], vars[4], vars[5]]])
        for i in range(2):
            for j in range(3):
                assert check_equality_expr(array[i, j], vars[i * 3 + j])

    def test_bool_array1d_size(self, solver):
        array = solver.bool_array(42)
        assert array.size() == 42

    def test_bool_array1d_iter(self, solver):
        array = solver.bool_array(10)
        array_as_list = list(iter(array))
        for i in range(10):
            assert check_equality_expr(array[i], array_as_list[i])

    def test_bool_array1d_len(self, solver):
        array = solver.bool_array(42)
        assert len(array) == 42

    def test_bool_array1d_reshape(self, solver):
        array = solver.bool_array(12)
        array_reshaped = array.reshape((3, 4))
        for i in range(3):
            for j in range(4):
                assert check_equality_expr(array_reshaped[i, j], array[i * 4 + j])

    def test_bool_array1d_reshape_bad_size(self, solver):
        array = solver.bool_array(14)
        with pytest.raises(ValueError):
            array.reshape((3, 5))

    def test_int_array1d_size(self, solver):
        array = solver.int_array(42, 0, 5)
        assert array.size() == 42

    def test_int_array1d_iter(self, solver):
        array = solver.int_array(10, 0, 5)
        array_as_list = list(iter(array))
        for i in range(10):
            assert check_equality_expr(array[i], array_as_list[i])

    def test_int_array1d_len(self, solver):
        array = solver.int_array(42, 0, 5)
        assert len(array) == 42

    def test_int_array1d_reshape(self, solver):
        array = solver.int_array(12, 0, 5)
        array_reshaped = array.reshape((3, 4))
        for i in range(3):
            for j in range(4):
                assert check_equality_expr(array_reshaped[i, j], array[i * 4 + j])

    def test_bool_array2d_len(self, solver):
        array = solver.bool_array((3, 4))
        assert len(array) == 3

    def test_bool_array2d_iter(self, solver):
        array = solver.bool_array((3, 4))
        array_as_list = list(iter(array))
        for i in range(3):
            for j in range(4):
                assert check_equality_expr(array[i, j], array_as_list[i * 4 + j])

    def test_int_array2d_len(self, solver):
        array = solver.int_array((3, 4), 0, 3)
        assert len(array) == 3

    def test_int_array2d_iter(self, solver):
        array = solver.int_array((3, 4), 0, 3)
        array_as_list = list(iter(array))
        for i in range(3):
            for j in range(4):
                assert check_equality_expr(array[i, j], array_as_list[i * 4 + j])

    def test_bool_array2d_flatten(self, solver):
        array = solver.bool_array((3, 5))
        array_flat = array.flatten()
        for i in range(3):
            for j in range(5):
                assert check_equality_expr(array[i, j], array_flat[i * 5 + j])

    def test_bool_int2d_flatten(self, solver):
        array = solver.int_array((3, 5), 0, 10)
        array_flat = array.flatten()
        for i in range(3):
            for j in range(5):
                assert check_equality_expr(array[i, j], array_flat[i * 5 + j])

    def test_bool_array2d_reshape(self, solver):
        array = solver.bool_array((3, 4))
        array_reshaped = array.reshape((2, 6))
        for i in range(3):
            for j in range(4):
                p = i * 4 + j
                i2 = p // 6
                j2 = p % 6
                assert check_equality_expr(array[i, j], array_reshaped[i2, j2])

    def test_int_array2d_reshape(self, solver):
        array = solver.int_array((3, 4), -1, 1)
        array_reshaped = array.reshape((2, 6))
        for i in range(3):
            for j in range(4):
                p = i * 4 + j
                i2 = p // 6
                j2 = p % 6
                assert check_equality_expr(array[i, j], array_reshaped[i2, j2])

    def test_bool_array1d_index(self, solver):
        array = solver.bool_array(10)
        assert check_equality_expr(array[-3], array[7])

    def test_bool_array1d_out_of_index(self, solver):
        array = solver.bool_array(10)
        with pytest.raises(IndexError):
            _ = array[10]

    def test_bool_array1d_out_of_index_negative(self, solver):
        array = solver.bool_array(10)
        with pytest.raises(IndexError):
            _ = array[-11]

    @pytest.mark.parametrize("key,expected", ARRAY_INDEX_TEST_PATTERN)
    def test_bool_array1d_getitem(self, solver, key, expected):
        array = solver.bool_array(10)
        actual = array[key]
        assert len(actual) == len(expected)
        for i in range(len(actual)):
            assert check_equality_expr(actual[i], array[expected[i]])

    @pytest.mark.parametrize("key,expected", ARRAY_INDEX_TEST_PATTERN)
    def test_int_array1d_getitem(self, solver, key, expected):
        array = solver.int_array(10, 0, 5)
        actual = array[key]
        assert len(actual) == len(expected)
        for i in range(len(actual)):
            assert check_equality_expr(actual[i], array[expected[i]])

    @pytest.mark.parametrize("key,expected", ARRAY_INDEX_TEST_PATTERN)
    def test_bool_array2d_getitem_first_dim(self, solver, key, expected):
        array = solver.bool_array((10, 10))
        actual = array[key, 2]
        assert actual.shape == (len(expected),)
        for i in range(len(actual)):
            assert check_equality_expr(actual[i], array[expected[i], 2])

    @pytest.mark.parametrize("key,expected", ARRAY_INDEX_TEST_PATTERN)
    def test_bool_array2d_getitem_second_dim(self, solver, key, expected):
        array = solver.bool_array((10, 10))
        actual = array[3, key]
        assert actual.shape == (len(expected),)
        for i in range(len(actual)):
            assert check_equality_expr(actual[i], array[3, expected[i]])

    @pytest.mark.parametrize("key,expected", ARRAY_INDEX_TEST_PATTERN)
    def test_int_array2d_getitem_first_dim(self, solver, key, expected):
        array = solver.int_array((10, 10), 0, 5)
        actual = array[key, 2]
        assert actual.shape == (len(expected),)
        for i in range(len(actual)):
            assert check_equality_expr(actual[i], array[expected[i], 2])

    @pytest.mark.parametrize("key,expected", ARRAY_INDEX_TEST_PATTERN)
    def test_int_array2d_getitem_second_dim(self, solver, key, expected):
        array = solver.int_array((10, 10), 0, 5)
        actual = array[3, key]
        assert actual.shape == (len(expected),)
        for i in range(len(actual)):
            assert check_equality_expr(actual[i], array[3, expected[i]])

    def test_bool_array2d_getitem_both_slice(self, solver):
        array = solver.bool_array((10, 10))
        actual = array[2:5, -3::-1]
        assert actual.shape == (3, 8)
        for i in range(3):
            for j in range(8):
                assert check_equality_expr(actual[i, j], array[i + 2, 7 - j])

    def test_int_array2d_getitem_both_slice(self, solver):
        array = solver.int_array((10, 10), 2, 4)
        actual = array[2:5, -3::-1]
        assert actual.shape == (3, 8)
        for i in range(3):
            for j in range(8):
                assert check_equality_expr(actual[i, j], array[i + 2, 7 - j])

    def test_bool_array2d_getitem_negative_index(self, solver):
        array = solver.bool_array((10, 10))
        assert check_equality_expr(array[-2, -5], array[8, 5])

    def test_int_array2d_getitem_negative_index(self, solver):
        array = solver.int_array((10, 10), 0, 3)
        assert check_equality_expr(array[-2, -5], array[8, 5])

    def test_bool_array2d_getitem_index_error(self, solver):
        array = solver.bool_array((10, 8))
        with pytest.raises(IndexError):
            _ = array[10, 5]

    def test_bool_array2d_getitem_index_error_negative(self, solver):
        array = solver.bool_array((10, 8))
        with pytest.raises(IndexError):
            _ = array[3, -9]

    def test_int_array2d_getitem_index_error(self, solver):
        array = solver.int_array((10, 8), -2, 5)
        with pytest.raises(IndexError):
            _ = array[10, 5]

    def test_int_array2d_getitem_index_error_negative(self, solver):
        array = solver.int_array((10, 8), -2, 5)
        with pytest.raises(IndexError):
            _ = array[3, -9]

    def test_bool_array2d_getitem_1d(self, solver):
        array = solver.bool_array((5, 8))
        actual = array[2:4]
        assert actual.shape == (2, 8)
        for i in range(2):
            for j in range(8):
                assert check_equality_expr(actual[i, j], array[i + 2, j])

    def test_int_array2d_getitem_1d(self, solver):
        array = solver.int_array((5, 8), 0, 2)
        actual = array[2:4]
        assert actual.shape == (2, 8)
        for i in range(2):
            for j in range(8):
                assert check_equality_expr(actual[i, j], array[i + 2, j])

    def test_bool_array2d_getitem_by_array(self, solver):
        array = solver.bool_array((8, 10))
        actual = array[[(1, 2), (-3, 7), (5, -5), (-1, -1)]]
        expected = [array[1, 2], array[5, 7], array[5, 5], array[7, 9]]
        assert actual.shape == (4,)
        for i in range(4):
            assert check_equality_expr(actual[i], expected[i])

    def test_int_array2d_getitem_by_array(self, solver):
        array = solver.int_array((8, 10), 0, 2)
        actual = array[[(1, 2), (-3, 7), (5, -5), (-1, -1)]]
        expected = [array[1, 2], array[5, 7], array[5, 5], array[7, 9]]
        assert actual.shape == (4,)
        for i in range(4):
            assert check_equality_expr(actual[i], expected[i])

    @pytest.mark.parametrize("height,width,y,x,expected", FOUR_NEIGHBOR_TEST_PATTERN)
    def test_bool_array2d_four_neighbor_indices(self, solver, height, width, y, x, expected):
        array = solver.bool_array((height, width))
        actual = array.four_neighbor_indices(y, x)
        assert set(actual) == set(expected)

    @pytest.mark.parametrize("height,width,y,x,expected", FOUR_NEIGHBOR_TEST_PATTERN)
    def test_bool_array2d_four_neighbors(self, solver, height, width, y, x, expected):
        array = solver.bool_array((height, width))
        indices = array.four_neighbor_indices(y, x)
        actual = array.four_neighbors(y, x)

        assert len(indices) == len(actual)
        for i in range(len(indices)):
            assert check_equality_expr(array[indices[i]], actual[i])

    @pytest.mark.parametrize("height,width,y,x,expected", FOUR_NEIGHBOR_TEST_PATTERN)
    def test_int_array2d_four_neighbor_indices(self, solver, height, width, y, x, expected):
        array = solver.int_array((height, width), -5, -2)
        actual = array.four_neighbor_indices(y, x)
        assert set(actual) == set(expected)
        actual2 = array.four_neighbor_indices((y, x))
        assert set(actual2) == set(expected)

    @pytest.mark.parametrize("height,width,y,x,expected", FOUR_NEIGHBOR_TEST_PATTERN)
    def test_int_array2d_four_neighbors(self, solver, height, width, y, x, expected):
        array = solver.int_array((height, width), 1, 4)
        indices = array.four_neighbor_indices(y, x)
        actual = array.four_neighbors(y, x)

        assert len(indices) == len(actual)
        for i in range(len(indices)):
            assert check_equality_expr(array[indices[i]], actual[i])

    @pytest.mark.parametrize("height,width,y,x,expected", FOUR_NEIGHBOR_TEST_PATTERN)
    def test_int_array2d_four_neighbors_as_tuple(self, solver, height, width, y, x, expected):
        array = solver.int_array((height, width), 1, 4)
        indices = array.four_neighbor_indices((y, x))
        actual = array.four_neighbors((y, x))

        assert len(indices) == len(actual)
        for i in range(len(indices)):
            assert check_equality_expr(array[indices[i]], actual[i])


class TestArrayOperators:
    @pytest.fixture
    def solver(self):
        return cspuz.Solver()

    def test_neg_ivar1d(self, solver):
        x = solver.int_array(7, 0, 5)
        res = -x
        assert isinstance(res, IntArray1D)
        assert res.shape == (7,)
        for i in range(7):
            assert check_equality_expr(res[i], -(x[i]))

    def test_neg_ivar2d(self, solver):
        x = solver.int_array((3, 4), 0, 5)
        res = -x
        assert isinstance(res, IntArray2D)
        assert res.shape == (3, 4)
        for i in range(3):
            for j in range(4):
                assert check_equality_expr(res[i, j], -(x[i, j]))

    @pytest.mark.parametrize("op", ["+", "-", "==", "!=", ">=", ">", "<=", "<"])
    @pytest.mark.parametrize("int_operand", [False, True])
    def test_operator_ivar1d_ivar(self, solver, op, int_operand):
        x = solver.int_array(7, 0, 5)
        y = 3 if int_operand else solver.int_var(0, 5)
        res = apply_binary_operator(x, op, y)
        assert isinstance(res, (BoolArray1D, IntArray1D))
        assert res.shape == (7,)
        for i in range(7):
            assert check_equality_expr(res[i], apply_binary_operator(x[i], op, y))

    @pytest.mark.parametrize(
        "op,op_flip",
        [
            ("+", None),
            ("-", None),
            ("==", "=="),
            ("!=", "!="),
            (">=", "<="),
            (">", "<"),
            ("<=", ">="),
            ("<", ">"),
        ],
    )
    @pytest.mark.parametrize("int_operand", [False, True])
    def test_operator_ivar_ivar1d(self, solver, op, op_flip, int_operand):
        x = 3 if int_operand else solver.int_var(0, 5)
        y = solver.int_array(7, 0, 5)
        res = apply_binary_operator(x, op, y)
        assert isinstance(res, (BoolArray1D, IntArray1D))
        assert res.shape == (7,)
        for i in range(7):
            if op_flip is None:
                assert check_equality_expr(res[i], apply_binary_operator(x, op, y[i]))
            else:
                assert check_equality_expr(res[i], apply_binary_operator(y[i], op_flip, x))

    @pytest.mark.parametrize("op", ["+", "-", "==", "!=", ">=", ">", "<=", "<"])
    @pytest.mark.parametrize("int_operand", [False, True])
    def test_operator_ivar2d_ivar(self, solver, op, int_operand):
        x = solver.int_array((4, 3), 0, 5)
        y = 3 if int_operand else solver.int_var(0, 5)
        res = apply_binary_operator(x, op, y)
        assert isinstance(res, (BoolArray2D, IntArray2D))
        assert res.shape == (4, 3)
        for i in range(4):
            for j in range(3):
                assert check_equality_expr(res[i, j], apply_binary_operator(x[i, j], op, y))

    @pytest.mark.parametrize(
        "op,op_flip",
        [
            ("+", None),
            ("-", None),
            ("==", "=="),
            ("!=", "!="),
            (">=", "<="),
            (">", "<"),
            ("<=", ">="),
            ("<", ">"),
        ],
    )
    @pytest.mark.parametrize("int_operand", [False, True])
    def test_operator_ivar_ivar2d(self, solver, op, op_flip, int_operand):
        x = 3 if int_operand else solver.int_var(0, 5)
        y = solver.int_array((4, 3), 0, 5)
        res = apply_binary_operator(x, op, y)
        assert isinstance(res, (BoolArray2D, IntArray2D))
        assert res.shape == (4, 3)
        for i in range(4):
            for j in range(3):
                if op_flip is None:
                    assert check_equality_expr(res[i, j], apply_binary_operator(x, op, y[i, j]))
                else:
                    assert check_equality_expr(
                        res[i, j], apply_binary_operator(y[i, j], op_flip, x)
                    )

    @pytest.mark.parametrize("op", ["+", "-", "==", "!=", ">=", ">", "<=", "<"])
    def test_operator_ivar2d_ivar1d(self, solver, op):
        x = solver.int_array((4, 3), 0, 5)
        y = solver.int_array(4, 0, 5)
        with pytest.raises(ValueError, match=r".*shape mismatch.*"):
            apply_binary_operator(x, op, y)

    @pytest.mark.parametrize("op", ["+", "-", "==", "!=", ">=", ">", "<=", "<"])
    def test_operator_ivar1d_ivar2d(self, solver, op):
        x = solver.int_array(4, 0, 5)
        y = solver.int_array((4, 3), 0, 5)
        with pytest.raises(ValueError, match=r".*shape mismatch.*"):
            apply_binary_operator(x, op, y)

    def test_invert_bvar1d(self, solver):
        x = solver.bool_array(7)
        res = ~x
        assert isinstance(res, BoolArray1D)
        assert res.shape == (7,)
        for i in range(7):
            assert check_equality_expr(res[i], ~(x[i]))

    def test_invert_bvar2d(self, solver):
        x = solver.bool_array((5, 4))
        res = ~x
        assert isinstance(res, BoolArray2D)
        assert res.shape == (5, 4)
        for i in range(5):
            for j in range(4):
                assert check_equality_expr(res[i, j], ~(x[i, j]))

    @pytest.mark.parametrize("op", ["&", "|", "^", "==", "!=", "then"])
    @pytest.mark.parametrize("bool_operand", [False, True])
    def test_operator_bvar1d_bvar(self, solver, op, bool_operand):
        x = solver.bool_array(7)
        y = True if bool_operand else solver.bool_var()
        res = apply_binary_operator(x, op, y)
        assert isinstance(res, BoolArray1D)
        assert res.shape == (7,)
        for i in range(7):
            assert check_equality_expr(res[i], apply_binary_operator(x[i], op, y))

    @pytest.mark.parametrize(
        "op,op_flip",
        [("&", None), ("|", None), ("^", None), ("==", "=="), ("!=", "!="), ("then", None)],
    )
    @pytest.mark.parametrize("bool_operand", [False, True])
    def test_operator_bvar_bvar1d(self, solver, op, op_flip, bool_operand):
        if op == "then" and bool_operand:
            return
        x = True if bool_operand else solver.bool_var()
        y = solver.bool_array(7)
        res = apply_binary_operator(x, op, y)
        assert isinstance(res, BoolArray1D)
        assert res.shape == (7,)
        for i in range(7):
            if op_flip is None:
                assert check_equality_expr(res[i], apply_binary_operator(x, op, y[i]))
            else:
                assert check_equality_expr(res[i], apply_binary_operator(y[i], op_flip, x))

    @pytest.mark.parametrize("op", ["&", "|", "^", "==", "!=", "then"])
    @pytest.mark.parametrize("bool_operand", [False, True])
    def test_operator_bvar2d_bvar(self, solver, op, bool_operand):
        x = solver.bool_array((3, 4))
        y = True if bool_operand else solver.bool_var()
        res = apply_binary_operator(x, op, y)
        assert isinstance(res, BoolArray2D)
        assert res.shape == (3, 4)
        for i in range(3):
            for j in range(4):
                assert check_equality_expr(res[i, j], apply_binary_operator(x[i, j], op, y))

    @pytest.mark.parametrize(
        "op,op_flip",
        [("&", None), ("|", None), ("^", None), ("==", "=="), ("!=", "!="), ("then", None)],
    )
    @pytest.mark.parametrize("bool_operand", [False, True])
    def test_operator_bvar_bvar2d(self, solver, op, op_flip, bool_operand):
        if op == "then" and bool_operand:
            return
        x = True if bool_operand else solver.bool_var()
        y = solver.bool_array((3, 4))
        res = apply_binary_operator(x, op, y)
        assert isinstance(res, BoolArray2D)
        assert res.shape == (3, 4)
        for i in range(3):
            for j in range(4):
                if op_flip is None:
                    assert check_equality_expr(res[i, j], apply_binary_operator(x, op, y[i, j]))
                else:
                    assert check_equality_expr(
                        res[i, j], apply_binary_operator(y[i, j], op_flip, x)
                    )

    @pytest.mark.parametrize("op", ["&", "|", "^", "==", "!=", "then"])
    def test_operator_bvar2d_bvar1d(self, solver, op):
        x = solver.bool_array((4, 3))
        y = solver.bool_array(4)
        with pytest.raises(ValueError, match=r".*shape mismatch.*"):
            apply_binary_operator(x, op, y)

    @pytest.mark.parametrize("op", ["&", "|", "^", "==", "!=", "then"])
    def test_operator_bvar1d_bvar2d(self, solver, op):
        x = solver.bool_array(
            4,
        )
        y = solver.bool_array((4, 3))
        with pytest.raises(ValueError, match=r".*shape mismatch.*"):
            apply_binary_operator(x, op, y)

    @pytest.mark.parametrize("dim_x", [0, 1, 2])
    @pytest.mark.parametrize("dim_y", [-1, 0, 1, 2])
    @pytest.mark.parametrize("dim_z", [-1, 0, 1, 2])
    def test_cond(self, solver, dim_x, dim_y, dim_z):
        if dim_x == 0:
            x = solver.bool_var()
        elif dim_x == 1:
            x = solver.bool_array(5)
        elif dim_x == 2:
            x = solver.bool_array((3, 4))
        else:
            raise ValueError()

        if dim_y == -1:
            y = 2
        elif dim_y == 0:
            y = solver.int_var(0, 2)
        elif dim_y == 1:
            y = solver.int_array(5, 0, 2)
        elif dim_y == 2:
            y = solver.int_array((3, 4), 0, 2)
        else:
            raise ValueError()

        if dim_z == -1:
            z = 3
        elif dim_z == 0:
            z = solver.int_var(0, 2)
        elif dim_z == 1:
            z = solver.int_array(5, 0, 2)
        elif dim_z == 2:
            z = solver.int_array((3, 4), 0, 2)
        else:
            raise ValueError()

        expected_dim = max(dim_x, dim_y, dim_z)
        if expected_dim == 2 and (dim_x == 1 or dim_y == 1 or dim_z == 1):
            with pytest.raises(ValueError, match=r".*shape mismatch.*"):
                _ = x.cond(y, z)
        else:
            res = x.cond(y, z)
            if expected_dim == 0:
                pass
            elif expected_dim == 1:
                assert isinstance(res, IntArray1D)
                for i in range(5):
                    if dim_x == 1:
                        px = x[i]
                    else:
                        px = x
                    if dim_y == 1:
                        py = y[i]
                    else:
                        py = y
                    if dim_z == 1:
                        pz = z[i]
                    else:
                        pz = z
                    assert check_equality_expr(res[i], px.cond(py, pz))
            else:
                assert isinstance(res, IntArray2D)
                for i in range(3):
                    for j in range(4):
                        if dim_x == 2:
                            px = x[i, j]
                        else:
                            px = x
                        if dim_y == 2:
                            py = y[i, j]
                        else:
                            py = y
                        if dim_z == 2:
                            pz = z[i, j]
                        else:
                            pz = z
                    assert check_equality_expr(res[i, j], px.cond(py, pz))
