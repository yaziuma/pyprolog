from prolog.logger import logger
from prolog.types import Number, Term
from .base import BaseTestCore


# --- 5.5. より詳細な再帰テスト ---
class TestAdvancedRecursion(BaseTestCore):
    """
    より複雑な再帰に関するテスト
    """

    def test_mutual_recursion(self):
        """相互再帰のテスト"""
        logger.info("Starting test: test_mutual_recursion")
        self._consult("even(0).")
        self._consult("even(N) :- N > 0, N1 is N - 1, odd(N1).")
        self._consult("odd(N) :- N > 0, N1 is N - 1, even(N1).")

        self._assert_true("even(0)", [])
        self._assert_true("even(2)", [])
        self._assert_true("even(4)", [])
        self._assert_false("even(1)")
        self._assert_false("even(3)")

        self._assert_true("odd(1)", [])
        self._assert_true("odd(3)", [])
        self._assert_false("odd(0)")
        self._assert_false("odd(2)")

    def test_recursive_definition_with_multiple_base_cases(self):
        """複数の基底ケースを持つ再帰定義のテスト"""
        logger.info("Starting test: test_recursive_definition_with_multiple_base_cases")
        self._consult("fibonacci(0, 0).")
        self._consult("fibonacci(1, 1).")
        self._consult(
            "fibonacci(N, F) :- N > 1, N1 is N - 1, N2 is N - 2, fibonacci(N1, F1), fibonacci(N2, F2), F is F1 + F2."
        )

        self._assert_true("fibonacci(0, F)", [{"F": Number(0)}])
        self._assert_true("fibonacci(1, F)", [{"F": Number(1)}])
        self._assert_true("fibonacci(2, F)", [{"F": Number(1)}])
        self._assert_true("fibonacci(3, F)", [{"F": Number(2)}])
        self._assert_true("fibonacci(4, F)", [{"F": Number(3)}])
        self._assert_true("fibonacci(5, F)", [{"F": Number(5)}])

    def test_accumulator_recursion(self):
        """アキュムレータを使った末尾再帰のテスト"""
        logger.info("Starting test: test_accumulator_recursion")
        self._consult("sum_list_acc([], Acc, Acc).")
        self._consult(
            "sum_list_acc([H|T], Acc, Sum) :- NewAcc is Acc + H, sum_list_acc(T, NewAcc, Sum)."
        )
        self._consult("sum_list(List, Sum) :- sum_list_acc(List, 0, Sum).")

        self._assert_true("sum_list([], Sum)", [{"Sum": Number(0)}])
        self._assert_true("sum_list([1,2,3], Sum)", [{"Sum": Number(6)}])
        self._assert_true("sum_list([10,20], Sum)", [{"Sum": Number(30)}])

        # より複雑な末尾再帰の例: 階乗
        self._consult("factorial_acc(0, Acc, Acc).")
        self._consult(
            "factorial_acc(N, Acc, F) :- N > 0, NewAcc is Acc * N, N1 is N - 1, factorial_acc(N1, NewAcc, F)."
        )
        self._consult("factorial_tail(N, F) :- factorial_acc(N, 1, F).")

        self._assert_true("factorial_tail(0, F)", [{"F": Number(1)}])
        self._assert_true("factorial_tail(1, F)", [{"F": Number(1)}])
        self._assert_true("factorial_tail(5, F)", [{"F": Number(120)}])

    # TestControlFlowStructuresクラスから移動したテスト
    def test_if_then_else_pattern(self):
        """if-then-elseパターンのテスト"""
        logger.info("Starting test: test_if_then_else_pattern")
        self._consult("if_then_else(Condition, Then, _Else) :- Condition, !, Then.")
        self._consult("if_then_else(_Condition, _Then, Else) :- Else.")

        self._consult("positive(X) :- X > 0.")
        self._consult("negative(X) :- X < 0.")
        self._consult("zero(X) :- X == 0.")

        self._consult(
            "sign(X, Result) :- if_then_else(positive(X), Result = positive, if_then_else(negative(X), Result = negative, Result = zero))."
        )

        self._assert_true("sign(5, R)", [{"R": Term("positive")}])
        self._assert_true("sign(-3, R)", [{"R": Term("negative")}])
        self._assert_true("sign(0, R)", [{"R": Term("zero")}])

    def test_repeat_and_fail_pattern(self):
        """repeat-failパターンのテスト"""
        logger.info("Starting test: test_repeat_and_fail_pattern")
        self._consult("repeat.")
        self._consult("repeat :- repeat.")

        self._consult("count_up_to(Max, Max) :- !.")
        self._consult(
            "count_up_to(Current, Max) :- Current < Max, Next is Current + 1, count_up_to(Next, Max)."
        )

        self._assert_true("count_up_to(1, 3), fail", [])  # 常に失敗する

        # repeatとfailの組み合わせ
        self._consult("generate_and_test(X) :- repeat, generate(X), test(X), !.")
        self._consult("generate(1). generate(2). generate(3).")
        self._consult("test(X) :- X > 1.")

        self._assert_true(
            "generate_and_test(X)", [{"X": Number(2)}]
        )  # 最初に条件を満たす値
