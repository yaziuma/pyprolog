from prolog.core.types import Term, Variable, Number, Rule, Fact
from prolog.core.binding_environment import BindingEnvironment
from prolog.parser.scanner import Scanner
from prolog.parser.parser import Parser
from prolog.runtime.math_interpreter import MathInterpreter
from prolog.runtime.logic_interpreter import LogicInterpreter
from prolog.core.operators import operator_registry, OperatorType, OperatorInfo
from prolog.core.errors import PrologError
from typing import Callable

# ログ設定
import logging

logger = logging.getLogger(__name__)


class Runtime:
    def __init__(self, rules=None):
        self.rules = rules if rules is not None else []
        self.math_interpreter = MathInterpreter()
        self.logic_interpreter = LogicInterpreter(self.rules, self)
        self._operator_evaluators = self._build_evaluator_map()

    def _build_evaluator_map(self):
        """演算子評価関数マップを構築"""
        evaluators = {}

        # 算術演算子
        arithmetic_ops = operator_registry.get_operators_by_type(
            OperatorType.ARITHMETIC
        )
        for op_info in arithmetic_ops:
            if op_info.symbol != "is":
                if op_info.evaluator is None:
                    evaluators[op_info.symbol] = self._create_arithmetic_evaluator(
                        op_info.symbol
                    )
                elif hasattr(op_info.evaluator, "__call__"):  # callable check
                    evaluators[op_info.symbol] = op_info.evaluator

        # 比較演算子
        comparison_ops = operator_registry.get_operators_by_type(
            OperatorType.COMPARISON
        )
        for op_info in comparison_ops:
            if op_info.evaluator is None:
                evaluators[op_info.symbol] = self._create_comparison_evaluator(
                    op_info.symbol
                )
            elif hasattr(op_info.evaluator, "__call__"):
                evaluators[op_info.symbol] = op_info.evaluator

        # 'is' 演算子の評価
        is_op = operator_registry.get_operator("is")
        if is_op:
            evaluators[is_op.symbol] = self._evaluate_is_operator

        # 単一化演算子 '='
        unify_op = operator_registry.get_operator("=")
        if unify_op:
            evaluators[unify_op.symbol] = self._evaluate_unification_operator

        return evaluators

    def _create_arithmetic_evaluator(self, op_symbol):
        """算術演算子の評価関数を生成"""

        def evaluator(left_expr, right_expr, env: BindingEnvironment):
            left_val = self.math_interpreter.evaluate(left_expr, env)
            right_val = self.math_interpreter.evaluate(right_expr, env)
            result = self.math_interpreter.evaluate_binary_op(
                op_symbol, left_val, right_val
            )
            return result

        return evaluator

    def _create_comparison_evaluator(self, op_symbol):
        """比較演算子の評価関数を生成"""

        def evaluator(left_expr, right_expr, env: BindingEnvironment):
            left_val = self.math_interpreter.evaluate(left_expr, env)
            right_val = self.math_interpreter.evaluate(right_expr, env)
            return self.math_interpreter.evaluate_comparison_op(
                op_symbol, left_val, right_val
            )

        return evaluator

    def _evaluate_is_operator(self, result_var, expression, env: BindingEnvironment):
        """'is' 演算子を評価"""
        if not isinstance(result_var, (Variable, Number)):
            raise PrologError(
                f"'is' の左辺は変数または数値でなければなりません: {result_var}"
            )

        value = self.math_interpreter.evaluate(expression, env)

        if not isinstance(value, (int, float)):
            raise PrologError(
                f"'is' の右辺は数値に評価されなければなりません: {expression} -> {value}"
            )

        if isinstance(result_var, Variable):
            unified, temp_env = self.logic_interpreter.unify(
                result_var, Number(value), env
            )
            return unified
        elif isinstance(result_var, Number):
            return result_var.value == value

        return False

    def _evaluate_unification_operator(
        self, left_term, right_term, env: BindingEnvironment
    ):
        """'=' (単一化) 演算子を評価"""
        unified, _ = self.logic_interpreter.unify(left_term, right_term, env)
        return unified

    def _evaluate_operator(
        self,
        term: Term,
        op_info: OperatorInfo,
        evaluator: Callable,
        env: BindingEnvironment,
    ):
        """統一された演算子評価処理"""
        if op_info.arity == 2:
            if len(term.args) != 2:
                raise PrologError(
                    f"演算子 {op_info.symbol} は2つの引数を取りますが、{len(term.args)}個指定されました。"
                )
            arg1, arg2 = term.args[0], term.args[1]
            return evaluator(arg1, arg2, env)
        elif op_info.arity == 1:
            if len(term.args) != 1:
                raise PrologError(
                    f"単項演算子 {op_info.symbol} は1つの引数を取りますが、{len(term.args)}個指定されました。"
                )
            raise NotImplementedError(
                f"単項演算子 {op_info.symbol} の評価は未実装です。"
            )
        elif op_info.arity == 0:
            if term.args:
                raise PrologError(
                    f"演算子 {op_info.symbol} は引数をを取りませんが、指定されました。"
                )
            return evaluator(env)

        raise PrologError(
            f"未対応のアリティを持つ演算子: {op_info.symbol} (アリティ {op_info.arity})"
        )

    def execute_query(self, query_string):
        logger.debug(f"Executing query: {query_string}")
        try:
            tokens = Scanner(query_string).scan_tokens()
            logger.debug(f"Tokens: {tokens}")

            if not query_string.strip().endswith("."):
                query_string_with_dot = query_string + "."
            else:
                query_string_with_dot = query_string

            tokens_for_query = Scanner(query_string_with_dot).scan_tokens()
            parsed_query_structures = Parser(tokens_for_query).parse()

            if not parsed_query_structures:
                logger.error("Query parsing failed or produced no structures.")
                return []

            if isinstance(parsed_query_structures[0], Fact):
                query_goal = parsed_query_structures[0].head
            elif isinstance(parsed_query_structures[0], Rule):
                logger.warning("Query parsed as a rule, using its head as the goal.")
                query_goal = parsed_query_structures[0].head
            else:
                logger.error(
                    f"Unexpected parsed query structure: {parsed_query_structures[0]}"
                )
                return []

            logger.debug(f"Parsed query goal: {query_goal}")

            solutions = []
            initial_env = BindingEnvironment()

            for env in self.execute(query_goal, initial_env):
                result = {}
                query_vars = self._get_vars_from_term(query_goal)

                for var_name in query_vars:
                    value = env.get_value(var_name)
                    if value is not None:
                        result[var_name] = self.logic_interpreter.dereference(
                            value, env
                        )

                if result:
                    solutions.append(result)
                elif not query_vars:
                    solutions.append({})

            logger.debug(f"Solutions: {solutions}")
            return solutions

        except PrologError as e:
            logger.error(f"Prolog execution error: {e}")
            return []
        except Exception as e:
            logger.error(f"Unexpected error during query execution: {e}", exc_info=True)
            return []

    def _get_vars_from_term(self, term):
        """項から変数のリストを再帰的に取得"""
        vars_found = set()

        def collect_vars(current_term):
            if isinstance(current_term, Variable):
                vars_found.add(current_term.name)
            elif isinstance(current_term, Term):
                for arg in current_term.args:
                    collect_vars(arg)

        collect_vars(term)
        return list(vars_found)

    def consult(self, filename):
        logger.info(f"Consulting file: {filename}")
        try:
            with open(filename, "r") as f:
                source = f.read()

            tokens = Scanner(source).scan_tokens()
            new_rules = Parser(tokens).parse()
            self.rules.extend(new_rules)
            self.logic_interpreter.rules = self.rules
            logger.info(f"Consulted {len(new_rules)} rules from {filename}.")
            return True
        except FileNotFoundError:
            logger.error(f"File not found: {filename}")
            return False
        except Exception as e:
            logger.error(f"Error consulting file {filename}: {e}", exc_info=True)
            return False

    def execute(self, goal, env: BindingEnvironment):
        """指定されたゴールを現在の環境で評価し、成功した環境のジェネレータを返す"""
        logger.debug(f"Executing goal: {goal} with env: {env}")

        if isinstance(goal, Term):
            op_info = operator_registry.get_operator(str(goal.functor))
            if op_info and op_info.symbol in self._operator_evaluators:
                evaluator = self._operator_evaluators[op_info.symbol]
                try:
                    success = self._evaluate_operator(goal, op_info, evaluator, env)

                    if success:
                        logger.debug(
                            f"Operator goal {goal} succeeded. Yielding env: {env}"
                        )
                        yield env
                    else:
                        logger.debug(f"Operator goal {goal} failed.")
                    return
                except PrologError as e:
                    logger.debug(f"Error evaluating operator goal {goal}: {e}")
                    return
                except NotImplementedError as e:
                    logger.warning(
                        f"Operator {op_info.symbol} evaluation not fully implemented: {e}"
                    )
                    return

        yield from self.logic_interpreter.solve_goal(goal, env)

    def add_rule(self, rule_string):
        """単一のルール文字列を解析して追加"""
        logger.debug(f"Adding rule: {rule_string}")
        try:
            if not rule_string.strip().endswith("."):
                rule_string_with_dot = rule_string + "."
            else:
                rule_string_with_dot = rule_string

            tokens = Scanner(rule_string_with_dot).scan_tokens()
            parsed_rules = Parser(tokens).parse()
            if parsed_rules:
                for rule in parsed_rules:
                    self.rules.append(rule)
                self.logic_interpreter.rules = self.rules
                logger.info(f"Added {len(parsed_rules)} rule(s): {rule_string}")
                return True
            else:
                logger.error(f"Failed to parse rule string: {rule_string}")
                return False
        except Exception as e:
            logger.error(f"Error adding rule '{rule_string}': {e}", exc_info=True)
            return False
