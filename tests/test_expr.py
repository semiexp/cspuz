import pytest

import cspuz
from cspuz.expr import Expr, Op

from tests.util import check_equality_expr


class TestExprConstruction:
    @pytest.fixture
    def solver(self):
        return cspuz.Solver()

    @pytest.fixture
    def ix(self, solver):
        return solver.int_var(0, 5)

    @pytest.fixture
    def iy(self, solver):
        return solver.int_var(0, 5)

    @pytest.fixture
    def bx(self, solver):
        return solver.bool_var()

    @pytest.fixture
    def by(self, solver):
        return solver.bool_var()

    def input(self, solver, x):
        if x == "ivar":
            return solver.int_var(0, 5)
        elif x == "bvar":
            return solver.bool_var()
        else:
            return x

    def test_cond_var_var_var(self, bx, ix, iy):
        assert check_equality_expr(bx.cond(ix, iy), Expr(Op.IF, [bx, ix, iy]))

    def test_cond_bool_var_var(self, ix, iy):
        assert check_equality_expr(cspuz.cond(True, ix, iy), Expr(Op.IF, [True, ix, iy]))

    def test_inv_var(self, bx):
        assert check_equality_expr(~bx, Expr(Op.NOT, [bx]))

    def test_and_var_var(self, bx, by):
        assert check_equality_expr(bx & by, Expr(Op.AND, [bx, by]))

    def test_and_var_bool(self, bx):
        assert check_equality_expr(bx & True, Expr(Op.AND, [bx, True]))

    def test_and_bool_var(self, bx):
        assert check_equality_expr(True & bx, Expr(Op.AND, [True, bx]))

    def test_or_var_var(self, bx, by):
        assert check_equality_expr(bx | by, Expr(Op.OR, [bx, by]))

    def test_or_var_bool(self, bx):
        assert check_equality_expr(bx | True, Expr(Op.OR, [bx, True]))

    def test_or_bool_var(self, bx):
        assert check_equality_expr(True | bx, Expr(Op.OR, [True, bx]))

    def test_beq_var_var(self, bx, by):
        assert check_equality_expr(bx == by, Expr(Op.IFF, [bx, by]))

    def test_beq_var_bool(self, bx):
        assert check_equality_expr(bx == True, Expr(Op.IFF, [bx, True]))  # noqa: E501, E712

    def test_beq_bool_var(self, bx):
        assert check_equality_expr(True == bx, Expr(Op.IFF, [bx, True]))  # noqa: E501, E712

    def test_bne_var_var(self, bx, by):
        assert check_equality_expr(bx != by, Expr(Op.XOR, [bx, by]))

    def test_bne_var_bool(self, bx):
        assert check_equality_expr(bx != True, Expr(Op.XOR, [bx, True]))  # noqa: E501, E712

    def test_bne_bool_var(self, bx):
        assert check_equality_expr(True != bx, Expr(Op.XOR, [bx, True]))  # noqa: E501, E712

    def test_bxor_var_var(self, bx, by):
        assert check_equality_expr(bx ^ by, Expr(Op.XOR, [bx, by]))

    def test_bxor_var_bool(self, bx):
        assert check_equality_expr(bx ^ True, Expr(Op.XOR, [bx, True]))

    def test_bxor_bool_var(self, bx):
        assert check_equality_expr(True ^ bx, Expr(Op.XOR, [True, bx]))

    def test_fold_or(self, bx):
        assert check_equality_expr(bx.fold_or(), bx)

    def test_fold_or_list(self, bx, by):
        assert check_equality_expr(cspuz.fold_or([bx, by]), Expr(Op.OR, [bx, by]))

    def test_fold_and(self, bx):
        assert check_equality_expr(bx.fold_and(), bx)

    def test_fold_and_list(self, bx, by):
        assert check_equality_expr(cspuz.fold_and([bx, by]), Expr(Op.AND, [bx, by]))

    def test_count_true(self, bx):
        assert check_equality_expr(bx.count_true(), Expr(Op.IF, [bx, 1, 0]))

    def test_neg_var(self, ix):
        assert check_equality_expr(-ix, Expr(Op.NEG, [ix]))

    def test_add_var_var(self, ix, iy):
        assert check_equality_expr(ix + iy, Expr(Op.ADD, [ix, iy]))

    def test_add_var_int(self, ix):
        assert check_equality_expr(ix + 2, Expr(Op.ADD, [ix, 2]))

    def test_add_int_var(self, ix):
        assert check_equality_expr(2 + ix, Expr(Op.ADD, [2, ix]))

    def test_sub_var_var(self, ix, iy):
        assert check_equality_expr(ix - iy, Expr(Op.SUB, [ix, iy]))

    def test_sub_var_int(self, ix):
        assert check_equality_expr(ix - 2, Expr(Op.SUB, [ix, 2]))

    def test_sub_int_var(self, ix):
        assert check_equality_expr(2 - ix, Expr(Op.SUB, [2, ix]))

    def test_ieq_var_var(self, ix, iy):
        assert check_equality_expr(ix == iy, Expr(Op.EQ, [ix, iy]))

    def test_ieq_var_int(self, ix):
        assert check_equality_expr(ix == 2, Expr(Op.EQ, [ix, 2]))

    def test_ieq_int_var(self, ix):
        assert check_equality_expr(2 == ix, Expr(Op.EQ, [ix, 2]))

    def test_ine_var_var(self, ix, iy):
        assert check_equality_expr(ix != iy, Expr(Op.NE, [ix, iy]))

    def test_ine_var_int(self, ix):
        assert check_equality_expr(ix != 2, Expr(Op.NE, [ix, 2]))

    def test_ine_int_var(self, ix):
        assert check_equality_expr(2 != ix, Expr(Op.NE, [ix, 2]))

    def test_ge_var_var(self, ix, iy):
        assert check_equality_expr(ix >= iy, Expr(Op.GE, [ix, iy]))

    def test_ge_var_int(self, ix):
        assert check_equality_expr(ix >= 2, Expr(Op.GE, [ix, 2]))

    def test_ge_int_var(self, ix):
        assert check_equality_expr(2 >= ix, Expr(Op.LE, [ix, 2]))

    def test_gt_var_var(self, ix, iy):
        assert check_equality_expr(ix > iy, Expr(Op.GT, [ix, iy]))

    def test_gt_var_int(self, ix):
        assert check_equality_expr(ix > 2, Expr(Op.GT, [ix, 2]))

    def test_gt_int_var(self, ix):
        assert check_equality_expr(2 > ix, Expr(Op.LT, [ix, 2]))

    def test_le_var_var(self, ix, iy):
        assert check_equality_expr(ix <= iy, Expr(Op.LE, [ix, iy]))

    def test_le_var_int(self, ix):
        assert check_equality_expr(ix <= 2, Expr(Op.LE, [ix, 2]))

    def test_le_int_var(self, ix):
        assert check_equality_expr(2 <= ix, Expr(Op.GE, [ix, 2]))

    def test_lt_var_var(self, ix, iy):
        assert check_equality_expr(ix < iy, Expr(Op.LT, [ix, iy]))

    def test_lt_var_int(self, ix):
        assert check_equality_expr(ix < 2, Expr(Op.LT, [ix, 2]))

    def test_lt_int_var(self, ix):
        assert check_equality_expr(2 < ix, Expr(Op.GT, [ix, 2]))

    def test_type_error_inv(self, ix):
        with pytest.raises(TypeError):
            res = ~ix  # noqa: F841

    @pytest.mark.parametrize(
        "lhs,rhs",
        [
            ("bvar", "ivar"),
            ("ivar", "bvar"),
            ("ivar", "ivar"),
            (True, "ivar"),
            ("bvar", 2),
            (2, "bvar"),
            ("ivar", True),
            (2, "ivar"),
            ("ivar", 2),
        ],
    )
    def test_type_error_and(self, solver, lhs, rhs):
        with pytest.raises(TypeError):
            self.input(solver, lhs) & self.input(solver, rhs)

    @pytest.mark.parametrize(
        "lhs,rhs",
        [
            ("bvar", "ivar"),
            ("ivar", "bvar"),
            ("ivar", "ivar"),
            (True, "ivar"),
            ("bvar", 2),
            (2, "bvar"),
            ("ivar", True),
            (2, "ivar"),
            ("ivar", 2),
        ],
    )
    def test_type_error_or(self, solver, lhs, rhs):
        with pytest.raises(TypeError):
            self.input(solver, lhs) | self.input(solver, rhs)

    def test_type_error_neg(self, bx):
        with pytest.raises(TypeError):
            res = -bx  # noqa: F841

    @pytest.mark.parametrize(
        "lhs,rhs",
        [
            ("bvar", "bvar"),
            ("bvar", "ivar"),
            ("ivar", "bvar"),
            (True, "bvar"),
            ("bvar", True),
            (True, "ivar"),
            ("bvar", 2),
            (2, "bvar"),
            ("ivar", True),
        ],
    )
    def test_type_error_add(self, solver, lhs, rhs):
        with pytest.raises(TypeError):
            self.input(solver, lhs) + self.input(solver, rhs)

    @pytest.mark.parametrize(
        "lhs,rhs",
        [
            ("bvar", "bvar"),
            ("bvar", "ivar"),
            ("ivar", "bvar"),
            (True, "bvar"),
            ("bvar", True),
            (True, "ivar"),
            ("bvar", 2),
            (2, "bvar"),
            ("ivar", True),
        ],
    )
    def test_type_error_sub(self, solver, lhs, rhs):
        with pytest.raises(TypeError):
            self.input(solver, lhs) - self.input(solver, rhs)

    @pytest.mark.parametrize(
        "lhs,rhs",
        [
            ("bvar", "bvar"),
            ("bvar", "ivar"),
            ("ivar", "bvar"),
            (True, "bvar"),
            ("bvar", True),
            (True, "ivar"),
            ("bvar", 2),
            (2, "bvar"),
            ("ivar", True),
        ],
    )
    def test_type_error_ge(self, solver, lhs, rhs):
        with pytest.raises(TypeError):
            res = self.input(solver, lhs) >= self.input(solver, rhs)  # noqa: E501, F841

    @pytest.mark.parametrize(
        "lhs,rhs",
        [
            ("bvar", "bvar"),
            ("bvar", "ivar"),
            ("ivar", "bvar"),
            (True, "bvar"),
            ("bvar", True),
            (True, "ivar"),
            ("bvar", 2),
            (2, "bvar"),
            ("ivar", True),
        ],
    )
    def test_type_error_gt(self, solver, lhs, rhs):
        with pytest.raises(TypeError):
            res = self.input(solver, lhs) > self.input(solver, rhs)  # noqa: E501, F841

    @pytest.mark.parametrize(
        "lhs,rhs",
        [
            ("bvar", "bvar"),
            ("bvar", "ivar"),
            ("ivar", "bvar"),
            (True, "bvar"),
            ("bvar", True),
            (True, "ivar"),
            ("bvar", 2),
            (2, "bvar"),
            ("ivar", True),
        ],
    )
    def test_type_error_le(self, solver, lhs, rhs):
        with pytest.raises(TypeError):
            res = self.input(solver, lhs) <= self.input(solver, rhs)  # noqa: E501, F841

    @pytest.mark.parametrize(
        "lhs,rhs",
        [
            ("bvar", "bvar"),
            ("bvar", "ivar"),
            ("ivar", "bvar"),
            (True, "bvar"),
            ("bvar", True),
            (True, "ivar"),
            ("bvar", 2),
            (2, "bvar"),
            ("ivar", True),
        ],
    )
    def test_type_error_lt(self, solver, lhs, rhs):
        with pytest.raises(TypeError):
            res = self.input(solver, lhs) < self.input(solver, rhs)  # noqa: E501, F841

    def test_is_variable(self, ix, iy, bx, by):
        assert ix.is_variable()
        assert bx.is_variable()
        assert not (ix + iy).is_variable()
        assert not (bx | by).is_variable()


class TestExprValue:
    @pytest.fixture(autouse=True, params=["sugar", "z3"])
    def default_backend(self, request):
        cspuz.config.default_backend = request.param

    @pytest.fixture
    def solver(self):
        return cspuz.Solver()

    @pytest.mark.parametrize("x_val,y_val,z_val,expected", [(True, 1, 2, 1), (False, 1, 2, 2)])
    def test_cond(self, solver, x_val, y_val, z_val, expected):
        x = solver.bool_var()
        y = solver.int_var(-2, 2)
        z = solver.int_var(-2, 2)
        solver.ensure(x == x_val)
        solver.ensure(y == y_val)
        solver.ensure(z == z_val)
        solver.ensure(cspuz.cond(x, y, z) == expected)
        assert solver.find_answer()

    @pytest.mark.parametrize(
        "x_val,y_val,is_sat",
        [(False, False, True), (False, True, True), (True, False, False), (True, True, True)],
    )
    def test_then(self, solver, x_val, y_val, is_sat):
        x = solver.bool_var()
        y = solver.bool_var()
        solver.ensure(x == x_val)
        solver.ensure(y == y_val)
        solver.ensure(x.then(y))
        assert solver.find_answer() == is_sat

    @pytest.mark.parametrize("x_val,is_sat", [(False, True), (True, False)])
    def test_inv(self, solver, x_val, is_sat):
        x = solver.bool_var()
        solver.ensure(x == x_val)
        solver.ensure(~x)
        assert solver.find_answer() == is_sat

    @pytest.mark.parametrize(
        "x_val,y_val,is_sat",
        [(False, False, False), (False, True, False), (True, False, False), (True, True, True)],
    )
    def test_and(self, solver, x_val, y_val, is_sat):
        x = solver.bool_var()
        y = solver.bool_var()
        solver.ensure(x == x_val)
        solver.ensure(y == y_val)
        solver.ensure(x & y)
        assert solver.find_answer() == is_sat

    @pytest.mark.parametrize(
        "x_val,y_val,is_sat",
        [(False, False, False), (False, True, True), (True, False, True), (True, True, True)],
    )
    def test_or(self, solver, x_val, y_val, is_sat):
        x = solver.bool_var()
        y = solver.bool_var()
        solver.ensure(x == x_val)
        solver.ensure(y == y_val)
        solver.ensure(x | y)
        assert solver.find_answer() == is_sat

    @pytest.mark.parametrize(
        "x_val,y_val,is_sat",
        [(False, False, True), (False, True, False), (True, False, False), (True, True, True)],
    )
    def test_beq(self, solver, x_val, y_val, is_sat):
        x = solver.bool_var()
        y = solver.bool_var()
        solver.ensure(x == x_val)
        solver.ensure(y == y_val)
        solver.ensure(x == y)
        assert solver.find_answer() == is_sat

    @pytest.mark.parametrize(
        "x_val,y_val,is_sat",
        [(False, False, False), (False, True, True), (True, False, True), (True, True, False)],
    )
    def test_bne(self, solver, x_val, y_val, is_sat):
        x = solver.bool_var()
        y = solver.bool_var()
        solver.ensure(x == x_val)
        solver.ensure(y == y_val)
        solver.ensure(x != y)
        assert solver.find_answer() == is_sat

    @pytest.mark.parametrize("x_val,expected", [(0, 0), (1, -1), (-1, 1)])
    def test_neg(self, solver, x_val, expected):
        x = solver.int_var(-2, 2)
        solver.ensure(x == x_val)
        solver.ensure(-x == expected)
        assert solver.find_answer()

    @pytest.mark.parametrize("x_val,y_val,expected", [(0, 0, 0), (1, 1, 2), (2, -1, 1)])
    def test_add(self, solver, x_val, y_val, expected):
        x = solver.int_var(-2, 2)
        y = solver.int_var(-2, 2)
        solver.ensure(x == x_val)
        solver.ensure(y == y_val)
        solver.ensure(x + y == expected)
        assert solver.find_answer()

    @pytest.mark.parametrize("x_val,y_val,expected", [(0, 0, 0), (1, 2, -1), (-1, 1, -2)])
    def test_sub(self, solver, x_val, y_val, expected):
        x = solver.int_var(-2, 2)
        y = solver.int_var(-2, 2)
        solver.ensure(x == x_val)
        solver.ensure(y == y_val)
        solver.ensure(x - y == expected)
        assert solver.find_answer()

    @pytest.mark.parametrize("x_val,y_val,is_sat", [(0, 0, True), (1, 2, False), (-2, -2, True)])
    def test_ieq(self, solver, x_val, y_val, is_sat):
        x = solver.int_var(-2, 2)
        y = solver.int_var(-2, 2)
        solver.ensure(x == x_val)
        solver.ensure(y == y_val)
        solver.ensure(x == y)
        assert solver.find_answer() == is_sat

    @pytest.mark.parametrize("x_val,y_val,is_sat", [(0, 0, False), (1, 2, True), (-2, -2, False)])
    def test_ine(self, solver, x_val, y_val, is_sat):
        x = solver.int_var(-2, 2)
        y = solver.int_var(-2, 2)
        solver.ensure(x == x_val)
        solver.ensure(y == y_val)
        solver.ensure(x != y)
        assert solver.find_answer() == is_sat

    @pytest.mark.parametrize("x_val,y_val,is_sat", [(0, 0, True), (1, 2, False), (-1, -2, True)])
    def test_ge(self, solver, x_val, y_val, is_sat):
        x = solver.int_var(-2, 2)
        y = solver.int_var(-2, 2)
        solver.ensure(x == x_val)
        solver.ensure(y == y_val)
        solver.ensure(x >= y)
        assert solver.find_answer() == is_sat

    @pytest.mark.parametrize("x_val,y_val,is_sat", [(0, 0, False), (1, 2, False), (-1, -2, True)])
    def test_gt(self, solver, x_val, y_val, is_sat):
        x = solver.int_var(-2, 2)
        y = solver.int_var(-2, 2)
        solver.ensure(x == x_val)
        solver.ensure(y == y_val)
        solver.ensure(x > y)
        assert solver.find_answer() == is_sat

    @pytest.mark.parametrize("x_val,y_val,is_sat", [(0, 0, True), (1, 2, True), (-1, -2, False)])
    def test_le(self, solver, x_val, y_val, is_sat):
        x = solver.int_var(-2, 2)
        y = solver.int_var(-2, 2)
        solver.ensure(x == x_val)
        solver.ensure(y == y_val)
        solver.ensure(x <= y)
        assert solver.find_answer() == is_sat

    @pytest.mark.parametrize("x_val,y_val,is_sat", [(0, 0, False), (1, 2, True), (-1, -2, False)])
    def test_lt(self, solver, x_val, y_val, is_sat):
        x = solver.int_var(-2, 2)
        y = solver.int_var(-2, 2)
        solver.ensure(x == x_val)
        solver.ensure(y == y_val)
        solver.ensure(x < y)
        assert solver.find_answer() == is_sat
