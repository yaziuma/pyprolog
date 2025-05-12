from .expression import Visitor
from .errors import InterpreterError
import typing
if typing.TYPE_CHECKING:
    from .types import Number, FALSE
from . import types as prolog_types # Use an alias to avoid conflict
from prolog.logger import logger # Added logger for zero division warning


class MathInterpreter(Visitor):
    """Arithmetic Interpreter

    This class walks the expression tree and evaluates returning
    the computed value.
    """

    def _evaluate_expr(self, expr):
        return expr.accept(self)

    def _compute_binary_operand(self, left, operand, right):
        if type(left) != type(right):
            raise InterpreterError(
                f'left {left} and right {right} operand must have the same type'
            )  # noqa
        if operand == '*':
            return left.multiply(right)
        elif operand == '/':
            return left.divide(right)
        elif operand == '+':
            return left.add(right)
        elif operand == '-':
            return left.substract(right)
        elif operand == 'mod':
            if not isinstance(left, prolog_types.Number) or not isinstance(right, prolog_types.Number):
                raise InterpreterError(f"Operands for 'mod' must be Numbers. Got {type(left)} and {type(right)}")
            if right.pred == 0:
                logger.warning("ZeroDivisionError: modulo by zero.")
                return prolog_types.FALSE() # Standard Prolog behavior for division by zero is often an error or false.
            return prolog_types.Number(left.pred % right.pred)
        elif operand == '//' or operand == 'div': # Supporting both // and div for integer division
            if not isinstance(left, prolog_types.Number) or not isinstance(right, prolog_types.Number):
                raise InterpreterError(f"Operands for '//' or 'div' must be Numbers. Got {type(left)} and {type(right)}")
            if right.pred == 0:
                logger.warning("ZeroDivisionError: integer division by zero.")
                return prolog_types.FALSE()
            return prolog_types.Number(left.pred // right.pred)
        else:
            raise InterpreterError(f'Invalid binary operand {operand}')

    def visit_binary(self, expr):
        left = self._evaluate_expr(expr.left)
        right = self._evaluate_expr(expr.right)

        return self._compute_binary_operand(left, expr.operand, right)

    def visit_primary(self, expr):
        return expr.exp
