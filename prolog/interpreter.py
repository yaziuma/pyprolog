import io
from .types import (
    TermFunction,
    Variable,
    Term,
    merge_bindings,
    Arithmetic,
    Logic,
    FALSE,
    TRUE,
    CUT, # This is the CUT Term from types.py
)
from .builtins import Write, Nl, Tab, Fail, Cut as BuiltinCut, Retract, AssertA, AssertZ # Renamed to avoid clash with types.CUT
from prolog.token_type import TokenType
from prolog.logger import logger

logger.debug("interpreter.py loaded")


# Scanner and Parser will be imported inside methods to break circular dependency
# from prolog.scanner import Scanner # Moved
# from prolog.parser import Parser   # Moved


class Rule:
    def __init__(self, head, body):
        # logger.debug(f"Rule initialized with head: {head}, body: {body}") # Can be verbose
        self.head = head
        self.body = body

    def __str__(self):
        return f'{self.head}{self.body}'

    def __repr__(self):
        return str(self)


class Conjunction(Term):
    def __init__(self, args):
        # logger.debug(f"Conjunction initialized with args: {args}") # Can be verbose
        super().__init__(None, *args)

    def _is_builtin(self, arg):
        if (
            isinstance(arg, Write)
            or isinstance(arg, Nl)
            or isinstance(arg, Tab)
        ):
            return True
        return False

    def _is_db_builtin(self, arg):
        if (
            isinstance(arg, Retract)
            or isinstance(arg, AssertA)
            or isinstance(arg, AssertZ)
        ):
            return True
        return False

    def _is_fail(self, arg):
        if isinstance(arg, Fail):
            return True
        return False

    def _is_cut(self, arg):
        # Checks if the argument is an instance of prolog.builtins.Cut
        if isinstance(arg, BuiltinCut): 
            return True
        return False

    def query(self, runtime):
        logger.debug(f"Conjunction.query called for args: {self.args}")
        def solutions(index, bindings):
            logger.debug(f"Conjunction.solutions: index={index}, bindings={bindings}, total_args={len(self.args)}")
            if index >= len(self.args):
                res_sub = self.substitute(bindings)
                logger.debug(f"Conjunction.solutions: base case, yielding substituted conjunction: {res_sub}")
                yield res_sub
            else:
                arg = self.args[index]
                logger.debug(f"Conjunction.solutions: processing arg[{index}] = {arg}")
                if self._is_cut(arg): # arg is an instance of builtins.Cut
                    logger.debug(f"Conjunction.solutions: arg is CUT {arg}")
                    # Cut execution itself doesn't yield solutions in the normal sense for the cut goal.
                    # It affects the parent's choice points.
                    # The original pyprolog's Conjunction.query for cut was:
                    # for item in runtime.execute(arg.substitute(bindings)): ... yield CUT()
                    # This seems to imply that the cut itself is "executed" and then a CUT signal is yielded.
                    # runtime.execute(builtins.Cut()) should handle the cut mechanism.
                    # What does runtime.execute(builtins.Cut()) yield?
                    # Let's assume it yields something that signifies success of the cut operation itself,
                    # or perhaps it doesn't yield anything but modifies runtime state.
                    # The `yield CUT()` here is likely the signal for the parent (evaluate_rules).
                    
                    # If arg is builtins.Cut(), its .query() or .execute() should handle the cut.
                    # The original code `runtime.execute(arg.substitute(bindings))` for a Cut term seems odd,
                    # as Cut itself doesn't usually unify or produce bindings.
                    # Let's assume builtins.Cut has a query method that signals the cut.
                    
                    # For a cut `!`, we proceed to the next goal and then signal CUT.
                    # The cut itself succeeds once.
                    # The crucial part is `yield CUT()` which is handled by `evaluate_rules`.
                    
                    # The original code for cut in Conjunction.query:
                    # for item in runtime.execute(arg.substitute(bindings)):
                    #     unified = merge_bindings(arg.match(item), bindings)
                    #     if unified is not None:
                    #         yield from solutions(index + 1, unified)
                    #         yield CUT() # This CUT is from types.py
                    # This implies `runtime.execute` on a `builtins.Cut` term might yield something (e.g., TRUE)
                    # that allows `arg.match(item)` to succeed.
                    # And `builtins.Cut.match` would need to be defined.
                    # This seems overly complex. A cut `!` in a conjunction simply succeeds,
                    # allows subsequent goals in the conjunction to be tried, and if they succeed,
                    # the `CUT` signal is propagated.

                    # Simpler model: cut succeeds, continue with next goal in conjunction.
                    # Then, after all solutions for the rest of the conjunction are found (or the first one if cut is strict),
                    # a CUT signal is yielded.
                    # The `yield CUT()` should be *after* `yield from solutions(index + 1, unified)`.
                    
                    # Let's follow the structure of other goals first.
                    # A cut goal itself succeeds once.
                    # We need to yield from solutions(index + 1, bindings) to execute subsequent goals.
                    # After that, the CUT signal is propagated.

                    # If `arg` is `builtins.Cut()`, it means this goal is `!`.
                    # It succeeds. We then try to solve `solutions(index + 1, bindings)`.
                    # For each solution found for the rest of the conjunction, we yield that solution,
                    # and then immediately after, we must yield the `CUT()` signal.
                    
                    # This means the loop structure for cut needs to be different.
                    # The cut commits to choices made *up to the cut in the current rule*
                    # and cuts away alternative clauses for the *parent goal*.
                    # The `yield CUT()` from `Conjunction.query` is caught by `evaluate_rules`.

                    # Let's assume `runtime.execute(arg.substitute(bindings))` for a `builtins.Cut` term
                    # will yield something like `TRUE` once if the cut is to be performed.
                    # And `builtins.Cut.match(TRUE)` would return `{}`.
                    
                    # Sticking to the provided code structure for now, assuming it has a rationale.
                    # `arg` here is `prolog.builtins.Cut` instance.
                    # `arg.substitute(bindings)` is still `prolog.builtins.Cut()`.
                    # `runtime.execute(prolog.builtins.Cut())` needs to be defined.
                    # Let's assume `builtins.Cut().query(runtime, bindings)` or similar is called by `runtime.execute`.
                    # And `builtins.Cut().query()` should yield `TRUE()` once.
                    
                    # If `arg` is `builtins.Cut`:
                    # It succeeds, effectively. Bindings don't change due to `!`.
                    # Then we solve the rest of the conjunction.
                    # For each solution from `solutions(index + 1, bindings)`, we yield it.
                    # After all solutions from `solutions(index + 1, bindings)` are exhausted (or the first one),
                    # we must then `yield CUT()` to signal the cut to the calling `evaluate_rules`.

                    # The original code's loop for cut:
                    # for item in runtime.execute(arg.substitute(bindings)): # item should be TRUE() if cut "succeeds"
                    #     unified = merge_bindings(arg.match(item), bindings) # unified should be bindings
                    #     if unified is not None:
                    #         yield from solutions(index + 1, unified) # execute rest of conjunction
                    #         yield CUT() # Signal cut AFTER solutions from rest of conjunction
                    # This structure means the CUT signal is sent *for each solution* of the rest of the conjunction.
                    # This is correct: the cut takes effect after the current rule (including goals after !) fully succeeds.

                    # Let's assume `runtime.execute(builtins.Cut_instance)` yields `TRUE_instance` once.
                    # And `builtins.Cut_instance.match(TRUE_instance)` yields `{}`.
                    for _ in runtime.execute(arg.substitute(bindings)): # Assuming this "succeeds" once for a cut
                        # The cut itself doesn't add bindings. `unified` should be same as `bindings`.
                        # This part is a bit hand-wavy without knowing how `execute(Cut)` and `Cut.match` work.
                        # A simpler way: a cut goal always "succeeds" with current bindings.
                        logger.debug(f"Conjunction.solutions: Executing goals after CUT for bindings: {bindings}")
                        yield from solutions(index + 1, bindings)
                        logger.debug("Conjunction.solutions: Yielding CUT signal after solutions for goals post-cut.")
                        yield CUT() # This is types.CUT
                        # Since a cut commits, there should be no further iterations of this loop for the cut goal itself.
                        # The `runtime.execute(arg.substitute(bindings))` should yield only once for a cut.
                        # And the `yield CUT()` should effectively stop further backtracking for the parent goal's alternatives.
                        # This also means the `solutions` generator for the parent of this conjunction should stop after this.
                        return # After yielding CUT, this path of the conjunction is done.

                elif self._is_fail(arg): # arg is builtins.Fail
                    logger.debug(f"Conjunction.solutions: arg is FAIL {arg}, yielding FALSE")
                    yield FALSE()
                elif self._is_builtin(arg): # Write, Nl, Tab
                    logger.debug(f"Conjunction.solutions: arg is IO builtin {arg}, executing its query")
                    _ = list(arg.query(runtime, bindings))  # consume iter to perform action
                    logger.debug(f"Conjunction.solutions: IO builtin executed, proceeding to next arg with bindings: {bindings}")
                    yield from solutions(index + 1, bindings)
                elif self._is_db_builtin(arg): # Retract, AssertA, AssertZ
                    logger.debug(f"Conjunction.solutions: arg is DB builtin {arg}, executing its query")
                    _ = list(arg.query(runtime, bindings))  # consume iter to perform action
                    logger.debug(f"Conjunction.solutions: DB builtin executed, proceeding to next arg with bindings: {bindings}")
                    yield from solutions(index + 1, bindings)
                elif isinstance(arg, Arithmetic):
                    logger.debug(f"Conjunction.solutions: arg is Arithmetic {arg}")
                    val = arg.substitute(bindings).evaluate()
                    unified = merge_bindings({arg.var: val}, bindings)
                    if unified is None: # Should not happen if var is fresh or matches
                        logger.error(f"Conjunction.solutions: Arithmetic merge_bindings failed for {arg.var}={val} with {bindings}")
                        # This would mean a contradiction, so this path fails.
                        # yield FALSE() ? Or just stop yielding.
                        return
                    logger.debug(f"Conjunction.solutions: Arithmetic evaluated, proceeding with unified bindings: {unified}")
                    yield from solutions(index + 1, unified)
                elif isinstance(arg, Logic):
                    logger.debug(f"Conjunction.solutions: arg is Logic {arg}, evaluating")
                    eval_result = arg.substitute(bindings).evaluate()
                    logger.debug(f"Conjunction.solutions: Logic evaluated to {eval_result}, yielding it.")
                    yield eval_result # This should be TRUE or FALSE
                else: # General term (atom or structure)
                    logger.debug(f"Conjunction.solutions: arg is general term {arg}, calling runtime.execute")
                    for item in runtime.execute(arg.substitute(bindings)):
                        logger.debug(f"Conjunction.solutions: item from runtime.execute({arg.substitute(bindings)}): {item}")
                        if isinstance(item, FALSE): # If a goal fails, this path of conjunction fails.
                            logger.debug("Conjunction.solutions: item is FALSE, this conjunction path fails.")
                            # We need to stop this path and allow backtracking to a previous goal if any.
                            # Yielding FALSE() here would be caught by evaluate_rules, but that's for the whole rule body.
                            # For a conjunction, if one part fails, the whole conjunction for that binding set fails.
                            # So, we just don't yield from solutions(index + 1, ...)
                            # This means this inner loop for `item` will look for other solutions for `arg`.
                            # If `runtime.execute` exhausts and no non-FALSE item found, this path ends.
                            continue # Try next solution for `arg`

                        if isinstance(item, CUT): # Should not happen here, CUT is from body.query in evaluate_rules
                            logger.error("Conjunction.solutions: Unexpected CUT signal received from runtime.execute on a general term.")
                            yield item # Propagate if it happens
                            return

                        unified = merge_bindings(arg.match(item), bindings)
                        logger.debug(f"Conjunction.solutions: unified bindings for {arg} and {item}: {unified} (original: {bindings})")
                        if unified is not None:
                            logger.debug(f"Conjunction.solutions: proceeding to next arg with unified bindings: {unified}")
                            yield from solutions(index + 1, unified)
                        else:
                            logger.debug(f"Conjunction.solutions: unification failed for {arg} and {item}, trying next item.")
                    # If loop finishes, all solutions for 'arg' are exhausted for current 'bindings'.
                    # This means this path of the conjunction (starting from current 'arg' with 'bindings') is done.
                    # Backtracking will occur to the previous goal in the conjunction, or to the parent rule.
                    logger.debug(f"Conjunction.solutions: runtime.execute for {arg} exhausted for bindings {bindings}.")
                    return # Critical: if a goal in conjunction has no (more) solutions, this path of conjunction fails.

        logger.debug("Conjunction.query: starting solutions generator")
        yield from solutions(0, {})

    def substitute(self, bindings):
        return Conjunction(
            map((lambda arg: arg.substitute(bindings)), self.args)
        )


class Runtime:
    def __init__(self, rules):
        logger.debug(f"Runtime initialized with rules (count: {len(rules)}): {rules[:3]}{'...' if len(rules) > 3 else ''}")
        self.rules = rules
        self.stream = io.StringIO()
        self.stream_pos = 0

    def __del__(self):
        logger.debug("Runtime.__del__ called")
        self.stream.close()

    def stream_write(self, text):
        # logger.debug(f"Runtime.stream_write: '{text}'") # Can be verbose
        self.stream.write(text)

    def stream_read(self):
        self.stream.seek(self.stream_pos)
        line = self.stream.read()
        self.stream_pos = self.stream.tell()
        # logger.debug(f"Runtime.stream_read: '{line}'") # Can be verbose
        return line

    def reset_stream(self):
        logger.debug("Runtime.reset_stream called")
        self.stream.seek(0)
        self.stream.truncate(0)
        self.stream_pos = 0

    def consult_rules(self, rules_str):
        from prolog.scanner import Scanner
        from prolog.parser import Parser
        logger.debug(f"Runtime.consult_rules called with: {rules_str[:100]}{'...' if len(rules_str) > 100 else ''}")
        if not rules_str.strip():
            logger.debug("Runtime.consult_rules: empty string, returning.")
            return

        tokens = Scanner(rules_str).tokenize()
        logger.debug(f"Runtime.consult_rules: tokens (first 5): {tokens[:5]}{'...' if len(tokens) > 5 else ''}")
        if not tokens or (len(tokens) == 1 and tokens[0].token_type == TokenType.EOF):
            logger.debug("Runtime.consult_rules: no relevant tokens, returning.")
            return
        
        new_rules = Parser(tokens).parse_rules()
        logger.debug(f"Runtime.consult_rules: parsed new rules (count {len(new_rules)}): {new_rules[:3]}{'...' if len(new_rules) > 3 else ''}")
        self.rules.extend(new_rules)
        logger.debug(f"Runtime.consult_rules: total rules now: {len(self.rules)}")


    def query(self, query_str):
        from prolog.scanner import Scanner
        from prolog.parser import Parser
        logger.debug(f"Runtime.query called with: '{query_str}'")
        tokens = Scanner(query_str).tokenize()
        logger.debug(f"Runtime.query: tokens (first 5): {tokens[:5]}{'...' if len(tokens) > 5 else ''}")

        if not tokens or (len(tokens) == 1 and tokens[0].token_type == TokenType.EOF):
            logger.debug("Runtime.query: no relevant tokens, returning (no solutions).")
            return

        parsed_query = Parser(tokens).parse_query()
        logger.debug(f"Runtime.query: parsed_query: {parsed_query}")

        query_vars = []
        if isinstance(parsed_query, Rule) and \
           isinstance(parsed_query.head, Term) and \
           parsed_query.head.pred == "##":
            for arg_q_var in parsed_query.head.args: # Renamed arg to arg_q_var
                if isinstance(arg_q_var, Variable):
                    query_vars.append(arg_q_var)
        logger.debug(f"Runtime.query: query_vars: {[v.name for v in query_vars]}")
        
        solution_count = 0
        for solution_item in self.execute(parsed_query):
            logger.debug(f"Runtime.query: solution_item from execute: {solution_item}")
            if isinstance(solution_item, FALSE) or solution_item is None:
                logger.debug("Runtime.query: solution_item is FALSE or None, skipping.")
                continue
            if isinstance(solution_item, CUT):
                logger.warning("Runtime.query: CUT signal reached top-level query. This should ideally be handled internally.")
                continue

            bindings = {}
            if query_vars:
                if isinstance(solution_item, Term) and solution_item.pred == "##":
                    if len(query_vars) == len(solution_item.args):
                        for i, original_var_obj in enumerate(query_vars):
                            bindings[original_var_obj] = solution_item.args[i]
                    else:
                        logger.error(f"Runtime.query: Mismatch in query_vars ({len(query_vars)}) and solution_item.args ({len(solution_item.args)})")
                
                if bindings:
                    logger.debug(f"Runtime.query: Yielding bindings: {bindings}")
                    solution_count +=1
                    yield bindings
            elif isinstance(solution_item, TRUE) or isinstance(solution_item, Term):
                logger.debug("Runtime.query: Yielding empty bindings for ground query success: {}")
                solution_count +=1
                yield {}
        logger.info(f"Runtime.query for '{query_str}' finished. Total solutions yielded: {solution_count}")


    def register_function(self, func, predicate, arity):
        logger.debug(f"Runtime.register_function: func={func}, predicate='{predicate}', arity={arity}")
        args = []
        for i in range(arity):
            args.append(f'placeholder_{i}')
        tf = TermFunction(func, predicate, *args)
        self.rules.append(Rule(tf, TRUE()))

    def insert_rule_left(self, entry):
        if isinstance(entry, Term):
            entry = Rule(entry, TRUE())
        for i, item in enumerate(self.rules):
            if entry.head.pred == item.head.pred:
                self.rules.insert(i, entry)
                return
        self.rules.append(entry)

    def insert_rule_right(self, entry):
        if isinstance(entry, Term):
            entry = Rule(entry, TRUE())
        last_index = -1
        for i, item in enumerate(self.rules):
            if entry.head.pred == item.head.pred:
                last_index = i

        if last_index == -1:
            self.rules.append(entry)
        else:
            self.rules.insert(last_index + 1, entry)

    def remove_rule(self, rule):
        if isinstance(rule, Term):
            rule = Rule(rule, TRUE())
        for i, item in enumerate(self.rules):
            if (
                rule.head.pred == item.head.pred
                and len(rule.head.args) == len(item.head.args)
                and all(
                    [
                        (
                            x.pred == y.pred
                            if isinstance(x, Term)
                            and isinstance(y, Term)  # noqa
                            else (
                                x.name == y.name
                                if isinstance(x, Variable)
                                and isinstance(y, Variable)  # noqa
                                else False
                            )
                        )
                        for x, y in zip(rule.head.args, item.head.args)
                    ]
                )
            ):
                self.rules.pop(i)
                break

    def all_rules(self, query):
        rules = self.rules[:]
        if isinstance(query, Rule):
            return rules + [query]
        return rules

    def evaluate_rules(self, query_rule_obj, goal_term): # Renamed params for clarity
        logger.debug(f"Runtime.evaluate_rules: query_rule_obj={query_rule_obj}, goal_term={goal_term}")
        for db_rule in self.all_rules(query_rule_obj):
            logger.debug(f"Runtime.evaluate_rules: Trying DB rule: {db_rule}")

            match_bindings = db_rule.head.match(goal_term)
            logger.debug(f"Runtime.evaluate_rules: Match attempt of {db_rule.head} with {goal_term} -> bindings: {match_bindings}")

            if match_bindings is not None:
                logger.debug(f"Runtime.evaluate_rules: Match success. DB rule head: {db_rule.head}, Goal: {goal_term}")
                substituted_rule_head = db_rule.head.substitute(match_bindings)
                substituted_rule_body = db_rule.body.substitute(match_bindings)
                logger.debug(f"Runtime.evaluate_rules: Substituted DB rule head: {substituted_rule_head}, body: {substituted_rule_body}")

                if isinstance(substituted_rule_body, Arithmetic):
                    logger.debug(f"Runtime.evaluate_rules: Body is Arithmetic: {substituted_rule_body}")
                    if hasattr(substituted_rule_body, 'var') and isinstance(substituted_rule_body.var, Variable):
                        var_to_bind = substituted_rule_body.var
                        value = substituted_rule_body.evaluate()
                        
                        final_head_for_arith = substituted_rule_head.substitute({var_to_bind: value})
                        logger.debug(f"Runtime.evaluate_rules: Arithmetic body evaluated. Yielding: {final_head_for_arith}")
                        yield final_head_for_arith
                    else:
                        logger.warning(f"Runtime.evaluate_rules: Arithmetic body {substituted_rule_body} does not have expected 'var' attribute.")

                else: # Body is TRUE, a Term, or a Conjunction
                    logger.debug(f"Runtime.evaluate_rules: Body is not Arithmetic. Calling body.query for: {substituted_rule_body}")
                    for body_solution_item in substituted_rule_body.query(self):
                        logger.debug(f"Runtime.evaluate_rules: Item from body.query: {body_solution_item}")
                        if isinstance(body_solution_item, CUT): # types.CUT signal
                            logger.debug("Runtime.evaluate_rules: CUT signal received from body.query. Yielding CUT and returning.")
                            yield body_solution_item
                            return
                        
                        if not isinstance(body_solution_item, FALSE):
                            final_solution_head = substituted_rule_head.substitute(
                                substituted_rule_body.match(body_solution_item)
                            )
                            logger.debug(f"Runtime.evaluate_rules: Yielding successful head: {final_solution_head}")
                            yield final_solution_head
                        elif isinstance(body_solution_item, FALSE):
                            logger.debug("Runtime.evaluate_rules: Body solution was FALSE. Trying next body solution or backtracking.")
            else:
                logger.debug(f"Runtime.evaluate_rules: Match failed for DB rule {db_rule.head} with goal {goal_term}")
        logger.debug(f"Runtime.evaluate_rules: All DB rules tried for goal_term={goal_term}. Finished.")


    def execute(self, query_obj): # query_obj is a Term or a Rule (from parser.parse_query)
        logger.debug(f"Runtime.execute called with query_obj: {query_obj}")
        goal_to_evaluate = query_obj
        if isinstance(query_obj, Arithmetic):
            logger.debug(f"Runtime.execute: query_obj is Arithmetic: {query_obj}")
            if hasattr(query_obj, 'var') and isinstance(query_obj.var, Variable):
                # This is for a query like `X is 1+2`.
                # We yield a structure that `Runtime.query` can turn into `{Variable('X'): Number(3)}`.
                # The `##` convention is used for this.
                # `parse_query` for `X is 1+2.` produces `Rule(Term("##", X), Arithmetic(X, 1+2))`.
                # So `execute` will get this Rule, not the Arithmetic term directly for such queries.
                # This path is for when an Arithmetic term is executed directly, perhaps as a subgoal.
                # In that case, it should yield its value, and the caller (e.g. Conjunction.query) handles it.
                value = query_obj.evaluate()
                logger.debug(f"Runtime.execute: Arithmetic {query_obj} (with var) evaluated to {value}. Yielding value.")
                yield value # Yield the evaluated value, Conjunction will handle binding.
            else: # e.g. a ground arithmetic expression like `1+2` as a goal (if supported)
                value = query_obj.evaluate()
                logger.debug(f"Runtime.execute: Arithmetic {query_obj} (ground) evaluated to {value}. Yielding value.")
                yield value

        else: # query_obj is a Term (fact/goal) or a Rule (parsed query or actual rule)
            if isinstance(query_obj, Rule):
                # This is typically the Rule object from parse_query, e.g., Rule(Term("##", Vars), BodyConjunction)
                # Or it could be a rule being asserted/retracted if those builtins call execute.
                goal_to_evaluate = query_obj.head # For Rule(##,Body), goal_to_evaluate is ##(...)
                logger.debug(f"Runtime.execute: query_obj is Rule. Goal to evaluate: {goal_to_evaluate}. Original query rule: {query_obj}")
            else: # query_obj is a simple Term (e.g. a fact `p(a)` used as a query, or a subgoal term)
                logger.debug(f"Runtime.execute: query_obj is Term: {query_obj}. Goal to evaluate is same.")
            
            yield from self.evaluate_rules(query_obj, goal_to_evaluate)
        logger.debug(f"Runtime.execute for query_obj: {query_obj} finished.")
