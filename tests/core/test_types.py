"""
Core Types テスト

Prologインタープリターの基本データ型（Atom, Variable, Number, String, Term, ListTerm, Rule, Fact）の
動作を検証するテストスイート。
"""

from prolog.core.types import (
    Atom, Variable, Number, String, Term, ListTerm, Rule, Fact, PrologType
)


class TestBasicTypes:
    """基本データ型のテスト"""

    def test_atom_creation_and_equality(self):
        """Atomの作成と等価性テスト"""
        # 基本的な作成
        atom1 = Atom("test")
        atom2 = Atom("test")
        atom3 = Atom("different")
        
        # 等価性の確認
        assert atom1 == atom2
        assert atom1 != atom3
        assert atom1.name == "test"
        
        # ハッシュ性の確認
        assert hash(atom1) == hash(atom2)
        assert hash(atom1) != hash(atom3)
        
        # repr の確認
        assert repr(atom1) == "test"

    def test_variable_creation_and_equality(self):
        """Variableの作成と等価性テスト"""
        # 基本的な作成
        var1 = Variable("X")
        var2 = Variable("X")
        var3 = Variable("Y")
        
        # 等価性の確認
        assert var1 == var2
        assert var1 != var3
        assert var1.name == "X"
        
        # ハッシュ性の確認
        assert hash(var1) == hash(var2)
        assert hash(var1) != hash(var3)
        
        # repr の確認
        assert repr(var1) == "X"

    def test_number_creation_and_operations(self):
        """Numberの作成と操作テスト"""
        # 整数の作成
        num1 = Number(42)
        num2 = Number(42)
        num3 = Number(24)
        
        # 浮動小数点数の作成
        float1 = Number(3.14)
        float2 = Number(3.14)
        float3 = Number(2.71)
        
        # 等価性の確認
        assert num1 == num2
        assert num1 != num3
        assert float1 == float2
        assert float1 != float3
        assert num1 != float1
        
        # 値の確認
        assert num1.value == 42
        assert float1.value == 3.14
        
        # ハッシュ性の確認
        assert hash(num1) == hash(num2)
        assert hash(float1) == hash(float2)
        
        # repr の確認
        assert repr(num1) == "42"
        assert repr(float1) == "3.14"

    def test_string_creation_and_operations(self):
        """Stringの作成と操作テスト"""
        # 基本的な作成
        str1 = String("hello")
        str2 = String("hello")
        str3 = String("world")
        
        # 等価性の確認
        assert str1 == str2
        assert str1 != str3
        assert str1.value == "hello"
        
        # ハッシュ性の確認
        assert hash(str1) == hash(str2)
        assert hash(str1) != hash(str3)
        
        # repr の確認
        assert repr(str1) == "'hello'"

    def test_term_creation_and_structure(self):
        """Termの作成と構造テスト"""
        # 引数なしのTerm（アトムと同等）
        term1 = Term(Atom("fact"))
        assert repr(term1) == "fact"
        
        # 引数ありのTerm
        term2 = Term(Atom("likes"), [Atom("john"), Atom("mary")])
        assert repr(term2) == "likes(john, mary)"
        
        # 複雑なネストしたTerm
        term3 = Term(Atom("parent"), [
            Term(Atom("father"), [Variable("X")]),
            Variable("Y")
        ])
        assert repr(term3) == "parent(father(X), Y)"
        
        # 等価性の確認
        term4 = Term(Atom("likes"), [Atom("john"), Atom("mary")])
        assert term2 == term4
        
        term5 = Term(Atom("likes"), [Atom("mary"), Atom("john")])
        assert term2 != term5

    def test_list_term_conversion(self):
        """ListTermの変換テスト"""
        # 空リスト
        empty_list = ListTerm([])
        internal_empty = empty_list.to_internal_list_term()
        assert isinstance(internal_empty, Atom)
        assert internal_empty.name == "[]"
        
        # 単一要素のリスト
        single_list = ListTerm([Atom("a")])
        internal_single = single_list.to_internal_list_term()
        expected_single = Term(Atom("."), [Atom("a"), Atom("[]")])
        assert internal_single == expected_single
        
        # 複数要素のリスト
        multi_list = ListTerm([Atom("a"), Atom("b"), Atom("c")])
        internal_multi = multi_list.to_internal_list_term()
        expected_multi = Term(Atom("."), [
            Atom("a"),
            Term(Atom("."), [
                Atom("b"),
                Term(Atom("."), [Atom("c"), Atom("[]")])
            ])
        ])
        assert internal_multi == expected_multi
        
        # テール付きリスト
        tail_list = ListTerm([Atom("a"), Atom("b")], Variable("T"))
        internal_tail = tail_list.to_internal_list_term()
        expected_tail = Term(Atom("."), [
            Atom("a"),
            Term(Atom("."), [Atom("b"), Variable("T")])
        ])
        assert internal_tail == expected_tail

    def test_rule_and_fact_creation(self):
        """RuleとFactの作成テスト"""
        # Factの作成
        fact = Fact(Term(Atom("likes"), [Atom("john"), Atom("mary")]))
        assert repr(fact) == "likes(john, mary)."
        
        # Ruleの作成
        head = Term(Atom("grandparent"), [Variable("X"), Variable("Z")])
        body = Term(Atom(","), [
            Term(Atom("parent"), [Variable("X"), Variable("Y")]),
            Term(Atom("parent"), [Variable("Y"), Variable("Z")])
        ])
        rule = Rule(head, body)
        expected_repr = "grandparent(X, Z) :- ,(parent(X, Y), parent(Y, Z))."
        assert repr(rule) == expected_repr
        
        # 等価性の確認
        fact2 = Fact(Term(Atom("likes"), [Atom("john"), Atom("mary")]))
        assert fact == fact2
        
        rule2 = Rule(head, body)
        assert rule == rule2


class TestListTerm:
    """ListTermの詳細テスト"""

    def test_empty_list_representation(self):
        """空リストの表現テスト"""
        empty1 = ListTerm([])
        empty2 = ListTerm([], Atom("[]"))
        empty3 = ListTerm([], None)
        
        assert repr(empty1) == "[]"
        assert repr(empty2) == "[]"
        assert repr(empty3) == "[]"

    def test_simple_list_representation(self):
        """単純なリストの表現テスト"""
        simple_list = ListTerm([Atom("a"), Atom("b"), Atom("c")])
        assert repr(simple_list) == "[a, b, c]"

    def test_tail_list_representation(self):
        """テール付きリストの表現テスト"""
        tail_list = ListTerm([Atom("a"), Atom("b")], Variable("T"))
        assert repr(tail_list) == "[a, b | T]"

    def test_nested_list_representation(self):
        """ネストしたリストの表現テスト"""
        inner_list = ListTerm([Atom("x"), Atom("y")])
        outer_list = ListTerm([Atom("a"), inner_list, Atom("c")])
        assert repr(outer_list) == "[a, [x, y], c]"

    def test_list_equality(self):
        """リストの等価性テスト"""
        list1 = ListTerm([Atom("a"), Atom("b")])
        list2 = ListTerm([Atom("a"), Atom("b")])
        list3 = ListTerm([Atom("b"), Atom("a")])
        
        assert list1 == list2
        assert list1 != list3

    def test_list_hashing(self):
        """リストのハッシュテスト"""
        list1 = ListTerm([Atom("a"), Atom("b")])
        list2 = ListTerm([Atom("a"), Atom("b")])
        
        # 同じ内容のリストは同じハッシュ値を持つ
        assert hash(list1) == hash(list2)
        
        # セットに追加できることを確認
        list_set = {list1, list2}
        assert len(list_set) == 1


class TestComplexStructures:
    """複雑なデータ構造のテスト"""

    def test_nested_terms(self):
        """ネストしたTermのテスト"""
        # f(g(X), h(Y, Z))
        inner_term1 = Term(Atom("g"), [Variable("X")])
        inner_term2 = Term(Atom("h"), [Variable("Y"), Variable("Z")])
        outer_term = Term(Atom("f"), [inner_term1, inner_term2])
        
        expected_repr = "f(g(X), h(Y, Z))"
        assert repr(outer_term) == expected_repr

    def test_mixed_data_types(self):
        """混合データ型のテスト"""
        # complex(atom, 42, "string", X, [a, b])
        mixed_term = Term(Atom("complex"), [
            Atom("atom"),
            Number(42),
            String("string"),
            Variable("X"),
            ListTerm([Atom("a"), Atom("b")])
        ])
        
        expected_repr = "complex(atom, 42, 'string', X, [a, b])"
        assert repr(mixed_term) == expected_repr

    def test_rule_with_complex_body(self):
        """複雑なボディを持つRuleのテスト"""
        # ancestor(X, Z) :- parent(X, Y), ancestor(Y, Z).
        head = Term(Atom("ancestor"), [Variable("X"), Variable("Z")])
        body = Term(Atom(","), [
            Term(Atom("parent"), [Variable("X"), Variable("Y")]),
            Term(Atom("ancestor"), [Variable("Y"), Variable("Z")])
        ])
        rule = Rule(head, body)
        
        expected_repr = "ancestor(X, Z) :- ,(parent(X, Y), ancestor(Y, Z))."
        assert repr(rule) == expected_repr