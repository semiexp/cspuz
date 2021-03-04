import pytest

import cspuz
from cspuz.array import BoolArray1D, BoolArray2D, IntArray1D, IntArray2D

from tests.util import check_equality_expr


def apply_binary_operator(left, op, right):
    if op == '+':
        return left + right
    elif op == '-':
        return left - right
    elif op == '==':
        return left == right
    elif op == '!=':
        return left != right
    elif op == '>=':
        return left >= right
    elif op == '>':
        return left > right
    elif op == '<=':
        return left <= right
    elif op == '<':
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
    (slice(4, 7, None), [4, 5, 6]), (slice(4, 2, None), []),
    (slice(2, -2, None), [2, 3, 4, 5, 6, 7]), (slice(8, 0, -2), [8, 6, 4, 2]),
    (slice(2, 11, 1), [2, 3, 4, 5, 6, 7, 8, 9]),
    (slice(-5, None, 1), [5, 6, 7, 8, 9])
]


class TestArray:
    @pytest.fixture
    def solver(self):
        return cspuz.Solver()

    @pytest.mark.parametrize("key,expected", ARRAY_INDEX_TEST_PATTERN)
    def test_array1d_getitem(self, solver, key, expected):
        array = solver.bool_array(10)
        actual = array[key]
        assert len(actual) == len(expected)
        for i in range(len(actual)):
            assert check_equality_expr(actual[i], array[expected[i]])

    @pytest.mark.parametrize("key,expected", ARRAY_INDEX_TEST_PATTERN)
    def test_array2d_getitem_first_dim(self, solver, key, expected):
        array = solver.bool_array((10, 10))
        actual = array[key, 2]
        assert actual.shape == (len(expected), )
        for i in range(len(actual)):
            assert check_equality_expr(actual[i], array[expected[i], 2])

    @pytest.mark.parametrize("key,expected", ARRAY_INDEX_TEST_PATTERN)
    def test_array2d_getitem_second_dim(self, solver, key, expected):
        array = solver.bool_array((10, 10))
        actual = array[3, key]
        assert actual.shape == (len(expected), )
        for i in range(len(actual)):
            assert check_equality_expr(actual[i], array[3, expected[i]])

    @pytest.mark.parametrize("op",
                             ["+", "-", "==", "!=", ">=", ">", "<=", "<"])
    @pytest.mark.parametrize("int_operand", [False, True])
    def test_operator_ivar1d_ivar(self, solver, op, int_operand):
        x = solver.int_array(7, 0, 5)
        y = 3 if int_operand else solver.int_var(0, 5)
        res = apply_binary_operator(x, op, y)
        assert isinstance(res, (BoolArray1D, IntArray1D))
        assert res.shape == (7, )
        for i in range(7):
            assert check_equality_expr(res[i],
                                       apply_binary_operator(x[i], op, y))

    @pytest.mark.parametrize("op,op_flip", [("+", None), ("-", None),
                                            ("==", "=="), ("!=", "!="),
                                            (">=", "<="), (">", "<"),
                                            ("<=", ">="), ("<", ">")])
    @pytest.mark.parametrize("int_operand", [False, True])
    def test_operator_ivar_ivar1d(self, solver, op, op_flip, int_operand):
        x = 3 if int_operand else solver.int_var(0, 5)
        y = solver.int_array(7, 0, 5)
        res = apply_binary_operator(x, op, y)
        assert isinstance(res, (BoolArray1D, IntArray1D))
        assert res.shape == (7, )
        for i in range(7):
            if op_flip is None:
                assert check_equality_expr(res[i],
                                           apply_binary_operator(x, op, y[i]))
            else:
                assert check_equality_expr(
                    res[i], apply_binary_operator(y[i], op_flip, x))

    @pytest.mark.parametrize("op",
                             ["+", "-", "==", "!=", ">=", ">", "<=", "<"])
    @pytest.mark.parametrize("int_operand", [False, True])
    def test_operator_ivar2d_ivar(self, solver, op, int_operand):
        x = solver.int_array((4, 3), 0, 5)
        y = 3 if int_operand else solver.int_var(0, 5)
        res = apply_binary_operator(x, op, y)
        assert isinstance(res, (BoolArray2D, IntArray2D))
        assert res.shape == (4, 3)
        for i in range(4):
            for j in range(3):
                assert check_equality_expr(
                    res[i, j], apply_binary_operator(x[i, j], op, y))

    @pytest.mark.parametrize("op,op_flip", [("+", None), ("-", None),
                                            ("==", "=="), ("!=", "!="),
                                            (">=", "<="), (">", "<"),
                                            ("<=", ">="), ("<", ">")])
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
                    assert check_equality_expr(
                        res[i, j], apply_binary_operator(x, op, y[i, j]))
                else:
                    assert check_equality_expr(
                        res[i, j], apply_binary_operator(y[i, j], op_flip, x))

    @pytest.mark.parametrize("op",
                             ["+", "-", "==", "!=", ">=", ">", "<=", "<"])
    def test_operator_ivar2d_ivar1d(self, solver, op):
        x = solver.int_array((4, 3), 0, 5)
        y = solver.int_array(4, 0, 5)
        with pytest.raises(ValueError, match=r".*shape mismatch.*"):
            apply_binary_operator(x, op, y)

    @pytest.mark.parametrize("op",
                             ["+", "-", "==", "!=", ">=", ">", "<=", "<"])
    def test_operator_ivar1d_ivar2d(self, solver, op):
        x = solver.int_array(4, 0, 5)
        y = solver.int_array((4, 3), 0, 5)
        with pytest.raises(ValueError, match=r".*shape mismatch.*"):
            apply_binary_operator(x, op, y)
