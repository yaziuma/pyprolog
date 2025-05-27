from prolog.logger import logger
from prolog.types import Term, Number, Dot
from .base import BaseTestCore


# --- 2.5. より詳細なリスト操作テスト ---
class TestAdvancedListOperations(BaseTestCore):
    """
    より複雑なリスト操作に関するテスト
    """

    def test_nested_lists(self):
        """ネストされたリストのテスト"""
        logger.info("Starting test: test_nested_lists")
        self._consult("nested_list([a, [b, c], d]).")
        self._assert_true("nested_list([a, [b, c], d])", [])
        self._assert_true(
            "nested_list([a, X, d])", [{"X": Dot.from_list([Term("b"), Term("c")])}]
        )

    def test_list_with_repeated_variables(self):
        """同じ変数が複数回出現するリストのテスト"""
        logger.info("Starting test: test_list_with_repeated_variables")
        self._assert_true("[X, X] = [a, a]", [{"X": Term("a")}])
        self._assert_false("[X, X] = [a, b]")
        self._assert_true("[X, Y, X] = [a, b, a]", [{"X": Term("a"), "Y": Term("b")}])

    def test_list_bar_notation(self):
        """[H|T]記法のテスト"""
        logger.info("Starting test: test_list_bar_notation")
        self._assert_true(
            "[H|T] = [a, b, c]",
            [{"H": Term("a"), "T": Dot.from_list([Term("b"), Term("c")])}],
        )
        self._assert_true(
            "[A, B|T] = [1, 2, 3, 4]",
            [
                {
                    "A": Number(1),
                    "B": Number(2),
                    "T": Dot.from_list([Number(3), Number(4)]),
                }
            ],
        )
        self._assert_false("[H|T] = []")

    def test_list_operations_with_empty_list(self):
        """空リストを含むリスト操作のテスト"""
        logger.info("Starting test: test_list_operations_with_empty_list")
        self._consult("append([], L, L).")
        self._consult("append([H|T], L, [H|R]) :- append(T, L, R).")
        self._assert_true("append([], [a], X)", [{"X": Dot.from_list([Term("a")])}])
        self._assert_true("append([], [], X)", [{"X": Dot.from_list([])}])

        self._consult("length([], 0).")
        self._consult("length([_|T], N) :- length(T, N1), N is N1 + 1.")
        self._assert_true("length([], N)", [{"N": Number(0)}])
