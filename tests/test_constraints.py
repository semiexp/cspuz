import pytest

import cspuz
from cspuz.expr import Expr, Op

from tests.util import check_equality_expr


class TestConstraints:
    @pytest.fixture
    def solver(self):
        return cspuz.Solver()

    def test_alldifferent(self, solver):
        a = solver.int_array((2, 2), -5, 5)
        b = solver.int_var(-10, 10)
        c = solver.int_var(-10, 10)
        d = solver.int_var(-10, 10)
        e = 2

        actual = cspuz.alldifferent(a, [b, c], d, e)
        assert check_equality_expr(
            actual,
            Expr(Op.ALLDIFF, [a[0, 0], a[0, 1], a[1, 0], a[1, 1], b, c, d, e]))

    def test_fold_or(self, solver):
        a = solver.bool_array((2, 2))
        b = solver.bool_var()
        c = solver.bool_var()
        d = solver.bool_var()

        actual = cspuz.fold_or([[a, b], c], d)
        assert check_equality_expr(
            actual, Expr(Op.OR, [a[0, 0], a[0, 1], a[1, 0], a[1, 1], b, c, d]))

    def test_fold_or_empty(self, solver):
        actual = cspuz.fold_or()
        assert check_equality_expr(actual, Expr(Op.BOOL_CONSTANT, [False]))

    def test_fold_or_with_true_constant(self, solver):
        a = solver.bool_var()
        b = solver.bool_var()
        c = solver.bool_var()
        actual = cspuz.fold_or(a, True, [b, c])
        assert check_equality_expr(actual, Expr(Op.BOOL_CONSTANT, [True]))

    def test_fold_and(self, solver):
        a = solver.bool_array((2, 2))
        b = solver.bool_var()
        c = solver.bool_var()
        d = solver.bool_var()

        actual = cspuz.fold_and([[a, b], c], d)
        assert check_equality_expr(
            actual, Expr(Op.AND,
                         [a[0, 0], a[0, 1], a[1, 0], a[1, 1], b, c, d]))

    def test_fold_and_empty(self, solver):
        actual = cspuz.fold_and()
        assert check_equality_expr(actual, Expr(Op.BOOL_CONSTANT, [True]))

    def test_fold_and_with_false_constant(self, solver):
        a = solver.bool_var()
        b = solver.bool_var()
        c = solver.bool_var()
        actual = cspuz.fold_and(a, False, [b, c])
        assert check_equality_expr(actual, Expr(Op.BOOL_CONSTANT, [False]))

    def test_count_true(self, solver):
        a = solver.bool_array((2, 2))
        b = solver.bool_var()
        actual = cspuz.count_true(False, [a, True], b)
        vars = [a[0, 0], a[0, 1], a[1, 0], a[1, 1], b]
        exprs = list(map(lambda x: Expr(Op.IF, [x, 1, 0]), vars)) + [1]
        assert check_equality_expr(actual, Expr(Op.ADD, exprs))

    def test_count_true_empty(self, solver):
        actual = cspuz.count_true()
        assert check_equality_expr(actual, Expr(Op.INT_CONSTANT, [0]))
