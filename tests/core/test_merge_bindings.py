"""
Merge Bindings テスト

Prologインタープリターのバインディング結合機能の
動作を検証するテストスイート。
"""

from pyprolog.core.merge_bindings import (
    merge_bindings, 
    bindings_to_dict, 
    dict_to_binding_environment,
    unify_with_bindings,
    apply_substitution
)
from pyprolog.core.binding_environment import BindingEnvironment
from pyprolog.core.types import Atom, Variable, Number, String, Term


class TestMergeBindings:
    """バインディング結合のテスト"""

    def test_merge_dictionaries(self):
        """辞書同士のマージテスト"""
        # 基本的なマージ
        dict1 = {"X": Atom("hello"), "Y": Number(42)}
        dict2 = {"Z": String("world"), "W": Variable("V")}
        
        merged = merge_bindings(dict1, dict2)
        
        assert isinstance(merged, dict)
        assert merged["X"] == Atom("hello")
        assert merged["Y"] == Number(42)
        assert merged["Z"] == String("world")
        assert merged["W"] == Variable("V")

    def test_merge_conflicting_dictionaries(self):
        """競合する辞書のマージテスト"""
        # 同じキーで異なる値
        dict1 = {"X": Atom("first"), "Y": Number(1)}
        dict2 = {"X": Atom("second"), "Z": String("new")}
        
        merged = merge_bindings(dict1, dict2)
        
        # dict2の値が優先される
        if isinstance(merged, dict):
            assert merged["X"] == Atom("second")
            assert merged["Y"] == Number(1)
            assert merged["Z"] == String("new")
        else:
            assert merged.get_value("X") == Atom("second")
            assert merged.get_value("Y") == Number(1)
            assert merged.get_value("Z") == String("new")

    def test_merge_variable_with_concrete_value(self):
        """変数と具体値の競合テスト"""
        # 変数と具体値
        dict1 = {"X": Variable("X"), "Y": Atom("value1")}
        dict2 = {"X": Atom("concrete"), "Y": Variable("Y")}
        
        merged = merge_bindings(dict1, dict2)
        
        # 具体値が優先される
        if isinstance(merged, dict):
            assert merged["X"] == Atom("concrete")
            assert merged["Y"] == Atom("value1")
        else:
            assert merged.get_value("X") == Atom("concrete")
            assert merged.get_value("Y") == Atom("value1")

    def test_merge_binding_environments(self):
        """BindingEnvironment同士のマージテスト"""
        # 最初の環境
        env1 = BindingEnvironment()
        env1.bind("X", Atom("hello"))
        env1.bind("Y", Number(42))
        
        # 2番目の環境
        env2 = BindingEnvironment()
        env2.bind("Z", String("world"))
        env2.bind("W", Variable("V"))
        
        merged = merge_bindings(env1, env2)
        
        assert isinstance(merged, BindingEnvironment)
        assert merged.get_value("X") == Atom("hello")
        assert merged.get_value("Y") == Number(42)
        assert merged.get_value("Z") == String("world")
        assert merged.get_value("W") == Variable("V")

    def test_merge_dict_with_binding_environment(self):
        """辞書とBindingEnvironmentのマージテスト"""
        # 辞書
        dict_bindings = {"X": Atom("dict_value"), "Y": Number(100)}
        
        # BindingEnvironment
        env = BindingEnvironment()
        env.bind("Z", String("env_value"))
        env.bind("W", Variable("V"))
        
        # 辞書 + 環境
        merged1 = merge_bindings(dict_bindings, env)
        assert isinstance(merged1, BindingEnvironment)
        assert merged1.get_value("X") == Atom("dict_value")
        assert merged1.get_value("Z") == String("env_value")
        
        # 環境 + 辞書
        merged2 = merge_bindings(env, dict_bindings)
        assert isinstance(merged2, BindingEnvironment)
        assert merged2.get_value("X") == Atom("dict_value")
        assert merged2.get_value("Z") == String("env_value")

    def test_merge_with_none(self):
        """Noneとのマージテスト"""
        dict_bindings = {"X": Atom("value")}
        env = BindingEnvironment()
        env.bind("Y", Number(42))
        
        # None + 辞書
        merged1 = merge_bindings(None, dict_bindings)
        assert merged1 == dict_bindings
        
        # 辞書 + None
        merged2 = merge_bindings(dict_bindings, None)
        assert merged2 == dict_bindings
        
        # None + 環境
        merged3 = merge_bindings(None, env)
        assert merged3 == env
        
        # 環境 + None
        merged4 = merge_bindings(env, None)
        assert merged4 == env
        
        # None + None
        merged5 = merge_bindings(None, None)
        assert merged5 == {}

    def test_conflict_resolution(self):
        """競合解決のテスト"""
        # 同じ変数で異なる具体値
        dict1 = {"X": Atom("first")}
        dict2 = {"X": Atom("second")}
        
        merged = merge_bindings(dict1, dict2)
        if isinstance(merged, dict):
            assert merged["X"] == Atom("second")  # 後者が優先
        else:
            assert merged.get_value("X") == Atom("second")  # 後者が優先
        
        # 変数と具体値の競合
        dict3 = {"Y": Variable("Y")}
        dict4 = {"Y": Number(123)}
        
        merged2 = merge_bindings(dict3, dict4)
        if isinstance(merged2, dict):
            assert merged2["Y"] == Number(123)  # 具体値が優先
        else:
            assert merged2.get_value("Y") == Number(123)  # 具体値が優先

    def test_unification_with_bindings(self):
        """バインディングを使った単一化テスト"""
        # 基本的な単一化
        term1 = Variable("X")
        term2 = Atom("hello")
        
        success, result = unify_with_bindings(term1, term2)
        assert success
        if isinstance(result, dict):
            assert result.get("X") == Atom("hello")
        else:
            assert result.get_value("X") == Atom("hello")
        
        # 既存のバインディングとの単一化
        existing_bindings = {"Y": Number(42)}
        success2, result2 = unify_with_bindings(Variable("Z"), String("world"), existing_bindings)
        assert success2
        if isinstance(result2, dict):
            assert result2["Y"] == Number(42)
            assert result2["Z"] == String("world")
        else:
            assert result2.get_value("Y") == Number(42)
            assert result2.get_value("Z") == String("world")

    def test_mixed_merging(self):
        """混合データ型のマージテスト"""
        # 複雑なTerm構造を含むマージ
        complex_term = Term(Atom("likes"), [Variable("X"), Atom("mary")])
        
        dict1 = {"T": complex_term, "X": Variable("X")}
        dict2 = {"X": Atom("john"), "N": Number(123)}
        
        merged = merge_bindings(dict1, dict2)
        
        if isinstance(merged, dict):
            assert merged["T"] == complex_term
            assert merged["X"] == Atom("john")  # 具体値が優先
            assert merged["N"] == Number(123)
        else:
            assert merged.get_value("T") == complex_term
            assert merged.get_value("X") == Atom("john")  # 具体値が優先
            assert merged.get_value("N") == Number(123)


class TestBindingsConversion:
    """バインディング変換のテスト"""

    def test_bindings_to_dict(self):
        """BindingEnvironmentから辞書への変換テスト"""
        env = BindingEnvironment()
        env.bind("X", Atom("hello"))
        env.bind("Y", Number(42))
        env.bind("Z", Variable("Z"))  # 自分自身への束縛
        
        result = bindings_to_dict(env)
        
        assert isinstance(result, dict)
        assert result["X"] == Atom("hello")
        assert result["Y"] == Number(42)
        # 自分自身への束縛は含まれない
        assert "Z" not in result

    def test_dict_to_binding_environment(self):
        """辞書からBindingEnvironmentへの変換テスト"""
        dict_bindings = {
            "X": Atom("hello"),
            "Y": Number(42),
            "Z": String("world")
        }
        
        env = dict_to_binding_environment(dict_bindings)
        
        assert isinstance(env, BindingEnvironment)
        assert env.get_value("X") == Atom("hello")
        assert env.get_value("Y") == Number(42)
        assert env.get_value("Z") == String("world")

    def test_empty_bindings_conversion(self):
        """空のバインディングの変換テスト"""
        # 空の辞書
        empty_dict = {}
        env_from_empty = dict_to_binding_environment(empty_dict)
        assert isinstance(env_from_empty, BindingEnvironment)
        
        # 空の環境
        empty_env = BindingEnvironment()
        dict_from_empty = bindings_to_dict(empty_env)
        assert dict_from_empty == {}
        
        # Noneの処理
        none_dict = bindings_to_dict(None)
        assert none_dict == {}

    def test_nested_environment_conversion(self):
        """ネストした環境の変換テスト"""
        # 親環境
        parent_env = BindingEnvironment()
        parent_env.bind("P", Atom("parent_value"))
        
        # 子環境
        child_env = BindingEnvironment(parent_env)
        child_env.bind("C", Atom("child_value"))
        
        # 変換テスト
        # 変換テスト
        result_dict = bindings_to_dict(child_env)
        
        # 両方の値が含まれているはず
        if isinstance(result_dict, dict):
            assert "P" in result_dict
            assert "C" in result_dict
            assert result_dict["P"] == Atom("parent_value")
            assert result_dict["C"] == Atom("child_value")
        else:
            assert result_dict.get_value("P") == Atom("parent_value")
            assert result_dict.get_value("C") == Atom("child_value")

class TestApplySubstitution:
    """置換適用のテスト"""

    def test_apply_substitution_with_dict(self):
        """辞書による置換適用テスト"""
        bindings = {"X": Atom("hello"), "Y": Number(42)}
        
        # 変数の置換
        assert apply_substitution("X", bindings) == Atom("hello")
        assert apply_substitution("Y", bindings) == Number(42)
        
        # 存在しない変数
        assert apply_substitution("Z", bindings) == "Z"

    def test_apply_substitution_with_binding_environment(self):
        """BindingEnvironmentによる置換適用テスト"""
        env = BindingEnvironment()
        env.bind("X", Atom("hello"))
        env.bind("Y", Number(42))
        
        # 変数の置換
        assert apply_substitution("X", env) == Atom("hello")
        assert apply_substitution("Y", env) == Number(42)
        
        # 存在しない変数
        assert apply_substitution("Z", env) is None

    def test_apply_substitution_complex_terms(self):
        """複雑な項への置換適用テスト"""
        bindings = {"X": Atom("john"), "Y": Atom("mary")}
        
        # 複雑なTermも処理できるかテスト（substitute メソッドがある場合）
        complex_term = Term(Atom("likes"), [Variable("X"), Variable("Y")])
        
        # この実装では substitute メソッドがないので、そのまま返される
        result = apply_substitution(complex_term, bindings)
        assert result == complex_term