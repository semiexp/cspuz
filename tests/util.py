from cspuz.expr import Expr, BoolVar, IntVar


def check_equality_expr(left: Expr, right: Expr):
    if left.op != right.op:
        return False
    if len(left.operands) != len(right.operands):
        return False
    if isinstance(left, (BoolVar, IntVar)):
        if not isinstance(right, (BoolVar, IntVar)):
            return False
        return left.id == right.id
    for i in range(len(left.operands)):
        is_expr_left = isinstance(left.operands[i], Expr)
        is_expr_right = isinstance(right.operands[i], Expr)
        if is_expr_left != is_expr_right:
            return False
        if is_expr_left:
            if not check_equality_expr(left.operands[i], right.operands[i]):
                return False
        else:
            if left.operands[i] != right.operands[i]:
                return False
    return True
