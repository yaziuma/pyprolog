# prolog/runtime/interpreter.py
from prolog.core.types import Term, Variable, Number, Rule, Fact, Atom 
from prolog.core.binding_environment import BindingEnvironment
from prolog.parser.scanner import Scanner
from prolog.parser.parser import Parser
from prolog.runtime.math_interpreter import MathInterpreter
from prolog.runtime.logic_interpreter import LogicInterpreter
from prolog.core.operators import operator_registry, OperatorType, OperatorInfo
from prolog.core.errors import PrologError
# Import new predicate classes
from prolog.runtime.builtins import (
    VarPredicate, AtomPredicate, NumberPredicate,
    FunctorPredicate, ArgPredicate, UnivPredicate # Added term manipulation predicates
)
from typing import List, Iterator, Dict, Any, Union, Optional, Callable
import logging

logger = logging.getLogger(__name__)


class Runtime:
    """演算子統合設計を活用した統合実行エンジン"""

    def __init__(self, rules: Optional[List[Union[Rule, Fact]]] = None):
        self.rules: List[Union[Rule, Fact]] = rules if rules is not None else []
        self.math_interpreter = MathInterpreter()
        self.logic_interpreter = LogicInterpreter(self.rules, self)

        # 統合設計：演算子評価システムの構築
        self._operator_evaluators = self._build_unified_evaluator_system()

        logger.info(
            f"Runtime initialized with {len(self.rules)} rules and {len(self._operator_evaluators)} operator evaluators"
        )

    def _build_unified_evaluator_system(self) -> Dict[str, Callable]:
        """統合設計：演算子評価システムの構築"""
        evaluators: Dict[str, Callable] = {}

        # 算術演算子の統合
        arithmetic_ops = operator_registry.get_operators_by_type(
            OperatorType.ARITHMETIC
        )
        for op_info in arithmetic_ops:
            if op_info.symbol == "is":
                evaluators[op_info.symbol] = self._create_is_evaluator()
            else:
                evaluators[op_info.symbol] = self._create_arithmetic_evaluator(op_info)

        # 比較演算子の統合
        comparison_ops = operator_registry.get_operators_by_type(
            OperatorType.COMPARISON
        )
        for op_info in comparison_ops:
            evaluators[op_info.symbol] = self._create_comparison_evaluator(op_info)

        # 論理演算子の統合
        logical_ops = operator_registry.get_operators_by_type(OperatorType.LOGICAL)
        for op_info in logical_ops:
            if op_info.symbol == "=":
                evaluators[op_info.symbol] = self._create_unification_evaluator()
            else:
                evaluators[op_info.symbol] = self._create_logical_evaluator(op_info)

        # 制御演算子の統合
        control_ops = operator_registry.get_operators_by_type(OperatorType.CONTROL)
        for op_info in control_ops:
            evaluators[op_info.symbol] = self._create_control_evaluator(op_info)

        # IO演算子の統合
        io_ops = operator_registry.get_operators_by_type(OperatorType.IO)
        for op_info in io_ops:
            evaluators[op_info.symbol] = self._create_io_evaluator(op_info)

        logger.debug(f"Built {len(evaluators)} unified operator evaluators")
        return evaluators

    def _create_arithmetic_evaluator(self, op_info: OperatorInfo):
        """算術演算子評価器の生成"""

        def evaluator(args: List, env: BindingEnvironment) -> bool:
            if len(args) != op_info.arity:
                raise PrologError(
                    f"Operator {op_info.symbol} expects {op_info.arity} arguments, got {len(args)}"
                )

            if op_info.arity == 2:
                left_val = self.math_interpreter.evaluate(args[0], env)
                right_val = self.math_interpreter.evaluate(args[1], env)
                result = self.math_interpreter.evaluate_binary_op(
                    op_info.symbol, left_val, right_val
                )
                return True  # 算術演算は常に成功（エラーでない限り）

            raise NotImplementedError(
                f"Unary arithmetic operator {op_info.symbol} not implemented"
            )

        return evaluator

    def _create_comparison_evaluator(self, op_info: OperatorInfo):
        """比較演算子評価器の生成"""

        def evaluator(args: List, env: BindingEnvironment) -> bool:
            if len(args) != 2:
                raise PrologError(
                    f"Comparison operator {op_info.symbol} requires 2 arguments"
                )

            left_val = self.math_interpreter.evaluate(args[0], env)
            right_val = self.math_interpreter.evaluate(args[1], env)
            return self.math_interpreter.evaluate_comparison_op(
                op_info.symbol, left_val, right_val
            )

        return evaluator

    def _create_is_evaluator(self):
        """'is' 演算子専用評価器"""

        def evaluator(
            args: List, env: BindingEnvironment
        ) -> Iterator[BindingEnvironment]:
            if len(args) != 2:
                raise PrologError("'is' operator requires exactly 2 arguments")

            result_term, expression = args[0], args[1]

            try:
                value = self.math_interpreter.evaluate(expression, env)
                result_number = Number(value)

                # 単一化を試行
                unified, new_env = self.logic_interpreter.unify(
                    result_term, result_number, env
                )
                if unified:
                    yield new_env

            except Exception as e:
                logger.debug(f"'is' evaluation failed: {e}")
                # 失敗時は何も yield しない

        return evaluator

    def _create_unification_evaluator(self):
        """単一化演算子評価器"""

        def evaluator(
            args: List, env: BindingEnvironment
        ) -> Iterator[BindingEnvironment]:
            if len(args) != 2:
                raise PrologError("Unification operator requires exactly 2 arguments")

            unified, new_env = self.logic_interpreter.unify(args[0], args[1], env)
            if unified:
                yield new_env

        return evaluator

    def _create_logical_evaluator(self, op_info: OperatorInfo):
        """論理演算子評価器の生成"""

        def evaluator(
            args: List, env: BindingEnvironment
        ) -> Iterator[BindingEnvironment]:
            if op_info.symbol == ",":
                # コンジャンクション（AND）: 両方のゴールが成功する必要
                if len(args) != 2:
                    raise PrologError("Conjunction requires exactly 2 arguments")

                left_goal, right_goal = args[0], args[1]

                # 左のゴールを実行
                for left_env in self.execute(left_goal, env):
                    # 左が成功した各環境で右のゴールを実行
                    yield from self.execute(right_goal, left_env)

            elif op_info.symbol == ";":
                # ディスジャンクション（OR）: どちらかのゴールが成功すればよい
                if len(args) != 2:
                    raise PrologError("Disjunction requires exactly 2 arguments")

                left_goal, right_goal = args[0], args[1]

                # 左のゴールを試行
                success_found = False
                for left_env in self.execute(left_goal, env):
                    success_found = True
                    yield left_env

                # 左が失敗した場合、右のゴールを試行
                if not success_found:
                    yield from self.execute(right_goal, env)

            elif op_info.symbol == "\\+":
                # 否定（NOT）: ゴールが失敗すれば成功
                if len(args) != 1:
                    raise PrologError("Negation requires exactly 1 argument")

                goal_to_negate = args[0] 

                # ゴールを試行
                success_found = False
                for _ in self.execute(goal_to_negate, env): 
                    success_found = True
                    break

                # 失敗した場合のみ成功
                if not success_found:
                    yield env

            elif op_info.symbol == "==":
                # 厳密同一性チェック
                if len(args) != 2:
                    raise PrologError("Identity operator requires exactly 2 arguments")

                left_deref = self.logic_interpreter.dereference(args[0], env)
                right_deref = self.logic_interpreter.dereference(args[1], env)
                if left_deref == right_deref:
                    yield env

            elif op_info.symbol == "\\==":
                # 厳密非同一性チェック
                if len(args) != 2:
                    raise PrologError(
                        "Non-identity operator requires exactly 2 arguments"
                    )

                left_deref = self.logic_interpreter.dereference(args[0], env)
                right_deref = self.logic_interpreter.dereference(args[1], env)
                if left_deref != right_deref:
                    yield env

            else:
                raise NotImplementedError(
                    f"Logical operator {op_info.symbol} not implemented"
                )

        return evaluator

    def _create_control_evaluator(self, op_info: OperatorInfo):
        """制御演算子評価器の生成"""

        def evaluator(
            args: List, env: BindingEnvironment
        ) -> Iterator[BindingEnvironment]:
            if op_info.symbol == "!":
                # カット：現在の環境で成功し、バックトラックを防ぐ
                yield env
                # カット信号をどう処理するかは実装依存
                # ここでは単純に成功として扱う
            elif op_info.symbol == "->":
                # IF-THEN: 条件が成功すれば結果を実行
                if len(args) != 2:
                    raise PrologError("If-then requires exactly 2 arguments")

                condition, then_part = args[0], args[1]

                # 条件を試行
                for cond_env in self.execute(condition, env):
                    yield from self.execute(then_part, cond_env)
                    break  # 最初の成功のみ
            else:
                raise NotImplementedError(
                    f"Control operator {op_info.symbol} not implemented"
                )

        return evaluator

    def _create_io_evaluator(self, op_info: OperatorInfo):
        """IO演算子評価器の生成"""

        def evaluator(
            args: List, env: BindingEnvironment
        ) -> Iterator[BindingEnvironment]:
            if op_info.symbol == "write":
                if len(args) != 1:
                    raise PrologError("write/1 requires exactly 1 argument")

                # 引数を文字列として出力
                arg_deref = self.logic_interpreter.dereference(args[0], env)
                print(str(arg_deref), end="")
                yield env

            elif op_info.symbol == "nl":
                if len(args) != 0:
                    raise PrologError("nl/0 requires no arguments")
                print()
                yield env

            elif op_info.symbol == "tab":
                if len(args) > 1: 
                    raise PrologError("tab requires 0 or 1 arguments")

                if len(args) == 1:
                    count_term = self.logic_interpreter.dereference(args[0], env)
                    if isinstance(count_term, Number):
                        print(" " * int(count_term.value), end="")
                    else:
                        print("\t", end="") 
                else: 
                    print("\t", end="")
                yield env
            else:
                raise NotImplementedError(
                    f"IO operator {op_info.symbol} not implemented"
                )

        return evaluator

    def execute(
        self, goal: Term, env: BindingEnvironment
    ) -> Iterator[BindingEnvironment]:
        """統合設計：統一されたゴール実行"""
        logger.debug(f"Executing goal: {goal}")

        if isinstance(goal, Term):
            functor_name = (
                goal.functor.name
                if hasattr(goal.functor, "name")
                else str(goal.functor)
            )

            op_info = operator_registry.get_operator(functor_name)

            if op_info and functor_name in self._operator_evaluators:
                evaluator = self._operator_evaluators[functor_name]
                try:
                    if op_info.operator_type == OperatorType.ARITHMETIC:
                        if functor_name == "is":
                            yield from evaluator(goal.args, env)
                        else:
                            success = evaluator(goal.args, env)
                            if success:
                                yield env
                    elif op_info.operator_type == OperatorType.COMPARISON:
                        success = evaluator(goal.args, env)
                        if success:
                            yield env
                    elif op_info.operator_type == OperatorType.LOGICAL:
                        yield from evaluator(goal.args, env)
                    else:
                        yield from evaluator(goal.args, env)
                except Exception as e:
                    logger.debug(f"Operator evaluation failed: {e}")
                    yield from self.logic_interpreter.solve_goal(goal, env)
            
            # Type-checking built-ins
            elif functor_name == "var" and len(goal.args) == 1:
                dereferenced_arg = self.logic_interpreter.dereference(goal.args[0], env)
                var_pred = VarPredicate(dereferenced_arg)
                yield from var_pred.execute(self, env)
            elif functor_name == "atom" and len(goal.args) == 1:
                dereferenced_arg = self.logic_interpreter.dereference(goal.args[0], env)
                atom_pred = AtomPredicate(dereferenced_arg)
                yield from atom_pred.execute(self, env)
            elif functor_name == "number" and len(goal.args) == 1:
                dereferenced_arg = self.logic_interpreter.dereference(goal.args[0], env)
                num_pred = NumberPredicate(dereferenced_arg)
                yield from num_pred.execute(self, env)
            
            # Term manipulation built-ins
            elif functor_name == "functor" and len(goal.args) == 3:
                functor_pred = FunctorPredicate(goal.args[0], goal.args[1], goal.args[2])
                yield from functor_pred.execute(self, env)
            elif functor_name == "arg" and len(goal.args) == 3:
                arg_pred = ArgPredicate(goal.args[0], goal.args[1], goal.args[2])
                yield from arg_pred.execute(self, env)
            elif functor_name == "=.." and len(goal.args) == 2:
                univ_pred = UnivPredicate(goal.args[0], goal.args[1])
                yield from univ_pred.execute(self, env)
            
            else:
                # Normal predicate
                yield from self.logic_interpreter.solve_goal(goal, env)
        else:
            yield from self.logic_interpreter.solve_goal(goal, env)


    def query(self, query_string: str) -> List[Dict[Variable, Any]]:
        logger.debug(f"Executing query: {query_string}")
        try:
            tokens = Scanner(query_string).scan_tokens()
            if not query_string.strip().endswith("."):
                query_string += "."
                tokens = Scanner(query_string).scan_tokens()

            parsed_structures = Parser(tokens).parse()
            if not parsed_structures:
                logger.warning("Query parsing failed")
                return []

            query_goal: Optional[Term] = None
            if isinstance(parsed_structures[0], Fact):
                query_goal = parsed_structures[0].head
            elif isinstance(parsed_structures[0], Rule): # Should not happen for a query
                query_goal = parsed_structures[0].head 
            elif isinstance(parsed_structures[0], Term):
                 query_goal = parsed_structures[0]
            
            if query_goal is None:
                logger.error(f"Could not extract a valid goal from parsed: {parsed_structures[0]}")
                return []
            
            solutions = []
            initial_env = BindingEnvironment()
            query_vars_names = self._extract_variables_names(query_goal)


            for env_solution in self.execute(query_goal, initial_env):
                result = {}
                for var_name_str in query_vars_names:
                    var_obj = Variable(var_name_str)
                    value_dereferenced = self.logic_interpreter.dereference(var_obj, env_solution)
                    result[var_obj] = value_dereferenced
                solutions.append(result)
            
            logger.debug(f"Query completed with {len(solutions)} solutions")
            return solutions

        except Exception as e:
            logger.error(f"Query execution error: {e}", exc_info=True)
            return []

    def _extract_variables_names(self, term) -> List[str]: # Changed name for clarity
        variables = set()
        queue = [term]
        while queue:
            current = queue.pop(0)
            if isinstance(current, Variable):
                variables.add(current.name)
            elif isinstance(current, Term):
                if isinstance(current.functor, Variable): # Functor can be variable in some contexts
                    variables.add(current.functor.name)
                queue.extend(current.args)
        return list(variables)

    def add_rule(self, rule_string: str) -> bool:
        try:
            if not rule_string.strip().endswith("."):
                rule_string += "."
            tokens = Scanner(rule_string).scan_tokens()
            parsed_items = Parser(tokens).parse()
            added_count = 0
            if parsed_items:
                for item in parsed_items:
                    if isinstance(item, (Rule, Fact)):
                        self.rules.append(item)
                        added_count +=1
                    else:
                        logger.warning(f"Skipping non-rule/fact from add_rule: {item}")
                if added_count > 0:
                    self.logic_interpreter.rules = self.rules
                    logger.info(f"Added {added_count} rule(s)/fact(s) from string.")
                else:
                    logger.warning("No rules/facts parsed from add_rule string.")
                return added_count > 0
            logger.warning("No rules/facts parsed from add_rule string.")
            return False
        except Exception as e:
            logger.error(f"Failed to add rule: {e}", exc_info=True)
            return False

    def consult(self, filename: str) -> bool:
        try:
            with open(filename, "r", encoding="utf-8") as f:
                source = f.read()

            tokens = Scanner(source).scan_tokens()
            new_rules_or_terms = Parser(tokens).parse()
            added_count = 0
            for item in new_rules_or_terms:
                if isinstance(item, (Rule, Fact)):
                    self.rules.append(item)
                    added_count +=1
                else:
                    logger.warning(f"Skipping non-rule/fact during consult: {item}")
            
            if added_count > 0:
                self.logic_interpreter.rules = self.rules
                logger.info(f"Consulted {added_count} rules/facts from {filename}")
            else:
                logger.info(f"No rules or facts consulted from {filename}")
            return True
        except Exception as e:
            logger.error(f"Failed to consult {filename}: {e}", exc_info=True)
            return False
