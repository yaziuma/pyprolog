import ast
import logging
from collections.abc import Iterator
from typing import TYPE_CHECKING

from pyprolog.core.binding_environment import BindingEnvironment
from pyprolog.core.errors import CutException, PrologError
from pyprolog.core.types import (
    Atom,
    Fact,
    Number,
    PrologType,
    Rule,
    String,
    Term,
    Variable,
)
from pyprolog.runtime.external.arg_policy import normalize_cli_args
from pyprolog.runtime.unified_input_system import StreamInputHandler

logger = logging.getLogger(__name__)
if TYPE_CHECKING:
    from pyprolog.runtime.interpreter import Runtime


def try_convert_atom_to_number(atom_value: str) -> int | float | None:
    """
    標準的なPython方式でatom文字列を数値に変換する。
    ast.literal_eval()を使用して安全に数値変換を行う。

    Args:
        atom_value: 変換対象の文字列

    Returns:
        変換成功時は数値(int/float)、失敗時はNone
    """
    try:
        result = ast.literal_eval(atom_value)
        if isinstance(result, (int, float)):
            return result
        return None
    except (ValueError, SyntaxError):
        return None


class BuiltinPredicate:
    def __init__(self, *args):
        self.args = args

    def execute(
        self, runtime: "Runtime", bindings: BindingEnvironment
    ) -> Iterator[BindingEnvironment]:
        raise NotImplementedError


class VarPredicate(BuiltinPredicate):
    def __init__(self, arg1: PrologType):
        super().__init__(arg1)

    def execute(
        self, runtime: "Runtime", env: BindingEnvironment
    ) -> Iterator[BindingEnvironment]:
        arg1 = self.args[0]
        if isinstance(arg1, Variable):
            yield env


class AtomPredicate(BuiltinPredicate):
    def __init__(self, arg1: PrologType):
        super().__init__(arg1)

    def execute(
        self, runtime: "Runtime", env: BindingEnvironment
    ) -> Iterator[BindingEnvironment]:
        arg1 = self.args[0]
        if isinstance(arg1, Atom):
            yield env


class NumberPredicate(BuiltinPredicate):
    def __init__(self, arg1: PrologType):
        super().__init__(arg1)

    def execute(
        self, runtime: "Runtime", env: BindingEnvironment
    ) -> Iterator[BindingEnvironment]:
        arg1 = self.args[0]
        if isinstance(arg1, Number):
            yield env


class AtomNumberPredicate(BuiltinPredicate):
    """
    Built-in predicate atom_number/2.
    Converts between atoms and numbers: atom_number(+Atom, ?Number) or atom_number(?Atom, +Number).
    """

    def __init__(self, atom_arg: PrologType, number_arg: PrologType):
        super().__init__(atom_arg, number_arg)
        if len(self.args) != 2:
            raise PrologError(
                f"atom_number/2 expects 2 arguments, got {len(self.args)}"
            )

    def execute(
        self, runtime: "Runtime", env: BindingEnvironment
    ) -> Iterator[BindingEnvironment]:
        atom_arg = runtime.logic_interpreter.dereference(self.args[0], env)
        number_arg = runtime.logic_interpreter.dereference(self.args[1], env)
        if isinstance(atom_arg, Atom) and (not isinstance(number_arg, Number)):
            number_value = try_convert_atom_to_number(atom_arg.name)
            if number_value is not None:
                target_number = Number(number_value)
                unified, final_env = runtime.logic_interpreter.unify(
                    self.args[1], target_number, env
                )
                if unified:
                    yield final_env
            return
        elif isinstance(number_arg, Number) and (not isinstance(atom_arg, Atom)):
            target_atom = Atom(str(number_arg.value))
            unified, final_env = runtime.logic_interpreter.unify(
                self.args[0], target_atom, env
            )
            if unified:
                yield final_env
            return
        elif isinstance(atom_arg, Atom) and isinstance(number_arg, Number):
            number_value = try_convert_atom_to_number(atom_arg.name)
            if number_value == number_arg.value:
                yield env
            return


class FunctorPredicate(BuiltinPredicate):
    def __init__(
        self, term_arg: PrologType, functor_arg: PrologType, arity_arg: PrologType
    ):
        super().__init__(term_arg, functor_arg, arity_arg)

    def execute(
        self, runtime: "Runtime", env: BindingEnvironment
    ) -> Iterator[BindingEnvironment]:
        term, d_functor, d_arity = (self.args[0], self.args[1], self.args[2])
        term_val = runtime.logic_interpreter.dereference(term, env)
        functor_val = runtime.logic_interpreter.dereference(d_functor, env)
        arity_val = runtime.logic_interpreter.dereference(d_arity, env)
        if not isinstance(term, Variable) or (
            isinstance(term, Variable) and (not env.is_unbound(term.name))
        ):
            actual_functor: PrologType
            actual_arity: Number
            if isinstance(term_val, Term):
                actual_functor = term_val.functor
                actual_arity = Number(len(term_val.args))
            elif isinstance(term_val, Atom):
                actual_functor = term_val
                actual_arity = Number(0)
            elif isinstance(term_val, Number):
                actual_functor = term_val
                actual_arity = Number(0)
            else:
                return
            unified_functor, env1 = runtime.logic_interpreter.unify(
                functor_val, actual_functor, env
            )
            if not unified_functor:
                return
            unified_arity, env2 = runtime.logic_interpreter.unify(
                arity_val, actual_arity, env1
            )
            if not unified_arity:
                return
            yield env2
            return
        elif isinstance(term, Variable) and env.is_unbound(term.name):
            if not isinstance(functor_val, (Atom, Number)):
                return
            if (
                not isinstance(arity_val, Number)
                or not arity_val.value.is_integer()
                or arity_val.value < 0
            ):
                return
            if isinstance(functor_val, Number) and arity_val.value != 0:
                return
            constructed_term: PrologType
            arity_int = int(arity_val.value)
            if arity_int == 0:
                constructed_term = functor_val
            else:
                if not isinstance(functor_val, Atom):
                    return
                args = [
                    Variable(f"_GFA{runtime.logic_interpreter._unique_var_counter + i}")
                    for i in range(arity_int)
                ]
                runtime.logic_interpreter._unique_var_counter += arity_int
                constructed_term = Term(functor_val, args)
            unified_term, final_env = runtime.logic_interpreter.unify(
                term, constructed_term, env
            )
            if unified_term:
                yield final_env
            return
        return


class ArgPredicate(BuiltinPredicate):
    def __init__(
        self, index_arg: PrologType, term_arg: PrologType, value_arg: PrologType
    ):
        super().__init__(index_arg, term_arg, value_arg)

    def execute(
        self, runtime: "Runtime", env: BindingEnvironment
    ) -> Iterator[BindingEnvironment]:
        index_val = runtime.logic_interpreter.dereference(self.args[0], env)
        term_val = runtime.logic_interpreter.dereference(self.args[1], env)
        if (
            not isinstance(index_val, Number)
            or not index_val.value.is_integer()
            or index_val.value <= 0
        ):
            return
        if not isinstance(term_val, Term):
            return
        idx = int(index_val.value)
        if idx > len(term_val.args):
            return
        target_arg = term_val.args[idx - 1]
        unified, final_env = runtime.logic_interpreter.unify(
            self.args[2], target_arg, env
        )
        if unified:
            yield final_env


class UnivPredicate(BuiltinPredicate):
    def __init__(self, term_arg: PrologType, list_arg: PrologType):
        super().__init__(term_arg, list_arg)

    def execute(
        self, runtime: "Runtime", env: BindingEnvironment
    ) -> Iterator[BindingEnvironment]:
        term_is_var_unbound = isinstance(self.args[0], Variable) and env.is_unbound(
            self.args[0].name
        )
        list_is_var_unbound = isinstance(self.args[1], Variable) and env.is_unbound(
            self.args[1].name
        )
        term_val = runtime.logic_interpreter.dereference(self.args[0], env)
        list_val = runtime.logic_interpreter.dereference(self.args[1], env)
        if not term_is_var_unbound:
            result_list_content: list[PrologType] = []
            if isinstance(term_val, Term):
                result_list_content.append(term_val.functor)
                result_list_content.extend(term_val.args)
            elif isinstance(term_val, (Atom, Number)):
                result_list_content.append(term_val)
            else:
                return
            prolog_list: PrologType = Atom("[]")
            for i in range(len(result_list_content) - 1, -1, -1):
                prolog_list = Term(Atom("."), [result_list_content[i], prolog_list])
            unified, final_env = runtime.logic_interpreter.unify(
                self.args[1], prolog_list, env
            )
            if unified:
                yield final_env
            return
        elif term_is_var_unbound and (not list_is_var_unbound):
            if not isinstance(list_val, Term) and (
                not (isinstance(list_val, Atom) and list_val.name == "[]")
            ):
                return
            py_list: list[PrologType] = []
            current_cell = list_val
            while (
                isinstance(current_cell, Term)
                and current_cell.functor.name == "."
                and (len(current_cell.args) == 2)
            ):
                py_list.append(
                    runtime.logic_interpreter.dereference(current_cell.args[0], env)
                )
                current_cell = runtime.logic_interpreter.dereference(
                    current_cell.args[1], env
                )
            if not (isinstance(current_cell, Atom) and current_cell.name == "[]"):
                return
            if not py_list:
                return
            functor_from_list = py_list[0]
            args_from_list = py_list[1:]
            if not isinstance(functor_from_list, (Atom, Number)):
                return
            if isinstance(functor_from_list, Number) and args_from_list:
                return
            if (
                isinstance(functor_from_list, Atom)
                and functor_from_list.name == "[]"
                and args_from_list
            ):
                return
            MAX_ARITY = 50
            if len(args_from_list) > MAX_ARITY:
                return
            constructed_term: PrologType
            if not args_from_list:
                constructed_term = functor_from_list
            else:
                if not isinstance(functor_from_list, Atom):
                    return
                constructed_term = Term(functor_from_list, args_from_list)
            unified, final_env = runtime.logic_interpreter.unify(
                self.args[0], constructed_term, env
            )
            if unified:
                yield final_env
            return
        elif term_is_var_unbound and list_is_var_unbound:
            return
        return


class DynamicAssertAPredicate(BuiltinPredicate):
    def __init__(self, clause_arg: PrologType):
        super().__init__(clause_arg)

    def execute(
        self, runtime: "Runtime", env: BindingEnvironment
    ) -> Iterator[BindingEnvironment]:
        logger.debug("ASSERTA: Entered with arg: %s", self.args[0])
        clause_val = runtime.logic_interpreter.dereference(self.args[0], env)
        logger.debug(
            "ASSERTA: Dereferenced clause_val: %s (type: %s)",
            clause_val,
            type(clause_val),
        )
        if isinstance(clause_val, Variable):
            logger.warning(
                "ASSERTA: Attempt to assert an uninstantiated variable: %s. Failing.",
                clause_val,
            )
            return
        if not isinstance(clause_val, (Term, Atom)):
            logger.warning(
                "ASSERTA: Attempt to assert a non-term/non-atom: %s (type: %s). Failing.",
                clause_val,
                type(clause_val),
            )
            return
        try:
            clause_val_as_term = (
                Term(clause_val, []) if isinstance(clause_val, Atom) else clause_val
            )
            logger.debug("ASSERTA: clause_val_as_term: %s", clause_val_as_term)
            if (
                clause_val_as_term.functor.name == ":-"
                and len(clause_val_as_term.args) == 2
            ):
                head = clause_val_as_term.args[0]
                body = clause_val_as_term.args[1]
                logger.debug(
                    "ASSERTA: Identified as rule. Head: %s, Body: %s", head, body
                )
                if not isinstance(head, (Term, Atom)):
                    logger.warning(
                        "ASSERTA: Rule head is not Term or Atom: %s. Failing on clause: %s",
                        head,
                        clause_val,
                    )
                    return
                if isinstance(head, Atom):
                    head = Term(head, [])
                    logger.debug("ASSERTA: Converted Atom head to Term: %s", head)
                processed_body = body
                if isinstance(body, Atom):
                    processed_body = Term(body, [])
                    logger.debug(
                        "ASSERTA: Converted Atom body %s to Term: %s",
                        body,
                        processed_body,
                    )
                elif not isinstance(body, Term):
                    logger.warning(
                        "ASSERTA: Rule body %s (type: %s) is not an Atom or Term. Failing assertion for clause: %s",
                        body,
                        type(body),
                        clause_val,
                    )
                    return
                new_rule = Rule(head, processed_body)
                logger.debug("ASSERTA: Created Rule: %s", new_rule)
                runtime.logic_interpreter.add_rule(new_rule, position="first")
                logger.info("ASSERTA: Successfully asserted rule: %s", new_rule)
            else:
                logger.debug("ASSERTA: Identified as fact: %s", clause_val_as_term)
                new_fact = Fact(clause_val_as_term)
                logger.debug("ASSERTA: Created Fact: %s", new_fact)
                runtime.logic_interpreter.add_rule(new_fact, position="first")
                logger.info("ASSERTA: Successfully asserted fact: %s", new_fact)
            logger.debug(
                "ASSERTA: About to yield environment for: %r", clause_val_as_term
            )
            yield env
            logger.debug(
                "ASSERTA: Successfully yielded environment for: %r", clause_val_as_term
            )
        except Exception as e:
            logger.error(
                "ASSERTA: Unexpected Python exception during assertion of %r: %s",
                clause_val,
                e,
                exc_info=True,
            )
            return


class DynamicAssertZPredicate(BuiltinPredicate):
    def __init__(self, clause_arg: PrologType):
        super().__init__(clause_arg)

    def execute(
        self, runtime: "Runtime", env: BindingEnvironment
    ) -> Iterator[BindingEnvironment]:
        logger.debug("ASSERTZ: Entered with arg: %s", self.args[0])
        clause_val = runtime.logic_interpreter.dereference(self.args[0], env)
        logger.debug(
            "ASSERTZ: Dereferenced clause_val: %r (type: %r)",
            clause_val,
            type(clause_val),
        )
        if isinstance(clause_val, Variable):
            logger.warning(
                "ASSERTZ: Attempt to assert an uninstantiated variable: %r. Failing.",
                clause_val,
            )
            return
        if not isinstance(clause_val, (Term, Atom)):
            logger.warning(
                "ASSERTZ: Attempt to assert a non-term/non-atom: %r (type: %r). Failing.",
                clause_val,
                type(clause_val),
            )
            return
        try:
            clause_val_as_term = (
                Term(clause_val, []) if isinstance(clause_val, Atom) else clause_val
            )
            logger.debug("ASSERTZ: clause_val_as_term: %s", clause_val_as_term)
            if (
                clause_val_as_term.functor.name == ":-"
                and len(clause_val_as_term.args) == 2
            ):
                head = clause_val_as_term.args[0]
                body = clause_val_as_term.args[1]
                logger.debug(
                    "ASSERTZ: Identified as rule. Head: %s, Body: %s", head, body
                )
                if not isinstance(head, (Term, Atom)):
                    logger.warning(
                        "ASSERTZ: Rule head is not Term or Atom: %s. Failing on clause: %s",
                        head,
                        clause_val,
                    )
                    return
                if isinstance(head, Atom):
                    head = Term(head, [])
                    logger.debug("ASSERTZ: Converted Atom head to Term: %s", head)
                processed_body = body
                if isinstance(body, Atom):
                    processed_body = Term(body, [])
                    logger.debug(
                        "ASSERTZ: Converted Atom body %s to Term: %s",
                        body,
                        processed_body,
                    )
                elif not isinstance(body, Term):
                    logger.warning(
                        "ASSERTZ: Rule body %s (type: %s) is not an Atom or Term. Failing assertion for clause: %s",
                        body,
                        type(body),
                        clause_val,
                    )
                    return
                new_rule = Rule(head, processed_body)
                logger.debug("ASSERTZ: Created Rule: %s", new_rule)
                runtime.logic_interpreter.add_rule(new_rule, position="last")
                logger.info("ASSERTZ: Successfully asserted rule: %s", new_rule)
            else:
                logger.debug("ASSERTZ: Identified as fact: %s", clause_val_as_term)
                new_fact = Fact(clause_val_as_term)
                logger.debug("ASSERTZ: Created Fact: %s", new_fact)
                runtime.logic_interpreter.add_rule(new_fact, position="last")
                logger.info("ASSERTZ: Successfully asserted fact: %s", new_fact)
            logger.debug(
                "ASSERTZ: About to yield environment for: %s", clause_val_as_term
            )
            yield env
            logger.debug(
                "ASSERTZ: Successfully yielded environment for: %s", clause_val_as_term
            )
        except Exception as e:
            logger.error(
                "ASSERTZ: Unexpected Python exception during assertion of %s: %s",
                clause_val,
                e,
                exc_info=True,
            )
            return


class MemberPredicate(BuiltinPredicate):
    def __init__(self, element_arg: PrologType, list_arg: PrologType):
        super().__init__(element_arg, list_arg)

    def execute(
        self, runtime: "Runtime", env: BindingEnvironment
    ) -> Iterator[BindingEnvironment]:
        current_list = runtime.logic_interpreter.dereference(self.args[1], env)
        element_to_match = self.args[0]
        while (
            isinstance(current_list, Term)
            and isinstance(current_list.functor, Atom)
            and (current_list.functor.name == ".")
            and (len(current_list.args) == 2)
        ):
            head = current_list.args[0]
            head = current_list.args[0]
            tail = current_list.args[1]
            logger.debug(
                "MEMBER: Loop iteration. current_list='%r', head='%r', tail='%r', element_to_match='%r'",
                current_list,
                head,
                tail,
                element_to_match,
            )
            unified, next_env = runtime.logic_interpreter.unify(
                element_to_match, head, env
            )
            logger.debug(
                "MEMBER: Unify result for element '%r' and head '%r': %r. Env after unify: %r",
                element_to_match,
                head,
                unified,
                next_env.bindings if unified else "N/A",
            )
            if unified:
                yield next_env
            current_list_before_deref = tail
            current_list = runtime.logic_interpreter.dereference(tail, env)
            logger.debug(
                "MEMBER: Tail dereferenced. Before='%r', After='%r', Type After='%r'",
                current_list_before_deref,
                current_list,
                type(current_list),
            )
        return


class AppendPredicate(BuiltinPredicate):
    def __init__(
        self, list1_arg: PrologType, list2_arg: PrologType, list3_arg: PrologType
    ):
        super().__init__(list1_arg, list2_arg, list3_arg)

    def execute(
        self, runtime: "Runtime", env: BindingEnvironment
    ) -> Iterator[BindingEnvironment]:
        """Execute append/3 using explicit stack (non-recursive).

        Implements:
        - append([], L, L).
        - append([H|T1], L2, [H|T3]) :- append(T1, L2, T3).

        Maintains multi-directionality:
        - Pattern 1: append(+List, +List, -Result) — concatenation
        - Pattern 2: append(-Prefix, -Suffix, +List) — splitting
        - Pattern 3: append(-X, -Y, +List) — enumeration of all splits
        """
        # Stack: list of (list1_arg, list2_arg, list3_arg, env)
        stack = [(self.args[0], self.args[1], self.args[2], env)]

        while stack:
            l1, l2, l3, current_env = stack.pop()

            # === Clause 1: append([], L, L) ===
            env_clause1 = current_env.copy()
            unified_l1_empty, env_clause1_after_l1 = runtime.logic_interpreter.unify(
                l1, Atom("[]"), env_clause1
            )
            logger.debug(
                "APPEND_CP1: L1='%r', L2='%r', L3='%r'. Trying to unify L1 with [].",
                l1,
                l2,
                l3,
            )
            if unified_l1_empty:
                logger.debug(
                    "APPEND_CP1: L1 unified with []. Env after L1 unify: %r",
                    env_clause1_after_l1.bindings,
                )
                unified_l2_l3, final_env_clause1 = runtime.logic_interpreter.unify(
                    l2, l3, env_clause1_after_l1
                )
                if unified_l2_l3:
                    logger.debug(
                        "APPEND_CP1: L2 and L3 unified. Yielding solution from CP1. Env: %r",
                        final_env_clause1.bindings,
                    )
                    yield final_env_clause1
                else:
                    logger.debug("APPEND_CP1: L2 and L3 failed to unify.")
            else:
                logger.debug("APPEND_CP1: L1 failed to unify with [].")

            # === Clause 2: append([H|T1], L2, [H|T3]) :- append(T1, L2, T3) ===
            logger.debug(
                "APPEND_CP2: L1='%r', L2='%r', L3='%r'. Creating patterns.",
                l1,
                l2,
                l3,
            )
            env_clause2 = current_env.copy()
            counter = runtime.logic_interpreter._unique_var_counter
            h1_var = Variable(f"_HAppend_{counter}")
            t1_var = Variable(f"_T1Append_{counter + 1}")
            t3_var = Variable(f"_T3Append_{counter + 2}")
            runtime.logic_interpreter._unique_var_counter += 3
            list1_pattern = Term(Atom("."), [h1_var, t1_var])
            logger.debug(
                "APPEND_CP2: Attempting to unify L1 ('%r') with pattern '%r'.",
                l1,
                list1_pattern,
            )
            unified_l1_cons, env_clause2_after_l1 = runtime.logic_interpreter.unify(
                l1, list1_pattern, env_clause2
            )
            if unified_l1_cons:
                logger.debug(
                    "APPEND_CP2: L1 unified with '%r'. Env after L1 unify: %r",
                    list1_pattern,
                    env_clause2_after_l1.bindings,
                )
                list3_pattern = Term(Atom("."), [h1_var, t3_var])
                logger.debug(
                    "APPEND_CP2: Attempting to unify L3 ('%r') with pattern '%r'.",
                    l3,
                    list3_pattern,
                )
                unified_l3_cons, env_clause2_after_l3 = runtime.logic_interpreter.unify(
                    l3, list3_pattern, env_clause2_after_l1
                )
                if unified_l3_cons:
                    logger.debug(
                        "APPEND_CP2: L3 unified with '%r'. Env after L3 unify: %r",
                        list3_pattern,
                        env_clause2_after_l3.bindings,
                    )
                    logger.debug(
                        "APPEND_CP2: Pushing recursive call: append(%r, %r, %r) with env: %r",
                        t1_var,
                        l2,
                        t3_var,
                        env_clause2_after_l3.bindings,
                    )
                    # Instead of recursive call, push to stack
                    stack.append((t1_var, l2, t3_var, env_clause2_after_l3))
                else:
                    logger.debug(
                        "APPEND_CP2: L3 failed to unify with '%s'.", list3_pattern
                    )
            else:
                logger.debug("APPEND_CP2: L1 failed to unify with '%s'.", list1_pattern)

        return


class FindallPredicate(BuiltinPredicate):
    def __init__(
        self, template_arg: PrologType, goal_arg: PrologType, list_arg: PrologType
    ):
        super().__init__(template_arg, goal_arg, list_arg)

    def execute(
        self, runtime: "Runtime", env: BindingEnvironment
    ) -> Iterator[BindingEnvironment]:
        template = self.args[0]
        goal_to_prove = runtime.logic_interpreter.dereference(self.args[1], env)
        result_list_arg = self.args[2]
        if isinstance(goal_to_prove, Variable):
            raise PrologError(
                f"instantiation_error: Goal in findall/3 cannot be an unbound variable. Got: {goal_to_prove}"
            )
        if isinstance(goal_to_prove, Atom) and goal_to_prove.name == "[]":
            raise PrologError(
                f"type_error(callable, {goal_to_prove}): Goal '[]' in findall/3 is not a callable term."
            )
        elif not isinstance(goal_to_prove, (Atom, Term)):
            raise PrologError(
                f"type_error(callable, {goal_to_prove}): Goal in findall/3 must be a callable term."
            )
        collected_templates: list[PrologType] = []
        try:
            for solution_env in runtime.execute(goal_to_prove, env):
                instantiated_template = runtime.logic_interpreter.instantiate_term(
                    template, solution_env
                )
                collected_templates.append(instantiated_template)
        except CutException:
            pass
        except PrologError as e:
            raise e
        prolog_solutions_list: PrologType = Atom("[]")
        for item in reversed(collected_templates):
            prolog_solutions_list = Term(Atom("."), [item, prolog_solutions_list])
        unified, final_env = runtime.logic_interpreter.unify(
            result_list_arg, prolog_solutions_list, env
        )
        if unified:
            yield final_env
        return


class DynamicRetractPredicate(BuiltinPredicate):
    def __init__(self, clause_arg: PrologType):
        super().__init__(clause_arg)

    def execute(
        self, runtime: "Runtime", env: BindingEnvironment
    ) -> Iterator[BindingEnvironment]:
        logger.debug("RETRACT: Entered with arg: %s", self.args[0])
        clause_to_retract_orig = self.args[0]
        import copy

        clause_to_retract_for_unify = copy.deepcopy(
            runtime.logic_interpreter.dereference(clause_to_retract_orig, env)
        )
        logger.debug(
            "RETRACT: Dereferenced clause_to_retract_for_unify: %r (type: %r)",
            clause_to_retract_for_unify,
            type(clause_to_retract_for_unify),
        )
        if isinstance(clause_to_retract_for_unify, Variable):
            logger.warning(
                "RETRACT: Attempt to retract an uninstantiated variable: %r. Failing (Instantiation Error).",
                clause_to_retract_for_unify,
            )
            return
        if not isinstance(clause_to_retract_for_unify, (Term, Atom)):
            logger.warning(
                "RETRACT: Argument is not a Term or Atom: %r (type: %r). Failing (Type Error).",
                clause_to_retract_for_unify,
                type(clause_to_retract_for_unify),
            )
            return
        target_clause_struct = (
            Term(clause_to_retract_for_unify, [])
            if isinstance(clause_to_retract_for_unify, Atom)
            else clause_to_retract_for_unify
        )
        is_retracting_rule_form = (
            isinstance(target_clause_struct, Term)
            and target_clause_struct.functor.name == ":-"
            and (len(target_clause_struct.args) == 2)
        )
        target_head_to_match = (
            target_clause_struct.args[0]
            if is_retracting_rule_form
            else target_clause_struct
        )
        target_body_to_match = (
            target_clause_struct.args[1] if is_retracting_rule_form else None
        )
        for i in range(len(runtime.rules) - 1, -1, -1):
            db_clause = runtime.rules[i]
            renamed_db_clause = runtime.logic_interpreter._rename_variables(
                db_clause, env
            )
            db_head: Term
            db_body: PrologType | None = None
            if isinstance(renamed_db_clause, Fact):
                db_head = renamed_db_clause.head
                if is_retracting_rule_form:
                    continue
            elif isinstance(renamed_db_clause, Rule):
                db_head = renamed_db_clause.head
                db_body = renamed_db_clause.body
                if not is_retracting_rule_form and db_body is not None:
                    pass
            else:
                logger.error("RETRACT: Unknown clause type in DB: %s", db_clause)
                continue
            unified_head, head_env = runtime.logic_interpreter.unify(
                target_head_to_match, db_head, env.copy()
            )
            if unified_head:
                if is_retracting_rule_form:
                    if db_body is None:
                        continue
                    db_body_term = (
                        Term(db_body, []) if isinstance(db_body, Atom) else db_body
                    )
                    if (
                        not isinstance(db_body_term, Term)
                        and target_body_to_match is not None
                    ):
                        continue
                    unified_body, final_env = runtime.logic_interpreter.unify(
                        target_body_to_match, db_body_term, head_env
                    )
                    if unified_body:
                        logger.info(
                            "RETRACT: Matched and removed rule: %r", runtime.rules[i]
                        )
                        runtime.logic_interpreter.remove_rule(db_clause)
                        yield final_env
                        return
                else:
                    logger.info(
                        "RETRACT: Matched and removed clause: %r (using head match for fact-form retract)",
                        runtime.rules[i],
                    )
                    runtime.logic_interpreter.remove_rule(db_clause)
                    yield head_env
                    return
        logger.debug("RETRACT: No matching clause found for: %s", target_clause_struct)
        return


class AtEndOfStreamPredicate(BuiltinPredicate):
    """
    at_end_of_stream/0述語実装
    EOF状態を非破壊的に確認する
    """

    def __init__(self, *args):
        super().__init__(*args)
        if len(self.args) > 1:
            raise PrologError(
                f"at_end_of_stream takes 0-1 arguments, got {len(self.args)}"
            )

    def execute(
        self, runtime: "Runtime", env: BindingEnvironment
    ) -> Iterator[BindingEnvironment]:
        """メイン実行ロジック"""
        try:
            stream = self._get_target_stream(runtime, env)
            if stream.at_end_of_stream():
                yield env
        except Exception as e:
            if "not support" in str(e).lower():
                logger.warning("at_end_of_stream stream operation failed: %s", e)
                return
            else:
                logger.error(
                    "Unexpected error in at_end_of_stream: %s", e, exc_info=True
                )
                raise PrologError(f"at_end_of_stream execution failed: {e}") from e

    def _get_target_stream(self, runtime: "Runtime", env: BindingEnvironment):
        """対象ストリームの特定"""
        if len(self.args) == 0:
            unified_input = getattr(runtime.io_manager, "unified_input", None)
            if unified_input and isinstance(
                unified_input.input_handler, StreamInputHandler
            ):
                return unified_input.input_handler.stream
            raise PrologError("at_end_of_stream requires StreamInputHandler")
        else:
            raise NotImplementedError("Stream argument not yet supported")


class ListingPredicate(BuiltinPredicate):
    """
    listing/0述語実装
    知識ベース内の全ルール・事実を標準Prolog形式で出力
    """

    def __init__(self):
        super().__init__()

    def execute(
        self, runtime: "Runtime", env: BindingEnvironment
    ) -> Iterator[BindingEnvironment]:
        """メイン実行ロジック"""
        try:
            from ..util.formatters import PrologFormatter

            formatter = PrologFormatter(
                variable_mapper=getattr(runtime, "variable_mapper", None),
                functor_mapper=getattr(runtime, "functor_mapper", None),
            )
            formatted_output = formatter.format_rules_list(runtime.rules)
            for char in formatted_output:
                runtime.io_manager.write_char_to_current(char)
            yield env
        except Exception as e:
            logger.error("Error in listing/0: %s", e, exc_info=True)
            return


class ListingWithPredicatePredicate(BuiltinPredicate):
    """
    listing/1述語実装
    指定述語のルール・事実のみを標準Prolog形式で出力
    """

    def __init__(self, predicate_spec: PrologType):
        super().__init__(predicate_spec)

    def execute(
        self, runtime: "Runtime", env: BindingEnvironment
    ) -> Iterator[BindingEnvironment]:
        """メイン実行ロジック"""
        try:
            from ..util.formatters import PrologFormatter

            predicate_name, arity = self._parse_predicate_spec(
                self.args[0], env, runtime
            )
            if predicate_name is None:
                return
            formatter = PrologFormatter(
                variable_mapper=getattr(runtime, "variable_mapper", None),
                functor_mapper=getattr(runtime, "functor_mapper", None),
            )
            formatted_output = formatter.format_predicate_rules(
                runtime.rules, predicate_name, arity
            )
            for char in formatted_output:
                runtime.io_manager.write_char_to_current(char)
            yield env
        except Exception as e:
            logger.error("Error in listing/1: %s", e, exc_info=True)
            return

    def _parse_predicate_spec(
        self, spec: PrologType, env: BindingEnvironment, runtime: "Runtime"
    ) -> tuple:
        """
        述語指定を解析してname/arityを取得

        Args:
            spec: 述語指定（例: person/2）
            env: 環境
            runtime: Runtime

        Returns:
            (predicate_name, arity) または (None, None)
        """
        try:
            dereferenced_spec = runtime.logic_interpreter.dereference(spec, env)
            if isinstance(dereferenced_spec, Term):
                if (
                    isinstance(dereferenced_spec.functor, Atom)
                    and dereferenced_spec.functor.name == "/"
                    and (len(dereferenced_spec.args) == 2)
                ):
                    functor_arg = runtime.logic_interpreter.dereference(
                        dereferenced_spec.args[0], env
                    )
                    arity_arg = runtime.logic_interpreter.dereference(
                        dereferenced_spec.args[1], env
                    )
                    if isinstance(functor_arg, Atom):
                        predicate_name = functor_arg.name
                    else:
                        logger.warning(
                            "Invalid functor in predicate spec: %r", functor_arg
                        )
                        return (None, None)
                    if isinstance(arity_arg, Number) and arity_arg.value >= 0:
                        if float(arity_arg.value).is_integer():
                            arity = int(arity_arg.value)
                        else:
                            logger.warning(
                                "Invalid arity in predicate spec: %r", arity_arg
                            )
                            return (None, None)
                    else:
                        logger.warning("Invalid arity in predicate spec: %s", arity_arg)
                        return (None, None)
                    return (predicate_name, arity)
            logger.warning(
                "Invalid predicate specification format: %r", dereferenced_spec
            )
            return (None, None)
        except Exception as e:
            logger.warning("Failed to parse predicate spec %s: %s", spec, e)
            return (None, None)


class ExportFactsPredicate(BuiltinPredicate):
    """
    export_facts/2述語実装
    指定述語の事実データを外部形式でエクスポート
    """

    def __init__(self, predicate_spec: PrologType, file_spec: PrologType):
        super().__init__(predicate_spec, file_spec)

    def execute(
        self, runtime: "Runtime", env: BindingEnvironment
    ) -> Iterator[BindingEnvironment]:
        """メイン実行ロジック"""
        try:
            from ..util.data_exporter import DataExporter

            predicate_name, arity = self._parse_predicate_spec(
                self.args[0], env, runtime
            )
            if predicate_name is None:
                return
            file_spec = runtime.logic_interpreter.dereference(self.args[1], env)
            target_facts = self._extract_facts(
                runtime.rules, predicate_name, arity, runtime
            )
            exporter = DataExporter(runtime)
            success = exporter.export_facts(target_facts, file_spec)
            if success:
                yield env
            else:
                return
        except Exception as e:
            logger.error("Error in export_facts/2: %s", e, exc_info=True)
            return

    def _parse_predicate_spec(
        self, spec: PrologType, env: BindingEnvironment, runtime: "Runtime"
    ) -> tuple:
        """
        述語指定を解析してname/arityを取得（listing/1と同じ）

        Args:
            spec: 述語指定（例: person/2）
            env: 環境
            runtime: Runtime

        Returns:
            (predicate_name, arity) または (None, None)
        """
        try:
            dereferenced_spec = runtime.logic_interpreter.dereference(spec, env)
            if isinstance(dereferenced_spec, Term):
                if (
                    isinstance(dereferenced_spec.functor, Atom)
                    and dereferenced_spec.functor.name == "/"
                    and (len(dereferenced_spec.args) == 2)
                ):
                    functor_arg = runtime.logic_interpreter.dereference(
                        dereferenced_spec.args[0], env
                    )
                    arity_arg = runtime.logic_interpreter.dereference(
                        dereferenced_spec.args[1], env
                    )
                    if isinstance(functor_arg, Atom):
                        predicate_name = functor_arg.name
                    else:
                        logger.warning(
                            "Invalid functor in predicate spec: %r", functor_arg
                        )
                        return (None, None)
                    if isinstance(arity_arg, Number) and arity_arg.value >= 0:
                        if float(arity_arg.value).is_integer():
                            arity = int(arity_arg.value)
                        else:
                            logger.warning(
                                "Invalid arity in predicate spec: %r", arity_arg
                            )
                            return (None, None)
                    else:
                        logger.warning("Invalid arity in predicate spec: %s", arity_arg)
                        return (None, None)
                    return (predicate_name, arity)
            logger.warning(
                "Invalid predicate specification format: %r", dereferenced_spec
            )
            return (None, None)
        except Exception as e:
            logger.warning("Failed to parse predicate spec %s: %s", spec, e)
            return (None, None)

    def _extract_facts(
        self,
        rules: list[Rule | Fact],
        predicate_name: str,
        arity: int,
        runtime: "Runtime",
    ) -> list[Fact]:
        """
        指定述語の事実のみを抽出

        Args:
            rules: 全ルール・事実リスト
            predicate_name: 対象述語名
            arity: 対象アリティ
            runtime: Runtime

        Returns:
            マッチする事実のリスト
        """
        facts = []
        for rule in rules:
            try:
                if not isinstance(rule, Fact):
                    continue
                head = rule.head
                if self._matches_predicate(head, predicate_name, arity, runtime):
                    facts.append(rule)
            except Exception as e:
                logger.warning("Error checking rule %s: %s", rule, e)
                continue
        return facts

    def _matches_predicate(
        self, term: Term, predicate_name: str, arity: int, runtime: "Runtime"
    ) -> bool:
        """
        項が指定述語にマッチするかチェック

        Args:
            term: チェック対象の項
            predicate_name: 対象述語名
            arity: 対象アリティ
            runtime: Runtime

        Returns:
            マッチする場合True
        """
        try:
            if isinstance(term, Term):
                term_functor_name = self._get_functor_name(term.functor, runtime)
                term_arity = len(term.args)
            elif isinstance(term, Atom):
                term_functor_name = self._get_functor_name(term, runtime)
                term_arity = 0
            else:
                return False
            name_match = term_functor_name == predicate_name
            if (
                not name_match
                and hasattr(runtime, "functor_mapper")
                and runtime.functor_mapper
            ):
                mapped_predicate = runtime.functor_mapper.map_non_ascii_to_english(
                    predicate_name
                )
                name_match = term_functor_name == mapped_predicate
                if not name_match:
                    mapped_term = runtime.functor_mapper.map_english_to_non_ascii(
                        term_functor_name
                    )
                    name_match = mapped_term == predicate_name
            return name_match and term_arity == arity
        except Exception as e:
            logger.warning("Error matching predicate for term %s: %s", term, e)
            return False

    def _get_functor_name(self, functor: PrologType, runtime: "Runtime") -> str:
        """
        ファンクターから名前を取得

        Args:
            functor: ファンクター
            runtime: Runtime

        Returns:
            ファンクター名
        """
        if isinstance(functor, Atom):
            functor_name = functor.name
            if hasattr(runtime, "functor_mapper") and runtime.functor_mapper:
                original_name = runtime.functor_mapper.map_english_to_non_ascii(
                    functor_name
                )
                return original_name
            return functor_name
        else:
            return str(functor)


def _require_atom_name(
    term: PrologType, runtime: "Runtime", env: BindingEnvironment, label: str
) -> str:
    value = runtime.logic_interpreter.dereference(term, env)
    if not isinstance(value, Atom):
        raise PrologError(f"{label} must be an atom")
    return value.name


def _require_text_value(
    term: PrologType, runtime: "Runtime", env: BindingEnvironment, label: str
) -> str:
    value = runtime.logic_interpreter.dereference(term, env)
    if isinstance(value, Atom):
        return value.name
    if isinstance(value, String):
        return value.value
    raise PrologError(f"{label} must be an atom or string")


class PyRegisterPredicate(BuiltinPredicate):
    def __init__(self, name_arg: PrologType, path_arg: PrologType):
        super().__init__(name_arg, path_arg)

    def execute(
        self, runtime: "Runtime", env: BindingEnvironment
    ) -> Iterator[BindingEnvironment]:
        name = _require_atom_name(self.args[0], runtime, env, "py_register/2 name")
        path = _require_text_value(self.args[1], runtime, env, "py_register/2 path")
        runtime.register_python_script(name, path)
        yield env


class PyUnregisterPredicate(BuiltinPredicate):
    def __init__(self, name_arg: PrologType):
        super().__init__(name_arg)

    def execute(
        self, runtime: "Runtime", env: BindingEnvironment
    ) -> Iterator[BindingEnvironment]:
        name = _require_atom_name(self.args[0], runtime, env, "py_unregister/1 name")
        runtime.unregister_python_script(name)
        yield env


class PyRegisteredPredicate(BuiltinPredicate):
    def __init__(self, name_arg: PrologType, path_arg: PrologType):
        super().__init__(name_arg, path_arg)

    def execute(
        self, runtime: "Runtime", env: BindingEnvironment
    ) -> Iterator[BindingEnvironment]:
        for name, path in runtime.iter_registered_python_scripts():
            unified_name, env_after_name = runtime.logic_interpreter.unify(
                self.args[0], Atom(name), env
            )
            if not unified_name:
                continue
            unified_path, final_env = runtime.logic_interpreter.unify(
                self.args[1], Atom(path), env_after_name
            )
            if unified_path:
                yield final_env


class PyCallPredicate(BuiltinPredicate):
    def __init__(
        self,
        name_arg: PrologType,
        args_arg: PrologType,
        exit_arg: PrologType,
        stdout_arg: PrologType,
        stderr_arg: PrologType,
    ):
        super().__init__(name_arg, args_arg, exit_arg, stdout_arg, stderr_arg)

    def execute(
        self, runtime: "Runtime", env: BindingEnvironment
    ) -> Iterator[BindingEnvironment]:
        name = _require_atom_name(self.args[0], runtime, env, "py_call/5 name")
        resolved_args = runtime.logic_interpreter.deep_dereference_term(
            self.args[1], env
        )
        cli_args = normalize_cli_args(resolved_args)
        result = runtime.execute_python_script(name, cli_args)

        unified_exit, env_after_exit = runtime.logic_interpreter.unify(
            self.args[2], Number(result.exit_code), env
        )
        if not unified_exit:
            return
        unified_stdout, env_after_stdout = runtime.logic_interpreter.unify(
            self.args[3], Atom(result.stdout), env_after_exit
        )
        if not unified_stdout:
            return
        unified_stderr, final_env = runtime.logic_interpreter.unify(
            self.args[4], Atom(result.stderr), env_after_stdout
        )
        if unified_stderr:
            yield final_env


def create_get_char_predicate(arg: PrologType) -> BuiltinPredicate:
    """
    get_char/1述語のファクトリ関数

    統一入力システム対応版を返す。
    """
    from .io_predicates import GetCharPredicate as UnifiedGetCharPredicate

    return UnifiedGetCharPredicate(arg)


def create_read_line_predicate(arg: PrologType) -> BuiltinPredicate:
    """
    read_line/1述語のファクトリ関数

    統一入力システム対応版を返す。
    """
    from .io_predicates import ReadLinePredicate as UnifiedReadLinePredicate

    return UnifiedReadLinePredicate(arg)


def create_peek_char_predicate(arg: PrologType) -> BuiltinPredicate:
    """
    peek_char/1述語のファクトリ関数

    統一入力システム対応版を返す。
    """
    from .io_predicates import PeekCharPredicate as UnifiedPeekCharPredicate

    return UnifiedPeekCharPredicate(arg)
