import multiprocessing
import os
import signal
import subprocess
import sys
import time
from types import SimpleNamespace

import pytest

from cspuz.configuration import config
from cspuz.backend.sugar_like import (
    CSugarBackend,
    CspuzCoreBackend,
    EnigmaCSPBackend,
    _run_with_timeout,
)

requires_fork = pytest.mark.skipif(
    "fork" not in multiprocessing.get_all_start_methods(), reason="requires fork"
)


def test_no_timeout_runs_in_parent() -> None:
    assert _run_with_timeout(os.getpid, timeout=None) == os.getpid()
    result = object()
    assert _run_with_timeout(lambda: result, timeout=None) is result


@requires_fork
def test_inherits_config(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(config, "backend_path", "custom-backend")

    def read_config(suffix: str) -> tuple:
        assert config.backend_path is not None
        return os.getpid(), config.backend_path + suffix

    pid, path = _run_with_timeout(read_config, "-suffix", timeout=5.0)
    assert pid != os.getpid()
    assert path == "custom-backend-suffix"


@requires_fork
def test_large_result() -> None:
    result = "x" * (2 * 1024 * 1024)
    assert _run_with_timeout(lambda: result, timeout=5.0) == result


@requires_fork
def test_exception_is_propagated() -> None:
    def fail() -> None:
        raise ValueError("solver failed")

    with pytest.raises(ValueError, match="solver failed"):
        _run_with_timeout(fail, timeout=5.0)


@requires_fork
@pytest.mark.parametrize("exitcode", [0, 1])
def test_child_exit(exitcode: int) -> None:
    with pytest.raises(RuntimeError, match="Solver subprocess exited"):
        _run_with_timeout(os._exit, exitcode, timeout=5.0)


@requires_fork
def test_timeout_kills_and_reaps_child() -> None:
    children = multiprocessing.active_children()

    def hang() -> None:
        signal.signal(signal.SIGTERM, signal.SIG_IGN)
        time.sleep(30)

    start = time.monotonic()
    with pytest.raises(subprocess.TimeoutExpired) as exc_info:
        _run_with_timeout(hang, timeout=0.1)
    assert exc_info.value.timeout == 0.1
    assert time.monotonic() - start < 5.0
    assert multiprocessing.active_children() == children


@requires_fork
@pytest.mark.parametrize(
    "backend_type,module_name,function_name",
    [
        (CSugarBackend, "pycsugar", "solver"),
        (EnigmaCSPBackend, "enigma_csp", "solver"),
        (CspuzCoreBackend, "cspuz_core", "solver_with_perf"),
    ],
)
def test_backends_use_timeout(
    monkeypatch: pytest.MonkeyPatch, backend_type: type, module_name: str, function_name: str
) -> None:
    module = SimpleNamespace(setting="custom", delay=0.0)

    def solve(description: str) -> object:
        assert module.setting == "custom"
        assert os.getpid() != parent_pid
        time.sleep(module.delay)
        if function_name == "solver_with_perf":
            return description, {"decisions": 42.0}
        return description

    parent_pid = os.getpid()
    setattr(module, function_name, solve)
    monkeypatch.setitem(sys.modules, module_name, module)
    monkeypatch.setattr(config, "solver_timeout", 5.0)
    backend = backend_type([])
    assert backend._call_solver("test input") == "test input"
    if function_name == "solver_with_perf":
        assert backend.perf_stats() == {"decisions": 42.0}

    module.delay = 30.0
    monkeypatch.setattr(config, "solver_timeout", 0.1)
    with pytest.raises(subprocess.TimeoutExpired):
        backend._call_solver("test input")


@requires_fork
def test_cspuz_core_with_timeout(monkeypatch: pytest.MonkeyPatch) -> None:
    pytest.importorskip("cspuz_core")
    from cspuz import Solver

    monkeypatch.setattr(config, "solver_timeout", 5.0)
    solver = Solver()
    x = solver.int_var(0, 2)
    solver.ensure(x == 1)
    solver.add_answer_key(x)
    assert solver.find_answer(backend="cspuz_core")
    assert x.sol == 1
    assert solver.perf_stats() is not None
    assert solver.solve(backend="cspuz_core")
    assert x.sol == 1
    solver.ensure(x == 2)
    assert not solver.find_answer(backend="cspuz_core")
    assert not solver.solve(backend="cspuz_core")
