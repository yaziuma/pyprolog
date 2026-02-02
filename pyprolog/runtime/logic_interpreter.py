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
from typing import TYPE_CHECKING, Tuple, Iterator, List, Union, Dict, Optional, Set
import logging

if TYPE_CHECKING:
    from pyprolog.runtime.interpreter import Runtime

logger = logging.getLogger(__name__)
_DEBUG = logger.isEnabledFor(logging.DEBUG)


class LogicInterpreter:
    def __init__(self, rules: List[Union[Rule, Fact]], runtime: "Runtime"):
        self.rules: List[Union[Rule, Fact]] = rules
        self.runtime: "Runtime" = runtime
        self._unique_var_counter = 0
        self.rules_by_pred: Dict[Tuple[str, int], List[Union[Rule, Fact]]] = {}
        self.rules_by_pred_arg0: Dict[
            Tuple[str, int, int, Union[str, int, float]], List[Union[Rule, Fact]]
        ] = {}
        self.rules_index: Dict[Tuple[str, int], List[Union[Rule, Fact]]] = {}
        self._rules_len = 0
        self.empty_list: List[Union[Rule, Fact]] = []
        # Dynamic directive support: two-registry approach
        self.dynamic_registry: Set[Tuple[str, int]] = set()  # Declared predicates (persistent)
        self.defined_registry: Set[Tuple[str, int]] = set()  # Currently defined predicates (removed on retract)
        self._build_index()

    def apply_dynamic(self, name: str, arity: int) -> None:
        """Apply dynamic directive: mark predicate as declared.

        Args:
            name: Predicate name
            arity: Predicate arity
        """
        key = (name, arity)
        self.dynamic_registry.add(key)
        logger.debug("Applied dynamic directive: %s/%d", name, arity)

    def _build_index(self) -> None:
        self.rules_by_pred = {}
        self.rules_by_pred_arg0 = {}
        # Also rebuild defined_registry from current rules
        self.defined_registry.clear()
        for rule in self.rules:
            self._add_to_index(rule)
            # Update defined_registry
            head = rule.head
            if isinstance(head, Term) and isinstance(head.functor, Atom):
                key = (head.functor.name, len(head.args))
                self.defined_registry.add(key)
            elif isinstance(head, Atom):
                key = (head.name, 0)
                self.defined_registry.add(key)
        self.rules_index = self.rules_by_pred
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

    def _arg0_index_key_from_head(
        self, head: Optional[Term]
    ) -> Optional[Tuple[str, int, int, Union[str, int, float]]]:
        if head is None or not isinstance(head.functor, Atom):
            return None
        if not head.args:
            return None
        arg0 = head.args[0]
        if isinstance(arg0, Atom):
            return (head.functor.name, len(head.args), 1, arg0.name)
        if isinstance(arg0, Number):
            return (head.functor.name, len(head.args), 2, arg0.value)
        if isinstance(arg0, String):
            return (head.functor.name, len(head.args), 3, arg0.value)
        return None

    def _add_to_index(self, entry: Union[Rule, Fact], position: str = "last") -> None:
        effective_head = self._effective_head_for_index(entry)
        key = self._index_key_from_head(effective_head)
        if key is None:
            return
        bucket = self.rules_by_pred.setdefault(key, [])
        if position == "first":
            bucket.insert(0, entry)
        else:
            bucket.append(entry)
        arg0_key = self._arg0_index_key_from_head(effective_head)
        if arg0_key is not None:
            arg0_bucket = self.rules_by_pred_arg0.setdefault(arg0_key, [])
            if position == "first":
                arg0_bucket.insert(0, entry)
            else:
                arg0_bucket.append(entry)

    def _remove_from_index(self, entry: Union[Rule, Fact]) -> None:
        effective_head = self._effective_head_for_index(entry)
        key = self._index_key_from_head(effective_head)
        if key is None:
            return
        bucket = self.rules_by_pred.get(key)
        if not bucket:
            bucket = []
        for i, item in enumerate(bucket):
            if item is entry:
                del bucket[i]
                break
        if not bucket:
            self.rules_by_pred.pop(key, None)
        arg0_key = self._arg0_index_key_from_head(effective_head)
        if arg0_key is None:
            return
        arg0_bucket = self.rules_by_pred_arg0.get(arg0_key)
        if not arg0_bucket:
            return
        for i, item in enumerate(arg0_bucket):
            if item is entry:
                del arg0_bucket[i]
                break
        if not arg0_bucket:
            self.rules_by_pred_arg0.pop(arg0_key, None)

    def get_candidate_clauses(
        self, goal: Term, env: BindingEnvironment
    ) -> Tuple[List[Union[Rule, Fact]], bool]:
        if not isinstance(goal.functor, Atom):
            return self.rules, False
        pred = goal.functor.name
        arity = len(goal.args)
        key = (pred, arity)
        primary_candidates = self.rules_by_pred.get(key)
        if not primary_candidates:
            return self.empty_list, False
        if arity == 0:
            return primary_candidates, False
        arg0 = self.dereference(goal.args[0], env)
        if isinstance(arg0, Atom):
            arg0_key = (pred, arity, 1, arg0.name)
        elif isinstance(arg0, Number):
            arg0_key = (pred, arity, 2, arg0.value)
        elif isinstance(arg0, String):
            arg0_key = (pred, arity, 3, arg0.value)
        else:
            arg0_key = None
        if arg0_key is not None:
            secondary_candidates = self.rules_by_pred_arg0.get(arg0_key)
            if secondary_candidates is not None:
                return secondary_candidates, True
        return primary_candidates, False

    def add_rule(self, entry: Union[Rule, Fact], position: str = "last") -> None:
        # Update defined_registry before adding rule
        head = entry.head
        if isinstance(head, Term) and isinstance(head.functor, Atom):
            key = (head.functor.name, len(head.args))
            self.defined_registry.add(key)
        elif isinstance(head, Atom):
            key = (head.name, 0)
            self.defined_registry.add(key)

        if position == "first":
            self.rules.insert(0, entry)
        else:
            self.rules.append(entry)
        self._add_to_index(entry, position=position)
        self._rules_len = len(self.rules)

    def remove_rule(self, entry: Union[Rule, Fact]) -> bool:
        # Extract predicate key before removal
        head = entry.head
        key = None
        if isinstance(head, Term) and isinstance(head.functor, Atom):
            key = (head.functor.name, len(head.args))
        elif isinstance(head, Atom):
            key = (head.name, 0)

        for i, item in enumerate(self.rules):
            if item is entry:
                del self.rules[i]
                self._remove_from_index(entry)
                self._rules_len = len(self.rules)

                # Check if this was the last clause for this predicate
                if key and key not in self.rules_by_pred:
                    # No clauses remain, remove from defined_registry
                    self.defined_registry.discard(key)
                    logger.debug("Removed %s/%d from defined_registry (no clauses remain)", key[0], key[1])

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

        def rename_var(v: Variable) -> Variable:
            # 現行仕様維持：同名Varは同じ新Varへ
            if v.name not in mapping:
                new_name = f"_V{self._unique_var_counter}_{v.name}"
                mapping[v.name] = Variable(new_name)
            return mapping[v.name]

        def rename_iter(root: PrologType) -> PrologType:
            # post-order 再構築（子→親）を明示スタックでやる
            out: Dict[int, PrologType] = {}
            stack: list[tuple[PrologType, bool]] = [(root, False)]

            while stack:
                node, expanded = stack.pop()
                nid = id(node)

                if nid in out:
                    continue

                # Variable
                if isinstance(node, Variable):
                    out[nid] = rename_var(node)
                    continue

                # Term
                if isinstance(node, Term):
                    if not expanded:
                        stack.append((node, True))
                        for arg in reversed(node.args):
                            stack.append((arg, False))
                    else:
                        new_args = [out[id(arg)] for arg in node.args]
                        if env.stats_enabled:
                            env.stats["term_allocs"] += 1
                            env.stats["term_allocs_rename"] += 1
                        out[nid] = Term(node.functor, new_args)
                    continue

                # ListTerm
                if isinstance(node, ListTerm):
                    if not expanded:
                        stack.append((node, True))
                        if node.tail is not None:
                            stack.append((node.tail, False))
                        for el in reversed(node.elements):
                            stack.append((el, False))
                    else:
                        new_elements = [out[id(el)] for el in node.elements]
                        renamed_tail_val = out[id(node.tail)] if node.tail is not None else None

                        # 現行の型制約維持
                        if not (
                            isinstance(renamed_tail_val, (Variable, Atom, ListTerm))
                            or renamed_tail_val is None
                        ):
                            raise PrologError(
                                "Internal error: Renamed tail of ListTerm is not a valid type: "
                                f"{type(renamed_tail_val)}"
                            )

                        out[nid] = ListTerm(new_elements, renamed_tail_val)
                    continue

                # Atom/Number/String などはそのまま
                out[nid] = node

            return out[id(root)]

        if isinstance(term_or_rule, Rule):
            renamed_head = rename_iter(term_or_rule.head)
            renamed_body = rename_iter(term_or_rule.body)

            if not isinstance(renamed_head, Term):
                raise PrologError("Internal error: Renamed head of Rule is not a Term.")
            if not isinstance(renamed_body, (Term, Atom, Variable)):
                raise PrologError(
                    "Internal error: Renamed body of Rule is not a Term, Atom, or Variable, "
                    f"got {type(renamed_body)}."
                )
            return Rule(renamed_head, renamed_body)

        elif isinstance(term_or_rule, Fact):
            renamed_head = rename_iter(term_or_rule.head)
            if not isinstance(renamed_head, Term):
                raise PrologError("Internal error: Renamed head of Fact is not a Term.")
            return Fact(renamed_head)

        else:
            return rename_iter(term_or_rule)

    def unify(
        self, term1: PrologType, term2: PrologType, env: BindingEnvironment
    ) -> Tuple[bool, BindingEnvironment]:
        current_env = env.copy()
        deref = self.dereference
        occurs_enabled = self.runtime.occurs_check_enabled
        bind = current_env.bind
        a_stack = [term1]
        b_stack = [term2]
        success_marker = object()

        def record_success() -> None:
            if env.stats_enabled:
                env.stats["unify_success_total"] += 1
                current_goal_key = env.stats.get("current_goal_key")
                if current_goal_key:
                    env.stats["unify_success_by_pred"][current_goal_key] = (
                        env.stats["unify_success_by_pred"].get(current_goal_key, 0) + 1
                    )

        def record_fail() -> None:
            if env.stats_enabled:
                env.stats["unify_fail_total"] += 1

        while a_stack:
            t1 = a_stack.pop()
            t2 = b_stack.pop()
            if t1 is success_marker:
                record_success()
                continue
            if env.stats_enabled:
                env.stats["unify_calls"] += 1
            t1 = deref(t1, current_env)
            t2 = deref(t2, current_env)
            if _DEBUG:
                logger.debug(
                    "UNIFY: %r (%s) with %r (%s)",
                    t1,
                    type(t1).__name__,
                    t2,
                    type(t2).__name__,
                )

            if t1 is t2 or t1 == t2:
                record_success()
                continue

            if isinstance(t1, Variable):
                if (
                    occurs_enabled
                    and isinstance(t2, (Term, ListTerm))
                    and self._occurs_check(t1, t2, current_env)
                ):
                    record_fail()
                    return False, env
                bind(t1.name, t2)
                record_success()
                continue
            if isinstance(t2, Variable):
                if (
                    occurs_enabled
                    and isinstance(t1, (Term, ListTerm))
                    and self._occurs_check(t2, t1, current_env)
                ):
                    record_fail()
                    return False, env
                bind(t2.name, t1)
                record_success()
                continue

            if isinstance(t1, Atom) and isinstance(t2, Atom):
                record_fail()
                return False, env
            if isinstance(t1, Number) and isinstance(t2, Number):
                record_fail()
                return False, env
            if isinstance(t1, String) and isinstance(t2, String):
                record_fail()
                return False, env

            if isinstance(t1, Term) and isinstance(t2, Term):
                if t1.functor != t2.functor or len(t1.args) != len(t2.args):
                    record_fail()
                    return False, env
                a_stack.append(success_marker)
                b_stack.append(success_marker)
                for i in range(len(t1.args) - 1, -1, -1):
                    a_stack.append(t1.args[i])
                    b_stack.append(t2.args[i])
                continue

            record_fail()
            return False, env

        return True, current_env

    def _occurs_check(
        self,
        var: Variable,
        term: PrologType,
        env: BindingEnvironment,
        seen: Optional[Set[int]] = None,
    ) -> bool:
        """
        Iterative occurs check using explicit stack (DFS).

        This method checks if a variable occurs in a term, which prevents
        infinite unification loops (e.g., X = f(X)).

        CRITICAL: Correct order to avoid missing bound variables:
        1. Dereference first (resolve variable bindings)
        2. Check if target variable (early return)
        3. Check seen AFTER deref (identity-based: id() only)
        4. Expand children to stack

        Args:
            var: Target variable to search for
            term: Term to search in
            env: Binding environment
            seen: Set of already-visited term IDs (identity-based)

        Returns:
            True if var occurs in term, False otherwise
        """
        if seen is None:
            seen = set()

        stack: list[PrologType] = [term]
        deref = self.dereference  # Local binding optimization

        while stack:
            # Step 1: Dereference FIRST (resolve any variable bindings)
            current = deref(stack.pop(), env)

            # Step 2: Check if target variable (early return for efficiency)
            if isinstance(current, Variable):
                if current == var:
                    return True
                continue

            # Step 3 & 4: Check seen AFTER deref, then expand children
            if isinstance(current, Term):
                term_id = id(current)  # Identity-based (not structural equality)
                if term_id in seen:
                    continue  # Already visited, skip
                seen.add(term_id)
                # Push args in reverse order to maintain DFS order (same as recursion)
                for i in range(len(current.args) - 1, -1, -1):
                    stack.append(current.args[i])
                continue

            if isinstance(current, ListTerm):
                term_id = id(current)  # Identity-based (not structural equality)
                if term_id in seen:
                    continue  # Already visited, skip
                seen.add(term_id)
                # Push tail first (processed last), then elements in reverse
                # IMPORTANT: Always push tail to handle edge cases
                # (variables, improper lists, circular references)
                if current.tail is not None:
                    stack.append(current.tail)
                for i in range(len(current.elements) - 1, -1, -1):
                    stack.append(current.elements[i])
                continue

        return False

    def dereference(self, term: PrologType, env: BindingEnvironment) -> PrologType:
        if not isinstance(term, Variable):
            return term
        if env.stats_enabled:
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
            if env.stats_enabled:
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
            if env.stats_enabled:
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
        if env.stats_enabled:
            env.stats["solve_calls_total"] += 1
        actual_goal: Term
        if isinstance(goal, Atom):
            actual_goal = Term(goal, [])
        elif isinstance(goal, Term):
            actual_goal = goal
        else:
            return

        current_goal_key: Optional[Tuple[str, int]] = None
        if isinstance(actual_goal.functor, Atom):
            current_goal_key = (actual_goal.functor.name, len(actual_goal.args))
        if env.stats_enabled:
            previous_goal_key = env.stats.get("current_goal_key")
            env.stats["current_goal_key"] = current_goal_key
            if current_goal_key:
                env.stats["solve_calls_by_pred"][current_goal_key] = (
                    env.stats["solve_calls_by_pred"].get(current_goal_key, 0) + 1
                )
        else:
            previous_goal_key = None

        try:
            self._refresh_index_if_needed()

            # Existence check: 2-registry approach
            # Step 1: true/fail special case (handled below)
            # Step 2 & 3: Check if predicate exists in either registry
            if isinstance(
                actual_goal.functor, Atom
            ) and actual_goal.functor.name not in (
                "true",
                "fail",
            ):
                key = (actual_goal.functor.name, len(actual_goal.args))

                # Step 2: Check registries (declared or has clauses)
                if key not in self.defined_registry and key not in self.dynamic_registry:
                    raise PrologError(
                        f"existence_error(procedure, {actual_goal.functor.name}/{len(actual_goal.args)})"
                    )

                # Step 3: Check clause count
                if key not in self.rules_by_pred or not self.rules_by_pred[key]:
                    # Predicate exists (in registry) but has no clauses → fail
                    if hasattr(self.runtime, "tracer") and self.runtime.tracer.enabled:
                        self.runtime.tracer.record_fail(actual_goal)
                    return  # Fail silently (no solutions)

            # トレース: ゴール呼び出し記録
            if hasattr(self.runtime, "tracer") and self.runtime.tracer.enabled:
                self.runtime.tracer.record_call(actual_goal, env)

            if actual_goal.functor.name == "true" and not actual_goal.args:
                # トレース: 成功記録
                if hasattr(self.runtime, "tracer") and self.runtime.tracer.enabled:
                    self.runtime.tracer.record_exit(actual_goal, env, Fact(actual_goal))
                yield env
                return
            elif actual_goal.functor.name == "fail" and not actual_goal.args:
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
                candidate_entries, used_secondary_index = self.get_candidate_clauses(
                    actual_goal, env
                )
                if env.stats_enabled:
                    if used_secondary_index:
                        env.stats["index2_hit"] += 1
                    else:
                        env.stats["index2_miss_or_fallback"] += 1
            else:
                candidate_entries = self.rules

            if env.stats_enabled:
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

            if _DEBUG:
                logger.debug(
                    "SOLVE: %r with %d candidates", actual_goal, len(candidate_entries)
                )

            for db_entry in candidate_entries:
                renamed_entry = self._rename_variables(db_entry, env)

                current_head: Term
                if isinstance(renamed_entry, Rule):
                    current_head = renamed_entry.head
                elif isinstance(renamed_entry, Fact):
                    current_head = renamed_entry.head
                else:
                    raise PrologError(
                        "Internal error: Renamed DB entry is not Rule or Fact."
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
                        try:
                            yield from self.runtime.execute(
                                rule_body_from_fact_structure, new_env_after_unify
                            )
                        except CutException:
                            raise
                        except Exception as e:
                            # IOManager例外などの重要な例外は伝播
                            if "Input required" in str(e) or hasattr(e, "input_type"):
                                raise
                            raise
                    elif isinstance(renamed_entry, Fact):  # Genuine Fact
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
                        try:
                            yield from self.runtime.execute(
                                renamed_entry.body, new_env_after_unify
                            )
                        except CutException:
                            raise
                        except Exception as e:
                            # IOManager例外などの重要な例外は伝播
                            if "Input required" in str(e) or hasattr(e, "input_type"):
                                raise
                            raise

            # トレース: 最終的に失敗した場合の記録
            if hasattr(self.runtime, "tracer") and self.runtime.tracer.enabled:
                self.runtime.tracer.record_fail(actual_goal)
        finally:
            if env.stats_enabled:
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
