# pyprolog/runtime/interpreter.py
import logging
from collections.abc import Callable, Iterator  # Optional was already here
from typing import (
    Any,
)

from pyprolog.core.binding_environment import BindingEnvironment
from pyprolog.core.errors import CutException, PrologError
from pyprolog.core.operators import OperatorInfo, OperatorType, operator_registry
from pyprolog.core.types import Atom, Fact, Number, PrologType, Rule, Term, Variable
from pyprolog.parser.parser import Parser
from pyprolog.parser.scanner import Scanner
from pyprolog.runtime.builtins import (
    AppendPredicate,
    ArgPredicate,
    AtEndOfStreamPredicate,
    AtomNumberPredicate,
    AtomPredicate,
    DynamicAssertAPredicate,
    DynamicAssertZPredicate,
    DynamicRetractPredicate,
    ExportFactsPredicate,
    FindallPredicate,
    FunctorPredicate,
    ListingPredicate,
    ListingWithPredicatePredicate,
    MemberPredicate,
    NumberPredicate,
    UnivPredicate,
    VarPredicate,
    # 統一入力システム対応版ファクトリ関数
    create_get_char_predicate,
    create_peek_char_predicate,
    create_read_line_predicate,
)
from pyprolog.runtime.execution_frames import (
    ExecutionState,
    GoalFrame,
    GoalSeqFrame,
)
from pyprolog.runtime.logic_interpreter import LogicInterpreter
from pyprolog.runtime.math_interpreter import MathInterpreter
from pyprolog.util.functor_mapper import FunctorMapper  # Added FunctorMapper
from pyprolog.util.variable_mapper import VariableMapper  # Added

from .io_manager import IOManager
from .tracer import Tracer

logger = logging.getLogger(__name__)


class Runtime:
    def __init__(
        self,
        rules: list[Rule | Fact] | None = None,
        variable_mapper: VariableMapper | None = None,
        functor_mapper: FunctorMapper | None = None,
        occurs_check_enabled: bool = True,
    ):
        self.rules: list[Rule | Fact] = rules if rules is not None else []
        self.variable_mapper = (
            variable_mapper if variable_mapper is not None else VariableMapper()
        )

        # 既存ルールからファンクター名を抽出して衝突回避
        existing_functors = self._extract_existing_functors()
        self.functor_mapper = (
            functor_mapper
            if functor_mapper is not None
            else FunctorMapper(existing_functors)
        )

        # 既にマッパーが提供されている場合は、既存ファンクターを登録
        if functor_mapper is not None:
            self.functor_mapper.register_existing_functors(existing_functors)

        self.math_interpreter = MathInterpreter()
        self.io_manager = IOManager()  # Initialize IOManager
        self.tracer = Tracer()  # Initialize Tracer
        self.occurs_check_enabled = occurs_check_enabled
        self.use_iterative_execution = False  # Feature flag for iterative execution
        self.logic_interpreter = LogicInterpreter(
            self.rules, self
        )  # Pass self (Runtime) to LogicInterpreter
        self._operator_evaluators = self._build_unified_evaluator_system()
        logger.info(
            "Runtime initialized with %d rules, IOManager, VariableMapper, FunctorMapper, Tracer, and %d operator evaluators",
            len(self.rules),
            len(self._operator_evaluators),
        )

    def _extract_existing_functors(self) -> set:
        """既存ルールからファンクター名を抽出"""
        functors = set()

        for rule in self.rules:
            if isinstance(rule, Fact):
                functors.update(self._extract_functors_from_term(rule.head))
            elif isinstance(rule, Rule):
                functors.update(self._extract_functors_from_term(rule.head))
                functors.update(self._extract_functors_from_term(rule.body))

        return functors

    def _extract_functors_from_term(self, term: Term | Variable) -> set:
        """項から再帰的にファンクター名を抽出"""
        functors = set()

        if isinstance(term, Term):
            if isinstance(term.functor, Atom):
                functors.add(term.functor.name)

            # 引数も再帰的にチェック
            for arg in term.args:
                functors.update(self._extract_functors_from_term(arg))

        elif isinstance(term, Atom):
            functors.add(term.name)

        elif isinstance(term, list):
            for item in term:
                functors.update(self._extract_functors_from_term(item))

        return functors

    def _build_unified_evaluator_system(self) -> dict[str, Callable]:
        evaluators: dict[str, Callable] = {}
        arithmetic_ops = operator_registry.get_operators_by_type(
            OperatorType.ARITHMETIC
        )
        for op_info in arithmetic_ops:
            if op_info.symbol == "is":
                evaluators[op_info.symbol] = self._create_is_evaluator()
            else:
                evaluators[op_info.symbol] = self._create_arithmetic_evaluator(op_info)
        comparison_ops = operator_registry.get_operators_by_type(
            OperatorType.COMPARISON
        )
        for op_info in comparison_ops:
            evaluators[op_info.symbol] = self._create_comparison_evaluator(op_info)
        logical_ops = operator_registry.get_operators_by_type(OperatorType.LOGICAL)
        for op_info in logical_ops:
            if op_info.symbol == "=":
                evaluators[op_info.symbol] = self._create_unification_evaluator()
            else:
                evaluators[op_info.symbol] = self._create_logical_evaluator(op_info)
        control_ops = operator_registry.get_operators_by_type(OperatorType.CONTROL)
        for op_info in control_ops:
            evaluators[op_info.symbol] = self._create_control_evaluator(op_info)
        io_ops = operator_registry.get_operators_by_type(OperatorType.IO)
        for op_info in io_ops:
            evaluators[op_info.symbol] = self._create_io_evaluator(op_info)
        logger.debug("Built %d unified operator evaluators", len(evaluators))
        return evaluators

    def _create_arithmetic_evaluator(self, op_info: OperatorInfo) -> Callable:
        def evaluator(args: list, env: BindingEnvironment) -> bool:
            if len(args) != op_info.arity:
                raise PrologError(
                    f"Operator {op_info.symbol} expects {op_info.arity} arguments, got {len(args)}"
                )
            if op_info.arity == 2:
                left_val = self.math_interpreter.evaluate(args[0], env)
                right_val = self.math_interpreter.evaluate(args[1], env)
                self.math_interpreter.evaluate_binary_op(
                    op_info.symbol, left_val, right_val
                )
                return True
            raise NotImplementedError(
                f"Unary arithmetic operator {op_info.symbol} not implemented"
            )

        return evaluator

    def _create_comparison_evaluator(self, op_info: OperatorInfo) -> Callable:
        def evaluator(args: list, env: BindingEnvironment) -> bool:
            if len(args) != 2:
                raise PrologError(
                    f"Comparison operator {op_info.symbol} requires 2 arguments"
                )
            try:
                left_val = self.math_interpreter.evaluate(args[0], env)
                right_val = self.math_interpreter.evaluate(args[1], env)
                return self.math_interpreter.evaluate_comparison_op(
                    op_info.symbol, left_val, right_val
                )
            except PrologError:
                return False

        return evaluator

    def _create_is_evaluator(self) -> Callable:
        def evaluator(
            args: list, env: BindingEnvironment
        ) -> Iterator[BindingEnvironment]:
            if len(args) != 2:
                raise PrologError("'is' operator requires exactly 2 arguments")
            result_term, expression = args[0], args[1]
            try:
                value = self.math_interpreter.evaluate(expression, env)
                result_number = Number(value)
                unified, new_env = self.logic_interpreter.unify(
                    result_term, result_number, env
                )
                if unified:
                    yield new_env
            except Exception as e:
                logger.debug("'is' evaluation failed: %s", e)

        return evaluator

    def _create_unification_evaluator(self) -> Callable:
        def evaluator(
            args: list, env: BindingEnvironment
        ) -> Iterator[BindingEnvironment]:
            if len(args) != 2:
                raise PrologError("Unification operator = requires exactly 2 arguments")
            unified, new_env = self.logic_interpreter.unify(args[0], args[1], env)
            if unified:
                yield new_env

        return evaluator

    def _is_conjunction_term(self, goal: PrologType) -> bool:
        return (
            isinstance(goal, Term)
            and isinstance(goal.functor, Atom)
            and goal.functor.name == ","
            and len(goal.args) == 2
        )

    def _flatten_conjunction(self, goal: PrologType) -> list[PrologType]:
        flattened: list[PrologType] = []
        stack: list[PrologType] = [goal]

        while stack:
            current = stack.pop()
            if self._is_conjunction_term(current):
                left_goal, right_goal = current.args
                stack.append(right_goal)
                stack.append(left_goal)
            else:
                flattened.append(current)

        return flattened

    def _execute_goal_sequence(
        self, goals: list[PrologType], env: BindingEnvironment
    ) -> Iterator[BindingEnvironment]:
        if not goals:
            yield env
            return

        stack: list[tuple[int, Iterator[BindingEnvironment]]] = [
            (0, self.execute(goals[0], env))
        ]

        while stack:
            index, iterator = stack[-1]
            try:
                next_env = next(iterator)
            except StopIteration:
                stack.pop()
                continue
            except CutException:
                raise

            if index == len(goals) - 1:
                yield next_env
                continue

            stack.append((index + 1, self.execute(goals[index + 1], next_env)))

    def _create_logical_evaluator(self, op_info: OperatorInfo) -> Callable:
        def evaluator(
            args: list, env: BindingEnvironment
        ) -> Iterator[BindingEnvironment]:
            if op_info.symbol == ",":  # Conjunction
                if len(args) != 2:
                    raise PrologError("Conjunction ,/2 requires exactly 2 arguments")
                left_goal, right_goal = args[0], args[1]
                goals = self._flatten_conjunction(
                    Term(Atom(","), [left_goal, right_goal])
                )
                yield from self._execute_goal_sequence(goals, env)
            elif op_info.symbol == ";":  # Disjunction
                if len(args) != 2:
                    raise PrologError("Disjunction ;/2 requires exactly 2 arguments")
                left_goal, right_goal = args[0], args[1]
                try:
                    for left_env in self.execute(left_goal, env):
                        yield left_env
                except CutException:
                    logger.debug(
                        "CutException from left part of disjunction ';'. Re-raising."
                    )
                    raise
                else:
                    for right_env_solution in self.execute(right_goal, env):
                        yield right_env_solution
            elif op_info.symbol == "\\+":  # Negation as failure
                if len(args) != 1:
                    raise PrologError("Negation \\+/1 requires exactly 1 argument")
                goal_to_negate = args[0]
                success_found = False
                try:
                    for _ in self.execute(goal_to_negate, env):
                        success_found = True
                        break
                except CutException:
                    logger.debug(
                        "CutException inside \\+ for goal %s. Standard \\+ would fail here.",
                        goal_to_negate,
                    )
                    success_found = True
                if not success_found:
                    yield env
            elif op_info.symbol == "==":
                if len(args) != 2:
                    raise PrologError("Identity ==/2 requires exactly 2 arguments")
                left_deref = self.logic_interpreter.dereference(args[0], env)
                right_deref = self.logic_interpreter.dereference(args[1], env)
                if left_deref == right_deref:
                    yield env
            elif op_info.symbol == "\\==":
                if len(args) != 2:
                    raise PrologError(
                        "Non-identity \\==/2 requires exactly 2 arguments"
                    )
                left_deref = self.logic_interpreter.dereference(args[0], env)
                right_deref = self.logic_interpreter.dereference(args[1], env)
                if left_deref != right_deref:
                    yield env
            elif op_info.symbol == "\\=":  # \=/2 Term non-unification
                if len(args) != 2:
                    raise PrologError(
                        "Non-unification operator \\=/2 requires exactly 2 arguments"
                    )
                term1, term2 = args[0], args[1]
                # We need to try unification and succeed if it fails.
                # Crucially, unify creates a *copy* of the environment.
                # So, any bindings made during a successful unify attempt should not persist
                # if we are only checking for unifiability.
                unified, _ = self.logic_interpreter.unify(term1, term2, env)
                if not unified:
                    yield env  # Succeeds if unify returns False
            elif op_info.symbol == "<>":  # NOT_EQUAL - alternative to \=
                if len(args) != 2:
                    raise PrologError(
                        "Not-equal operator <>/2 requires exactly 2 arguments"
                    )
                term1, term2 = args[0], args[1]
                # Same logic as \= - succeed if unification fails
                unified, _ = self.logic_interpreter.unify(term1, term2, env)
                if not unified:
                    yield env
            elif op_info.symbol == "!=":  # NOT_EQUAL_ALT - alternative to \=
                if len(args) != 2:
                    raise PrologError(
                        "Not-equal operator !=/2 requires exactly 2 arguments"
                    )
                term1, term2 = args[0], args[1]
                # Same logic as \= - succeed if unification fails
                unified, _ = self.logic_interpreter.unify(term1, term2, env)
                if not unified:
                    yield env
            else:
                raise NotImplementedError(
                    f"Logical operator {op_info.symbol} not implemented"
                )

        return evaluator

    def _create_control_evaluator(self, op_info: OperatorInfo) -> Callable:
        def evaluator(
            args: list, env: BindingEnvironment
        ) -> Iterator[BindingEnvironment]:
            if op_info.symbol == "!":
                if args:
                    raise PrologError("Cut !/0 takes no arguments")
                logger.debug("CUTTING! Environment: %s", env.bindings)
                yield env
                raise CutException()
            elif op_info.symbol == "->":
                if len(args) != 2:
                    raise PrologError("If-then ->/2 requires exactly 2 arguments")
                condition, then_part = args[0], args[1]
                solution_found_for_condition = False
                try:
                    for cond_env in self.execute(condition, env):
                        solution_found_for_condition = True
                        try:
                            for then_env_solution in self.execute(then_part, cond_env):
                                yield then_env_solution
                        except CutException:
                            logger.debug(
                                "CutException from then_part of '->', re-raising to cut '->' and parent choices."
                            )
                            raise
                        raise CutException()
                except CutException:
                    if solution_found_for_condition:
                        logger.debug(
                            "CutException after processing 'then_part' or from within 'then_part' for '->'. Re-raising."
                        )
                        raise
                    else:
                        logger.debug(
                            "CutException from 'condition' part of '->' before any solution. Re-raising."
                        )
                        raise
            else:
                raise NotImplementedError(
                    f"Control operator {op_info.symbol} not implemented"
                )

        return evaluator

    def _create_io_evaluator(self, op_info: OperatorInfo) -> Callable:
        def evaluator(
            args: list, env: BindingEnvironment
        ) -> Iterator[BindingEnvironment]:
            if op_info.symbol == "write":
                if len(args) != 1:
                    raise PrologError("write/1 requires exactly 1 argument")
                arg_deref = self.logic_interpreter.dereference(args[0], env)
                # Use IOManager's write method instead of print
                text = str(arg_deref)
                for char in text:
                    self.io_manager.write_char_to_current(char)
                yield env
            elif op_info.symbol == "nl":
                if len(args) != 0:
                    raise PrologError("nl/0 requires no arguments")
                # Use IOManager's write method instead of print
                self.io_manager.write_char_to_current("\n")
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
        self, goal: Any, env: BindingEnvironment
    ) -> Iterator[BindingEnvironment]:
        logger.debug(
            "EXECUTE: Called with goal: %s (type: %s) in env: %s",
            goal,
            type(goal),
            env.bindings,
        )

        # Feature flag: Use iterative execution if enabled
        if self.use_iterative_execution:
            yield from self.execute_iterative(goal, env)
            return

        def _record_builtin_call(name: str) -> None:
            if env.stats_enabled:
                env.stats["builtin_calls_by_name"][name] = (
                    env.stats["builtin_calls_by_name"].get(name, 0) + 1
                )

        processed_goal: Term
        if (
            isinstance(goal, Atom)
            and goal.name == "!"
            and "!" in self._operator_evaluators
        ):
            logger.debug("EXECUTE: Atom('!') detected, routing to operator.")
            processed_goal = Term(
                goal, []
            )  # Convert to Term to be handled by operator logic
        elif isinstance(goal, Term):
            processed_goal = goal
        elif isinstance(goal, Atom):
            # IOオペレータの特別処理を追加
            if goal.name in self._operator_evaluators:
                logger.debug("EXECUTE Atom IO Operator: %s", goal.name)
                # AtomをTermに変換してIOオペレータとして処理
                processed_goal = Term(goal, [])
                evaluator = self._operator_evaluators[goal.name]
                _record_builtin_call(goal.name)
                try:
                    for item in evaluator(processed_goal.args, env):
                        logger.debug(
                            "EXECUTE Atom IO op %s: Yielding: %s",
                            goal.name,
                            item.bindings if item else "None",
                        )
                        yield item
                except Exception as e:
                    logger.debug("Exception in Atom IO operator %s: %s", goal.name, e)
                    raise
                return

            # 既存の通常述語処理
            logger.debug(
                "EXECUTE Atom: Attempting Normal Predicate solve_goal for Atom: %s",
                goal,
            )
            try:
                for item in self.logic_interpreter.solve_goal(goal, env):
                    logger.debug(
                        "EXECUTE Atom (solve_goal): Yielding: %s",
                        item.bindings if item else "None",
                    )
                    yield item
            except CutException:
                logger.debug(
                    "CutException propagated from solve_goal for Atom: %s. Re-raising.",
                    goal,
                )
                raise
            return
        else:
            logger.debug(
                "Goal %s (type %s) is not directly executable by Runtime.execute, failing.",
                goal,
                type(goal),
            )
            return

        functor_name = (
            processed_goal.functor.name
            if hasattr(processed_goal.functor, "name")
            else str(processed_goal.functor)
        )
        op_info = operator_registry.get_operator(functor_name)

        if op_info and functor_name in self._operator_evaluators:
            evaluator = self._operator_evaluators[functor_name]
            _record_builtin_call(functor_name)
            try:
                if (
                    op_info.operator_type == OperatorType.ARITHMETIC
                    and functor_name != "is"
                ):
                    if evaluator(processed_goal.args, env):
                        logger.debug(
                            "EXECUTE op %s: Yielding env (bool success): %s",
                            functor_name,
                            env.bindings,
                        )
                        yield env
                elif op_info.operator_type == OperatorType.COMPARISON:
                    if evaluator(processed_goal.args, env):
                        logger.debug(
                            "EXECUTE op %s: Yielding env (bool success): %s",
                            functor_name,
                            env.bindings,
                        )
                        yield env
                else:
                    for item in evaluator(processed_goal.args, env):
                        logger.debug(
                            "EXECUTE op %s: Yielding item from evaluator: %s",
                            functor_name,
                            item.bindings if item else "None",
                        )
                        yield item
            except CutException:
                logger.debug(
                    "CutException caught while evaluating operator %s. Re-raising.",
                    functor_name,
                )
                raise
            except Exception as e:
                # IOManager例外などの重要な例外は伝播
                if "Input required" in str(e) or hasattr(e, "input_type"):
                    logger.debug(
                        "Critical exception in operator %s: %s", functor_name, e
                    )
                    raise
                if isinstance(e, PrologError):
                    raise
                logger.error(
                    "Error evaluating operator %s: %s", functor_name, e, exc_info=True
                )
                return
        elif functor_name == "var" and len(processed_goal.args) == 1:
            _record_builtin_call(functor_name)
            dereferenced_arg = self.logic_interpreter.dereference(
                processed_goal.args[0], env
            )
            var_pred = VarPredicate(dereferenced_arg)
            for item in var_pred.execute(self, env):
                yield item
        elif functor_name == "atom" and len(processed_goal.args) == 1:
            _record_builtin_call(functor_name)
            dereferenced_arg = self.logic_interpreter.dereference(
                processed_goal.args[0], env
            )
            atom_pred = AtomPredicate(dereferenced_arg)
            for item in atom_pred.execute(self, env):
                yield item
        elif functor_name == "number" and len(processed_goal.args) == 1:
            _record_builtin_call(functor_name)
            dereferenced_arg = self.logic_interpreter.dereference(
                processed_goal.args[0], env
            )
            num_pred = NumberPredicate(dereferenced_arg)
            for item in num_pred.execute(self, env):
                yield item
        elif functor_name == "atom_number" and len(processed_goal.args) == 2:
            _record_builtin_call(functor_name)
            atom_number_pred = AtomNumberPredicate(
                processed_goal.args[0], processed_goal.args[1]
            )
            for item in atom_number_pred.execute(self, env):
                yield item
        elif functor_name == "functor" and len(processed_goal.args) == 3:
            _record_builtin_call(functor_name)
            functor_pred = FunctorPredicate(
                processed_goal.args[0], processed_goal.args[1], processed_goal.args[2]
            )
            try:
                for item in functor_pred.execute(self, env):
                    yield item
            except CutException:
                logger.debug("CutException from functor/3. Re-raising.")
                raise
        elif functor_name == "arg" and len(processed_goal.args) == 3:
            _record_builtin_call(functor_name)
            arg_pred = ArgPredicate(
                processed_goal.args[0], processed_goal.args[1], processed_goal.args[2]
            )
            try:
                for item in arg_pred.execute(self, env):
                    yield item
            except CutException:
                logger.debug("CutException from arg/3. Re-raising.")
                raise
        elif functor_name == "=.." and len(processed_goal.args) == 2:
            _record_builtin_call(functor_name)
            univ_pred = UnivPredicate(processed_goal.args[0], processed_goal.args[1])
            try:
                for item in univ_pred.execute(self, env):
                    yield item
            except CutException:
                logger.debug("CutException from =../2. Re-raising.")
                raise
        elif functor_name == "asserta" and len(processed_goal.args) == 1:
            _record_builtin_call(functor_name)
            asserta_pred = DynamicAssertAPredicate(processed_goal.args[0])
            for item in asserta_pred.execute(self, env):
                yield item
        elif functor_name == "assertz" and len(processed_goal.args) == 1:
            _record_builtin_call(functor_name)
            assertz_pred = DynamicAssertZPredicate(processed_goal.args[0])
            for item in assertz_pred.execute(self, env):
                yield item
        elif functor_name == "member" and len(processed_goal.args) == 2:
            # Note: MemberPredicate's execute method handles dereferencing its arguments as needed.
            _record_builtin_call(functor_name)
            member_pred = MemberPredicate(
                processed_goal.args[0], processed_goal.args[1]
            )
            try:
                for item in member_pred.execute(self, env):
                    yield item
            except CutException:  # Should member/2 propagate CutException? Typically not, but being consistent.
                logger.debug("CutException from member/2. Re-raising.")
                raise
        elif functor_name == "append" and len(processed_goal.args) == 3:
            # AppendPredicate handles dereferencing its arguments internally as needed.
            _record_builtin_call(functor_name)
            append_pred = AppendPredicate(
                processed_goal.args[0], processed_goal.args[1], processed_goal.args[2]
            )
            try:
                for item in append_pred.execute(self, env):
                    yield item
            except (
                CutException
            ):  # append/3 is not typically a source of CutException by itself
                logger.debug(
                    "CutException from append/3. Re-raising."
                )  # Though unlikely
                raise
        elif functor_name == "findall" and len(processed_goal.args) == 3:
            _record_builtin_call(functor_name)
            findall_pred = FindallPredicate(
                processed_goal.args[0], processed_goal.args[1], processed_goal.args[2]
            )
            # FindallPredicate's execute method handles internal exceptions and re-throws PrologErrors
            # It also handles CutException internally as per standard behavior (cut affects Goal, not findall itself)
            for item in findall_pred.execute(self, env):
                yield item
        elif functor_name == "get_char" and len(processed_goal.args) == 1:
            _record_builtin_call(functor_name)
            get_char_pred = create_get_char_predicate(processed_goal.args[0])
            try:
                for item in get_char_pred.execute(self, env):
                    yield item
            except Exception as e:
                # IOManager例外などをそのまま伝播
                logger.debug("Exception in %s: %s", functor_name, e)
                raise
        elif functor_name == "read_line" and len(processed_goal.args) == 1:
            _record_builtin_call(functor_name)
            read_line_pred = create_read_line_predicate(processed_goal.args[0])
            try:
                for item in read_line_pred.execute(self, env):
                    yield item
            except Exception as e:
                # IOManager例外などをそのまま伝播
                logger.debug("Exception in %s: %s", functor_name, e)
                raise
        elif functor_name == "peek_char" and len(processed_goal.args) == 1:
            _record_builtin_call(functor_name)
            peek_char_pred = create_peek_char_predicate(processed_goal.args[0])
            for item in peek_char_pred.execute(self, env):
                yield item
        elif functor_name == "at_end_of_stream" and len(processed_goal.args) == 0:
            _record_builtin_call(functor_name)
            at_end_pred = AtEndOfStreamPredicate()
            for item in at_end_pred.execute(self, env):
                yield item
        elif functor_name == "retract" and len(processed_goal.args) == 1:
            _record_builtin_call(functor_name)
            retract_pred = DynamicRetractPredicate(processed_goal.args[0])
            for item in retract_pred.execute(self, env):  # self is runtime
                yield item
        elif functor_name == "listing" and len(processed_goal.args) == 0:
            _record_builtin_call(functor_name)
            listing_pred = ListingPredicate()
            for item in listing_pred.execute(self, env):
                yield item
        elif functor_name == "listing" and len(processed_goal.args) == 1:
            _record_builtin_call(functor_name)
            listing_pred = ListingWithPredicatePredicate(processed_goal.args[0])
            for item in listing_pred.execute(self, env):
                yield item
        elif functor_name == "export_facts" and len(processed_goal.args) == 2:
            _record_builtin_call(functor_name)
            export_pred = ExportFactsPredicate(
                processed_goal.args[0], processed_goal.args[1]
            )
            for item in export_pred.execute(self, env):
                yield item
        else:
            logger.debug(
                "EXECUTE Term: Attempting Normal Predicate solve_goal for: %s",
                processed_goal,
            )
            try:
                for item in self.logic_interpreter.solve_goal(processed_goal, env):
                    logger.debug(
                        "EXECUTE Term (solve_goal): Yielding: %s",
                        item.bindings if item else "None",
                    )
                    yield item
            except CutException:
                logger.debug(
                    "CutException propagated from solve_goal for Term: %s. Re-raising.",
                    processed_goal,
                )
                raise

    def _execute_single_goal(
        self, goal: PrologType, env: BindingEnvironment
    ) -> Iterator[BindingEnvironment]:
        r"""Execute a single atomic goal (non-logical-operator).

        Handles:
        - Cut (!) - raises CutException
        - Operators (=, is, <, etc.) via _operator_evaluators
        - Built-in predicates (var, atom, functor, etc.)
        - User-defined predicates via solve_goal

        Does NOT handle logical operators (,/2, ;/2, \+/1) - caller must handle.

        Args:
            goal: Atomic goal (Atom or Term, not logical operator)
            env: Binding environment

        Yields:
            Binding environments for each solution

        Raises:
            CutException: When cut (!) is executed
            PrologError: On predicate errors

        Note:
            This method does NOT call execute() to avoid recursion.
        """
        logger.debug(
            "_execute_single_goal: Called with goal: %s (type: %s)",
            goal,
            type(goal).__name__,
        )

        # Architectural enforcement: reject logical operators
        if isinstance(goal, Term) and isinstance(goal.functor, Atom):
            assert goal.functor.name not in (",", ";", "\\+"), (
                f"Logical operator {goal.functor.name} must be handled by execute(), "
                "not _execute_single_goal()"
            )

        # Helper for statistics
        def _record_builtin_call(name: str) -> None:
            if env.stats_enabled:
                env.stats["builtin_calls_by_name"][name] = (
                    env.stats["builtin_calls_by_name"].get(name, 0) + 1
                )
                env.stats["builtin_calls_total"] += 1

        # === Goal Preprocessing ===
        processed_goal: Term
        if (
            isinstance(goal, Atom)
            and goal.name == "!"
            and "!" in self._operator_evaluators
        ):
            logger.debug("_execute_single_goal: Atom('!') detected, routing to operator.")
            processed_goal = Term(goal, [])
        elif isinstance(goal, Term):
            processed_goal = goal
        elif isinstance(goal, Atom):
            # IO operators as Atoms (nl, tab, etc.)
            if goal.name in self._operator_evaluators:
                logger.debug("_execute_single_goal Atom IO Operator: %s", goal.name)
                processed_goal = Term(goal, [])
                evaluator = self._operator_evaluators[goal.name]
                _record_builtin_call(goal.name)
                try:
                    for item in evaluator(processed_goal.args, env):
                        logger.debug(
                            "_execute_single_goal Atom IO op %s: Yielding: %s",
                            goal.name,
                            item.bindings if item else "None",
                        )
                        yield item
                except Exception as e:
                    logger.debug("Exception in Atom IO operator %s: %s", goal.name, e)
                    raise
                return

            # Normal predicate via solve_goal
            logger.debug(
                "_execute_single_goal Atom: Attempting Normal Predicate solve_goal for Atom: %s",
                goal,
            )
            try:
                for item in self.logic_interpreter.solve_goal(goal, env):
                    logger.debug(
                        "_execute_single_goal Atom (solve_goal): Yielding: %s",
                        item.bindings if item else "None",
                    )
                    yield item
            except CutException:
                logger.debug(
                    "CutException propagated from solve_goal for Atom: %s. Re-raising.",
                    goal,
                )
                raise
            return
        else:
            logger.debug(
                "Goal %s (type %s) is not directly executable by _execute_single_goal, failing.",
                goal,
                type(goal),
            )
            return

        functor_name = (
            processed_goal.functor.name
            if hasattr(processed_goal.functor, "name")
            else str(processed_goal.functor)
        )
        op_info = operator_registry.get_operator(functor_name)

        # === Operator Evaluation ===
        if op_info and functor_name in self._operator_evaluators:
            evaluator = self._operator_evaluators[functor_name]
            _record_builtin_call(functor_name)
            try:
                if (
                    op_info.operator_type == OperatorType.ARITHMETIC
                    and functor_name != "is"
                ):
                    if evaluator(processed_goal.args, env):
                        logger.debug(
                            "_execute_single_goal op %s: Yielding env (bool success): %s",
                            functor_name,
                            env.bindings,
                        )
                        yield env
                elif op_info.operator_type == OperatorType.COMPARISON:
                    if evaluator(processed_goal.args, env):
                        logger.debug(
                            "_execute_single_goal op %s: Yielding env (bool success): %s",
                            functor_name,
                            env.bindings,
                        )
                        yield env
                else:
                    for item in evaluator(processed_goal.args, env):
                        logger.debug(
                            "_execute_single_goal op %s: Yielding item from evaluator: %s",
                            functor_name,
                            item.bindings if item else "None",
                        )
                        yield item
            except CutException:
                logger.debug(
                    "CutException caught while evaluating operator %s. Re-raising.",
                    functor_name,
                )
                raise
            except Exception as e:
                # IO exceptions and PrologErrors should propagate
                if "Input required" in str(e) or hasattr(e, "input_type"):
                    logger.debug(
                        "Critical exception in operator %s: %s", functor_name, e
                    )
                    raise
                if isinstance(e, PrologError):
                    raise
                logger.error(
                    "Error evaluating operator %s: %s", functor_name, e, exc_info=True
                )
                return
            return

        # === Built-in Predicates ===
        if functor_name == "var" and len(processed_goal.args) == 1:
            _record_builtin_call(functor_name)
            dereferenced_arg = self.logic_interpreter.dereference(
                processed_goal.args[0], env
            )
            var_pred = VarPredicate(dereferenced_arg)
            for item in var_pred.execute(self, env):
                yield item
            return
        elif functor_name == "atom" and len(processed_goal.args) == 1:
            _record_builtin_call(functor_name)
            dereferenced_arg = self.logic_interpreter.dereference(
                processed_goal.args[0], env
            )
            atom_pred = AtomPredicate(dereferenced_arg)
            for item in atom_pred.execute(self, env):
                yield item
            return
        elif functor_name == "number" and len(processed_goal.args) == 1:
            _record_builtin_call(functor_name)
            dereferenced_arg = self.logic_interpreter.dereference(
                processed_goal.args[0], env
            )
            num_pred = NumberPredicate(dereferenced_arg)
            for item in num_pred.execute(self, env):
                yield item
            return
        elif functor_name == "atom_number" and len(processed_goal.args) == 2:
            _record_builtin_call(functor_name)
            atom_number_pred = AtomNumberPredicate(
                processed_goal.args[0], processed_goal.args[1]
            )
            for item in atom_number_pred.execute(self, env):
                yield item
            return
        elif functor_name == "functor" and len(processed_goal.args) == 3:
            _record_builtin_call(functor_name)
            functor_pred = FunctorPredicate(
                processed_goal.args[0], processed_goal.args[1], processed_goal.args[2]
            )
            try:
                for item in functor_pred.execute(self, env):
                    yield item
            except CutException:
                logger.debug("CutException from functor/3. Re-raising.")
                raise
            return
        elif functor_name == "arg" and len(processed_goal.args) == 3:
            _record_builtin_call(functor_name)
            arg_pred = ArgPredicate(
                processed_goal.args[0], processed_goal.args[1], processed_goal.args[2]
            )
            try:
                for item in arg_pred.execute(self, env):
                    yield item
            except CutException:
                logger.debug("CutException from arg/3. Re-raising.")
                raise
            return
        elif functor_name == "=.." and len(processed_goal.args) == 2:
            _record_builtin_call(functor_name)
            univ_pred = UnivPredicate(processed_goal.args[0], processed_goal.args[1])
            try:
                for item in univ_pred.execute(self, env):
                    yield item
            except CutException:
                logger.debug("CutException from =../2. Re-raising.")
                raise
            return
        elif functor_name == "asserta" and len(processed_goal.args) == 1:
            _record_builtin_call(functor_name)
            asserta_pred = DynamicAssertAPredicate(processed_goal.args[0])
            for item in asserta_pred.execute(self, env):
                yield item
            return
        elif functor_name == "assertz" and len(processed_goal.args) == 1:
            _record_builtin_call(functor_name)
            assertz_pred = DynamicAssertZPredicate(processed_goal.args[0])
            for item in assertz_pred.execute(self, env):
                yield item
            return
        elif functor_name == "member" and len(processed_goal.args) == 2:
            _record_builtin_call(functor_name)
            member_pred = MemberPredicate(
                processed_goal.args[0], processed_goal.args[1]
            )
            try:
                for item in member_pred.execute(self, env):
                    yield item
            except CutException:
                logger.debug("CutException from member/2. Re-raising.")
                raise
            return
        elif functor_name == "append" and len(processed_goal.args) == 3:
            _record_builtin_call(functor_name)
            append_pred = AppendPredicate(
                processed_goal.args[0], processed_goal.args[1], processed_goal.args[2]
            )
            try:
                for item in append_pred.execute(self, env):
                    yield item
            except CutException:
                logger.debug("CutException from append/3. Re-raising.")
                raise
            return
        elif functor_name == "findall" and len(processed_goal.args) == 3:
            _record_builtin_call(functor_name)
            findall_pred = FindallPredicate(
                processed_goal.args[0], processed_goal.args[1], processed_goal.args[2]
            )
            for item in findall_pred.execute(self, env):
                yield item
            return
        elif functor_name == "get_char" and len(processed_goal.args) == 1:
            _record_builtin_call(functor_name)
            get_char_pred = create_get_char_predicate(processed_goal.args[0])
            try:
                for item in get_char_pred.execute(self, env):
                    yield item
            except Exception as e:
                logger.debug("Exception in %s: %s", functor_name, e)
                raise
            return
        elif functor_name == "read_line" and len(processed_goal.args) == 1:
            _record_builtin_call(functor_name)
            read_line_pred = create_read_line_predicate(processed_goal.args[0])
            try:
                for item in read_line_pred.execute(self, env):
                    yield item
            except Exception as e:
                logger.debug("Exception in %s: %s", functor_name, e)
                raise
            return
        elif functor_name == "peek_char" and len(processed_goal.args) == 1:
            _record_builtin_call(functor_name)
            peek_char_pred = create_peek_char_predicate(processed_goal.args[0])
            for item in peek_char_pred.execute(self, env):
                yield item
            return
        elif functor_name == "at_end_of_stream" and len(processed_goal.args) == 0:
            _record_builtin_call(functor_name)
            at_end_pred = AtEndOfStreamPredicate()
            for item in at_end_pred.execute(self, env):
                yield item
            return
        elif functor_name == "retract" and len(processed_goal.args) == 1:
            _record_builtin_call(functor_name)
            retract_pred = DynamicRetractPredicate(processed_goal.args[0])
            for item in retract_pred.execute(self, env):
                yield item
            return
        elif functor_name == "listing" and len(processed_goal.args) == 0:
            _record_builtin_call(functor_name)
            listing_pred = ListingPredicate()
            for item in listing_pred.execute(self, env):
                yield item
            return
        elif functor_name == "listing" and len(processed_goal.args) == 1:
            _record_builtin_call(functor_name)
            listing_pred = ListingWithPredicatePredicate(processed_goal.args[0])
            for item in listing_pred.execute(self, env):
                yield item
            return
        elif functor_name == "export_facts" and len(processed_goal.args) == 2:
            _record_builtin_call(functor_name)
            export_pred = ExportFactsPredicate(
                processed_goal.args[0], processed_goal.args[1]
            )
            for item in export_pred.execute(self, env):
                yield item
            return

        # === Fallback: User-defined predicates via solve_goal ===
        logger.debug(
            "_execute_single_goal Term: Attempting Normal Predicate solve_goal for: %s",
            processed_goal,
        )
        try:
            for item in self.logic_interpreter.solve_goal(processed_goal, env):
                logger.debug(
                    "_execute_single_goal Term (solve_goal): Yielding: %s",
                    item.bindings if item else "None",
                )
                yield item
        except CutException:
            logger.debug(
                "CutException propagated from solve_goal for Term: %s. Re-raising.",
                processed_goal,
            )
            raise

    def execute_iterative(
        self, goal: PrologType, env: BindingEnvironment
    ) -> Iterator[BindingEnvironment]:
        """Iterative goal execution using explicit stack.

        Replaces mutual recursion between execute/evaluator/_execute_goal_sequence
        with an explicit frame-based stack approach.

        Args:
            goal: The goal to execute
            env: The binding environment

        Yields:
            Binding environments for each solution

        Raises:
            CutException: When cut (!) is executed
        """
        state = ExecutionState(stack=[], choice_points=[])
        state.push_goal(goal, env)

        while state.stack:
            frame = state.stack[-1]

            try:
                # Special handling for GoalSeqFrame
                if isinstance(frame, GoalSeqFrame):
                    result = frame.step(self)

                    if result is None:
                        # Need to push next goal in sequence
                        if frame.current_index < len(frame.goals):
                            next_goal = frame.goals[frame.current_index]
                            state.push_goal(next_goal, frame.env)
                        else:
                            # Should not happen (step() should return env)
                            state.stack.pop()
                        continue

                    # result is not None: sequence complete
                    yield result
                    state.stack.pop()
                    continue

                # Regular frame processing
                result = frame.step(self)

                if result is None:
                    # Frame exhausted, pop and continue
                    state.stack.pop()
                    continue

                # Frame produced a result
                if isinstance(frame, GoalFrame):
                    # Check if this is part of a sequence
                    parent_frame = (
                        state.stack[-2] if len(state.stack) >= 2 else None
                    )

                    if isinstance(parent_frame, GoalSeqFrame):
                        # Goal in sequence succeeded, advance parent
                        parent_frame.advance(result)
                        state.stack.pop()  # Pop current GoalFrame

                        # Check if sequence is complete
                        if parent_frame.current_index >= len(parent_frame.goals):
                            # Sequence complete, will be yielded in next iteration
                            pass
                        # else: next goal will be pushed in next iteration
                    else:
                        # Standalone goal succeeded
                        yield result
                        # Continue to try next solution from this frame
                else:
                    # Other frame types
                    yield result
                    state.stack.pop()

            except CutException:
                # Handle cut: remove choice points
                state.apply_cut()
                raise

            except StopIteration:
                # Frame exhausted, try backtracking
                if not state.backtrack():
                    state.stack.pop()

    def query(self, query_string: str) -> list[dict[Variable, Any]]:
        logger.debug("QUERY: Executing query: %s", query_string)
        solutions = []
        try:
            # Ensure query ends with a dot for parsing consistency
            if not query_string.strip().endswith("."):
                query_string += "."
            tokens = Scanner(
                query_string,
                variable_mapper=self.variable_mapper,
                functor_mapper=self.functor_mapper,
            ).scan_tokens()
            parsed_structures = Parser(
                tokens,
                variable_mapper=self.variable_mapper,
                functor_mapper=self.functor_mapper,
            ).parse()
            if not parsed_structures:
                logger.warning("Query parsing failed")
                return []
            query_goal: Any | None = None
            if isinstance(parsed_structures[0], Fact):
                query_goal = parsed_structures[0].head
            elif isinstance(parsed_structures[0], Rule):
                query_goal = parsed_structures[0].head
            elif isinstance(parsed_structures[0], Term):
                query_goal = parsed_structures[0]
            elif isinstance(parsed_structures[0], Atom):
                query_goal = parsed_structures[0]

            if query_goal is None:
                logger.error(
                    "Could not extract a valid goal from parsed: %s",
                    parsed_structures[0],
                )
                return []

            initial_env = BindingEnvironment()

            term_for_vars_extraction: Term
            if isinstance(query_goal, Atom):
                term_for_vars_extraction = Term(query_goal, [])
            elif isinstance(query_goal, Term):
                term_for_vars_extraction = query_goal
            else:
                logger.error(
                    "Cannot extract vars from non-Term/Atom goal: %s",
                    query_goal,
                )
                return []
            query_vars_names = self._extract_variables_names(term_for_vars_extraction)

            try:
                logger.debug("QUERY: Starting execute loop for goal: %s", query_goal)
                for i, env_solution in enumerate(self.execute(query_goal, initial_env)):
                    logger.debug(
                        "QUERY: Received solution #%d from execute: %s",
                        i,
                        env_solution.bindings if env_solution else "None",
                    )
                    if env_solution is None:
                        continue
                    result = {}
                    for var_name_str in query_vars_names:
                        var_obj = Variable(
                            var_name_str
                        )  # This is the English (mapped) variable name
                        value_fully_dereferenced = (
                            self.logic_interpreter.deep_dereference_term(
                                var_obj, env_solution
                            )
                        )
                        # Convert variable name back to Japanese for display
                        original_var_name = (
                            self.variable_mapper.map_english_to_japanese(var_obj.name)
                        )
                        display_var_obj = Variable(original_var_name)
                        # Convert any variables within the result term back to Japanese
                        result[display_var_obj] = self._convert_vars_to_japanese(
                            value_fully_dereferenced
                        )
                    solutions.append(result)
            except CutException:
                logger.info(
                    "Cut execution stopped further solutions at query level. Returning %d solution(s).",
                    len(solutions),
                )

            logger.debug("QUERY: Completed with %d solutions", len(solutions))
            return solutions

        except PrologError as pe:  # Catch PrologError specifically
            logger.warning(
                "PrologError during query execution: %s", pe, exc_info=True
            )  # Log as warning or info
            raise pe  # Re-throw PrologError so tests can catch it

        except Exception as e:  # Catch other, unexpected exceptions
            logger.error(
                "Unexpected query execution error during query '%s': %s",
                query_string,
                e,
                exc_info=True,
            )
            # Re-raise the exception to make it visible in test output
            raise e

    def query_with_trace(
        self, query_string: str, max_depth: int | None = None
    ) -> tuple[list[dict[Variable, Any]], list]:
        """トレース付きでクエリを実行"""

        logger.debug("TRACE QUERY: Executing query with trace: %s", query_string)

        # 新しいTracerインスタンスを作成
        self.tracer = Tracer(max_depth)
        self.tracer.start_trace()

        try:
            solutions = self.query(query_string)
            trace_events = self.tracer.get_events()
            return solutions, trace_events
        finally:
            self.tracer.stop_trace()

    def _extract_variables_names(self, term: Term) -> list[str]:
        variables = set()
        queue = [term]
        while queue:
            current = queue.pop(0)
            if isinstance(current, Variable):
                variables.add(current.name)
            elif isinstance(current, Term):
                if isinstance(current.functor, Variable):
                    variables.add(current.functor.name)
                queue.extend(current.args)
        return list(variables)

    def add_rule(self, rule_string: str) -> bool:
        try:
            if not rule_string.strip().endswith("."):
                rule_string += "."
            tokens = Scanner(
                rule_string,
                variable_mapper=self.variable_mapper,
                functor_mapper=self.functor_mapper,
            ).scan_tokens()
            parsed_items = Parser(
                tokens,
                variable_mapper=self.variable_mapper,
                functor_mapper=self.functor_mapper,
            ).parse()
            added_count = 0
            if parsed_items:
                for item in parsed_items:
                    if isinstance(item, (Rule, Fact)):
                        self.logic_interpreter.add_rule(item, position="last")
                        added_count += 1
                    else:
                        logger.warning("Skipping non-rule/fact from add_rule: %s", item)
                if added_count > 0:
                    logger.info("Added %d rule(s)/fact(s) from string.", added_count)
                else:
                    logger.warning("No rules/facts parsed from add_rule string.")
                return added_count > 0
            logger.warning("No rules/facts parsed from add_rule string.")
            return False
        except Exception as e:
            logger.error("Failed to add rule: %s", e, exc_info=True)
            return False

    def consult(self, filename: str) -> bool:
        try:
            with open(filename, encoding="utf-8") as f:
                source = f.read()
            tokens = Scanner(
                source,
                variable_mapper=self.variable_mapper,
                functor_mapper=self.functor_mapper,
            ).scan_tokens()
            parser = Parser(
                tokens,
                variable_mapper=self.variable_mapper,
                functor_mapper=self.functor_mapper,
            )
            new_rules_or_terms = parser.parse()

            # Apply directives FIRST
            directives = parser.directives
            for directive_type, pred_name, arity in directives:
                if directive_type == "dynamic":
                    self.logic_interpreter.apply_dynamic(pred_name, arity)
                    logger.info("Applied dynamic directive: %s/%d from %s", pred_name, arity, filename)

            # Then add rules
            added_count = 0
            for item in new_rules_or_terms:
                if isinstance(item, (Rule, Fact)):
                    self.logic_interpreter.add_rule(item, position="last")
                    added_count += 1
                else:
                    logger.warning("Skipping non-rule/fact during consult: %s", item)

            if added_count > 0 or directives:
                logger.info(
                    "Consulted %d directive(s) and %d rule(s)/fact(s) from %s",
                    len(directives), added_count, filename
                )
            else:
                logger.info("No directives, rules or facts consulted from %s", filename)
            return True
        except Exception as e:
            logger.error("Failed to consult %s: %s", filename, e, exc_info=True)
            return False

    def _convert_vars_to_japanese(self, term: Any) -> Any:
        if isinstance(term, Variable):
            return Variable(self.variable_mapper.map_english_to_japanese(term.name))
        elif isinstance(term, Term):
            new_args = [self._convert_vars_to_japanese(arg) for arg in term.args]
            # FunctorがVariableの場合も変換する（通常はAtomだが念のため）
            current_functor = term.functor
            if isinstance(current_functor, Variable):
                # FunctorがVariableの場合は変数として変換
                functor_display_name = self.variable_mapper.map_english_to_japanese(
                    current_functor.name
                )
                return Term(Variable(functor_display_name), new_args)
            elif isinstance(current_functor, Atom):
                # FunctorがAtomの場合は、まずファンクター名の日本語復元を試す
                functor_name = current_functor.name
                # FunctorMapperで日本語復元を試行
                restored_functor_name = self.functor_mapper.map_english_to_non_ascii(
                    functor_name
                )
                return Term(Atom(restored_functor_name), new_args)
            else:
                # その他の場合（通常は発生しない）
                functor_display_name = str(current_functor)
                return Term(Atom(functor_display_name), new_args)
        elif isinstance(term, list):  # For lists (e.g. from findall)
            return [self._convert_vars_to_japanese(item) for item in term]
        # Other types (Number, Atom, String) are returned as is.
        return term
