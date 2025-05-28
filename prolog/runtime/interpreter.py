# prolog/runtime/interpreter.py
from prolog.core.types import Term, Variable, Number, Rule, Fact, Atom, String
from prolog.core.binding_environment import BindingEnvironment
from prolog.parser.scanner import Scanner
from prolog.parser.parser import Parser
from prolog.runtime.math_interpreter import MathInterpreter
from prolog.runtime.logic_interpreter import LogicInterpreter
from prolog.core.operators import operator_registry, OperatorType, OperatorInfo
from prolog.core.errors import PrologError
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
        
        logger.info(f"Runtime initialized with {len(self.rules)} rules and {len(self._operator_evaluators)} operator evaluators")

    def _build_unified_evaluator_system(self) -> Dict[str, Callable]:
        """統合設計：演算子評価システムの構築"""
        evaluators: Dict[str, Callable] = {}
        
        # 算術演算子の統合
        arithmetic_ops = operator_registry.get_operators_by_type(OperatorType.ARITHMETIC)
        for op_info in arithmetic_ops:
            if op_info.symbol == "is":
                evaluators[op_info.symbol] = self._create_is_evaluator()
            else:
                evaluators[op_info.symbol] = self._create_arithmetic_evaluator(op_info)
        
        # 比較演算子の統合
        comparison_ops = operator_registry.get_operators_by_type(OperatorType.COMPARISON)
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
                raise PrologError(f"Operator {op_info.symbol} expects {op_info.arity} arguments, got {len(args)}")
            
            if op_info.arity == 2:
                left_val = self.math_interpreter.evaluate(args[0], env)
                right_val = self.math_interpreter.evaluate(args[1], env)
                result = self.math_interpreter.evaluate_binary_op(op_info.symbol, left_val, right_val)
                return True  # 算術演算は常に成功（エラーでない限り）
            
            raise NotImplementedError(f"Unary arithmetic operator {op_info.symbol} not implemented")
        
        return evaluator

    def _create_comparison_evaluator(self, op_info: OperatorInfo):
        """比較演算子評価器の生成"""
        def evaluator(args: List, env: BindingEnvironment) -> bool:
            if len(args) != 2:
                raise PrologError(f"Comparison operator {op_info.symbol} requires 2 arguments")
            
            left_val = self.math_interpreter.evaluate(args[0], env)
            right_val = self.math_interpreter.evaluate(args[1], env)
            return self.math_interpreter.evaluate_comparison_op(op_info.symbol, left_val, right_val)
        
        return evaluator

    def _create_is_evaluator(self):
        """'is' 演算子専用評価器"""
        def evaluator(args: List, env: BindingEnvironment) -> Iterator[BindingEnvironment]:
            if len(args) != 2:
                raise PrologError("'is' operator requires exactly 2 arguments")
            
            result_term, expression = args[0], args[1]
            
            try:
                value = self.math_interpreter.evaluate(expression, env)
                result_number = Number(value)
                
                # 単一化を試行
                unified, new_env = self.logic_interpreter.unify(result_term, result_number, env)
                if unified:
                    yield new_env
                    
            except Exception as e:
                logger.debug(f"'is' evaluation failed: {e}")
                # 失敗時は何も yield しない
        
        return evaluator

    def _create_unification_evaluator(self):
        """単一化演算子評価器"""
        def evaluator(args: List, env: BindingEnvironment) -> Iterator[BindingEnvironment]:
            if len(args) != 2:
                raise PrologError("Unification operator requires exactly 2 arguments")
            
            unified, new_env = self.logic_interpreter.unify(args[0], args[1], env)
            if unified:
                yield new_env
        
        return evaluator

    def _create_logical_evaluator(self, op_info: OperatorInfo):
        """論理演算子評価器の生成"""
        def evaluator(args: List, env: BindingEnvironment) -> bool:
            if len(args) != 2:
                raise PrologError(f"Logical operator {op_info.symbol} requires 2 arguments")
            
            # 論理演算子の実装（例：==, \==）
            if op_info.symbol == "==":
                # 厳密同一性チェック
                left_deref = self.logic_interpreter.dereference(args[0], env)
                right_deref = self.logic_interpreter.dereference(args[1], env)
                return left_deref == right_deref
            elif op_info.symbol == "\\==":
                # 厳密非同一性チェック
                left_deref = self.logic_interpreter.dereference(args[0], env)
                right_deref = self.logic_interpreter.dereference(args[1], env)
                return left_deref != right_deref
            
            raise NotImplementedError(f"Logical operator {op_info.symbol} not implemented")
        
        return evaluator

    def _create_control_evaluator(self, op_info: OperatorInfo):
        """制御演算子評価器の生成"""
        def evaluator(args: List, env: BindingEnvironment) -> Iterator[BindingEnvironment]:
            if op_info.symbol == "!":
                # カット：現在の環境で成功し、バックトラックを防ぐ
                yield env
                # カット信号をどう処理するかは実装依存
                # ここでは単純に成功として扱う
            else:
                raise NotImplementedError(f"Control operator {op_info.symbol} not implemented")
        
        return evaluator

    def _create_io_evaluator(self, op_info: OperatorInfo):
        """IO演算子評価器の生成"""
        def evaluator(args: List, env: BindingEnvironment) -> Iterator[BindingEnvironment]:
            if op_info.symbol == "write":
                if len(args) != 1:
                    raise PrologError("write/1 requires exactly 1 argument")
                
                # 引数を文字列として出力
                arg_deref = self.logic_interpreter.dereference(args[0], env)
                print(str(arg_deref), end='')
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
                    # 引数指定の場合
                    count_term = self.logic_interpreter.dereference(args[0], env)
                    if isinstance(count_term, Number):
                        print(' ' * int(count_term.value), end='')
                    else:
                        print('\t', end='')
                else:
                    print('\t', end='')
                yield env
            else:
                raise NotImplementedError(f"IO operator {op_info.symbol} not implemented")
        
        return evaluator

    def execute(self, goal: Term, env: BindingEnvironment) -> Iterator[BindingEnvironment]:
        """統合設計：統一されたゴール実行"""
        logger.debug(f"Executing goal: {goal}")
        
        if isinstance(goal, Term):
            functor_name = goal.functor.name if hasattr(goal.functor, 'name') else str(goal.functor)
            
            # 統合設計：operator_registry で演算子判定
            op_info = operator_registry.get_operator(functor_name)
            
            if op_info and functor_name in self._operator_evaluators:
                # 演算子として評価
                evaluator = self._operator_evaluators[functor_name]
                
                try:
                    # 演算子タイプに応じた評価
                    if op_info.operator_type in [OperatorType.ARITHMETIC, OperatorType.COMPARISON, OperatorType.LOGICAL]:
                        if functor_name in ["=", "is"]:
                            # ジェネレータ型評価器
                            yield from evaluator(goal.args, env)
                        else:
                            # ブール型評価器
                            success = evaluator(goal.args, env)
                            if success:
                                yield env
                    else:
                        # 制御・IO演算子（ジェネレータ型）
                        yield from evaluator(goal.args, env)
                        
                except Exception as e:
                    logger.debug(f"Operator evaluation failed: {e}")
                    # 演算子評価失敗時は通常の述語として処理を続行
                    yield from self.logic_interpreter.solve_goal(goal, env)
            else:
                # 通常の述語として処理
                yield from self.logic_interpreter.solve_goal(goal, env)
        else:
            # Termでない場合（通常はありえない）
            yield from self.logic_interpreter.solve_goal(goal, env)

    def query(self, query_string: str) -> List[Dict[Variable, Any]]:
        """クエリ実行（既存API互換性維持）"""
        logger.debug(f"Executing query: {query_string}")
        
        try:
            # 統合設計：Scanner と Parser を使用
            tokens = Scanner(query_string).scan_tokens()
            
            if not query_string.strip().endswith("."):
                query_string += "."
                tokens = Scanner(query_string).scan_tokens()
            
            parsed_structures = Parser(tokens).parse()
            
            if not parsed_structures:
                logger.warning("Query parsing failed")
                return []

            # ゴール抽出
            if isinstance(parsed_structures[0], Fact):
                query_goal = parsed_structures[0].head
            elif isinstance(parsed_structures[0], Rule):
                query_goal = parsed_structures[0].head
            else:
                logger.error(f"Unexpected parsed structure: {type(parsed_structures[0])}")
                return []

            # 統合実行エンジンで実行
            solutions = []
            initial_env = BindingEnvironment()

            for env in self.execute(query_goal, initial_env):
                result = {}
                query_vars = self._extract_variables(query_goal)

                for var_name in query_vars:
                    var_obj = Variable(var_name)
                    value = env.get_value(var_name)
                    if value is not None:
                        result[var_obj] = self.logic_interpreter.dereference(value, env)

                if result or not query_vars:
                    solutions.append(result)

            logger.debug(f"Query completed with {len(solutions)} solutions")
            return solutions

        except Exception as e:
            logger.error(f"Query execution error: {e}", exc_info=True)
            return []

    def _extract_variables(self, term) -> List[str]:
        """項から変数名を抽出"""
        variables = set()
        
        def extract_recursive(current_term):
            if isinstance(current_term, Variable):
                variables.add(current_term.name)
            elif isinstance(current_term, Term):
                for arg in current_term.args:
                    extract_recursive(arg)
        
        extract_recursive(term)
        return list(variables)

    def add_rule(self, rule_string: str) -> bool:
        """動的ルール追加"""
        try:
            if not rule_string.strip().endswith("."):
                rule_string += "."
            
            tokens = Scanner(rule_string).scan_tokens()
            parsed_rules = Parser(tokens).parse()
            
            if parsed_rules:
                self.rules.extend(parsed_rules)
                self.logic_interpreter.rules = self.rules
                logger.info(f"Added {len(parsed_rules)} rule(s)")
                return True
            return False
            
        except Exception as e:
            logger.error(f"Failed to add rule: {e}")
            return False

    def consult(self, filename: str) -> bool:
        """ファイルからルールを読み込み"""
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                source = f.read()
            
            tokens = Scanner(source).scan_tokens()
            new_rules = Parser(tokens).parse()
            
            self.rules.extend(new_rules)
            self.logic_interpreter.rules = self.rules
            
            logger.info(f"Consulted {len(new_rules)} rules from {filename}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to consult {filename}: {e}")
            return False
