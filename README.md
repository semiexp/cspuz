# cspuz: A library for making puzzle solvers based on CSP reduction

cspuz is a Python library for making puzzle solvers based on CSP reduction.
It offers:
- Intuitive interfaces to use efficient CSP solvers from Python, and
- A collection of functionalities which makes writing puzzle solvers easier.

## Requirements

cspuz requires a CSP solver corresponding to the backend specified in the program.
Currently, three backends are supported:

- [z3](https://pypi.org/project/z3-solver/)
- [Sugar](http://bach.istc.kobe-u.ac.jp/sugar/)
- sugar-ext, which aims to reduce the overhead of invokation of `sugar` script of Sugar.

In cspuz, Sugar backend is used by default.
However, for better performance, sugar-ext is highly recommended.
You can change the default backend to sugar-ext by setting the `$CSPUZ_DEFAULT_BACKEND` environment variable to `sugar_extended`.

##  Setup

Before installing cspuz, you need to setup a backend CSP solver.

### z3 backend

Installing z3 will be as easy as just running

```
pip install z3-solver
```

in your terminal.

### Sugar backend

To use Sugar backend, you first need to install Sugar (which can be downloaded from [Sugar's website](http://bach.istc.kobe-u.ac.jp/sugar/)).
Then, you need to specify the path of `sugar` script (provided in the Sugar archive) by `$CSPUZ_BACKEND_PATH` environment variable.

### sugar-ext backend

sugar-ext backend also depends on Sugar.
Therefore, as in the case of Sugar backend, you need to install Sugar first.
After installing Sugar, you need to specify the path of Sugar JAR file by `$SUGAR_JAR` environment variable, then compile `CspuzSugarInterface` by running `sugar_extension/compile.sh` (JDK required).
Then, you need to specify the path of `sugar_extension/sugar_ext.sh` script (rather than `sugar`) by `$CSPUZ_BACKEND_PATH` environment variable.
Please note that `$SUGAR_JAR` is also required for running `sugar_ext.sh`.

### csugar backend

[csugar](https://github.com/semiexp/csugar) is a reimplementation of Sugar CSP solver in C++.
Although it is not fully verified, it offers several performance advangates:

- It can use MiniSat incrementally. This contributes to improve the performance of finding non-refutable assignments (`Solver.solve` in cspuz).
- Moreover, it supports graph connectivity as a *native constraint*. Thus, it can handle constraints such as `cspuz.graph.active_vertices_connected`, `cspuz.graph.division_connected` and `cspuz.graph.active_edges_single_cycle`. To utilize this feature from cspuz, you need to set `$CSPUZ_USE_GRAPH_PRIMITIVE` environment variable to `1`.

`csugar` binary which will be produced by building csugar is designed to run in the same way as `sugar_ext.sh`.
Therefore, you can set the `$CSPUZ_DEFAULT_BACKEND` to `sugar_extended` in order to use csugar.

### Installing cspuz

First clone this repository to whichever directory you like, and run `pip install .` in the directory in which you cloned it.
