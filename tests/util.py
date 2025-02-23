from cspuz.expr import Expr, ExprLike, BoolVar, IntVar


def check_equality_expr(left: ExprLike, right: ExprLike) -> bool:
    if not isinstance(left, Expr) or not isinstance(right, Expr):
        if isinstance(left, Expr) or isinstance(right, Expr):
            return False
        return left == right

    if left.op != right.op:
        return False
    if len(left.operands) != len(right.operands):
        return False
    if isinstance(left, (BoolVar, IntVar)):
        if not isinstance(right, (BoolVar, IntVar)):
            return False
        return left.id == right.id
    for i in range(len(left.operands)):
        if not check_equality_expr(left.operands[i], right.operands[i]):
            return False
    return True
