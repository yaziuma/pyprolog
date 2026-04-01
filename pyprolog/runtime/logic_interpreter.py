import logging
from collections.abc import Iterator
from typing import TYPE_CHECKING

from pyprolog.core.binding_environment import BindingEnvironment
from pyprolog.core.errors import CutException, PrologError
from pyprolog.core.types import (
    Atom,
    Fact,
    ListTerm,
    Number,
    PrologType,
    Rule,
    String,
    Term,
    Variable,
)
from pyprolog.runtime.execution_frames import (
    DisjunctionFrame,
    GoalFrame,
    NegationFrame,
    PushFrame,
    YieldEnv,
)

if TYPE_CHECKING:
    from pyprolog.runtime.interpreter import Runtime

logger = logging.getLogger(__name__)
_DEBUG = logger.isEnabledFor(logging.DEBUG)


class LogicInterpreter:
    def __init__(self, rules: list[Rule | Fact], runtime: "Runtime"):
        self.rules: list[Rule | Fact] = rules
        self.runtime: Runtime = runtime
        self._unique_var_counter = 0
        self.rules_by_pred: dict[tuple[str, int], list[Rule | Fact]] = {}
        self.rules_by_pred_arg0: dict[
            tuple[str, int, int, str | int | float], list[Rule | Fact]
        ] = {}
        self.rules_index: dict[tuple[str, int], list[Rule | Fact]] = {}
        self._rules_len = 0
        self.empty_list: list[Rule | Fact] = []
        # Dynamic directive support: two-registry approach
        self.dynamic_registry: set[tuple[str, int]] = (
            set()
        )  # Declared predicates (persistent)
        self.defined_registry: set[tuple[str, int]] = (
            set()
        )  # Currently defined predicates (removed on retract)
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

    def _effective_head_for_index(self, entry: Rule | Fact) -> Term | None:
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

    def _index_key_from_head(self, head: Term | None) -> tuple[str, int] | None:
        if head is None:
            return None
        if not isinstance(head.functor, Atom):
            return None
        return (head.functor.name, len(head.args))

    def _arg0_index_key_from_head(
        self, head: Term | None
    ) -> tuple[str, int, int, str | int | float] | None:
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

    def _add_to_index(self, entry: Rule | Fact, position: str = "last") -> None:
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

    def _remove_from_index(self, entry: Rule | Fact) -> None:
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
    ) -> tuple[list[Rule | Fact], bool]:
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

    def add_rule(self, entry: Rule | Fact, position: str = "last") -> None:
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

    def remove_rule(self, entry: Rule | Fact) -> bool:
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
                    logger.debug(
                        "Removed %s/%d from defined_registry (no clauses remain)",
                        key[0],
                        key[1],
                    )

                return True
        return False

    def replace_rules(self, rules: list[Rule | Fact]) -> None:
        self.rules = rules
        self._build_index()

    def _rename_variables(
        self,
        term_or_rule: PrologType | Rule | Fact,
        env: BindingEnvironment | None = None,
    ) -> PrologType | Rule | Fact:
        if env is None:
            env = BindingEnvironment()

        self._unique_var_counter += 1
        mapping: dict[str, Variable] = {}

        def rename_var(v: Variable) -> Variable:
            # 現行仕様維持：同名Varは同じ新Varへ
            if v.name not in mapping:
                new_name = f"_V{self._unique_var_counter}_{v.name}"
                mapping[v.name] = Variable(new_name)
            return mapping[v.name]

        def rename_iter(root: PrologType) -> PrologType:
            # post-order 再構築（子→親）を明示スタックでやる
            out: dict[int, PrologType] = {}
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
                        renamed_tail_val = (
                            out[id(node.tail)] if node.tail is not None else None
                        )

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
    ) -> tuple[bool, BindingEnvironment]:
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
        seen: set[int] | None = None,
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
        visited: list[str] = []
        visited_set = set()
        trail: list[str] = []
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

        current_goal_key: tuple[str, int] | None = None
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
                if (
                    key not in self.defined_registry
                    and key not in self.dynamic_registry
                ):
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

            candidate_entries: list[Rule | Fact]
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

    def solve_goal_direct(
        self, goal: PrologType, env: BindingEnvironment
    ) -> Iterator[BindingEnvironment]:
        """Solve goal without calling runtime.execute() for rule bodies.

        This method is used by _execute_single_goal() to avoid recursion:
        _execute_single_goal → solve_goal → execute → execute_iterative →
          _execute_single_goal → ...

        Instead, it handles logical operators manually and delegates atomic
        goals to _execute_single_goal().

        Args:
            goal: Goal to solve
            env: Binding environment

        Yields:
            Binding environments for each solution

        Raises:
            CutException: When cut is encountered
            PrologError: On predicate errors
        """
        if env.stats_enabled:
            env.stats["solve_calls_total"] += 1

        actual_goal: Term
        if isinstance(goal, Atom):
            actual_goal = Term(goal, [])
        elif isinstance(goal, Term):
            actual_goal = goal
        else:
            return

        current_goal_key: tuple[str, int] | None = None
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

            # Check for builtin predicates (meta-predicates, list operations, dynamic predicates, etc.)
            # These are handled in runtime.execute() but not yet in defined_registry
            if isinstance(actual_goal.functor, Atom):
                functor_name = actual_goal.functor.name
                arity = len(actual_goal.args)
                builtin_predicates = {
                    # Type checking
                    ("var", 1),
                    ("atom", 1),
                    ("number", 1),
                    ("atom_number", 2),
                    ("functor", 3),
                    ("arg", 3),
                    ("=..", 2),
                    # Dynamic predicates
                    ("asserta", 1),
                    ("assertz", 1),
                    ("retract", 1),
                    # List operations
                    ("member", 2),
                    ("append", 3),
                    # Meta predicates
                    ("findall", 3),
                    # Listing/export
                    ("listing", 0),
                    ("listing", 1),
                    ("export_facts", 2),
                    # Unsafe external execution
                    ("py_register", 2),
                    ("py_unregister", 1),
                    ("py_registered", 2),
                    ("py_call", 5),
                    # IO predicates
                    ("get_char", 1),
                    ("read_line", 1),
                    ("peek_char", 1),
                    ("at_end_of_stream", 0),
                }
                if (functor_name, arity) in builtin_predicates:
                    # Delegate to runtime.execute() which has the builtin implementations
                    for result_env in self.runtime._execute_single_goal(
                        actual_goal, env
                    ):
                        yield YieldEnv(env=result_env)
                    return

            # Existence check
            if isinstance(
                actual_goal.functor, Atom
            ) and actual_goal.functor.name not in (
                "true",
                "fail",
            ):
                key = (actual_goal.functor.name, len(actual_goal.args))

                if (
                    key not in self.defined_registry
                    and key not in self.dynamic_registry
                ):
                    raise PrologError(
                        f"existence_error(procedure, {actual_goal.functor.name}/{len(actual_goal.args)})"
                    )

                if key not in self.rules_by_pred or not self.rules_by_pred[key]:
                    if hasattr(self.runtime, "tracer") and self.runtime.tracer.enabled:
                        self.runtime.tracer.record_fail(actual_goal)
                    return

            # Tracer: call
            if hasattr(self.runtime, "tracer") and self.runtime.tracer.enabled:
                self.runtime.tracer.record_call(actual_goal, env)

            # Special predicates
            if actual_goal.functor.name == "true" and not actual_goal.args:
                if hasattr(self.runtime, "tracer") and self.runtime.tracer.enabled:
                    self.runtime.tracer.record_exit(actual_goal, env, Fact(actual_goal))
                yield env
                return
            elif actual_goal.functor.name == "fail" and not actual_goal.args:
                if hasattr(self.runtime, "tracer") and self.runtime.tracer.enabled:
                    self.runtime.tracer.record_fail(actual_goal)
                return

            # Get candidate clauses
            candidate_entries: list[Rule | Fact]
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

            # Try each candidate clause
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

                # Handle potential parser issue
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
                    effective_head = current_head.args[0]
                    rule_body_from_fact_structure = current_head.args[1]
                    is_rule_from_fact_structure = True

                unified, new_env_after_unify = self.unify(
                    actual_goal, effective_head, env
                )

                if unified:
                    if is_rule_from_fact_structure:
                        # Execute body with frame-driven iterative approach (Phase 2)
                        try:
                            yield from self._execute_body_iterative(
                                rule_body_from_fact_structure, new_env_after_unify
                            )
                        except CutException:
                            raise
                        except Exception as e:
                            if "Input required" in str(e) or hasattr(e, "input_type"):
                                raise
                            raise
                    elif isinstance(renamed_entry, Fact):
                        # Genuine Fact
                        if (
                            hasattr(self.runtime, "tracer")
                            and self.runtime.tracer.enabled
                        ):
                            self.runtime.tracer.record_exit(
                                actual_goal, new_env_after_unify, renamed_entry
                            )
                        yield new_env_after_unify
                    elif isinstance(renamed_entry, Rule):
                        # Execute body with frame-driven iterative approach (Phase 2)
                        try:
                            yield from self._execute_body_iterative(
                                renamed_entry.body, new_env_after_unify
                            )
                        except CutException:
                            raise
                        except Exception as e:
                            if "Input required" in str(e) or hasattr(e, "input_type"):
                                raise
                            raise

            # Tracer: fail
            if hasattr(self.runtime, "tracer") and self.runtime.tracer.enabled:
                self.runtime.tracer.record_fail(actual_goal)
        finally:
            if env.stats_enabled:
                env.stats["current_goal_key"] = previous_goal_key

    def _execute_body_direct(
        self, body: PrologType, env: BindingEnvironment
    ) -> Iterator[BindingEnvironment]:
        """Execute rule body without calling runtime.execute() (HYBRID VERSION).

        Uses iterative flattening for conjunction chains (reduces recursion depth),
        but keeps recursive execution for proper Cut handling and simplicity.

        Args:
            body: Rule body to execute
            env: Binding environment

        Yields:
            Binding environments for each solution

        Raises:
            CutException: When cut is encountered
        """
        from pyprolog.core.types import Atom, Term

        # Detect logical operators
        if isinstance(body, Term) and isinstance(body.functor, Atom):
            functor_name = body.functor.name

            # Conjunction (,/2): flatten then execute recursively (hybrid approach)
            if functor_name == "," and len(body.args) == 2:
                # Flatten conjunction chain to reduce recursion depth
                goals = self._flatten_conjunction_iterative(body)
                # Execute flattened goals iteratively (no recursion, explicit stack)
                yield from self._execute_conjunction_iterative(goals, env)
                return

            # Disjunction (;/2): try left, then right
            if functor_name == ";" and len(body.args) == 2:
                left_goal, right_goal = body.args[0], body.args[1]
                # Try left alternative
                try:
                    yield from self._execute_body_direct(left_goal, env)
                except CutException:
                    # Cut in left branch prevents right branch
                    raise
                # Try right alternative
                yield from self._execute_body_direct(right_goal, env)
                return

            # Negation (\+/1): negation as failure
            if functor_name == "\\+" and len(body.args) == 1:
                inner_goal = body.args[0]
                # Try to prove inner goal
                solution_found = False
                try:
                    for _ in self._execute_body_direct(inner_goal, env):
                        solution_found = True
                        break  # One solution is enough
                except CutException:
                    # Cut within negation doesn't escape
                    solution_found = True

                # Negation succeeds if inner goal failed
                if not solution_found:
                    yield env
                return

        # Atomic goal: delegate to _execute_single_goal()
        yield from self.runtime._execute_single_goal(body, env)

    # ═══════════════════════════════════════════════════════════════
    # Phase 2: Complete Frame-Driven Execution (while + explicit stack)
    # ═══════════════════════════════════════════════════════════════

    def _make_frame(self, body: PrologType, env: BindingEnvironment):
        """Create appropriate frame for body based on its type.

        This is a helper for _execute_body_iterative to dispatch to the correct frame type.

        Args:
            body: Goal to execute
            env: Binding environment

        Returns:
            Frame object (GoalFrame, DisjunctionFrame, NegationFrame, etc.)
        """
        # Detect logical operators
        if isinstance(body, Term) and isinstance(body.functor, Atom):
            functor_name = body.functor.name

            # Disjunction (;/2)
            if functor_name == ";" and len(body.args) == 2:
                left_goal, right_goal = body.args[0], body.args[1]
                return DisjunctionFrame(
                    env=env, left_goal=left_goal, right_goal=right_goal
                )

            # Negation (\+/1)
            if functor_name == "\\+" and len(body.args) == 1:
                inner_goal = body.args[0]
                # Note: entry_stack_depth/entry_choice_depth are not used in _execute_body_iterative context
                # They default to 0, which is fine for this local stack-based execution
                return NegationFrame(
                    env=env,
                    inner_goal=inner_goal,
                    entry_stack_depth=0,  # Not used in local stack context
                    entry_choice_depth=0,  # Not used in local stack context
                )

        # Atomic goal (including conjunction, which is handled in _execute_body_iterative)
        return GoalFrame(env=env, goal=body)

    def _solve_goal_for_frame(
        self, goal: PrologType, env: BindingEnvironment
    ) -> Iterator[PushFrame | YieldEnv]:
        """Solve goal for frame-driven execution (PushFrame/YieldEnv version of solve_goal_direct).

        This is called by GoalFrame.step(). It's essentially solve_goal_direct but instead of
        yielding BindingEnvironment directly or using yield from _execute_body_direct(), it:
        - Yields PushFrame for clause bodies (to push onto frame stack)
        - Yields YieldEnv for builtin solutions

        Args:
            goal: Goal to solve
            env: Binding environment

        Yields:
            PushFrame: For clause bodies that need execution
            YieldEnv: For builtin/fact solutions

        Raises:
            CutException: When cut is encountered
            PrologError: On predicate errors
        """
        # Operator check: delegate to _execute_single_goal and wrap in YieldEnv
        from pyprolog.core.operators import operator_registry

        # Check for Atom operators (like "!")
        if isinstance(goal, Atom):
            functor_name = goal.name
            op_info = operator_registry.get_operator(functor_name)

            if (
                op_info
                and functor_name in self.runtime._operator_evaluators
                and functor_name not in (",", ";", "\\+")
            ):
                # Delegate to _execute_single_goal and wrap results in YieldEnv
                for result_env in self.runtime._execute_single_goal(goal, env):
                    yield YieldEnv(env=result_env)
                return

        # Check for Term operators (like "=(X, Y)", "is(X, Y)", etc.)
        if isinstance(goal, Term) and isinstance(goal.functor, Atom):
            functor_name = goal.functor.name
            op_info = operator_registry.get_operator(functor_name)

            # If it's an operator (not a logical operator, those are handled elsewhere)
            if (
                op_info
                and functor_name in self.runtime._operator_evaluators
                and functor_name not in (",", ";", "\\+")
            ):
                # Delegate to _execute_single_goal and wrap results in YieldEnv
                for result_env in self.runtime._execute_single_goal(goal, env):
                    yield YieldEnv(env=result_env)
                return

        # This is a copy of solve_goal_direct with body execution changed to PushFrame
        if env.stats_enabled:
            env.stats["solve_calls_total"] += 1

        actual_goal: Term
        if isinstance(goal, Atom):
            actual_goal = Term(goal, [])
        elif isinstance(goal, Term):
            actual_goal = goal
        else:
            return

        current_goal_key: tuple[str, int] | None = None
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

            # Check for builtin predicates (meta-predicates, list operations, dynamic predicates, etc.)
            # These are handled in runtime.execute() but not yet in defined_registry
            if isinstance(actual_goal.functor, Atom):
                functor_name = actual_goal.functor.name
                arity = len(actual_goal.args)
                builtin_predicates = {
                    # Type checking
                    ("var", 1),
                    ("atom", 1),
                    ("number", 1),
                    ("atom_number", 2),
                    ("functor", 3),
                    ("arg", 3),
                    ("=..", 2),
                    # Dynamic predicates
                    ("asserta", 1),
                    ("assertz", 1),
                    ("retract", 1),
                    # List operations
                    ("member", 2),
                    ("append", 3),
                    # Meta predicates
                    ("findall", 3),
                    # Listing/export
                    ("listing", 0),
                    ("listing", 1),
                    ("export_facts", 2),
                    # Unsafe external execution
                    ("py_register", 2),
                    ("py_unregister", 1),
                    ("py_registered", 2),
                    ("py_call", 5),
                    # IO predicates
                    ("get_char", 1),
                    ("read_line", 1),
                    ("peek_char", 1),
                    ("at_end_of_stream", 0),
                }
                if (functor_name, arity) in builtin_predicates:
                    # Delegate to runtime.execute() which has the builtin implementations
                    for result_env in self.runtime._execute_single_goal(
                        actual_goal, env
                    ):
                        yield YieldEnv(env=result_env)
                    return

            # Existence check
            if isinstance(
                actual_goal.functor, Atom
            ) and actual_goal.functor.name not in (
                "true",
                "fail",
            ):
                key = (actual_goal.functor.name, len(actual_goal.args))

                if (
                    key not in self.defined_registry
                    and key not in self.dynamic_registry
                ):
                    raise PrologError(
                        f"existence_error(procedure, {actual_goal.functor.name}/{len(actual_goal.args)})"
                    )

                if key not in self.rules_by_pred or not self.rules_by_pred[key]:
                    if hasattr(self.runtime, "tracer") and self.runtime.tracer.enabled:
                        self.runtime.tracer.record_fail(actual_goal)
                    return

            # Tracer: call
            if hasattr(self.runtime, "tracer") and self.runtime.tracer.enabled:
                self.runtime.tracer.record_call(actual_goal, env)

            # Special predicates
            if actual_goal.functor.name == "true" and not actual_goal.args:
                if hasattr(self.runtime, "tracer") and self.runtime.tracer.enabled:
                    self.runtime.tracer.record_exit(actual_goal, env, Fact(actual_goal))
                yield YieldEnv(env=env)
                return
            elif actual_goal.functor.name == "fail" and not actual_goal.args:
                if hasattr(self.runtime, "tracer") and self.runtime.tracer.enabled:
                    self.runtime.tracer.record_fail(actual_goal)
                return

            # Get candidate clauses
            candidate_entries: list[Rule | Fact]
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

            # Try each candidate clause
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

                # Handle potential parser issue
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
                    effective_head = current_head.args[0]
                    rule_body_from_fact_structure = current_head.args[1]
                    is_rule_from_fact_structure = True

                unified, new_env_after_unify = self.unify(
                    actual_goal, effective_head, env
                )

                if unified:
                    if is_rule_from_fact_structure:
                        # Execute body: yield PushFrame instead of yield from
                        try:
                            yield PushFrame(
                                goal=rule_body_from_fact_structure,
                                env=new_env_after_unify,
                            )
                        except CutException:
                            raise
                        except Exception as e:
                            if "Input required" in str(e) or hasattr(e, "input_type"):
                                raise
                            raise
                    elif isinstance(renamed_entry, Fact):
                        # Genuine Fact: yield solution
                        if (
                            hasattr(self.runtime, "tracer")
                            and self.runtime.tracer.enabled
                        ):
                            self.runtime.tracer.record_exit(
                                actual_goal, new_env_after_unify, renamed_entry
                            )
                        yield YieldEnv(env=new_env_after_unify)
                    elif isinstance(renamed_entry, Rule):
                        # Execute body: yield PushFrame instead of yield from
                        try:
                            yield PushFrame(
                                goal=renamed_entry.body, env=new_env_after_unify
                            )
                        except CutException:
                            raise
                        except Exception as e:
                            if "Input required" in str(e) or hasattr(e, "input_type"):
                                raise
                            raise

            # Tracer: fail
            if hasattr(self.runtime, "tracer") and self.runtime.tracer.enabled:
                self.runtime.tracer.record_fail(actual_goal)
        finally:
            if env.stats_enabled:
                env.stats["current_goal_key"] = previous_goal_key

    def _execute_body_iterative(
        self, body: PrologType, env: BindingEnvironment
    ) -> Iterator[BindingEnvironment]:
        """Execute rule body with complete frame-driven approach (Phase 2).

        This replaces _execute_body_direct to eliminate Python stack consumption from
        Prolog predicate recursion. Uses while loop + explicit frame stack.

        Key features:
        - yield ONLY in one place (while loop)
        - No yield from for goal → solve → body recursion
        - Frames communicate via PushFrame/YieldEnv

        Args:
            body: Rule body to execute
            env: Binding environment

        Yields:
            Binding environments for each solution

        Raises:
            CutException: When cut is encountered
        """
        from pyprolog.core.types import Atom, Term

        # Special case: conjunction is handled with existing iterative approach
        # (conjunction chains are flattened, not deeply recursive)
        if isinstance(body, Term) and isinstance(body.functor, Atom):
            if body.functor.name == "," and len(body.args) == 2:
                goals = self._flatten_conjunction_iterative(body)
                yield from self._execute_conjunction_with_frame(goals, env)
                return

        # Frame-driven execution with explicit stack
        stack = [self._make_frame(body, env)]

        while stack:
            frame = stack[-1]

            try:
                result = frame.step(self.runtime)
            except StopIteration:
                # Frame exhausted
                stack.pop()
                # For NegationFrame: if inner goal failed, step() would have returned YieldEnv
                # If we get StopIteration, it means negation failed (inner goal succeeded)
                continue
            except CutException:
                # Cut within negation: mark inner goal as succeeded
                if any(isinstance(f, NegationFrame) for f in stack):
                    for f in reversed(stack):
                        if isinstance(f, NegationFrame):
                            f.record_success()
                            break
                    continue
                # Normal cut: clear stack and propagate
                stack.clear()
                raise

            if result is None:
                # Internal state transition
                # For NegationFrame: need to push inner goal
                if (
                    isinstance(frame, NegationFrame)
                    and frame.inner_started
                    and not frame.checked
                ):
                    inner_frame = self._make_frame(frame.inner_goal, frame.env.copy())
                    stack.append(inner_frame)
                # For other frames: just continue to next step
                continue
            elif isinstance(result, PushFrame):
                # Push child frame
                new_frame = self._make_frame(result.goal, result.env)
                stack.append(new_frame)
            elif isinstance(result, YieldEnv):
                # Check if this is within a NegationFrame
                parent_frame = stack[-2] if len(stack) >= 2 else None
                if isinstance(parent_frame, NegationFrame):
                    # Inner goal of negation succeeded → mark it
                    parent_frame.record_success()
                    # Pop inner goal frame
                    stack.pop()
                    # Negation will fail on next step
                else:
                    # Normal solution: yield it
                    yield result.env
            # Other cases: continue

    def _execute_conjunction_with_frame(
        self, goals: list[PrologType], env: BindingEnvironment
    ) -> Iterator[BindingEnvironment]:
        """Execute conjunction iteratively with frame-driven body execution.

        This is based on _execute_conjunction_iterative but calls _execute_body_iterative
        for each goal instead of _execute_body_direct.

        Args:
            goals: Flattened list of goals from conjunction
            env: Initial environment

        Yields:
            Binding environments for each solution

        Raises:
            CutException: When cut is encountered
        """
        # Base case: no goals
        if not goals:
            yield env
            return

        n = len(goals)
        # Stack: list of (goal_index, result_iterator)
        stack: list[tuple[int, Iterator[BindingEnvironment]]] = []

        # Start with first goal (using _execute_body_iterative)
        try:
            first_iter = self._execute_body_iterative(goals[0], env)
            stack.append((0, first_iter))
        except CutException:
            raise

        # Process stack iteratively
        while stack:
            goal_idx, iterator = stack[-1]

            try:
                result_env = next(iterator)
            except StopIteration:
                # Current goal exhausted, backtrack
                stack.pop()
                continue
            except CutException:
                # Cut encountered
                raise

            # Check if this is the last goal
            if goal_idx == n - 1:
                # All goals succeeded, yield solution
                yield result_env
                # Continue to get next solution from current goal
            else:
                # Move to next goal (using _execute_body_iterative)
                next_idx = goal_idx + 1
                try:
                    next_iter = self._execute_body_iterative(
                        goals[next_idx], result_env
                    )
                    stack.append((next_idx, next_iter))
                except CutException:
                    raise

    def _flatten_conjunction_iterative(self, body: PrologType) -> list[PrologType]:
        """Flatten nested conjunctions into a flat list (iterative, no recursion).

        Converts nested structure like (A, (B, (C, D))) into [A, B, C, D].
        This eliminates O(n) recursion depth for conjunction chains.

        Args:
            body: Goal (possibly nested conjunctions)

        Returns:
            Flat list of goals
        """
        from collections import deque

        from pyprolog.core.types import Atom, Term

        result = []
        stack = deque([body])

        while stack:
            current = stack.pop()

            if isinstance(current, Term) and isinstance(current.functor, Atom):
                if current.functor.name == "," and len(current.args) == 2:
                    # Push right first (processed after left due to stack order)
                    stack.append(current.args[1])
                    stack.append(current.args[0])
                    continue

            # Not a conjunction - add to result
            result.append(current)

        return result

    def _execute_conjunction_recursive(
        self, goals: list[PrologType], env: BindingEnvironment
    ) -> Iterator[BindingEnvironment]:
        """Execute flattened conjunction goals recursively (tail-optimized).

        This is a simpler, more maintainable approach than full iterative execution,
        with correct Cut handling. Recursion depth is O(k) where k = number of
        non-conjunction goals, NOT O(n) where n = total conjunction chain length.

        Args:
            goals: Flattened list of goals from conjunction
            env: Initial environment

        Yields:
            Binding environments for each solution

        Raises:
            CutException: When cut is encountered
        """
        # Base case: no more goals
        if not goals:
            yield env
            return

        # Recursive case: execute first goal, then remaining goals
        first_goal = goals[0]
        remaining_goals = goals[1:]

        try:
            for result_env in self._execute_body_direct(first_goal, env):
                # Execute remaining goals with result environment
                yield from self._execute_conjunction_recursive(
                    remaining_goals, result_env
                )
        except CutException:
            raise

    def _execute_conjunction_iterative(
        self, goals: list[PrologType], env: BindingEnvironment
    ) -> Iterator[BindingEnvironment]:
        """Execute flattened conjunction goals iteratively (no recursion).

        This replaces _execute_conjunction_recursive to eliminate stack consumption
        from conjunction execution. Uses explicit stack to manage backtracking.

        Args:
            goals: Flattened list of goals from conjunction
            env: Initial environment

        Yields:
            Binding environments for each solution

        Raises:
            CutException: When cut is encountered
        """
        # Base case: no goals
        if not goals:
            yield env
            return

        n = len(goals)
        # Stack: list of (goal_index, result_iterator)
        # Represents the execution state for backtracking
        stack: list[tuple[int, Iterator[BindingEnvironment]]] = []

        # Start with first goal
        try:
            first_iter = self._execute_body_direct(goals[0], env)
            stack.append((0, first_iter))
        except CutException:
            raise

        # Process stack iteratively
        while stack:
            goal_idx, iterator = stack[-1]

            try:
                result_env = next(iterator)
            except StopIteration:
                # Current goal exhausted, backtrack
                stack.pop()
                continue
            except CutException:
                # Cut encountered
                raise

            # Check if this is the last goal
            if goal_idx == n - 1:
                # All goals succeeded, yield solution
                yield result_env
                # Continue to get next solution from current goal
            else:
                # Move to next goal
                next_idx = goal_idx + 1
                try:
                    next_iter = self._execute_body_direct(goals[next_idx], result_env)
                    stack.append((next_idx, next_iter))
                except CutException:
                    raise

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
