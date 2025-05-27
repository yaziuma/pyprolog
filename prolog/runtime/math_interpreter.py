from prolog.core.types import Term, Variable, Number, PrologType  # String を追加
from prolog.core.binding_environment import BindingEnvironment
from prolog.core.errors import PrologError
from prolog.core.operators import (
    operator_registry,
)  # 循環参照の可能性を低減するため、必要な場合のみインポート
from typing import Union  # Union をインポート


class MathInterpreter:
    def evaluate(
        self, expression: PrologType, env: BindingEnvironment
    ) -> Union[int, float]:
        if isinstance(expression, Number):
            return expression.value
        if isinstance(expression, Variable):
            value = env.get_value(expression.name)
            if value is None:
                raise PrologError(
                    f"Instantiation error: Variable {expression.name} is not bound."
                )
            # 束縛された値がさらに評価が必要な式である可能性を考慮
            # Number 型に直接キャストするのではなく、再帰的に evaluate を呼び出す
            if isinstance(value, (Number, Term, Variable)):  # String は評価できない
                return self.evaluate(value, env)
            else:
                raise PrologError(
                    f"Cannot evaluate bound value of {expression.name} as arithmetic expression: {value} (type: {type(value)})"
                )

        if isinstance(expression, Term):
            # is/2 の右辺の評価ロジック
            # ここでは、Term が算術演算子を表すと仮定
            op_symbol = str(expression.functor.name)  # TermのfunctorはAtom
            op_info = operator_registry.get_operator(op_symbol)

            if op_info and op_info.operator_type == OperatorType.ARITHMETIC:
                if op_info.arity == 2 and len(expression.args) == 2:
                    left_val = self.evaluate(expression.args[0], env)
                    right_val = self.evaluate(expression.args[1], env)
                    return self.evaluate_binary_op(op_symbol, left_val, right_val)
                # TODO: 単項算術演算子の処理 (例: -X)
                # elif op_info.arity == 1 and len(expression.args) == 1:
                #     operand_val = self.evaluate(expression.args[0], env)
                #     return self.evaluate_unary_op(op_symbol, operand_val)
            raise PrologError(
                f"Cannot evaluate arithmetic expression: {expression}. Unknown operator or arity mismatch."
            )

        raise PrologError(
            f"Unsupported expression type for math evaluation: {type(expression)} - {expression}"
        )

    def evaluate_binary_op(
        self, op_symbol: str, left_val: Union[int, float], right_val: Union[int, float]
    ) -> Union[int, float]:
        if not (
            isinstance(left_val, (int, float)) and isinstance(right_val, (int, float))
        ):
            # このエラーは evaluate でキャッチされるべきだが、念のため
            raise PrologError(
                f"Arithmetic operation {op_symbol} requires numeric arguments, got {left_val} ({type(left_val)}) and {right_val} ({type(right_val)})"
            )

        if op_symbol == "+":
            return left_val + right_val
        if op_symbol == "-":
            return left_val - right_val
        if op_symbol == "*":
            return left_val * right_val
        if op_symbol == "/":
            if right_val == 0:
                raise PrologError("Division by zero")
            return left_val / right_val
        if op_symbol == "//":
            if right_val == 0:
                raise PrologError("Integer division by zero")
            return left_val // right_val
        if op_symbol == "**":
            return left_val**right_val
        if op_symbol == "mod":
            if right_val == 0:
                raise PrologError("Modulo by zero")
            return left_val % right_val

        raise PrologError(f"Unknown binary arithmetic operator: {op_symbol}")

    # def evaluate_unary_op(self, op_symbol: str, operand_val: Union[int, float]) -> Union[int, float]:
    #     if op_symbol == '-': return -operand_val
    #     # 他の単項算術演算子
    #     raise PrologError(f"Unknown unary arithmetic operator: {op_symbol}")

    def evaluate_comparison_op(
        self, op_symbol: str, left_val: Union[int, float], right_val: Union[int, float]
    ) -> bool:
        if not (
            isinstance(left_val, (int, float)) and isinstance(right_val, (int, float))
        ):
            # このエラーは evaluate でキャッチされるべきだが、念のため
            raise PrologError(
                f"Comparison operation {op_symbol} requires numeric arguments, got {left_val} ({type(left_val)}) and {right_val} ({type(right_val)})"
            )

        if op_symbol == "=:=":
            return left_val == right_val
        if op_symbol == "=\\=":
            return left_val != right_val
        if op_symbol == "<":
            return left_val < right_val
        if op_symbol == "=<":
            return left_val <= right_val
        if op_symbol == ">":
            return left_val > right_val
        if op_symbol == ">=":
            return left_val >= right_val

        raise PrologError(f"Unknown comparison operator: {op_symbol}")


# OperatorType をインポートするために必要 (evaluateメソッド内)
from prolog.core.operators import OperatorType
