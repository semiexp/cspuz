from ..configuration import config
from ..expr import BoolVar, IntVar
from . import sugar

from ._subproc import run_subprocess


class CSPSolver(sugar.CSPSolver):
    def __init__(self, variables):
        super(CSPSolver, self).__init__(variables)

    def solve_irrefutably(self, is_answer_key):
        answer_keys = []
        for i in range(len(self.variables)):
            if is_answer_key[i]:
                if isinstance(self.variables[i], BoolVar):
                    answer_keys.append('b{}'.format(self.variables[i].id))
                elif isinstance(self.variables[i], IntVar):
                    answer_keys.append('i{}'.format(self.variables[i].id))
                else:
                    raise TypeError()
        answer_keys_desc = '#' + ' '.join(answer_keys)
        csp_description = '\n'.join(self.converted_variables +
                                    self.converted_constraints +
                                    [answer_keys_desc])
        sugar_path = config.backend_path or 'sugar'
        out = run_subprocess([sugar_path, '/dev/stdin'],
                             csp_description,
                             timeout=config.solver_timeout).split('\n')
        for v in self.variables:
            v.sol = None

        if 'unsat' in out[0]:
            return False

        assignment = [None] * (self.max_var_id + 1)
        for line in out[1:]:
            if len(line) <= 2:
                break
            var, val = line.split(' ')
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
