"""
IOPredicate基底クラスのテスト

統一入力システム設計に基づくIOPredicate基底クラスの
テンプレートメソッドパターンと共通処理をテストする。
"""

import pytest
from unittest.mock import Mock
from abc import ABC, abstractmethod
from typing import Iterator, Optional


# テスト用の抽象基底クラス実装（実際の実装前のテスト用）
class BuiltinPredicate:
    """テスト用BuiltinPredicate基底クラス"""

    def __init__(self, *args):
        self.args = list(args)


class PrologType:
    """テスト用PrologType基底クラス"""

    pass


class Atom(PrologType):
    """テスト用Atom実装"""

    def __init__(self, value: str):
        self.value = value

    def __eq__(self, other):
        return isinstance(other, Atom) and self.value == other.value

    def __repr__(self):
        return f"Atom({self.value})"


class Number(PrologType):
    """テスト用Number実装"""

    def __init__(self, value):
        self.value = value

    def __eq__(self, other):
        return isinstance(other, Number) and self.value == other.value

    def __repr__(self):
        return f"Number({self.value})"


class PrologError(Exception):
    """テスト用PrologError"""

    pass


class BindingEnvironment:
    """テスト用束縛環境"""

    def __init__(self, bindings=None):
        self.bindings = bindings or {}


def try_convert_atom_to_number(value: str):
    """テスト用数値変換関数"""
    try:
        if "." in value:
            return float(value)
        else:
            return int(value)
    except ValueError:
        return None


# IOPredicate基底クラス（設計に基づく実装）
class IOPredicate(BuiltinPredicate, ABC):
    """
    入出力述語の共通基底クラス

    テンプレートメソッドパターンを使用し、共通処理を基底クラスに集約。
    サブクラスは入力タイプ固有の処理のみ実装する。
    """

    def __init__(self, *args):
        super().__init__(*args)
        self._validate_arguments()

    # 抽象メソッド（サブクラスで実装必須）
    @abstractmethod
    def _get_expected_arg_count(self) -> int:
        """期待する引数数を返す"""
        pass

    @abstractmethod
    def _get_predicate_name(self) -> str:
        """述語名を返す"""
        pass

    @abstractmethod
    def _get_input_type(self) -> str:
        """入力タイプを返す"""
        pass

    @abstractmethod
    def _convert_to_prolog_term(self, input_value: Optional[str]) -> PrologType:
        """入力値をPrologタームに変換"""
        pass

    # 共通実装（テンプレートメソッドパターン）
    def execute(
        self, runtime: Mock, env: BindingEnvironment
    ) -> Iterator[BindingEnvironment]:
        """共通実行フロー"""
        try:
            # Step 1: 統一入力システム経由で入力取得
            input_value = self._request_input(runtime)

            # Step 2: Prologターム変換
            target_term = self._convert_to_prolog_term(input_value)

            # Step 3: 統一化実行
            yield from self._unify_with_argument(runtime, env, target_term)

        except Exception:
            # エラー時は述語失敗（何もyieldしない）
            return

    def _validate_arguments(self):
        """引数数検証"""
        expected_count = self._get_expected_arg_count()
        actual_count = len(self.args)

        if actual_count != expected_count:
            raise PrologError(
                f"{self._get_predicate_name()}/{expected_count} expects "
                f"{expected_count} argument(s), got {actual_count}"
            )

    def _request_input(self, runtime: Mock) -> Optional[str]:
        """統一入力システム経由での入力要求"""
        return runtime.io_manager.request_input(
            input_type=self._get_input_type(),
            predicate_name=self._get_predicate_name(),
            prompt=self._get_prompt(),
        )

    def _unify_with_argument(
        self, runtime: Mock, env: BindingEnvironment, target_term: PrologType
    ) -> Iterator[BindingEnvironment]:
        """引数との統一化"""
        prolog_arg = self.args[0]

        unified, next_env = runtime.logic_interpreter.unify(
            prolog_arg, target_term, env
        )

        if unified:
            yield next_env

    # ユーティリティメソッド
    def _get_prompt(self) -> str:
        """プロンプト文字列を取得"""
        return f"{self._get_predicate_name()}: "

    def _handle_eof(self) -> Atom:
        """EOF処理"""
        return Atom("end_of_file")

    def _try_convert_to_number(self, value: str) -> Optional[PrologType]:
        """数値変換試行"""
        if not value:
            return None

        number_value = try_convert_atom_to_number(value)
        if number_value is not None:
            return Number(number_value)
        return None


# テスト用具象クラス
class TestGetCharPredicate(IOPredicate):
    """get_char/1述語のテスト用実装"""

    def _get_expected_arg_count(self) -> int:
        return 1

    def _get_predicate_name(self) -> str:
        return "get_char"

    def _get_input_type(self) -> str:
        return "char"

    def _convert_to_prolog_term(self, input_value: Optional[str]) -> PrologType:
        if input_value is None or input_value == "":
            return self._handle_eof()

        char = input_value[0] if len(input_value) > 0 else ""

        if char.isdigit():
            return Number(int(char))
        else:
            return Atom(char)


class TestReadLinePredicate(IOPredicate):
    """read_line/1述語のテスト用実装"""

    def _get_expected_arg_count(self) -> int:
        return 1

    def _get_predicate_name(self) -> str:
        return "read_line"

    def _get_input_type(self) -> str:
        return "line"

    def _convert_to_prolog_term(self, input_value: Optional[str]) -> PrologType:
        if input_value is None:
            return self._handle_eof()

        number_term = self._try_convert_to_number(input_value)
        return number_term if number_term else Atom(input_value)


class TestIOPredicateBase:
    """IOPredicate基底クラスのテストクラス"""

    def test_argument_validation_success(self):
        """引数数検証：正常ケース"""
        # 1つの引数で初期化（get_char/1）
        predicate = TestGetCharPredicate("X")
        assert len(predicate.args) == 1

    def test_argument_validation_failure(self):
        """引数数検証：異常ケース"""
        # 引数数が不正な場合、PrologErrorが発生
        with pytest.raises(
            PrologError, match=r"get_char/1 expects 1 argument\(s\), got 0"
        ):
            TestGetCharPredicate()

        with pytest.raises(
            PrologError, match=r"get_char/1 expects 1 argument\(s\), got 2"
        ):
            TestGetCharPredicate("X", "Y")

    def test_prompt_generation(self):
        """プロンプト文字列生成"""
        predicate = TestGetCharPredicate("X")
        assert predicate._get_prompt() == "get_char: "

        line_predicate = TestReadLinePredicate("X")
        assert line_predicate._get_prompt() == "read_line: "

    def test_eof_handling(self):
        """EOF処理"""
        predicate = TestGetCharPredicate("X")
        eof_atom = predicate._handle_eof()

        assert isinstance(eof_atom, Atom)
        assert eof_atom.value == "end_of_file"

    def test_number_conversion_success(self):
        """数値変換：成功ケース"""
        predicate = TestGetCharPredicate("X")

        # 整数変換
        result = predicate._try_convert_to_number("123")
        assert isinstance(result, Number)
        assert result.value == 123

        # 浮動小数点変換
        result = predicate._try_convert_to_number("45.67")
        assert isinstance(result, Number)
        assert result.value == 45.67

    def test_number_conversion_failure(self):
        """数値変換：失敗ケース"""
        predicate = TestGetCharPredicate("X")

        # 空文字列
        result = predicate._try_convert_to_number("")
        assert result is None

        # 数値以外の文字列
        result = predicate._try_convert_to_number("hello")
        assert result is None

    def test_get_char_conversion(self):
        """get_char述語のPrologターム変換"""
        predicate = TestGetCharPredicate("X")

        # 数字文字
        result = predicate._convert_to_prolog_term("5")
        assert isinstance(result, Number)
        assert result.value == 5

        # アルファベット文字
        result = predicate._convert_to_prolog_term("a")
        assert isinstance(result, Atom)
        assert result.value == "a"

        # 複数文字（最初の文字のみ使用）
        result = predicate._convert_to_prolog_term("abc")
        assert isinstance(result, Atom)
        assert result.value == "a"

        # EOF
        result = predicate._convert_to_prolog_term(None)
        assert isinstance(result, Atom)
        assert result.value == "end_of_file"

        result = predicate._convert_to_prolog_term("")
        assert isinstance(result, Atom)
        assert result.value == "end_of_file"

    def test_read_line_conversion(self):
        """read_line述語のPrologターム変換"""
        predicate = TestReadLinePredicate("X")

        # 数値文字列
        result = predicate._convert_to_prolog_term("123")
        assert isinstance(result, Number)
        assert result.value == 123

        # 一般文字列
        result = predicate._convert_to_prolog_term("hello")
        assert isinstance(result, Atom)
        assert result.value == "hello"

        # EOF
        result = predicate._convert_to_prolog_term(None)
        assert isinstance(result, Atom)
        assert result.value == "end_of_file"

    def test_request_input_call(self):
        """統一入力システム呼び出し"""
        predicate = TestGetCharPredicate("X")

        # モックRuntime作成
        mock_runtime = Mock()
        mock_runtime.io_manager.request_input.return_value = "a"

        result = predicate._request_input(mock_runtime)

        # 正しいパラメータで呼び出されることを確認
        mock_runtime.io_manager.request_input.assert_called_once_with(
            input_type="char", predicate_name="get_char", prompt="get_char: "
        )
        assert result == "a"

    def test_unify_with_argument(self):
        """引数との統一化"""
        predicate = TestGetCharPredicate("X")

        # モック設定
        mock_runtime = Mock()
        mock_env = BindingEnvironment()
        mock_next_env = BindingEnvironment()

        # 統一化成功ケース
        mock_runtime.logic_interpreter.unify.return_value = (True, mock_next_env)

        target_term = Atom("a")
        results = list(
            predicate._unify_with_argument(mock_runtime, mock_env, target_term)
        )

        # 統一化が呼ばれることを確認
        mock_runtime.logic_interpreter.unify.assert_called_once_with(
            "X", target_term, mock_env
        )

        # 成功時は新しい束縛環境が返される
        assert len(results) == 1
        assert results[0] == mock_next_env

        # 統一化失敗ケース
        mock_runtime.logic_interpreter.unify.return_value = (False, None)
        results = list(
            predicate._unify_with_argument(mock_runtime, mock_env, target_term)
        )

        # 失敗時は空のリストが返される
        assert len(results) == 0

    def test_execute_template_method(self):
        """execute()テンプレートメソッドの動作"""
        predicate = TestGetCharPredicate("X")

        # モック設定
        mock_runtime = Mock()
        mock_env = BindingEnvironment()
        mock_next_env = BindingEnvironment()

        # 入力取得の設定
        mock_runtime.io_manager.request_input.return_value = "5"

        # 統一化成功の設定
        mock_runtime.logic_interpreter.unify.return_value = (True, mock_next_env)

        # execute()実行
        results = list(predicate.execute(mock_runtime, mock_env))

        # 各ステップが実行されることを確認
        # Step 1: 入力要求
        mock_runtime.io_manager.request_input.assert_called_once_with(
            input_type="char", predicate_name="get_char", prompt="get_char: "
        )

        # Step 2: 変換 → Step 3: 統一化
        mock_runtime.logic_interpreter.unify.assert_called_once_with(
            "X", Number(5), mock_env
        )

        # 成功時は束縛環境が返される
        assert len(results) == 1
        assert results[0] == mock_next_env

    def test_execute_with_io_error(self):
        """execute()でIOエラーが発生した場合"""
        predicate = TestGetCharPredicate("X")

        # モック設定：IOエラーを発生させる
        mock_runtime = Mock()
        mock_runtime.io_manager.request_input.side_effect = Exception("IO Error")

        mock_env = BindingEnvironment()

        # execute()実行
        results = list(predicate.execute(mock_runtime, mock_env))

        # エラー時は述語失敗（空のリスト）
        assert len(results) == 0

    def test_execute_with_unification_failure(self):
        """execute()で統一化が失敗した場合"""
        predicate = TestGetCharPredicate("X")

        # モック設定
        mock_runtime = Mock()
        mock_env = BindingEnvironment()

        # 入力取得は成功
        mock_runtime.io_manager.request_input.return_value = "a"

        # 統一化は失敗
        mock_runtime.logic_interpreter.unify.return_value = (False, None)

        # execute()実行
        results = list(predicate.execute(mock_runtime, mock_env))

        # 統一化失敗時は述語失敗（空のリスト）
        assert len(results) == 0


class TestIOPredicateIntegration:
    """IOPredicate統合テスト"""

    def test_multiple_predicates_same_runtime(self):
        """同一Runtime上で複数述語を実行"""
        get_char = TestGetCharPredicate("X")
        read_line = TestReadLinePredicate("Y")

        # 共通Runtime
        mock_runtime = Mock()
        mock_env = BindingEnvironment()
        mock_next_env1 = BindingEnvironment()
        mock_next_env2 = BindingEnvironment()

        # get_char実行用設定
        def input_side_effect(input_type, predicate_name, prompt):
            if input_type == "char":
                return "5"
            elif input_type == "line":
                return "hello"
            return None

        mock_runtime.io_manager.request_input.side_effect = input_side_effect

        # 統一化は常に成功
        mock_runtime.logic_interpreter.unify.side_effect = [
            (True, mock_next_env1),  # get_char用
            (True, mock_next_env2),  # read_line用
        ]

        # 各述語を実行
        get_char_results = list(get_char.execute(mock_runtime, mock_env))
        read_line_results = list(read_line.execute(mock_runtime, mock_env))

        # 両方とも成功
        assert len(get_char_results) == 1
        assert len(read_line_results) == 1
        assert get_char_results[0] == mock_next_env1
        assert read_line_results[0] == mock_next_env2

        # 適切な入力タイプで呼び出されていることを確認
        calls = mock_runtime.io_manager.request_input.call_args_list
        assert len(calls) == 2

        # get_char呼び出し
        assert calls[0][1]["input_type"] == "char"
        assert calls[0][1]["predicate_name"] == "get_char"

        # read_line呼び出し
        assert calls[1][1]["input_type"] == "line"
        assert calls[1][1]["predicate_name"] == "read_line"
