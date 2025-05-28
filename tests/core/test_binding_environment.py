"""
Binding Environment テスト

Prologインタープリターのバインディング環境（変数の束縛管理）の
動作を検証するテストスイート。
"""

from prolog.core.binding_environment import BindingEnvironment
from prolog.core.types import Atom, Variable, Number, String, Term


class TestBindingEnvironment:
    """バインディング環境のテスト"""

    def test_bind_and_get_value(self):
        """基本的な束縛と値取得のテスト"""
        env = BindingEnvironment()
        
        # 変数の束縛
        env.bind("X", Atom("hello"))
        env.bind("Y", Number(42))
        env.bind("Z", String("world"))
        
        # 値の取得
        assert env.get_value("X") == Atom("hello")
        assert env.get_value("Y") == Number(42)
        assert env.get_value("Z") == String("world")
        
        # 存在しない変数
        assert env.get_value("W") is None

    def test_parent_environment_inheritance(self):
        """親環境からの継承テスト"""
        # 親環境の作成
        parent_env = BindingEnvironment()
        parent_env.bind("X", Atom("parent_value"))
        parent_env.bind("Y", Number(100))
        
        # 子環境の作成
        child_env = BindingEnvironment(parent_env)
        child_env.bind("Z", String("child_value"))
        
        # 子環境から親の値にアクセス
        assert child_env.get_value("X") == Atom("parent_value")
        assert child_env.get_value("Y") == Number(100)
        assert child_env.get_value("Z") == String("child_value")
        
        # 親環境からは子の値にアクセスできない
        assert parent_env.get_value("Z") is None

    def test_variable_shadowing(self):
        """変数のシャドウイングテスト"""
        # 親環境の作成
        parent_env = BindingEnvironment()
        parent_env.bind("X", Atom("parent_value"))
        
        # 子環境で同じ変数を束縛
        child_env = BindingEnvironment(parent_env)
        child_env.bind("X", Atom("child_value"))
        
        # 子環境では子の値が優先される
        assert child_env.get_value("X") == Atom("child_value")
        
        # 親環境の値は変更されない
        assert parent_env.get_value("X") == Atom("parent_value")

    def test_copy_environment(self):
        """環境のコピーテスト"""
        # 元の環境を作成
        original_env = BindingEnvironment()
        original_env.bind("X", Atom("original"))
        original_env.bind("Y", Number(42))
        
        # コピーを作成
        copied_env = original_env.copy()
        
        # コピーされた値の確認
        assert copied_env.get_value("X") == Atom("original")
        assert copied_env.get_value("Y") == Number(42)
        
        # コピーを変更しても元は影響されない
        copied_env.bind("X", Atom("modified"))
        copied_env.bind("Z", String("new"))
        
        assert original_env.get_value("X") == Atom("original")
        assert original_env.get_value("Z") is None
        assert copied_env.get_value("X") == Atom("modified")
        assert copied_env.get_value("Z") == String("new")

    def test_copy_with_parent_environment(self):
        """親環境を持つ環境のコピーテスト"""
        # 親環境の作成
        parent_env = BindingEnvironment()
        parent_env.bind("P", Atom("parent"))
        
        # 子環境の作成
        child_env = BindingEnvironment(parent_env)
        child_env.bind("C", Atom("child"))
        
        # 子環境のコピー
        copied_child = child_env.copy()
        
        # 親環境への参照が維持されているか確認
        assert copied_child.get_value("P") == Atom("parent")
        assert copied_child.get_value("C") == Atom("child")
        
        # コピーを変更しても元の子環境は影響されない
        copied_child.bind("C", Atom("modified_child"))
        copied_child.bind("N", String("new"))
        
        assert child_env.get_value("C") == Atom("child")
        assert child_env.get_value("N") is None
        assert copied_child.get_value("C") == Atom("modified_child")
        assert copied_child.get_value("N") == String("new")

    def test_variable_scoping(self):
        """変数スコープのテスト"""
        # 3層の環境を作成
        root_env = BindingEnvironment()
        root_env.bind("global", Atom("root_value"))
        
        mid_env = BindingEnvironment(root_env)
        mid_env.bind("local", Atom("mid_value"))
        mid_env.bind("global", Atom("mid_override"))  # ルートの変数をシャドウ
        
        leaf_env = BindingEnvironment(mid_env)
        leaf_env.bind("specific", Atom("leaf_value"))
        
        # 各レベルからのアクセス確認
        # ルートレベル
        assert root_env.get_value("global") == Atom("root_value")
        assert root_env.get_value("local") is None
        assert root_env.get_value("specific") is None
        
        # 中間レベル
        assert mid_env.get_value("global") == Atom("mid_override")
        assert mid_env.get_value("local") == Atom("mid_value")
        assert mid_env.get_value("specific") is None
        
        # リーフレベル
        assert leaf_env.get_value("global") == Atom("mid_override")
        assert leaf_env.get_value("local") == Atom("mid_value")
        assert leaf_env.get_value("specific") == Atom("leaf_value")

    def test_binding_conflicts(self):
        """束縛の競合テスト"""
        env = BindingEnvironment()
        
        # 最初の束縛
        env.bind("X", Atom("first"))
        assert env.get_value("X") == Atom("first")
        
        # 同じ変数への再束縛（上書き）
        env.bind("X", Atom("second"))
        assert env.get_value("X") == Atom("second")
        
        # 複雑な値への束縛
        complex_term = Term(Atom("f"), [Variable("Y"), Number(42)])
        env.bind("X", complex_term)
        assert env.get_value("X") == complex_term

    def test_term_binding(self):
        """Term型の束縛テスト"""
        env = BindingEnvironment()
        
        # 単純なTerm
        simple_term = Term(Atom("atom"))
        env.bind("T1", simple_term)
        assert env.get_value("T1") == simple_term
        
        # 引数を持つTerm
        complex_term = Term(Atom("likes"), [Atom("john"), Atom("mary")])
        env.bind("T2", complex_term)
        assert env.get_value("T2") == complex_term
        
        # ネストしたTerm
        nested_term = Term(Atom("parent"), [
            Term(Atom("father"), [Variable("X")]),
            Variable("Y")
        ])
        env.bind("T3", nested_term)
        assert env.get_value("T3") == nested_term

    def test_variable_to_variable_binding(self):
        """変数から変数への束縛テスト"""
        env = BindingEnvironment()
        
        # X を Y に束縛
        env.bind("X", Variable("Y"))
        assert env.get_value("X") == Variable("Y")
        
        # Y を値に束縛
        env.bind("Y", Atom("value"))
        assert env.get_value("Y") == Atom("value")
        
        # X の値は依然として Y のまま（間接参照は別の処理で行われる）
        assert env.get_value("X") == Variable("Y")

    def test_empty_environment(self):
        """空の環境のテスト"""
        env = BindingEnvironment()
        
        # 何も束縛されていない状態
        assert env.get_value("X") is None
        assert env.get_value("Y") is None
        assert env.get_value("") is None

    def test_environment_representation(self):
        """環境の文字列表現テスト"""
        # 空の環境
        empty_env = BindingEnvironment()
        repr_str = repr(empty_env)
        assert "Env(" in repr_str
        
        # 値を持つ環境
        env = BindingEnvironment()
        env.bind("X", Atom("hello"))
        env.bind("Y", Number(42))
        repr_str = repr(env)
        assert "X: hello" in repr_str
        assert "Y: 42" in repr_str
        
        # 親環境を持つ環境
        parent_env = BindingEnvironment()
        parent_env.bind("P", Atom("parent"))
        child_env = BindingEnvironment(parent_env)
        child_env.bind("C", Atom("child"))
        repr_str = repr(child_env)
        # 両方の環境の情報が含まれているはず
        assert "C: child" in repr_str
        assert "P: parent" in repr_str