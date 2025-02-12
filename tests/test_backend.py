import pytest

import cspuz


class TestBackend:
    # TODO: test sugar, sugar_extended, csugar and enigma_csp
    @pytest.fixture(autouse=True, params=["z3", "cspuz_core"])
    def default_backend(self, request):
        cspuz.config.default_backend = request.param

    @pytest.fixture
    def solver(self):
        return cspuz.Solver()

    def test_find_answer(self, solver):
        x = solver.bool_var()
        y = solver.bool_var()

        solver.ensure(x.then(y))
        solver.ensure((~x).then(y))

        assert solver.find_answer()

    def test_solve(self, solver):
        x = solver.bool_var()
        y = solver.bool_var()

        solver.ensure(x.then(y))
        solver.ensure((~x).then(y))
        solver.add_answer_key(x, y)

        assert solver.solve()
        assert x.sol is None
        assert y.sol is True
