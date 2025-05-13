from prolog.logger import logger
from prolog.types import Term, Number, CUT
from .base import BaseTestCore

# --- 4. Cut Operator ---
class TestCutOperator(BaseTestCore):

    def test_cut_operator_simple(self):
        logger.info(f"Starting test: test_cut_operator_simple")
        self._consult("p(X) :- q(X), !, r(X).")
        self._consult("p(X) :- s(X).")
        self._consult("q(1).")
        self._consult("q(2).") 
        self._consult("r(1).")
        self._consult("s(3).") 
        self._assert_true("p(X)", [{"X": Number(1)}]) 

    def test_cut_in_rule_body_only(self):
        logger.info(f"Starting test: test_cut_in_rule_body_only")
        self._consult("cut_test1 :- !.")
        self._consult("cut_test1 :- fail.") 
        self._assert_true("cut_test1", []) 

        self._consult("cut_test2(a) :- !.")
        self._consult("cut_test2(b).") 
        self._assert_true("cut_test2(X)", [{"X": Term("a")}])

    def test_cut_prevents_backtracking_for_alternatives_in_same_predicate(self):
        logger.info(f"Starting test: test_cut_prevents_backtracking_for_alternatives_in_same_predicate")
        self._consult("pred_cut(X) :- a(X), !, b(X).")
        self._consult("pred_cut(fallback).") 
        self._consult("a(1).")
        self._consult("a(2).") 
        self._consult("b(1).")
        self._assert_true("pred_cut(X)", [{"X": Number(1)}])

    def test_cut_prevents_backtracking_for_goals_before_cut(self):
        logger.info(f"Starting test: test_cut_prevents_backtracking_for_goals_before_cut")
        self._consult("path(X,Y) :- edge(X,Z), !, path(Z,Y).") 
        self._consult("path(X,X).")
        self._consult("edge(a,b).")
        self._consult("edge(a,c).") 
        self._consult("edge(b,d).")
        self._assert_true("path(a,Y)", [{"Y": Term("d")}])

    def test_cut_with_failure_after_cut(self):
        logger.info(f"Starting test: test_cut_with_failure_after_cut")
        self._consult("try_cut(X) :- first(X), !, second(X).")
        self._consult("try_cut(default).") 
        self._consult("first(1).")
        self._consult("first(2).")
        self._consult("second(1) :- fail.") 
        self._consult("second(2).")
        self._assert_false("try_cut(1)")
        self._assert_true("try_cut(2)", []) 

    def test_cut_match_behavior(self): 
        logger.info(f"Starting test: test_cut_match_behavior")
        self._consult("is_cut_term(!).") 
        self._assert_true("is_cut_term(!)", []) 
        self._assert_true("X = !, is_cut_term(X).", [{"X": CUT}]) 

        self._assert_true("! = !.", []) 
        self._assert_true("X = !.", [{"X": CUT}])
        self._assert_false("! = a.")
        self._assert_false("a = !.")

        self._consult("struct_has_cut(s(!)).")
        self._assert_true("struct_has_cut(s(!))", []) 
        self._assert_true("struct_has_cut(s(X)), X = !.", [{"X": CUT}])
        self._assert_false("struct_has_cut(s(a))")
        logger.info("Finished test_cut_match_behavior")
