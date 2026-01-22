from pyprolog.core.types import (
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
from pyprolog.core.binding_environment import BindingEnvironment
from pyprolog.core.errors import PrologError, CutException
from typing import TYPE_CHECKING, Tuple, Iterator, List, Union, Dict, Optional
import logging

if TYPE_CHECKING:
    from pyprolog.runtime.interpreter import Runtime

logger = logging.getLogger(__name__)


class LogicInterpreter:
    def __init__(self, rules: List[Union[Rule, Fact]], runtime: "Runtime"):
        self.rules: List[Union[Rule, Fact]] = rules
        self.runtime: "Runtime" = runtime
        self._unique_var_counter = 0
        self.rules_index: Dict[Tuple[str, int], List[Union[Rule, Fact]]] = {}
        self._rules_len = 0
        self._build_index()

    def _build_index(self) -> None:
        self.rules_index = {}
        for rule in self.rules:
            self._add_to_index(rule)
        self._rules_len = len(self.rules)

    def _refresh_index_if_needed(self) -> None:
        if len(self.rules) != self._rules_len:
            self._build_index()

    def _effective_head_for_index(self, entry: Union[Rule, Fact]) -> Optional[Term]:
        head = entry.head

        if (
            isinstance(entry, Fact)
            and isinstance(head, Term)
            and isinstance(head.functor, Atom)
            and head.functor.name == ":-"
            and len(head.args) == 2
        ):
            effective_head = head.args[0]
        else:
            effective_head = head

        if isinstance(effective_head, Atom):
            return Term(effective_head, [])
        if isinstance(effective_head, Term):
            return effective_head
        return None

    def _index_key_from_head(self, head: Optional[Term]) -> Optional[Tuple[str, int]]:
        if head is None:
            return None
        if not isinstance(head.functor, Atom):
            return None
        return (head.functor.name, len(head.args))

    def _add_to_index(self, entry: Union[Rule, Fact], position: str = "last") -> None:
        key = self._index_key_from_head(self._effective_head_for_index(entry))
        if key is None:
            return
        bucket = self.rules_index.setdefault(key, [])
        if position == "first":
            bucket.insert(0, entry)
        else:
            bucket.append(entry)

    def _remove_from_index(self, entry: Union[Rule, Fact]) -> None:
        key = self._index_key_from_head(self._effective_head_for_index(entry))
        if key is None:
            return
        bucket = self.rules_index.get(key)
        if not bucket:
            return
        for i, item in enumerate(bucket):
            if item is entry:
                del bucket[i]
                break
        if not bucket:
            self.rules_index.pop(key, None)

    def add_rule(self, entry: Union[Rule, Fact], position: str = "last") -> None:
        if position == "first":
            self.rules.insert(0, entry)
        else:
            self.rules.append(entry)
        self._add_to_index(entry, position=position)
        self._rules_len = len(self.rules)

    def remove_rule(self, entry: Union[Rule, Fact]) -> bool:
        for i, item in enumerate(self.rules):
            if item is entry:
                del self.rules[i]
                self._remove_from_index(entry)
                self._rules_len = len(self.rules)
                return True
        return False

    def replace_rules(self, rules: List[Union[Rule, Fact]]) -> None:
        self.rules = rules
        self._build_index()

    def _rename_variables(
        self,
        term_or_rule: Union[PrologType, Rule, Fact],
        env: Optional[BindingEnvironment] = None,
    ) -> Union[PrologType, Rule, Fact]:
        if env is None:
            env = BindingEnvironment()
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
                env.stats["term_allocs"] += 1
                env.stats["term_allocs_rename"] += 1
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
            # Allow body to be a Term, Atom, or Variable
            if not isinstance(renamed_body, (Term, Atom, Variable)):
                raise PrologError(
                    f"Internal error: Renamed body of Rule is not a Term, Atom, or Variable, got {type(renamed_body)}."
                )
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
        env.stats["unify_calls"] += 1
        logger.debug(
            "LOGIC_INTERP_UNIFY: Unifying term1: %s (type %s) with term2: %s (type %s) in env: %s",
            term1,
            type(term1).__name__,
            term2,
            type(term2).__name__,
            env.bindings,
        )
        current_env = env.copy()
        t1 = self.dereference(term1, current_env)
        t2 = self.dereference(term2, current_env)
        logger.debug(
            "LOGIC_INTERP_UNIFY: Dereferenced t1: %s (type %s), t2: %s (type %s)",
            t1,
            type(t1).__name__,
            t2,
            type(t2).__name__,
        )

        if t1 == t2:
            logger.debug(
                "LOGIC_INTERP_UNIFY: t1 == t2 (%s), returning True, env: %s",
                t1,
                current_env.bindings,
            )
            env.stats["unify_success_total"] += 1
            current_goal_key = env.stats.get("current_goal_key")
            if current_goal_key:
                env.stats["unify_success_by_pred"][current_goal_key] = (
                    env.stats["unify_success_by_pred"].get(current_goal_key, 0) + 1
                )
            return True, current_env

        if isinstance(t1, Variable):
            if (
                self.runtime.occurs_check_enabled
                and isinstance(t2, (Term, ListTerm))
                and self._occurs_check(t1, t2, current_env)
            ):
                logger.debug(
                    "LOGIC_INTERP_UNIFY: Occurs check failed for var %s in term %s, returning False",
                    t1,
                    t2,
                )
                env.stats["unify_fail_total"] += 1
                return False, env
            current_env.bind(t1.name, t2)
            logger.debug(
                "LOGIC_INTERP_UNIFY: Bound var %s to %s, returning True, env: %s",
                t1.name,
                t2,
                current_env.bindings,
            )
            env.stats["unify_success_total"] += 1
            current_goal_key = env.stats.get("current_goal_key")
            if current_goal_key:
                env.stats["unify_success_by_pred"][current_goal_key] = (
                    env.stats["unify_success_by_pred"].get(current_goal_key, 0) + 1
                )
            return True, current_env
        if isinstance(t2, Variable):
            if (
                self.runtime.occurs_check_enabled
                and isinstance(t1, (Term, ListTerm))
                and self._occurs_check(t2, t1, current_env)
            ):
                logger.debug(
                    "LOGIC_INTERP_UNIFY: Occurs check failed for var %s in term %s, returning False",
                    t2,
                    t1,
                )
                env.stats["unify_fail_total"] += 1
                return False, env
            current_env.bind(t2.name, t1)
            logger.debug(
                "LOGIC_INTERP_UNIFY: Bound var %s to %s, returning True, env: %s",
                t2.name,
                t1,
                current_env.bindings,
            )
            env.stats["unify_success_total"] += 1
            current_goal_key = env.stats.get("current_goal_key")
            if current_goal_key:
                env.stats["unify_success_by_pred"][current_goal_key] = (
                    env.stats["unify_success_by_pred"].get(current_goal_key, 0) + 1
                )
            return True, current_env

        if isinstance(t1, Atom) and isinstance(t2, Atom):
            success = t1.name == t2.name
            logger.debug(
                "LOGIC_INTERP_UNIFY: Atom vs Atom (%s vs %s), success: %s, returning env: %s",
                t1.name,
                t2.name,
                success,
                current_env.bindings,
            )
            return success, current_env
        if isinstance(t1, Number) and isinstance(t2, Number):
            success = t1.value == t2.value
            logger.debug(
                "LOGIC_INTERP_UNIFY: Number vs Number (%s vs %s), success: %s, returning env: %s",
                t1.value,
                t2.value,
                success,
                current_env.bindings,
            )
            return success, current_env
        if isinstance(t1, String) and isinstance(t2, String):
            success = t1.value == t2.value
            logger.debug(
                "LOGIC_INTERP_UNIFY: String vs String ('%s' vs '%s'), success: %s, returning env: %s",
                t1.value,
                t2.value,
                success,
                current_env.bindings,
            )
            return success, current_env

        if isinstance(t1, Term) and isinstance(t2, Term):
            if t1.functor == t2.functor and len(t1.args) == len(t2.args):
                logger.debug(
                    "LOGIC_INTERP_UNIFY: Term vs Term (%s/%s), unifying args.",
                    t1.functor,
                    len(t1.args),
                )
                temp_env = current_env.copy()
                all_args_unified = True
                for i in range(len(t1.args)):
                    unified, temp_env_after_arg_unify = self.unify(
                        t1.args[i], t2.args[i], temp_env
                    )
                    if not unified:
                        all_args_unified = False
                        logger.debug(
                            "LOGIC_INTERP_UNIFY: Arg #%s unification failed.",
                            i + 1,
                        )
                        break
                    temp_env = temp_env_after_arg_unify

                if all_args_unified:
                    logger.debug(
                        "LOGIC_INTERP_UNIFY: All args unified for %s/%s, returning True, env: %s",
                        t1.functor,
                        len(t1.args),
                        temp_env.bindings,
                    )
                    env.stats["unify_success_total"] += 1
                    current_goal_key = env.stats.get("current_goal_key")
                    if current_goal_key:
                        env.stats["unify_success_by_pred"][current_goal_key] = (
                            env.stats["unify_success_by_pred"].get(current_goal_key, 0)
                            + 1
                        )
                    return True, temp_env
                else:
                    logger.debug(
                        "LOGIC_INTERP_UNIFY: Arg unification failed for %s/%s, returning False, original env: %s",
                        t1.functor,
                        len(t1.args),
                        env.bindings,
                    )
                    env.stats["unify_fail_total"] += 1
                    return False, env
            else:
                logger.debug(
                    "LOGIC_INTERP_UNIFY: Term functor/arity mismatch (%s/%s vs %s/%s), returning False",
                    t1.functor,
                    len(t1.args),
                    t2.functor,
                    len(t2.args),
                )
                env.stats["unify_fail_total"] += 1
                return False, env

        logger.debug(
            "LOGIC_INTERP_UNIFY: Unification failed by falling through (t1 type: %s, t2 type: %s), returning False",
            type(t1),
            type(t2),
        )
        env.stats["unify_fail_total"] += 1
        return False, env

    def _occurs_check(
        self, var: Variable, term: PrologType, env: BindingEnvironment
    ) -> bool:
        env.stats["occurs_calls"] += 1
        term_deref = self.dereference(term, env)
        if var == term_deref:
            return True
        if isinstance(term_deref, Term):
            for arg in term_deref.args:
                if self._occurs_check(var, arg, env):
                    return True
        return False

    def dereference(self, term: PrologType, env: BindingEnvironment) -> PrologType:
        if not isinstance(term, Variable):
            return term
        env.stats["deref_calls"] += 1
        current: PrologType = term
        visited: List[str] = []
        visited_set = set()
        trail: List[str] = []
        while isinstance(current, Variable):
            var_name = current.name
            if var_name in visited_set:
                cycle = " -> ".join(visited + [var_name])
                raise PrologError(
                    f"Internal error: dereference cycle detected: {cycle}"
                )
            visited_set.add(var_name)
            visited.append(var_name)
            bound_value = env.get_value(var_name)
            if bound_value is None or bound_value == current:
                break
            env.stats["deref_steps"] += 1
            trail.append(var_name)
            current = bound_value
        if trail:
            for name in trail:
                env.bind(name, current)
        return current

    def deep_dereference_term(
        self, term: PrologType, env: BindingEnvironment
    ) -> PrologType:
        """
        Recursively dereferences all variables within a given term structure.
        """
        # First, dereference the term itself (if it's a variable)
        # This initial dereference is important if term is a variable bound to another variable, etc.
        current_term = self.dereference(term, env)

        if isinstance(current_term, Variable):
            # If it's still a variable after initial dereferencing, it means it's unbound in this context
            # or bound to itself (which dereference handles).
            return current_term
        elif isinstance(current_term, Term):
            # Recursively dereference arguments
            new_args = [
                self.deep_dereference_term(arg, env) for arg in current_term.args
            ]
            # Functor itself could theoretically be a variable if we allowed higher-order, but not currently.
            # Assuming functor is Atom or similar, not needing dereferencing here.
            env.stats["term_allocs"] += 1
            env.stats["term_allocs_deep_deref"] += 1
            return Term(current_term.functor, new_args)
        elif isinstance(current_term, ListTerm):
            # This type is not fully used/fleshed out in the current codebase snippets,
            # but providing a basic handling.
            new_elements = [
                self.deep_dereference_term(el, env) for el in current_term.elements
            ]
            new_tail = None
            if current_term.tail is not None:
                new_tail = self.deep_dereference_term(current_term.tail, env)
            return ListTerm(new_elements, new_tail)
        # Atoms, Numbers, Strings are returned as is
        return current_term

    def solve_goal(
        self, goal: PrologType, env: BindingEnvironment
    ) -> Iterator[BindingEnvironment]:
        env.stats["solve_calls_total"] += 1
        logger.debug(
            "LOGIC_INTERP: solve_goal called with goal: %s, rules count: %d",
            goal,
            len(self.rules),
        )
        actual_goal: Term
        if isinstance(goal, Atom):
            actual_goal = Term(goal, [])
            logger.debug(
                "LOGIC_INTERP: Goal %s (Atom) converted to Term: %s for solving.",
                goal,
                actual_goal,
            )
        elif isinstance(goal, Term):
            actual_goal = goal
        else:
            logger.debug(
                "Goal %s (type %s) is not callable, failing.", goal, type(goal)
            )
            return

        logger.debug(
            "LOGIC_INTERP: Attempting to solve actual_goal: %s with env: %s",
            actual_goal,
            env.bindings,
        )

        current_goal_key: Optional[Tuple[str, int]] = None
        if isinstance(actual_goal.functor, Atom):
            current_goal_key = (actual_goal.functor.name, len(actual_goal.args))
        previous_goal_key = env.stats.get("current_goal_key")
        env.stats["current_goal_key"] = current_goal_key
        if current_goal_key:
            env.stats["solve_calls_by_pred"][current_goal_key] = (
                env.stats["solve_calls_by_pred"].get(current_goal_key, 0) + 1
            )

        try:
            self._refresh_index_if_needed()

            # 未定義述語は existence_error を返す（builtin/演算子は execute 側で処理済み）
            if isinstance(
                actual_goal.functor, Atom
            ) and actual_goal.functor.name not in (
                "true",
                "fail",
            ):
                key = (actual_goal.functor.name, len(actual_goal.args))
                if key not in self.rules_index:
                    raise PrologError(
                        f"existence_error(procedure, {actual_goal.functor.name}/{len(actual_goal.args)})"
                    )

            # トレース: ゴール呼び出し記録
            if hasattr(self.runtime, "tracer") and self.runtime.tracer.enabled:
                self.runtime.tracer.record_call(actual_goal, env)

            if actual_goal.functor.name == "true" and not actual_goal.args:
                logger.debug("Goal %s is true, yielding current env.", actual_goal)
                # トレース: 成功記録
                if hasattr(self.runtime, "tracer") and self.runtime.tracer.enabled:
                    self.runtime.tracer.record_exit(actual_goal, env, Fact(actual_goal))
                yield env
                return
            elif actual_goal.functor.name == "fail" and not actual_goal.args:
                logger.debug("Goal %s is fail, returning.", actual_goal)
                # トレース: 失敗記録
                if hasattr(self.runtime, "tracer") and self.runtime.tracer.enabled:
                    self.runtime.tracer.record_fail(actual_goal)
                return

            # カットの特別扱いは Runtime.execute で行うので、ここでは不要
            # if actual_goal.functor.name == "!" and not actual_goal.args:
            #     logger.debug(f"Goal {actual_goal} is CUT (handled by Runtime), yielding current env.")
            #     yield env
            #     return

            candidate_entries: List[Union[Rule, Fact]]
            if isinstance(actual_goal.functor, Atom):
                key = (actual_goal.functor.name, len(actual_goal.args))
                candidate_entries = list(self.rules_index.get(key, []))
                if key in self.rules_index:
                    env.stats["index_hit_total"] += 1
                else:
                    env.stats["index_miss_total"] += 1
            else:
                candidate_entries = list(self.rules)

            env.stats["candidate_entries_scanned_total"] += len(candidate_entries)
            if current_goal_key:
                env.stats["candidate_entries_scanned_by_pred"][current_goal_key] = (
                    env.stats["candidate_entries_scanned_by_pred"].get(
                        current_goal_key, 0
                    )
                    + len(candidate_entries)
                )
            if env.stats["solve_calls_total"]:
                env.stats["avg_candidates_per_goal"] = (
                    env.stats["candidate_entries_scanned_total"]
                    / env.stats["solve_calls_total"]
                )

            for db_entry_idx, db_entry in enumerate(candidate_entries):
                logger.debug(
                    "LOGIC_INTERP: Trying rule/fact #%d: %s", db_entry_idx, db_entry
                )
                renamed_entry = self._rename_variables(db_entry, env)
                logger.debug("LOGIC_INTERP: Renamed entry: %s", renamed_entry)

                current_head: Term
                if isinstance(renamed_entry, Rule):
                    current_head = renamed_entry.head
                elif isinstance(renamed_entry, Fact):
                    current_head = renamed_entry.head
                else:
                    raise PrologError(
                        "Internal error: Renamed DB entry is not Rule or Fact."
                    )
                logger.debug(
                    "LOGIC_INTERP: Current head to unify against from db_entry: %s",
                    current_head,
                )

                # PATCH for potential parser issue where a rule H:-B might be stored as Fact(Term(':-', [H,B]))
                # In such a case, current_head (from renamed_entry.head) would be Term(':-', [H,B])
                effective_head = current_head
                is_rule_from_fact_structure = False
                rule_body_from_fact_structure = None

                if (
                    isinstance(renamed_entry, Fact)
                    and isinstance(current_head, Term)
                    and current_head.functor.name == ":-"
                    and len(current_head.args) == 2
                ):
                    logger.warning(
                        "LOGIC_INTERP (PATCH DETECTED): Fact's head is a ':-' term: %s. Treating as rule.",
                        current_head,
                    )
                    effective_head = current_head.args[0]  # The actual head H
                    rule_body_from_fact_structure = current_head.args[
                        1
                    ]  # The actual body B
                    is_rule_from_fact_structure = True

                unified, new_env_after_unify = self.unify(
                    actual_goal, effective_head, env
                )

                if unified:
                    if is_rule_from_fact_structure:
                        logger.debug(
                            "LOGIC_INTERP (PATCH USED): Unified %s with %s (from Fact). Solving body: %s",
                            actual_goal,
                            effective_head,
                            rule_body_from_fact_structure,
                        )
                        try:
                            yield from self.runtime.execute(
                                rule_body_from_fact_structure, new_env_after_unify
                            )
                        except CutException:
                            logger.debug(
                                "CutException propagated from patched rule body: %s. Re-raising.",
                                rule_body_from_fact_structure,
                            )
                            raise
                        except Exception as e:
                            # IOManager例外などの重要な例外は伝播
                            if "Input required" in str(e) or hasattr(e, "input_type"):
                                logger.debug(
                                    "Critical exception propagated from patched rule body: %s",
                                    e,
                                )
                                raise
                            # その他の例外もログ出力して伝播
                            logger.debug(
                                "Exception in patched rule body execution: %s", e
                            )
                            raise
                    elif isinstance(renamed_entry, Fact):  # Genuine Fact
                        logger.debug(
                            "LOGIC_INTERP: Unified Fact %s with %s. Yielding env: %s",
                            actual_goal,
                            effective_head,
                            new_env_after_unify.bindings,
                        )
                        # トレース: 事実による成功記録
                        if (
                            hasattr(self.runtime, "tracer")
                            and self.runtime.tracer.enabled
                        ):
                            self.runtime.tracer.record_exit(
                                actual_goal, new_env_after_unify, renamed_entry
                            )
                        yield new_env_after_unify
                    elif isinstance(renamed_entry, Rule):  # Properly parsed Rule
                        logger.debug(
                            "LOGIC_INTERP: Unified Rule Head %s with %s. Solving body: %s with env: %s",
                            actual_goal,
                            effective_head,
                            renamed_entry.body,
                            new_env_after_unify.bindings,
                        )
                        try:
                            yield from self.runtime.execute(
                                renamed_entry.body, new_env_after_unify
                            )
                        except CutException:
                            logger.debug(
                                "CutException propagated from rule body: %s. Re-raising.",
                                renamed_entry.body,
                            )
                            raise
                        except Exception as e:
                            # IOManager例外などの重要な例外は伝播
                            if "Input required" in str(e) or hasattr(e, "input_type"):
                                logger.debug(
                                    "Critical exception propagated from rule body: %s",
                                    e,
                                )
                                raise
                            # その他の例外もログ出力して伝播
                            logger.debug("Exception in rule body execution: %s", e)
                            raise

            # If we've iterated through all rules and no solution was yielded by this path,
            # it means this specific goal (actual_goal) could not be proven with the current database.
            # Standard Prolog would raise an existence_error if there are NO clauses for the predicate.
            # This check is simplified: if this solve_goal attempt yields nothing, and it's not 'true' or 'fail',
            # it implies the predicate is undefined or fails.
            # トレース: 最終的に失敗した場合の記録
            if hasattr(self.runtime, "tracer") and self.runtime.tracer.enabled:
                self.runtime.tracer.record_fail(actual_goal)

            logger.debug(
                "LOGIC_INTERP: Finished iterating DB for goal %s. No more (or no) solutions found from this path.",
                actual_goal,
            )
        finally:
            env.stats["current_goal_key"] = previous_goal_key

    def instantiate_term(self, term: PrologType, env: BindingEnvironment) -> PrologType:
        """
        Creates a deep copy of the term and then instantiates variables in
        that copy using the provided environment. Variables in the term
        that are not found in the environment remain as (copied) variables.
        """
        # Python's copy.deepcopy is essential here to ensure that the returned term
        # is independent of the original template and any structures within the binding environment,
        # especially if those structures might be modified by future unifications or dereferencing
        # in other branches of computation.
        import copy

        term_copy = copy.deepcopy(term)

        # Memoization helps handle shared subterms and cyclic structures correctly within the term_copy
        # during the substitution process. It ensures that each unique part of the copied term
        # is processed only once.
        memo = {}

        def _substitute_vars_in_copy(current_part: PrologType) -> PrologType:
            # If this exact object in the copied structure has been processed, return its substituted form.
            if id(current_part) in memo:
                return memo[id(current_part)]

            if isinstance(current_part, Variable):
                # Use deep_dereference_term to get the fully resolved value of this variable
                # according to the given solution environment 'env'.
                # This resolved value is what the variable from the template copy should become.
                # deep_dereference_term itself should handle complex cases like var bound to var bound to value.
                # The result of deep_dereference_term is the actual instantiated value.
                instantiated_value = self.deep_dereference_term(current_part, env)
                memo[id(current_part)] = instantiated_value
                return instantiated_value

            elif isinstance(current_part, Term):
                # For complex terms, we need to recursively instantiate their arguments.
                # Since term_copy is a deep copy, current_part is part of this copy.
                # We modify its args list in place with instantiated arguments.
                new_args = [_substitute_vars_in_copy(arg) for arg in current_part.args]
                current_part.args = new_args
                # Functor is an Atom, does not need substitution.
                memo[id(current_part)] = current_part
                return current_part

            # Atomic types (Atom, Number, String) are immutable and don't contain variables to substitute.
            # They are already correctly copied by deepcopy.
            memo[id(current_part)] = current_part
            return current_part

        return _substitute_vars_in_copy(term_copy)
