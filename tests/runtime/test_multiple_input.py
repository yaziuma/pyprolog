"""
複数回入力処理のテスト
multiple_input_calculator.plの機能をテスト
"""

from pyprolog import Runtime
from pyprolog.runtime.io_streams import StringStream
from pyprolog.runtime.unified_input_system import StreamInputHandler


class TestMultipleInputCalculator:
    """複数回入力計算機のテストクラス"""

    def setup_method(self):
        """各テストメソッドの前に実行される初期化"""
        self.runtime = Runtime()
        # テストファイルを読み込み
        self.runtime.consult("tests/data/multiple_input_calculator.pl")

    def test_valid_two_numbers(self):
        """正常な2つの数値入力のテスト"""
        # 入力ストリームを設定（5と3を入力）
        input_data = "5\n3\n"
        self.runtime.io_manager.set_input_handler(
            StreamInputHandler(StringStream(input_data))
        )

        # 出力をキャプチャするためのストリーム
        output_stream = StringStream("")
        self.runtime.io_manager.set_output_stream(output_stream)

        # calculate_sumを実行
        results = self.runtime.query("calculate_sum")

        # 成功することを確認
        assert len(results) == 1

        # 出力を確認（合計8が出力される）
        output = output_stream.get_output_string()
        assert "合計: 8" in output

    def test_first_input_invalid_then_valid(self):
        """1つ目の入力が無効、再入力で有効な値のテスト"""
        # 1つ目に無効値"abc"、再入力で"7"、2つ目に"4"
        input_data = "abc\n7\n4\n"
        self.runtime.io_manager.set_input_handler(
            StreamInputHandler(StringStream(input_data))
        )

        output_stream = StringStream("")
        self.runtime.io_manager.set_output_stream(output_stream)

        results = self.runtime.query("calculate_sum")

        # 成功することを確認
        assert len(results) == 1

        # エラーメッセージと正しい合計が出力される
        output = output_stream.get_output_string()
        assert "エラー: 数値ではありません" in output
        assert "合計: 11" in output

    def test_second_input_invalid_then_valid(self):
        """2つ目の入力が無効、再入力で有効な値のテスト"""
        # 1つ目に"6"、2つ目に無効値"xyz"、再入力で"2"
        input_data = "6\nxyz\n2\n"
        self.runtime.io_manager.set_input_handler(
            StreamInputHandler(StringStream(input_data))
        )

        output_stream = StringStream("")
        self.runtime.io_manager.set_output_stream(output_stream)

        results = self.runtime.query("calculate_sum")

        # 成功することを確認
        assert len(results) == 1

        # エラーメッセージと正しい合計が出力される
        output = output_stream.get_output_string()
        assert "エラー: 数値ではありません" in output
        assert "合計: 8" in output

    def test_both_inputs_invalid_then_valid(self):
        """両方の入力が無効、それぞれ再入力で有効な値のテスト"""
        # 1つ目に"hello"→再入力"10"、2つ目に"world"→再入力"5"
        input_data = "hello\n10\nworld\n5\n"
        self.runtime.io_manager.set_input_handler(
            StreamInputHandler(StringStream(input_data))
        )

        output_stream = StringStream("")
        self.runtime.io_manager.set_output_stream(output_stream)

        results = self.runtime.query("calculate_sum")

        # 成功することを確認
        assert len(results) == 1

        # 2回のエラーメッセージと正しい合計が出力される
        output = output_stream.get_output_string()
        error_count = output.count("エラー: 数値ではありません")
        assert error_count == 2
        assert "合計: 15" in output

    def test_negative_numbers(self):
        """負の数値の入力テスト"""
        input_data = "-5\n3\n"
        self.runtime.io_manager.set_input_handler(
            StreamInputHandler(StringStream(input_data))
        )

        output_stream = StringStream("")
        self.runtime.io_manager.set_output_stream(output_stream)

        results = self.runtime.query("calculate_sum")

        assert len(results) == 1

        output = output_stream.get_output_string()
        assert "合計: -2" in output

    def test_decimal_numbers(self):
        """小数点数の入力テスト"""
        input_data = "2.5\n1.5\n"
        self.runtime.io_manager.set_input_handler(
            StreamInputHandler(StringStream(input_data))
        )

        output_stream = StringStream("")
        self.runtime.io_manager.set_output_stream(output_stream)

        results = self.runtime.query("calculate_sum")

        assert len(results) == 1

        output = output_stream.get_output_string()
        assert "合計: 4.0" in output or "合計: 4" in output

    def test_zero_values(self):
        """ゼロ値の入力テスト"""
        input_data = "0\n0\n"
        self.runtime.io_manager.set_input_handler(
            StreamInputHandler(StringStream(input_data))
        )

        output_stream = StringStream("")
        self.runtime.io_manager.set_output_stream(output_stream)

        results = self.runtime.query("calculate_sum")

        assert len(results) == 1

        output = output_stream.get_output_string()
        assert "合計: 0" in output

    def test_large_numbers(self):
        """大きな数値の入力テスト"""
        input_data = "1000000\n2000000\n"
        self.runtime.io_manager.set_input_handler(
            StreamInputHandler(StringStream(input_data))
        )

        output_stream = StringStream("")
        self.runtime.io_manager.set_output_stream(output_stream)

        results = self.runtime.query("calculate_sum")

        assert len(results) == 1

        output = output_stream.get_output_string()
        assert "合計: 3000000" in output

    def test_multiple_invalid_attempts(self):
        """複数回の無効入力後に有効入力のテスト"""
        # 1つ目に複数回の無効入力後に"8"、2つ目に"2"
        input_data = "abc\ndef\n8\n2\n"
        self.runtime.io_manager.set_input_handler(
            StreamInputHandler(StringStream(input_data))
        )

        output_stream = StringStream("")
        self.runtime.io_manager.set_output_stream(output_stream)

        results = self.runtime.query("calculate_sum")

        assert len(results) == 1

        output = output_stream.get_output_string()
        # 2回のエラーメッセージが出力される
        error_count = output.count("エラー: 数値ではありません")
        assert error_count == 2
        assert "合計: 10" in output

    def test_input_prompts_appear(self):
        """入力プロンプトが正しく表示されることのテスト"""
        input_data = "5\n3\n"
        self.runtime.io_manager.set_input_handler(
            StreamInputHandler(StringStream(input_data))
        )

        output_stream = StringStream("")
        self.runtime.io_manager.set_output_stream(output_stream)

        results = self.runtime.query("calculate_sum")

        output = output_stream.get_output_string()
        assert "数値を2つ入力して合計を計算します" in output
        assert "1つ目の値を入力してください:" in output
        assert "2つ目の値を入力してください:" in output

    def test_individual_predicates(self):
        """個別の述語のテスト"""
        # get_first_numberのテスト
        input_data = "42\n"
        self.runtime.io_manager.set_input_handler(
            StreamInputHandler(StringStream(input_data))
        )

        output_stream = StringStream("")
        self.runtime.io_manager.set_output_stream(output_stream)

        results = self.runtime.query("get_first_number(X)")
        assert len(results) == 1
        # Get the actual variable name from the result
        variable_name = list(results[0].keys())[0]
        # Use approximate equality to handle int/float differences
        prolog_value = results[0][variable_name]
        # Extract numeric value from Number object if needed
        if hasattr(prolog_value, "value"):
            value = prolog_value.value
        else:
            value = prolog_value
        assert abs(value - 42) < 0.001

    def test_validation_predicate_direct(self):
        """validate_number述語の直接テスト"""
        # 数値の検証テスト
        results = self.runtime.query("validate_number(42, X, first)")
        assert len(results) == 1
        # Get the actual variable name from the result
        variable_name = list(results[0].keys())[0]
        # Use approximate equality to handle int/float differences
        prolog_value = results[0][variable_name]
        # Extract numeric value from Number object if needed
        if hasattr(prolog_value, "value"):
            value = prolog_value.value
        else:
            value = prolog_value
        assert abs(value - 42) < 0.001

        # 非数値の検証テスト（再帰呼び出しが発生するため入力ストリームが必要）
        input_data = "100\n"
        self.runtime.io_manager.set_input_handler(
            StreamInputHandler(StringStream(input_data))
        )

        output_stream = StringStream("")
        self.runtime.io_manager.set_output_stream(output_stream)

        results = self.runtime.query("validate_number(abc, X, first)")
        assert len(results) == 1
        # Get the actual variable name from the result
        variable_name = list(results[0].keys())[0]
        # Use approximate equality to handle int/float differences
        prolog_value = results[0][variable_name]
        # Extract numeric value from Number object if needed
        if hasattr(prolog_value, "value"):
            value = prolog_value.value
        else:
            value = prolog_value
        assert abs(value - 100) < 0.001
