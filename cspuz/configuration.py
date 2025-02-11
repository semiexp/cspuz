from distutils.util import strtobool
import os
from typing import Optional


def _get_default(infer_from_env, env_key, default):
    if infer_from_env:
        return os.environ.get(env_key, default)
    else:
        return default


def _strtobool_optional(s: Optional[str]) -> Optional[bool]:
    if s is None:
        return None
    else:
        return strtobool(s)


def _detect_backend() -> str:
    try:
        import cspuz_core  # type: ignore  # noqa

        return "cspuz_core"
    except ImportError:
        pass

    try:
        import enigma_csp  # type: ignore  # noqa

        return "enigma_csp"
    except ImportError:
        pass

    try:
        import pycsugar  # type: ignore  # noqa

        return "csugar"
    except ImportError:
        pass

    try:
        import z3  # type: ignore  # noqa

        return "z3"
    except ImportError:
        pass

    return "sugar"


class Config(object):
    """
    Class for maintaining the solver configurations.

    Currently, there are 5 different backends supported:

    - `sugar`
    Sugar CSP solver (https://cspsat.gitlab.io/sugar/).
    - `sugar_extended`
    Sugar CSP solver with an optimization for `solve_irrefutably` feature.
    - `z3`
    z3 SMT solver (https://pypi.org/project/z3-solver/).
    Prerequisite: `import z3` succeeds.
    - `csugar`
    csugar CSP solver (https://github.com/semiexp/csugar) with Python
    interface.
    Prerequisite: `import pycsugar` succeeds.
    - `cspuz_core`
    cspuz_core CSP solver (https://github.com/semiexp/cspuz_core) with Python
    interface.
    Prerequisite: `import cspuz_core` succeeds.
    - `auto`
    Automatically decide the backend based on availability of the libraries.
    The priority is as follows:
      - `cspuz_core`
      - `enigma_csp`
      - `csugar`
      - `z3`
      - `sugar`

    For backward compatibility, `enigma_csp` (the former name of `cspuz_core`)
    is also supported.

    `default_backend` is the name of a backend (listed above) which is used
    by default in `Solver`.

    `backend_path` specifies the path to the executable of the backend solver
    (e.g. `sugar` script, `sugar_ext.sh`, or a binary of Sugar-compatible
    CSP solver like csugar) for `sugar` and `sugar_extended` backends.

    `use_graph_primitive` controls whether native graph constraints are used.
    This feature is supported by csugar and cspuz_core CSP solver and is
    enabled by default for `csugar` and `cspuz_core` backends.
    You can use this for `sugar` and `sugar_extended` backends to work with
    csugar or cspuz_core CLI, but cspuz does not check whether the backend
    actually supports native graph constraints.
    Note that `use_graph_primitive` affects how graph constraints are
    translated on the invocation of graph constraints methods (like
    `active_vertices_connected`). Therefore, it is strongly recommended to set
    `default_backend` correctly, rather than specifying the backend on calling
    `Solver.solve` or `Solver.solve_irrefutably`.
    """

    default_backend: str
    backend_path: Optional[str]
    csugar_binding: Optional[str]
    use_graph_primitive: bool
    use_graph_division_primitive: bool
    solver_timeout: Optional[float]

    def __init__(self, infer_from_env=True):
        default_backend = _get_default(infer_from_env, "CSPUZ_DEFAULT_BACKEND", "auto")

        if default_backend == "auto":
            self.default_backend = _detect_backend()
        else:
            self.default_backend = default_backend

        self.backend_path = _get_default(infer_from_env, "CSPUZ_BACKEND_PATH", None)
        if self.default_backend in ("csugar", "enigma_csp", "cspuz_core"):
            graph_primitive_default = "True"
        else:
            graph_primitive_default = "False"
        if self.default_backend in ("enigma_csp", "cspuz_core"):
            graph_division_primitive_default = "True"
        else:
            graph_division_primitive_default = "False"
        self.use_graph_primitive = _strtobool_optional(
            _get_default(infer_from_env, "CSPUZ_USE_GRAPH_PRIMITIVE", graph_primitive_default)
        )
        self.use_graph_division_primitive = _strtobool_optional(
            _get_default(
                infer_from_env,
                "CSPUZ_USE_GRAPH_DIVISION_PRIMITIVE",
                graph_division_primitive_default,
            )
        )
        self.solver_timeout = None


config = Config()
