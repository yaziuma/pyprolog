import io
# from typing import cast # Not used in the design doc's Runtime snippets
from prolog.core_types import (
    Term, Variable, Rule, Conjunction,
    TRUE_TERM, FALSE_TERM, CUT_SIGNAL, FAIL_TERM # Import renamed singletons
)
from prolog.types import TermFunction # Import TermFunction
from prolog.token_type import TokenType
from prolog.logger import logger
from prolog.binding_environment import BindingEnvironment
# Ensure builtins are correctly referenced, assuming prolog.builtins for these
from prolog.builtins import Cut as BuiltinCut, Fail as BuiltinFail

# Scanner and Parser will be imported inside methods to break circular dependency

# Rule and Conjunction classes are now imported from prolog.core_types.
# Their definitions have been removed from this file.

class Runtime:
    def __init__(self, rules):
        # logger.debug(f"Runtime initialized with rules (count: {len(rules)}): {rules[:3]}{'...' if len(rules) > 3 else ''}")
        self.rules = rules # List of Rule objects
        self.stream = io.StringIO()
        self.stream_pos = 0
        self.binding_env = BindingEnvironment()
        self._registered_functions = {} # For TermFunction

    def __del__(self):
        # logger.debug("Runtime.__del__ called")
        self.stream.close()

    def stream_write(self, text):
        self.stream.write(text)

    def stream_read(self):
        self.stream.seek(self.stream_pos)
        line = self.stream.read()
        self.stream_pos = self.stream.tell()
        return line

    def reset_stream(self):
        # logger.debug("Runtime.reset_stream called")
        self.stream.seek(0)
        self.stream.truncate(0)
        self.stream_pos = 0

    def consult_rules(self, rules_str):
        from prolog.scanner import Scanner
        from prolog.parser import Parser
        # logger.debug(f"Runtime.consult_rules called with: {rules_str[:100]}{'...' if len(rules_str) > 100 else ''}")
        if not rules_str.strip():
            return

        tokens = Scanner(rules_str).tokenize()
        if not tokens or (len(tokens) == 1 and tokens[0].token_type == TokenType.EOF):
            return
        
        new_rules = Parser(tokens).parse_rules() # This should return list of Rule objects
        self.rules.extend(new_rules)

    def query(self, query_str):
        from prolog.scanner import Scanner
        from prolog.parser import Parser
        # logger.debug(f"Runtime.query called with: '{query_str}'")
        
        self.binding_env = BindingEnvironment() # Reset for each new query
        
        tokens = Scanner(query_str).tokenize()
        # logger.debug(f"Runtime.query: tokens (first 5): {tokens[:5]}{'...' if len(tokens) > 5 else ''}")

        if not tokens or (len(tokens) == 1 and tokens[0].token_type == TokenType.EOF):
            # logger.debug("Runtime.query: no relevant tokens, returning (no solutions).")
            return

        parsed_query = Parser(tokens).parse_query() 
        # logger.debug(f"Runtime.query: parsed_query: {parsed_query}, type: {type(parsed_query)}")

        query_vars = []
        
        def find_variables(term, found_vars_list): 
            if isinstance(term, Variable):
                if term.name != '_' and term not in found_vars_list:
                     found_vars_list.append(term)
            elif isinstance(term, Rule): # Check Rule first as it's more specific
                if hasattr(term, 'head') and term.head is not None:
                    find_variables(term.head, found_vars_list)
                if hasattr(term, 'body') and term.body is not None:
                    find_variables(term.body, found_vars_list)
            elif isinstance(term, Term): # General Term (includes Conjunction)
                if hasattr(term, 'args') and term.args is not None: 
                    for arg_item in term.args: 
                        find_variables(arg_item, found_vars_list)
        
        temp_query_vars = []
        find_variables(parsed_query, temp_query_vars)
        query_vars = temp_query_vars

        # logger.debug(f"Runtime.query: Found variables in query: {[var.name for var in query_vars if var is not None]}")
        
        solution_count = 0
        for solution_item in self.execute(parsed_query): 
            # logger.debug(f"Runtime.query: solution_item from execute: {solution_item}, type: {type(solution_item)}")
            
            if solution_item is FALSE_TERM or solution_item is None: # Use singleton instance
                # logger.debug("Runtime.query: solution_item is FALSE_TERM or None, skipping.")
                continue
            if solution_item is CUT_SIGNAL: # Use singleton instance
                logger.warning("Runtime.query: CUT_SIGNAL reached top-level query.")
                break 

            current_bindings = {}
            if query_vars:
                for var in query_vars:
                    value = self.binding_env.get_value(var)
                    if value != var: 
                        current_bindings[var] = value
                
                if current_bindings or not query_vars: 
                    solution_count += 1
                    yield current_bindings
            elif solution_item is TRUE_TERM: # Use singleton instance
                solution_count += 1
                yield {} 
        
        # logger.info(f"Runtime.query for '{query_str}' finished. Total solutions yielded: {solution_count}")

    # Methods for dynamic rule manipulation (asserta, assertz, retract)
    def asserta(self, rule_to_assert):
        if not isinstance(rule_to_assert, Rule):
            if isinstance(rule_to_assert, Term):
                rule_to_assert = Rule(rule_to_assert, TRUE_TERM)
            else:
                logger.error(f"asserta: Expected Rule or Term, got {type(rule_to_assert)}")
                return False 
        self.rules.insert(0, rule_to_assert)
        return True 

    def assertz(self, rule_to_assert):
        if not isinstance(rule_to_assert, Rule):
            if isinstance(rule_to_assert, Term):
                rule_to_assert = Rule(rule_to_assert, TRUE_TERM)
            else:
                logger.error(f"assertz: Expected Rule or Term, got {type(rule_to_assert)}")
                return False
        self.rules.append(rule_to_assert)
        return True

    def retract(self, rule_template_to_retract):
        rules_to_keep = []
        retracted_once = False
        for r in self.rules:
            if not retracted_once:
                can_match = False
                # Simplified matching for retract. A full implementation needs robust unification.
                # If rule_template_to_retract is a Rule, attempt to match head and body.
                # If it's a Term, attempt to match r.head.
                if isinstance(rule_template_to_retract, Rule):
                    # This requires Rule to have a proper __eq__ or a match method.
                    # For now, assume a simple direct comparison or head predicate/arity match.
                    if r.head.pred == rule_template_to_retract.head.pred and \
                       len(r.head.args) == len(rule_template_to_retract.head.args):
                        # A more complete check would unify r.head with rule_template_to_retract.head
                        # and r.body with rule_template_to_retract.body using a temporary BindingEnvironment.
                        # For now, if heads match by pred/arity and bodies are structurally similar (e.g. both TRUE_TERM)
                        if type(r.body) is type(rule_template_to_retract.body): # Simplistic body check
                             # This is still a placeholder. Real unification is needed.
                             # Let's assume if the test provides a Rule object, it expects exact match.
                             if r == rule_template_to_retract: # Requires Rule.__eq__
                                can_match = True

                elif isinstance(rule_template_to_retract, Term):
                    temp_env = BindingEnvironment()
                    # Create a fresh copy of r.head to avoid side effects during unification test
                    # This is important if r.head contains variables.
                    # A simple way: r_head_copy = r.head.substitute({}) 
                    # However, substitute might not be deep enough or might create new var names.
                    # For now, assume unify handles this correctly or that heads are ground.
                    if temp_env.unify(r.head, rule_template_to_retract):
                        can_match = True
                
                if can_match:
                    retracted_once = True
                    continue 
            rules_to_keep.append(r)
        
        self.rules = rules_to_keep
        return retracted_once

    def insert_rule_left(self, rule):
        return self.asserta(rule)

    def insert_rule_right(self, rule):
        return self.assertz(rule)

    def remove_rule(self, rule_template): 
        return self.retract(rule_template)

    def register_function(self, predicate_name, arity, python_callable):
        logger.info(f"Runtime.register_function for {predicate_name}/{arity}.")
        # Store the callable. It's assumed that the parser or a specific mechanism
        # will create TermFunction instances for these when they appear in queries/rules.
        self._registered_functions[(predicate_name, arity)] = python_callable
        # This registration itself doesn't make them callable through normal rule lookup.
        # `execute` needs to handle `TermFunction` instances.

    def _execute_conjunction(self, conjunction):
        def execute_goals_recursive(index):
            if index >= len(conjunction.args):
                yield TRUE_TERM 
                return
                
            goal = conjunction.args[index]
            mark = self.binding_env.mark_trail()
            
            if goal is CUT_SIGNAL: 
                for _ in execute_goals_recursive(index + 1): 
                    yield CUT_SIGNAL 
                    return 
                self.binding_env.backtrack(mark) 
                return

            any_solution_for_current_goal = False
            for result in self.execute(goal): 
                any_solution_for_current_goal = True
                if result is FALSE_TERM: 
                    continue 
                if result is CUT_SIGNAL: 
                    yield CUT_SIGNAL 
                    self.binding_env.backtrack(mark) 
                    return 
                for _ in execute_goals_recursive(index + 1): 
                    yield TRUE_TERM 
            self.binding_env.backtrack(mark)
            if not any_solution_for_current_goal:
                 pass 
        yield from execute_goals_recursive(0)

    def execute(self, query_obj):
        if query_obj is TRUE_TERM: 
            yield TRUE_TERM
            return
        
        if isinstance(query_obj, BuiltinFail) or query_obj is FAIL_TERM: 
            return 

        if isinstance(query_obj, BuiltinCut):
            yield CUT_SIGNAL 
            return

        # Handle TermFunction before general Term processing
        if isinstance(query_obj, TermFunction):
            # logger.debug(f"Runtime.execute: query_obj is TermFunction: {query_obj}")
            # The original TermFunction._execute_func modified its own args.
            # We need to replicate that behavior or adapt.
            # Let's assume query_obj._execute_func() is called and it updates query_obj.args
            # then we attempt to unify this (now concrete) term.
            try:
                # This is a bit of a guess based on prolog.types.TermFunction.match
                # It implies the function is executed, its results become args,
                # and then it's treated like a fact to be unified.
                query_obj._execute_func() # Modifies query_obj.args in place
                # logger.debug(f"Runtime.execute[TermFunction]: after _execute_func, query_obj: {query_obj}")
                # Now, this TermFunction (with concrete args) needs to "succeed".
                # If it were to be unified against something, that would happen here.
                # For a standalone TermFunction goal, executing it and it not failing means success.
                yield TRUE_TERM
            except Exception:
                # logger.error(f"Runtime.execute[TermFunction]: Error executing function for {query_obj}: {e}")
                # Execution of the Python function failed, so the Prolog goal fails.
                pass # Yield nothing for failure
            return
            
        if isinstance(query_obj, Rule):
            mark = self.binding_env.mark_trail()
            for body_result in self.execute(query_obj.body): 
                if body_result is FALSE_TERM: 
                    self.binding_env.backtrack(mark) 
                    mark = self.binding_env.mark_trail() 
                    continue
                if body_result is CUT_SIGNAL: 
                    yield CUT_SIGNAL
                    return 
                yield TRUE_TERM 
                self.binding_env.backtrack(mark) 
                mark = self.binding_env.mark_trail() 
            self.binding_env.backtrack(mark) 
            return 
                
        elif isinstance(query_obj, Term): 
            if query_obj.pred == '=': 
                if len(query_obj.args) == 2:
                    lhs, rhs = query_obj.args
                    if self.binding_env.unify(lhs, rhs):
                        yield TRUE_TERM 
                    return
                
            for db_rule_template in self.rules: 
                # Standardize apart: Create a fresh copy of the rule.
                # Rule.substitute({}) is a way to get new Variable instances.
                # A more robust solution might involve a dedicated "freshen" method.
                current_scope_id = self.binding_env.get_next_scope_id() # For unique var names
                
                # Simple freshening by creating new variable instances.
                # This relies on Variable.__hash__ and __eq__ being based on unique IDs or names + scope.
                # For now, assume substitute({}) and BindingEnvironment handle distinctness.
                # A more explicit way:
                var_map = {}
                def freshen_term(t):
                    if isinstance(t, Variable):
                        if t not in var_map:
                            var_map[t] = Variable(f"{t.name}_{current_scope_id}") # Or just new instance
                        return var_map[t]
                    elif isinstance(t, Term):
                        return Term(t.pred, *[freshen_term(arg) for arg in t.args])
                    return t

                fresh_head = freshen_term(db_rule_template.head)
                fresh_body = freshen_term(db_rule_template.body)
                fresh_rule = Rule(fresh_head, fresh_body)

                if fresh_rule.head.pred == query_obj.pred and \
                   len(fresh_rule.head.args) == len(query_obj.args):
                    
                    mark = self.binding_env.mark_trail()
                    if self.binding_env.unify(fresh_rule.head, query_obj):
                        for body_result in self.execute(fresh_rule.body):
                            if body_result is FALSE_TERM: 
                                continue 
                            if body_result is CUT_SIGNAL: 
                                yield CUT_SIGNAL
                                # Cut from body commits to this rule. Do not backtrack `mark` for this rule choice.
                                # However, the bindings made by this rule attempt up to the cut are kept.
                                # The cut prunes other choices for `query_obj` and other choices for goals in `fresh_rule.body` after the cut.
                                return 
                            yield TRUE_TERM 
                            # Backtrack for next solution from *this rule's body*
                            # The mark is for the *entire rule attempt*.
                            # When Prolog backtracks here, it asks `execute(fresh_rule.body)` for its next solution.
                            # No explicit backtrack/re-mark here inside the body solution loop for this specific purpose.
                        
                        # After body is exhausted for this rule instance
                        self.binding_env.backtrack(mark) 
                        # No re-mark here; the loop `for db_rule_template` continues to the next rule.
                    else: 
                        self.binding_env.backtrack(mark)
            return 
                        
        elif isinstance(query_obj, Conjunction):
            yield from self._execute_conjunction(query_obj)
            return 
            
        return
