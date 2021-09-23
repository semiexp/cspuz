"""
CSP backend using the Sugar CSP solver (http://bach.istc.kobe-u.ac.jp/sugar/).
"""

from ..configuration import config
from ..expr import Op, Expr, BoolVar, IntVar

from ._binding import call_sugar_binding
from ._subproc import run_subprocess

OP_TO_OPNAME = {
    Op.NEG: '-',
    Op.ADD: '+',
    Op.SUB: '-',
    Op.EQ: '=',
    Op.NE: '!=',
    Op.LE: '<=',
    Op.LT: '<',
    Op.GE: '>=',
    Op.GT: '>',
    Op.NOT: '!',
    Op.AND: '&&',
    Op.OR: '||',
    Op.IFF: 'iff',
    Op.XOR: 'xor',
    Op.IMP: '=>',
    Op.IF: 'if',
    Op.ALLDIFF: 'alldifferent',
    Op.GRAPH_ACTIVE_VERTICES_CONNECTED: 'graph-active-vertices-connected'
}


def _convert_variable(v):
    if isinstance(v, BoolVar):
        return '(bool b{})'.format(v.id)
    elif isinstance(v, IntVar):
        return '(int i{} {} {})'.format(v.id, v.lo, v.hi)
    else:
        raise TypeError()


def _convert_expr(e):
    if isinstance(e, bool):
        return ('true' if e else 'false')
    if isinstance(e, int):
        return str(e)
    if not isinstance(e, Expr):
        raise TypeError()

    if isinstance(e, BoolVar):
        return 'b{}'.format(e.id)
    elif isinstance(e, IntVar):
        return 'i{}'.format(e.id)
    elif e.op == Op.BOOL_CONSTANT:
        return 'true' if e.operands[0] else 'false'
    elif e.op == Op.INT_CONSTANT:
        return str(e.operands[0])
    else:
        return '({} {})'.format(OP_TO_OPNAME[e.op],
                                ' '.join(map(_convert_expr, e.operands)))


class CSPSolver(object):
    def __init__(self, variables):
        self.variables = variables
        max_var_id = -1
        for v in self.variables:
            if isinstance(v, (BoolVar, IntVar)):
                max_var_id = max(max_var_id, v.id)
            else:
                raise TypeError()
        self.max_var_id = max_var_id
        self.converted_variables = list(map(_convert_variable, self.variables))
        self.converted_constraints = []

    def add_constraint(self, constraint):
        if isinstance(constraint, list):
            self.converted_constraints += map(_convert_expr, constraint)
        else:
            self.converted_constraints.append(_convert_expr(constraint))

    def solve(self):
        csp_description = '\n'.join(self.converted_variables +
                                    self.converted_constraints)
        sugar_path = config.backend_path or 'sugar'
        if config.sugar_binding is not None:
            out = call_sugar_binding(config.sugar_binding,
                                     csp_description).split('\n')
        else:
            out = run_subprocess([sugar_path, '/dev/stdin'],
                                 csp_description,
                                 timeout=config.solver_timeout).split('\n')
        if 'UNSATISFIABLE' in out[0]:
            for v in self.variables:
                v.sol = None
            return False

        assignment = [None] * (self.max_var_id + 1)
        for line in out[1:]:
            if len(line) <= 2:
                break
            var, val = line[2:].strip().split('\t')
            if val == 'true':
                converted_val = True
            elif val == 'false':
                converted_val = False
            else:
                converted_val = int(val)
            assignment[int(var[1:])] = converted_val
        for v in self.variables:
            v.sol = assignment[v.id]
        return True
