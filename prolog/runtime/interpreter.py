import io
from prolog.core.types import (
    Term,
    Variable,
    Rule,
    Conjunction,
    TRUE_TERM,
    FALSE_TERM,
    CUT_SIGNAL,
    FAIL_TERM,
)
from prolog.parser.token_type import TokenType
from prolog.util.logger import logger
from prolog.core.binding_environment import BindingEnvironment

# BuiltinCutとBuiltinFailをインポート
from prolog.runtime.builtins import Cut as BuiltinCut, Fail as BuiltinFail


class Runtime:
    def __init__(self, rules):
        if isinstance(rules, Rule):
            self.rules = [rules]
        elif rules is None: # Handle cases where rules might be None
            self.rules = []
        else: # Assuming rules is already a list or an iterable that list() can handle
            self.rules = list(rules)
        self.stream = io.StringIO()
        self.stream_pos = 0
        self.binding_env = BindingEnvironment()
        self._registered_functions = {}

    def __del__(self):
        self.stream.close()

    def stream_write(self, text):
        self.stream.write(text)

    def stream_read(self):
        self.stream.seek(self.stream_pos)
        line = self.stream.read()
        self.stream_pos = self.stream.tell()
        return line

    def reset_stream(self):
        self.stream.seek(0)
        self.stream.truncate(0)
        self.stream_pos = 0

    def consult_rules(self, rules_str):
        from prolog.parser.scanner import Scanner
        from prolog.parser.parser import Parser

        if not rules_str.strip():
            return

        tokens = Scanner(rules_str).tokenize()
        if not tokens or (len(tokens) == 1 and tokens[0].token_type == TokenType.EOF):
            return

        # Use parse() to get a list of rules
        parsed_result = Parser(tokens).parse()
        if isinstance(parsed_result, list):
            new_rules = parsed_result
        elif parsed_result is not None: # If parse() somehow returns a single rule
            new_rules = [parsed_result]
        else: # If parse() returns None (e.g., on error and no recovery)
            new_rules = []

        if new_rules: # Only extend if there are rules to add
            self.rules.extend(new_rules)

    def query(self, query_str):
        from prolog.parser.scanner import Scanner
        from prolog.parser.parser import Parser

        # 新しいクエリごとにバインディング環境をリセット
        self.binding_env = BindingEnvironment()

        tokens = Scanner(query_str).tokenize()

        if not tokens or (len(tokens) == 1 and tokens[0].token_type == TokenType.EOF):
            return

        parsed_query = Parser(tokens)._parse_term()

        query_vars = []

        def find_variables(term, found_vars_list):
            if isinstance(term, Variable):
                if term.name != "_" and term not in found_vars_list:
                    found_vars_list.append(term)
            elif isinstance(term, Rule):
                if hasattr(term, "head") and term.head is not None:
                    find_variables(term.head, found_vars_list)
                if hasattr(term, "body") and term.body is not None:
                    find_variables(term.body, found_vars_list)
            elif isinstance(term, Term):
                if hasattr(term, "args") and term.args is not None:
                    for arg_item in term.args:
                        find_variables(arg_item, found_vars_list)

        temp_query_vars = []
        find_variables(parsed_query, temp_query_vars)
        query_vars = temp_query_vars

        solution_count = 0
        for solution_item in self.execute(parsed_query):
            if solution_item is FALSE_TERM or solution_item is None:
                continue
            if solution_item is CUT_SIGNAL:
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
            elif solution_item is TRUE_TERM:
                solution_count += 1
                yield {}

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
                if isinstance(rule_template_to_retract, Rule):
                    if (r.head.pred == rule_template_to_retract.head.pred and 
                        len(r.head.args) == len(rule_template_to_retract.head.args)):
                        if type(r.body) is type(rule_template_to_retract.body):
                            if r == rule_template_to_retract:
                                can_match = True
                elif isinstance(rule_template_to_retract, Term):
                    temp_env = BindingEnvironment()
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
        self._registered_functions[(predicate_name, arity)] = python_callable

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

        # TermFunction処理（もし実装されている場合）
        if hasattr(query_obj, '_execute_func') and callable(getattr(query_obj, '_execute_func')):
            try:
                query_obj._execute_func()
                yield TRUE_TERM
            except Exception:
                pass
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
            # '=' の特別処理
            if query_obj.pred == "=":
                if len(query_obj.args) == 2:
                    lhs, rhs = query_obj.args
                    if self.binding_env.unify(lhs, rhs):
                        yield TRUE_TERM
                    return

            # データベースルールとのマッチング
            for db_rule_template in self.rules:
                # 新しいスコープIDで変数を標準化
                current_scope_id = self.binding_env.get_next_scope_id()

                var_map = {}

                def freshen_term(t):
                    if isinstance(t, Variable):
                        if t not in var_map:
                            var_map[t] = Variable(f"{t.name}_{current_scope_id}")
                        return var_map[t]
                    elif isinstance(t, Term):
                        return Term(t.pred, *[freshen_term(arg) for arg in t.args])
                    return t

                fresh_head = freshen_term(db_rule_template.head)
                fresh_body = freshen_term(db_rule_template.body)
                fresh_rule = Rule(fresh_head, fresh_body)

                if (fresh_rule.head.pred == query_obj.pred and 
                    len(fresh_rule.head.args) == len(query_obj.args)):
                    mark = self.binding_env.mark_trail()
                    if self.binding_env.unify(fresh_rule.head, query_obj):
                        for body_result in self.execute(fresh_rule.body):
                            if body_result is FALSE_TERM:
                                continue
                            if body_result is CUT_SIGNAL:
                                yield CUT_SIGNAL
                                return
                            yield TRUE_TERM

                        self.binding_env.backtrack(mark)
                    else:
                        self.binding_env.backtrack(mark)
            return

        elif isinstance(query_obj, Conjunction):
            yield from self._execute_conjunction(query_obj)
            return

        return
