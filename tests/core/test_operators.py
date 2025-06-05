"""
Operator Registry テスト

Prologインタープリターの演算子レジストリの
動作を検証するテストスイート。
"""

from pyprolog.core.operators import (
    OperatorRegistry, OperatorInfo, OperatorType, Associativity, operator_registry
)


class TestOperatorRegistry:
    """演算子レジストリのテスト"""

    def test_builtin_operators_registration(self):
        """組み込み演算子の登録テスト"""
        registry = OperatorRegistry()
        
        # 基本的な算術演算子が登録されているか確認
        assert registry.is_operator("+")
        assert registry.is_operator("-")
        assert registry.is_operator("*")
        assert registry.is_operator("/")
        
        # 比較演算子が登録されているか確認
        assert registry.is_operator("=:=")
        assert registry.is_operator("=\\=")
        assert registry.is_operator("<")
        assert registry.is_operator(">")
        assert registry.is_operator("=<")
        assert registry.is_operator(">=")
        
        # 論理演算子が登録されているか確認
        assert registry.is_operator("=")
        assert registry.is_operator("\\=")
        assert registry.is_operator("==")
        assert registry.is_operator("\\==")
        
        # 制御演算子が登録されているか確認
        assert registry.is_operator(",")
        assert registry.is_operator(";")
        assert registry.is_operator("->")
        assert registry.is_operator("\\+")
        assert registry.is_operator("!")
        
        # 特殊演算子が登録されているか確認
        assert registry.is_operator("is")

    def test_operator_precedence(self):
        """演算子優先度のテスト"""
        registry = OperatorRegistry()
        
        # 算術演算子の優先度
        power_prec = registry.get_precedence("**")
        mult_prec = registry.get_precedence("*")
        add_prec = registry.get_precedence("+")
        
        assert power_prec is not None
        assert mult_prec is not None
        assert add_prec is not None
        assert power_prec < mult_prec  # ** は * より高い優先度
        assert mult_prec < add_prec    # * は + より高い優先度
        
        # 比較演算子の優先度
        comp_prec = registry.get_precedence("=:=")
        assert comp_prec is not None
        assert add_prec < comp_prec    # + は =:= より高い優先度
        
        # 論理演算子の優先度
        unify_prec = registry.get_precedence("=")
        comma_prec = registry.get_precedence(",")
        semicolon_prec = registry.get_precedence(";")
        
        assert unify_prec is not None
        assert comma_prec is not None
        assert semicolon_prec is not None
        assert unify_prec < comma_prec      # = は , より高い優先度
        assert comma_prec < semicolon_prec  # , は ; より高い優先度

    def test_operator_associativity(self):
        """演算子結合性のテスト"""
        registry = OperatorRegistry()
        
        # 左結合演算子
        plus_op = registry.get_operator("+")
        assert plus_op is not None
        assert plus_op.associativity == Associativity.LEFT
        
        mult_op = registry.get_operator("*")
        assert mult_op is not None
        assert mult_op.associativity == Associativity.LEFT
        
        # 右結合演算子
        power_op = registry.get_operator("**")
        assert power_op is not None
        assert power_op.associativity == Associativity.RIGHT
        
        comma_op = registry.get_operator(",")
        assert comma_op is not None
        assert comma_op.associativity == Associativity.RIGHT
        
        # 非結合演算子
        eq_op = registry.get_operator("=:=")
        assert eq_op is not None
        assert eq_op.associativity == Associativity.NON
        
        unify_op = registry.get_operator("=")
        assert unify_op is not None
        assert unify_op.associativity == Associativity.NON

    def test_operator_types(self):
        """演算子タイプのテスト"""
        registry = OperatorRegistry()
        
        # 算術演算子
        plus_op = registry.get_operator("+")
        assert plus_op is not None
        assert plus_op.operator_type == OperatorType.ARITHMETIC
        
        # 比較演算子
        less_op = registry.get_operator("<")
        assert less_op is not None
        assert less_op.operator_type == OperatorType.COMPARISON
        
        # 論理演算子
        unify_op = registry.get_operator("=")
        assert unify_op is not None
        assert unify_op.operator_type == OperatorType.LOGICAL
        
        # 制御演算子
        cut_op = registry.get_operator("!")
        assert cut_op is not None
        assert cut_op.operator_type == OperatorType.CONTROL

    def test_user_defined_operators(self):
        """ユーザー定義演算子のテスト"""
        registry = OperatorRegistry()
        
        # ユーザー定義演算子を追加
        registry.add_user_operator(
            "custom", 600, Associativity.LEFT, OperatorType.ARITHMETIC, 2
        )
        
        # 登録されたか確認
        assert registry.is_operator("custom")
        
        custom_op = registry.get_operator("custom")
        assert custom_op is not None
        assert custom_op.symbol == "custom"
        assert custom_op.precedence == 600
        assert custom_op.associativity == Associativity.LEFT
        assert custom_op.operator_type == OperatorType.ARITHMETIC
        assert custom_op.arity == 2

    def test_token_type_mapping(self):
        """トークンタイプマッピングのテスト"""
        registry = OperatorRegistry()
        
        # 基本演算子のトークンタイプ
        assert registry.get_token_type("+") == "PLUS"
        assert registry.get_token_type("-") == "MINUS"
        assert registry.get_token_type("*") == "STAR"
        assert registry.get_token_type("/") == "SLASH"
        
        # 比較演算子のトークンタイプ
        assert registry.get_token_type("=:=") == "ARITH_EQ"
        assert registry.get_token_type("<") == "LESS"
        assert registry.get_token_type(">") == "GREATER"
        
        # 論理演算子のトークンタイプ
        assert registry.get_token_type("=") == "UNIFY"
        assert registry.get_token_type("\\=") == "NON_UNIFIABLE_OPERATOR"
        
        # 存在しない演算子
        assert registry.get_token_type("nonexistent") is None

    def test_operators_by_type(self):
        """タイプ別演算子取得のテスト"""
        registry = OperatorRegistry()
        
        # 算術演算子の取得
        arithmetic_ops = registry.get_operators_by_type(OperatorType.ARITHMETIC)
        arithmetic_symbols = [op.symbol for op in arithmetic_ops]
        assert "+" in arithmetic_symbols
        assert "-" in arithmetic_symbols
        assert "*" in arithmetic_symbols
        assert "/" in arithmetic_symbols
        assert "is" in arithmetic_symbols
        
        # 比較演算子の取得
        comparison_ops = registry.get_operators_by_type(OperatorType.COMPARISON)
        comparison_symbols = [op.symbol for op in comparison_ops]
        assert "=:=" in comparison_symbols
        assert "<" in comparison_symbols
        assert ">" in comparison_symbols
        
        # 論理演算子の取得
        logical_ops = registry.get_operators_by_type(OperatorType.LOGICAL)
        logical_symbols = [op.symbol for op in logical_ops]
        assert "=" in logical_symbols
        assert "\\=" in logical_symbols
        assert "," in logical_symbols

    def test_operators_by_precedence(self):
        """優先度別演算子取得のテスト"""
        registry = OperatorRegistry()
        
        # 優先度700の演算子（比較・論理演算子）
        prec_700_ops = registry.get_operators_by_precedence(700)
        prec_700_symbols = [op.symbol for op in prec_700_ops]
        assert "=:=" in prec_700_symbols
        assert "=" in prec_700_symbols
        assert "<" in prec_700_symbols
        
        # 優先度500の演算子（加減算）
        prec_500_ops = registry.get_operators_by_precedence(500)
        prec_500_symbols = [op.symbol for op in prec_500_ops]
        assert "+" in prec_500_symbols
        assert "-" in prec_500_symbols
        
        # 存在しない優先度
        nonexistent_ops = registry.get_operators_by_precedence(999)
        assert len(nonexistent_ops) == 0

    def test_operator_arity(self):
        """演算子のアリティテスト"""
        registry = OperatorRegistry()
        
        # 二項演算子
        plus_op = registry.get_operator("+")
        assert plus_op is not None
        assert plus_op.arity == 2
        
        unify_op = registry.get_operator("=")
        assert unify_op is not None
        assert unify_op.arity == 2
        
        # 単項演算子
        not_op = registry.get_operator("\\+")
        assert not_op is not None
        assert not_op.arity == 1
        
        # 0項演算子（カット）
        cut_op = registry.get_operator("!")
        assert cut_op is not None
        assert cut_op.arity == 0

    def test_operator_symbols_sorted(self):
        """演算子記号のソート取得テスト"""
        registry = OperatorRegistry()
        
        symbols = registry.get_all_symbols()
        
        # 長い記号が先に来る（最長マッチ用）
        assert len(symbols) > 0
        
        # 複数文字の演算子が単一文字より前に来る
        if "=:=" in symbols and "=" in symbols:
            eq_arith_idx = symbols.index("=:=")
            eq_idx = symbols.index("=")
            assert eq_arith_idx < eq_idx

    def test_singleton_pattern(self):
        """シングルトンパターンのテスト"""
        registry1 = OperatorRegistry()
        registry2 = OperatorRegistry()
        
        # 同じインスタンスであることを確認
        assert registry1 is registry2
        
        # グローバルインスタンスと同じことを確認
        assert registry1 is operator_registry

    def test_operator_info_validation(self):
        """OperatorInfo の検証テスト"""
        # 正常なケース
        valid_op = OperatorInfo(
            "+", 500, Associativity.LEFT, OperatorType.ARITHMETIC, 2, None, "PLUS"
        )
        assert valid_op.symbol == "+"
        assert valid_op.precedence == 500
        
        # 異常なケース：優先度が範囲外
        try:
            invalid_op = OperatorInfo(
                "invalid", 1300, Associativity.LEFT, OperatorType.ARITHMETIC, 2, None, "INVALID"
            )
            assert False, "Should have raised ValueError"
        except ValueError:
            pass  # 期待される例外
        
        # 異常なケース：トークンタイプが空
        try:
            invalid_op2 = OperatorInfo(
                "invalid", 500, Associativity.LEFT, OperatorType.ARITHMETIC, 2, None, ""
            )
            assert False, "Should have raised ValueError"
        except ValueError:
            pass  # 期待される例外

    def test_nonexistent_operator(self):
        """存在しない演算子のテスト"""
        registry = OperatorRegistry()
        
        # 存在しない演算子
        assert not registry.is_operator("nonexistent")
        assert registry.get_operator("nonexistent") is None
        assert registry.get_precedence("nonexistent") is None
        assert registry.get_token_type("nonexistent") is None

    def test_io_operators(self):
        """入出力演算子のテスト"""
        registry = OperatorRegistry()
        
        # IO演算子が登録されているか確認
        assert registry.is_operator("write")
        assert registry.is_operator("nl")
        assert registry.is_operator("tab")
        
        # IO演算子の情報確認
        write_op = registry.get_operator("write")
        assert write_op is not None
        assert write_op.operator_type == OperatorType.IO
        assert write_op.arity == 1
        
        nl_op = registry.get_operator("nl")
        assert nl_op is not None
        assert nl_op.operator_type == OperatorType.IO
        assert nl_op.arity == 0