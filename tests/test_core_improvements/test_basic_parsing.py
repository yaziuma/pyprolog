from prolog.logger import logger
from prolog.types import Term
from .base import BaseTestCore

# --- 1. Basic Parsing, Types, and Simple Predicates ---
class TestBasicParsingAndTypes(BaseTestCore):

    def test_simple_fact_consult_and_query(self):
        logger.info("Starting test: test_simple_fact_consult_and_query")
        self._consult("p(a).")
        self._assert_true("p(a)", []) 
        self._assert_true("p(X)", [{"X": Term("a")}])
        self._assert_false("p(b)")

    def test_true_predicate(self):
        logger.info("Starting test: test_true_predicate")
        self._assert_true("true", [])

    def test_fail_predicate(self):
        logger.info("Starting test: test_fail_predicate")
        self._assert_false("fail")
        self._consult("my_fail :- fail.")
        self._assert_false("my_fail")

    def test_query_resulting_in_false_type(self): 
        logger.info("Starting test: test_query_resulting_in_false_type")
        self._assert_false("a = b") 
        self._consult("always_fail_rule :- fail.")
        self._assert_false("always_fail_rule")
