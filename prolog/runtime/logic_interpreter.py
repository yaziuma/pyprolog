from prolog.core.types import (
    Term,
    Variable,
    Atom,
    Number,
    Rule,
    Fact,
    PrologType,
    ListTerm,
    String,
)
from prolog.core.binding_environment import BindingEnvironment
from prolog.core.errors import PrologError
from typing import TYPE_CHECKING, Tuple, Iterator, List, Union, Dict
import logging

if TYPE_CHECKING:
    from prolog.runtime.interpreter import Runtime

logger = logging.getLogger(__name__)

class LogicInterpreter:
    def __init__(self, rules: List[Union[Rule, Fact]], runtime: "Runtime"):
        self.rules: List[Union[Rule, Fact]] = rules
        self.runtime: "Runtime" = runtime
        self._unique_var_counter = 0

    def _rename_variables(
        self, term_or_rule: Union[PrologType, Rule, Fact]
    ) -> Union[PrologType, Rule, Fact]:
        self._unique_var_counter += 1
        mapping: Dict[str, Variable] = {}

        def rename_recursive(current_term: PrologType) -> PrologType:
            if isinstance(current_term, Variable):
                if current_term.name not in mapping:
                    new_name = f"_V{self._unique_var_counter}_{current_term.name}"
                    mapping[current_term.name] = Variable(new_name)
                return mapping[current_term.name]
            elif isinstance(current_term, Term):
                new_args = [rename_recursive(arg) for arg in current_term.args]
                return Term(current_term.functor, new_args)
            elif isinstance(current_term, ListTerm):
                new_elements = [rename_recursive(el) for el in current_term.elements]
                new_tail_val = current_term.tail
                renamed_tail_val = (
                    rename_recursive(new_tail_val) if new_tail_val is not None else None
                )
                if not (
                    isinstance(renamed_tail_val, (Variable, Atom, ListTerm))
                    or renamed_tail_val is None
                ):
                    raise PrologError(
                        f"Internal error: Renamed tail of ListTerm is not a valid type: {type(renamed_tail_val)}"
                    )
                return ListTerm(new_elements, renamed_tail_val)
            return current_term

        if isinstance(term_or_rule, Rule):
            renamed_head = rename_recursive(term_or_rule.head)
            renamed_body = rename_recursive(term_or_rule.body)
            if not isinstance(renamed_head, Term):
                raise PrologError("Internal error: Renamed head of Rule is not a Term.")
            if not isinstance(renamed_body, (Term, Atom)):
                raise PrologError(f"Internal error: Renamed body of Rule is not a Term or Atom, got {type(renamed_body)}.")
            return Rule(renamed_head, renamed_body)
        elif isinstance(term_or_rule, Fact):
            renamed_head = rename_recursive(term_or_rule.head)
            if not isinstance(renamed_head, Term):
                raise PrologError("Internal error: Renamed head of Fact is not a Term.")
            return Fact(renamed_head)
        else:
            return rename_recursive(term_or_rule)

    def unify(
        self, term1: PrologType, term2: PrologType, env: BindingEnvironment
    ) -> Tuple[bool, BindingEnvironment]:
        logger.critical(f"LOGIC_INTERP_UNIFY: Unifying term1: {term1} (type {type(term1)}) with term2: {term2} (type {type(term2)}) in env: {env.bindings}")
        current_env = env.copy()
        t1 = self.dereference(term1, current_env)
        t2 = self.dereference(term2, current_env)
        logger.debug(f"LOGIC_INTERP_UNIFY: Dereferenced t1: {t1} (type {type(t1)}), t2: {t2} (type {type(t2)})")

        if t1 == t2:
            logger.critical(f"LOGIC_INTERP_UNIFY: t1 == t2 ({t1}), returning True, env: {current_env.bindings}")
            return True, current_env

        if isinstance(t1, Variable):
            if self._occurs_check(t1, t2, current_env):
                logger.critical(f"LOGIC_INTERP_UNIFY: Occurs check failed for var {t1} in term {t2}, returning False")
                return False, env
            current_env.bind(t1.name, t2)
            logger.critical(f"LOGIC_INTERP_UNIFY: Bound var {t1.name} to {t2}, returning True, env: {current_env.bindings}")
            return True, current_env
        if isinstance(t2, Variable):
            if self._occurs_check(t2, t1, current_env):
                logger.critical(f"LOGIC_INTERP_UNIFY: Occurs check failed for var {t2} in term {t1}, returning False")
                return False, env
            current_env.bind(t2.name, t1)
            logger.critical(f"LOGIC_INTERP_UNIFY: Bound var {t2.name} to {t1}, returning True, env: {current_env.bindings}")
            return True, current_env

        if isinstance(t1, Atom) and isinstance(t2, Atom):
            success = t1.name == t2.name
            logger.critical(f"LOGIC_INTERP_UNIFY: Atom vs Atom ({t1.name} vs {t2.name}), success: {success}, returning env: {current_env.bindings}")
            return success, current_env
        if isinstance(t1, Number) and isinstance(t2, Number):
            success = t1.value == t2.value
            logger.critical(f"LOGIC_INTERP_UNIFY: Number vs Number ({t1.value} vs {t2.value}), success: {success}, returning env: {current_env.bindings}")
            return success, current_env
        if isinstance(t1, String) and isinstance(t2, String):
            success = t1.value == t2.value
            logger.critical(f"LOGIC_INTERP_UNIFY: String vs String ('{t1.value}' vs '{t2.value}'), success: {success}, returning env: {current_env.bindings}")
            return success, current_env

        if isinstance(t1, Term) and isinstance(t2, Term):
            if t1.functor == t2.functor and len(t1.args) == len(t2.args):
                logger.debug(f"LOGIC_INTERP_UNIFY: Term vs Term ({t1.functor}/{len(t1.args)}), unifying args.")
                temp_env = current_env.copy()
                all_args_unified = True
                for i in range(len(t1.args)):
                    unified, temp_env_after_arg_unify = self.unify(
                        t1.args[i], t2.args[i], temp_env
                    )
                    if not unified:
                        all_args_unified = False
                        logger.debug(f"LOGIC_INTERP_UNIFY: Arg #{i+1} unification failed.")
                        break
                    temp_env = temp_env_after_arg_unify

                if all_args_unified:
                    logger.critical(f"LOGIC_INTERP_UNIFY: All args unified for {t1.functor}/{len(t1.args)}, returning True, env: {temp_env.bindings}")
                    return True, temp_env
                else:
                    logger.critical(f"LOGIC_INTERP_UNIFY: Arg unification failed for {t1.functor}/{len(t1.args)}, returning False, original env: {env.bindings}")
                    return False, env
            else:
                logger.critical(f"LOGIC_INTERP_UNIFY: Term functor/arity mismatch ({t1.functor}/{len(t1.args)} vs {t2.functor}/{len(t2.args)}), returning False")
                return False, env

        logger.critical(f"LOGIC_INTERP_UNIFY: Unification failed by falling through (t1 type: {type(t1)}, t2 type: {type(t2)}), returning False")
        return False, env

    def _occurs_check(
        self, var: Variable, term: PrologType, env: BindingEnvironment
    ) -> bool:
        term_deref = self.dereference(term, env)
        if var == term_deref:
            return True
        if isinstance(term_deref, Term):
            for arg in term_deref.args:
                if self._occurs_check(var, arg, env):
                    return True
        return False

    def dereference(self, term: PrologType, env: BindingEnvironment) -> PrologType:
        if isinstance(term, Variable):
            bound_value = env.get_value(term.name)
            if bound_value is not None and bound_value != term:
                return self.dereference(bound_value, env)
        return term

    def solve_goal(
        self, goal: PrologType, env: BindingEnvironment
    ) -> Iterator[BindingEnvironment]:
        logger.critical(f"LOGIC_INTERP: solve_goal called with goal: {goal}, rules in DB: {[str(r) for r in self.rules]}")
        actual_goal: Term
        if isinstance(goal, Atom):
            actual_goal = Term(goal, [])
            logger.critical(f"LOGIC_INTERP: Goal {goal} (Atom) converted to Term: {actual_goal} for solving.")
        elif isinstance(goal, Term):
            actual_goal = goal
        else:
            logger.debug(f"Goal {goal} (type {type(goal)}) is not callable, failing.")
            return

        logger.critical(f"LOGIC_INTERP: Attempting to solve actual_goal: {actual_goal} with env: {env.bindings}")

        if actual_goal.functor.name == "true" and not actual_goal.args:
            logger.critical(f"Goal {actual_goal} is true, yielding current env.")
            yield env
            return
        elif actual_goal.functor.name == "fail" and not actual_goal.args:
            logger.critical(f"Goal {actual_goal} is fail, returning.")
            return

        # カットの特別扱いは Runtime.execute で行うので、ここでは不要
        # if actual_goal.functor.name == "!" and not actual_goal.args:
        #     logger.debug(f"Goal {actual_goal} is CUT (handled by Runtime), yielding current env.")
        #     yield env
        #     return

        for db_entry_idx, db_entry in enumerate(self.rules):
            logger.debug(f"LOGIC_INTERP: Trying rule/fact #{db_entry_idx}: {db_entry}")
            renamed_entry = self._rename_variables(db_entry)
            logger.debug(f"LOGIC_INTERP: Renamed entry: {renamed_entry}")

            current_head: Term
            if isinstance(renamed_entry, Rule):
                current_head = renamed_entry.head
            elif isinstance(renamed_entry, Fact):
                current_head = renamed_entry.head
            else:
                raise PrologError("Internal error: Renamed DB entry is not Rule or Fact.")
            logger.debug(f"LOGIC_INTERP: Current head to unify against: {current_head}")

            unified, new_env_after_unify = self.unify(actual_goal, current_head, env)
            # logger.debug(f"LOGIC_INTERP: Unification result: {unified}, new_env: {new_env_after_unify.bindings if unified else 'N/A'}") # Redundant due to unify logs

            if unified:
                if isinstance(renamed_entry, Fact):
                    logger.critical(f"LOGIC_INTERP: Unified Fact {actual_goal} with {current_head}. Yielding env: {new_env_after_unify.bindings}")
                    yield new_env_after_unify
                elif isinstance(renamed_entry, Rule):
                    logger.critical(f"LOGIC_INTERP: Unified Rule Head {actual_goal} with {current_head}. Solving body: {renamed_entry.body} with env: {new_env_after_unify.bindings}")
                    try:
                        yield from self.runtime.execute(renamed_entry.body, new_env_after_unify)
                    except CutException: # ルールボディ内でカットが発生した場合、このルールの選択肢をカット
                        logger.debug(f"CutException propagated from rule body: {renamed_entry.body}. Re-raising.")
                        raise
        logger.debug(f"LOGIC_INTERP: Finished iterating DB for goal {actual_goal}. No more (or no) solutions found from this path.")
