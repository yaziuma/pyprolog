from prolog.logger import logger
from prolog.parser import Parser
from prolog.scanner import Scanner
from prolog.types import Term, Number, Dot
from .base import BaseTestCore

# --- 2. List Processing ---
class TestListProcessing(BaseTestCore):

    def test_parse_empty_list_direct(self):
        logger.info("Starting test: test_parse_empty_list_direct")
        rule_tokens = Scanner("p([]).").tokenize()
        parsed_rule = Parser(rule_tokens).parse_rules()[0]
        empty_list_term = parsed_rule.head.args[0]

        assert isinstance(empty_list_term, Dot), "Empty list should be parsed as a Dot object."
        assert Term("[]") == empty_list_term.head, f"Head of empty list should be Term('[]'), got {empty_list_term.head}"
        assert empty_list_term.tail is None, f"Tail of empty list should be None, got {empty_list_term.tail}"

        self._consult("sum_list_basic([], 0).")
        self._consult("sum_list_basic([H|T], S) :- sum_list_basic(T, ST), S is H + ST.")
        # ここを修正: 0 を 0.0 に変更
        self._assert_true("sum_list_basic([], Sum)", [{"Sum": Number(0.0)}])

    def test_empty_list_in_query(self):
        logger.info("Starting test: test_empty_list_in_query")
        self._consult("is_empty_list([]).")
        self._assert_true("is_empty_list([])", [])
        self._assert_false("is_empty_list([a])")

    def test_list_unification_with_empty_list(self):
        logger.info("Starting test: test_list_unification_with_empty_list")
        self._assert_true("X = [].", [{"X": Dot.from_list([])}])
        self._assert_true("[] = [].", [])
        self._assert_false("[] = [a].")
        self._assert_false("[a] = [].")

    def test_distinguish_empty_list_from_list_containing_empty_list(self):
        logger.info("Starting test: test_distinguish_empty_list_from_list_containing_empty_list")
        self._consult("p([]).")
        self._consult("q([[]]).")

        self._assert_true("p([])", [])
        self._assert_false("p([[]])")

        self._assert_true("q([[]])", [])
        list_of_empty_list = Dot.from_list([Dot.from_list([])])
        self._assert_true("q(X), X = [[]].", [{"X": list_of_empty_list}]) 
        self._assert_false("q([])")

    def test_recursive_list_processing_sum_list(self):
        logger.info("Starting test: test_recursive_list_processing_sum_list")
        self._consult("sum_list_rec([], 0).")
        self._consult("sum_list_rec([H|T], S) :- sum_list_rec(T, ST), S is H + ST.")
        self._assert_true("sum_list_rec([], X)", [{"X": Number(0)}])
        self._assert_true("sum_list_rec([1,2,3], X)", [{"X": Number(6)}])
        self._assert_true("sum_list_rec([10,20], X)", [{"X": Number(30)}])
        self._assert_false("sum_list_rec(abc, X)")

    def test_member_recursive(self):
        logger.info("Starting test: test_member_recursive")
        self._consult("member_rec(X, [X|_]).")
        self._consult("member_rec(X, [_|T]) :- member_rec(X, T).")
        self._assert_true("member_rec(a, [a,b,c])", []) 
        self._assert_true("member_rec(b, [a,b,c])", [])
        self._assert_true("member_rec(c, [a,b,c])", [])
        self._assert_false("member_rec(d, [a,b,c])")
        self._assert_false("member_rec(a, [])")

        self._assert_true("member_rec(X, [1,2,3])", 
                          [{"X": Number(1)}, {"X": Number(2)}, {"X": Number(3)}])

    def test_deeply_nested_recursive_calls_and_bindings_append(self):
        logger.info("Starting test: test_deeply_nested_recursive_calls_and_bindings_append")
        self._consult("append_rec([], L, L).")
        self._consult("append_rec([H|T1], L2, [H|T3]) :- append_rec(T1, L2, T3).")

        expected_list_1234 = Dot.from_list([Number(1), Number(2), Number(3), Number(4)])
        self._assert_true("append_rec([1,2], [3,4], X)", [{"X": expected_list_1234}])

        expected_x_ab = Dot.from_list([Term("a"), Term("b")])
        self._assert_true("append_rec(X, [c,d], [a,b,c,d])", [{"X": expected_x_ab}])

        expected_y_34 = Dot.from_list([Number(3), Number(4)])
        self._assert_true("append_rec([1,2], Y, [1,2,3,4])", [{"Y": expected_y_34}])
        
        self._assert_true("append_rec(X, Y, [a,b])", [
            {"X": Dot.from_list([]), "Y": Dot.from_list([Term("a"), Term("b")])},
            {"X": Dot.from_list([Term("a")]), "Y": Dot.from_list([Term("b")])},
            {"X": Dot.from_list([Term("a"), Term("b")]), "Y": Dot.from_list([])},
        ])
