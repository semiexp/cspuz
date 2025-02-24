import pytest

import cspuz


# TODO: test sugar, sugar_extended, csugar and enigma_csp
@pytest.fixture(
    autouse=True,
    params=[
        pytest.param("z3"),
        pytest.param("cspuz_core"),
        pytest.param("csugar", marks=pytest.mark.all_backends),
    ],
)
def default_backend(request: pytest.FixtureRequest) -> None:
    cspuz.config.default_backend = request.param


@pytest.fixture
def solver() -> cspuz.Solver:
    return cspuz.Solver()


def test_find_answer(solver: cspuz.Solver) -> None:
    x = solver.bool_var()
    y = solver.bool_var()

    solver.ensure(x.then(y))
    solver.ensure((~x).then(y))

    assert solver.find_answer()


def test_solve(solver: cspuz.Solver) -> None:
    x = solver.bool_var()
    y = solver.bool_var()

    solver.ensure(x.then(y))
    solver.ensure((~x).then(y))
    solver.add_answer_key(x, y)

    assert solver.solve()
    assert x.sol is None
    assert y.sol is True
