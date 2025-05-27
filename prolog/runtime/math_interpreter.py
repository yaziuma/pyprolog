from prolog.parser.expression import Visitor
from prolog.core.errors import InterpreterError
import typing

if typing.TYPE_CHECKING:
    pass
from prolog.parser import types as prolog_types  # Use an alias to avoid conflict
from prolog.util.logger import logger  # Added logger for zero division warning


class MathInterpreter(Visitor):
    """Arithmetic Interpreter

    This class walks the expression tree and evaluates returning
    the computed value.
    """
    def __init__(self, binding_env):
        self.binding_env = binding_env

    def _evaluate_expr(self, expr):
        # If expr is a Term (e.g. from parser like Term('+', Var, Num)),
        # it needs to be handled by visit_term or similar.
        # If expr is already a Number or Variable from prolog.core.types,
        # it should be handled by visit_prolog_number or visit_prolog_variable.
        if isinstance(expr, prolog_types.Number): # prolog.parser.types.Number
            return expr # Already a number, return as is.
        elif isinstance(expr, prolog_types.Variable): # prolog.core.types.Variable
            return self.visit_prolog_variable(expr)
        elif isinstance(expr, prolog_types.Term): # prolog.core.types.Term (e.g. from parser for +, -, *)
            return self.visit_prolog_term_expression(expr)
        # Assuming expr from parser.expression (BinaryExpression, PrimaryExpression)
        # will have an accept method.
        elif hasattr(expr, 'accept'):
            return expr.accept(self)
        else:
            # This case might indicate an unexpected type for an arithmetic expression.
            # For example, an atom that isn't a number or a bound variable.
            logger.error(f"MathInterpreter._evaluate_expr: Cannot evaluate type {type(expr)}: {expr}")
            raise InterpreterError(f"Cannot evaluate non-arithmetic expression: {expr}")


    def _compute_binary_operand(self, left_val, operand_str, right_val):
        # Ensure left_val and right_val are Python numbers for computation
        if not isinstance(left_val, (int, float)):
            raise InterpreterError(f"Left operand '{left_val}' is not a number.")
        if not isinstance(right_val, (int, float)):
            raise InterpreterError(f"Right operand '{right_val}' is not a number.")

        if operand_str == "*":
            result = left_val * right_val
        elif operand_str == "/":
            if right_val == 0:
                logger.warning("ZeroDivisionError: division by zero.")
                raise InterpreterError("Division by zero") # Or return a specific Prolog error indicator
            result = left_val / right_val
        elif operand_str == "+":
            result = left_val + right_val
        elif operand_str == "-":
            result = left_val - right_val
        elif operand_str == "mod":
            if right_val == 0:
                logger.warning("ZeroDivisionError: modulo by zero.")
                raise InterpreterError("Modulo by zero")
            result = left_val % right_val
        elif operand_str == "//" or operand_str == "div":
            if right_val == 0:
                logger.warning("ZeroDivisionError: integer division by zero.")
                raise InterpreterError("Integer division by zero")
            result = left_val // right_val
        else:
            raise InterpreterError(f"Invalid binary operand {operand_str}")
        
        # Return as prolog.parser.types.Number
        return prolog_types.Number(result)

    def visit_prolog_term_expression(self, term_expr: prolog_types.Term):
        # Handles expressions like Term('+', [Op1, Op2])
        # This is called when _evaluate_expr gets a prolog.core.types.Term
        # that represents an arithmetic operation.
        op_name = term_expr.pred
        args = term_expr.args

        if op_name in ['+', '-', '*', '/', '//', 'div', 'mod'] and len(args) == 2:
            left_operand = self._evaluate_expr(args[0]) # Recursively evaluate left operand
            right_operand = self._evaluate_expr(args[1]) # Recursively evaluate right operand
            
            # Ensure operands are evaluated to prolog_types.Number which have a .pred (value)
            if not isinstance(left_operand, prolog_types.Number):
                raise InterpreterError(f"Left operand '{args[0]}' did not evaluate to a number for operator '{op_name}'. Got: {left_operand}")
            if not isinstance(right_operand, prolog_types.Number):
                raise InterpreterError(f"Right operand '{args[1]}' did not evaluate to a number for operator '{op_name}'. Got: {right_operand}")

            return self._compute_binary_operand(left_operand.pred, op_name, right_operand.pred)
        # Handle unary minus/plus if necessary, e.g., Term('-', [Op1])
        # For now, assuming binary ops as per parser's current output for arithmetic.
        else:
            # If it's a Term but not a recognized arithmetic operation,
            # it might be a variable or a number-like atom that needs dereferencing.
            # However, _evaluate_expr should handle Variable and Number directly.
            # This path implies a Term that isn't an arithmetic op, variable, or number.
            # This could be an error or a function call if Prolog functions were supported.
            logger.error(f"MathInterpreter.visit_prolog_term_expression: Unhandled Term structure for arithmetic: {term_expr}")
            raise InterpreterError(f"Term '{term_expr}' is not a recognized arithmetic expression.")


    def visit_binary(self, expr): # expr is BinaryExpression from prolog.parser.expression
        # This method is part of the Visitor pattern for AST nodes from prolog.parser.expression
        # It's less likely to be used if the parser directly creates prolog.core.types.Term for arithmetic.
        left_eval = self._evaluate_expr(expr.left) # Should yield prolog_types.Number
        right_eval = self._evaluate_expr(expr.right) # Should yield prolog_types.Number

        if not isinstance(left_eval, prolog_types.Number) or not isinstance(right_eval, prolog_types.Number):
            raise InterpreterError("Operands in BinaryExpression did not evaluate to Numbers.")

        return self._compute_binary_operand(left_eval.pred, expr.operand.lexeme, right_eval.pred)

    def visit_primary(self, expr): # expr is PrimaryExpression from prolog.parser.expression
        # This method is also for AST nodes from prolog.parser.expression.
        # It needs to handle numbers and variables from that AST structure.
        # The 'exp' attribute of PrimaryExpression seems to hold the actual value/token.
        
        # If expr.exp is already a prolog_types.Number (e.g. from scanner/parser)
        if isinstance(expr.exp, prolog_types.Number):
            return expr.exp
        
        # If expr.exp is a Token (e.g. VARIABLE token)
        # This part is speculative as PrimaryExpression structure is not fully clear here.
        # Assuming expr.exp might be a token that needs to be converted to Variable or Number.
        # However, the parser seems to create prolog.core.types.Variable or prolog.parser.types.Number directly.
        # For now, let's assume _evaluate_expr handles these cases before calling accept().

        # Fallback: if expr.exp is something else, try to evaluate it.
        # This might be redundant if _evaluate_expr is comprehensive.
        return self._evaluate_expr(expr.exp)


    def visit_prolog_number(self, number_node: prolog_types.Number):
        # Called when _evaluate_expr gets a prolog.parser.types.Number
        return number_node

    def visit_prolog_variable(self, var_node: prolog_types.Variable):
        # Called when _evaluate_expr gets a prolog.core.types.Variable
        value = self.binding_env.get_value(var_node)
        if isinstance(value, prolog_types.Variable) and value.name == var_node.name and not self.binding_env.is_bound(value): # Unbound variable
            logger.warning(f"Instantiation error: Variable {var_node.name} is not bound.")
            raise InterpreterError(f"Instantiation error: Variable {var_node.name} is not bound.")
        
        if isinstance(value, prolog_types.Number):
            return value # Return the prolog_types.Number object
        elif isinstance(value, (int, float)): # If it somehow got a raw Python number
             return prolog_types.Number(value)
        else:
            logger.warning(f"Type error: Variable {var_node.name} is bound to non-numeric value {value}.")
            raise InterpreterError(f"Type error: Variable {var_node.name} is bound to non-numeric value {value}.")
