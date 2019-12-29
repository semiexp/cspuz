# cspuz: A library for making puzzle solvers based on CSP reduction

cspuz is a Python library for making puzzle solvers based on CSP reduction.
It offers:
- Intuitive interfaces to use efficient CSP solvers from Python, and
- A collection of functionalities which makes writing puzzle solvers easier.

## Requirements

cspuz requires a CSP solver corresponding to the backend specified in the program.
Currently, two backends are supported:

- [Sugar](http://bach.istc.kobe-u.ac.jp/sugar/)
- sugar-ext, which aims to reduce the overhead of invokation of `sugar` script of Sugar.

In cspuz, Sugar backend is used by default.
However, for better performance, sugar-ext is highly recommended.

##  Setup

###  Sugar backend

To use Sugar backend, you first need to install Sugar (which can be downloaded from [Sugar's website](http://bach.istc.kobe-u.ac.jp/sugar/)).
Then, you need to specify the path of `sugar` script (provided in the Sugar archive) by `$SUGAR_PATH` environment variable.

### sugar-ext backend

sugar-ext backend also depends on Sugar.
Therefore, as in the case of Sugar backend, you need to install Sugar first.
After installing Sugar, you need to specify the path of Sugar JAR file by `$SUGAR_JAR` environment variable, then compile `CspuzSugarInterface` by running `sugar_extension/compile.sh` (JDK required).
Then, you need to specify the path of `sugar_extension/sugar_ext.sh` script (rather than `sugar`) by `$SUGAR_PATH` environment variable.
Please note that `$SUGAR_JAR` is also required for running `sugar_ext.sh`.
