"""
End-to-End テスト

システム全体の統合動作を検証するテストスイート。
パーサー、ランタイム、論理エンジンの連携を総合的にテストします。
"""

import pytest

from pyprolog.core.errors import PrologError
from pyprolog.core.types import Atom, Number, Term, Variable
from pyprolog.runtime.io_streams import StringStream


class TestEndToEnd:
    """エンドツーエンドテスト"""

    def setup_method(self):
        """各テストの前処理"""
        from pyprolog.runtime.interpreter import Runtime

        self.runtime = Runtime()
        self.runtime.rules.clear()
        if hasattr(self.runtime, "logic_interpreter") and self.runtime.logic_interpreter:
            self.runtime.logic_interpreter.replace_rules(self.runtime.rules)

    def _make_list(self, elements):
        result = Atom("[]")
        for element in reversed(elements):
            result = Term(Atom("."), [element, result])
        return result

    def _add_rules(self, *rules: str):
        for rule in rules:
            assert self.runtime.add_rule(rule), f"Failed to add rule: {rule}"

    def test_simple_queries(self):
        """単純なクエリのテスト"""
        self._add_rules(
            "likes(mary, food).",
            "likes(mary, wine).",
            "likes(john, wine).",
            "likes(john, mary).",
        )

        results = self.runtime.query("likes(mary, wine)")
        assert len(results) == 1

        results = self.runtime.query("likes(mary, X)")
        values = {solution.get(Variable("X")) for solution in results}
        assert Atom("food") in values
        assert Atom("wine") in values

    def test_complex_queries(self):
        """複雑なクエリのテスト"""
        self._add_rules(
            "parent(tom, bob).",
            "parent(bob, ann).",
            "grandparent(GP, GC) :- parent(GP, P), parent(P, GC).",
        )

        results = self.runtime.query("grandparent(tom, ann)")
        assert len(results) == 1

        results = self.runtime.query("grandparent(tom, X)")
        assert results[0].get(Variable("X")) == Atom("ann")

    def test_recursive_rules(self):
        """再帰ルールのテスト"""
        self._add_rules(
            "parent(a,b).",
            "parent(b,c).",
            "parent(c,d).",
            "ancestor(X, Y) :- parent(X, Y).",
            "ancestor(X, Z) :- parent(X, Y), ancestor(Y, Z).",
        )

        assert len(self.runtime.query("ancestor(a, d)")) == 1
        assert len(self.runtime.query("ancestor(d, a)")) == 0

    def test_arithmetic_integration(self):
        """算術演算の統合テスト"""
        results = self.runtime.query("X is 5 + 2 * 3 - 1")
        assert results[0].get(Variable("X")) == Number(10)
        assert len(self.runtime.query("1 is 1 + 1")) == 0

    def test_list_operations(self):
        """リスト操作の統合テスト"""
        results = self.runtime.query("member(X, [a,b,c])")
        values = [solution.get(Variable("X")) for solution in results]
        assert values == [Atom("a"), Atom("b"), Atom("c")]

        results = self.runtime.query("append([a,b], [c], L)")
        assert results[0].get(Variable("L")) == self._make_list(
            [Atom("a"), Atom("b"), Atom("c")]
        )

    def test_cut_behavior(self):
        """カットの動作テスト"""
        self._add_rules(
            "data(one).",
            "data(two).",
            "data(three).",
            "cut_test(X) :- data(X), !.",
        )

        results = self.runtime.query("cut_test(X)")
        assert len(results) == 1
        assert results[0].get(Variable("X")) == Atom("one")

    def test_negation_as_failure(self):
        """失敗による否定のテスト"""
        self._add_rules("p(a).")

        assert len(self.runtime.query("\\+ p(a)")) == 0
        assert len(self.runtime.query("\\+ p(b)")) == 1

    def test_variable_scoping(self):
        """変数スコープのテスト"""
        self._add_rules(
            "q(1).",
            "q(2).",
            "r(2).",
            "p(X) :- q(X), r(X).",
        )

        results = self.runtime.query("p(X)")
        assert len(results) == 1
        assert results[0].get(Variable("X")) == Number(2)

    def test_complex_unification(self):
        """複雑な単一化のテスト"""
        self._add_rules("pair(f(a), g(b)).")

        results = self.runtime.query("pair(f(X), g(Y))")
        assert results[0].get(Variable("X")) == Atom("a")
        assert results[0].get(Variable("Y")) == Atom("b")

        results = self.runtime.query("f(X, g(Y)) = f(a, g(b))")
        assert results[0].get(Variable("X")) == Atom("a")
        assert results[0].get(Variable("Y")) == Atom("b")

    def test_meta_predicates(self):
        """メタ述語のテスト"""
        self._add_rules("p(a).", "p(b).")

        results = self.runtime.query("findall(X, p(X), L)")
        assert results[0].get(Variable("L")) == self._make_list(
            [Atom("a"), Atom("b")]
        )

    def test_error_recovery(self):
        """エラー回復のテスト"""
        with pytest.raises(PrologError):
            self.runtime.query("undefined_predicate(X)")

        results = self.runtime.query("true")
        assert len(results) == 1

    def test_performance_basic(self):
        """基本的なパフォーマンステスト"""
        results = self.runtime.query("member(X, [a,b,c,d,e,f,g,h,i])")
        assert len(results) == 9

    def test_memory_management_integration(self):
        """メモリ管理の統合テスト"""
        for i in range(50):
            assert self.runtime.add_rule(f"fact({i}).")

        results = self.runtime.query("fact(X)")
        assert len(results) == 50

    def test_parser_integration(self):
        """パーサー統合のテスト"""
        self._add_rules(
            "person('John Jones', boston).",
            "calc(X) :- X is (5 + 2) * (3 - 1).",
            "list_item([a,b,c]).",
        )

        results = self.runtime.query("calc(Z)")
        assert results[0].get(Variable("Z")) == Number(14)
        assert len(self.runtime.query("person('John Jones', boston)")) == 1
        assert len(self.runtime.query("list_item([a,b,c])")) == 1

    def test_runtime_state_management(self):
        """ランタイム状態管理のテスト"""
        assert len(self.runtime.query("asserta(state(a))")) == 1
        assert len(self.runtime.query("assertz(state(b))")) == 1

        results = self.runtime.query("state(X)")
        assert [solution.get(Variable("X")) for solution in results] == [
            Atom("a"),
            Atom("b"),
        ]

        assert len(self.runtime.query("retract(state(a))")) == 1
        results = self.runtime.query("state(X)")
        assert [solution.get(Variable("X")) for solution in results] == [Atom("b")]

    def test_comprehensive_scenario(self):
        """包括的なシナリオテスト"""
        assert self.runtime.consult("tests/data/fixed_medical_diagnosis.pl")

        output = StringStream()
        self.runtime.io_manager.set_output_stream(output)

        results = self.runtime.query("diagnose_disease([fever], Disease, Probability)")
        assert len(results) == 3

        results = self.runtime.query(
            "patient_diagnosis([fever], 30, [], [], Result)"
        )
        assert len(results) == 3
        assert "Starting diagnosis" in output.get_output_string()

    def test_query_parsing(self):
        """クエリ解析のテスト"""
        self._add_rules("likes(mary, food).")
        results = self.runtime.query("likes(mary, food)")
        assert len(results) == 1

    def test_multiple_solutions(self):
        """複数解のテスト"""
        self._add_rules("item(apple).", "item(banana).")
        results = self.runtime.query("item(X)")
        values = {solution.get(Variable("X")) for solution in results}
        assert values == {Atom("apple"), Atom("banana")}

    def test_built_in_predicates(self):
        """組み込み述語のテスト"""
        output = StringStream()
        self.runtime.io_manager.set_output_stream(output)

        results = self.runtime.query("write(hello), nl")
        assert len(results) == 1
        assert output.get_output_string() == "hello\n"

    def test_constraint_satisfaction(self):
        """制約充足のテスト"""
        results = self.runtime.query("X is 5, X >= 5, X < 10")
        assert results[0].get(Variable("X")) == Number(5)

    def test_database_operations(self):
        """データベース操作のテスト"""
        assert len(self.runtime.query("asserta(db_fact(1))")) == 1
        assert len(self.runtime.query("assertz(db_fact(2))")) == 1
        results = self.runtime.query("db_fact(X)")
        assert [solution.get(Variable("X")) for solution in results] == [
            Number(1),
            Number(2),
        ]
        assert len(self.runtime.query("retract(db_fact(1))")) == 1
        assert len(self.runtime.query("db_fact(1)")) == 0

    def test_exception_handling(self):
        """例外処理のテスト"""
        with pytest.raises(PrologError):
            self.runtime.query("throw(error)")

    def test_module_system(self):
        """モジュールシステムのテスト"""
        with pytest.raises(PrologError):
            self.runtime.query("module(user)")

    def test_io_operations(self):
        """入出力操作のテスト"""
        output = StringStream()
        self.runtime.io_manager.set_output_stream(output)
        assert len(self.runtime.query("write(output_test), nl")) == 1
        assert output.get_output_string() == "output_test\n"

    def test_term_inspection(self):
        """項検査のテスト"""
        results = self.runtime.query("functor(f(a,b), F, A)")
        assert results[0].get(Variable("F")) == Atom("f")
        assert results[0].get(Variable("A")) == Number(2)

        results = self.runtime.query("arg(2, f(a,b), X)")
        assert results[0].get(Variable("X")) == Atom("b")

        results = self.runtime.query("f(a,b) =.. L")
        assert results[0].get(Variable("L")) == self._make_list(
            [Atom("f"), Atom("a"), Atom("b")]
        )

    def test_type_checking_integration(self):
        """型チェック統合のテスト"""
        assert len(self.runtime.query("var(X)")) == 1
        assert len(self.runtime.query("atom(sample)")) == 1
        assert len(self.runtime.query("number(123)")) == 1

    def test_goal_expansion(self):
        """ゴール展開のテスト"""
        with pytest.raises(PrologError):
            self.runtime.query("goal_expansion(a, b)")

    def test_operator_definitions(self):
        """演算子定義のテスト"""
        with pytest.raises(PrologError):
            self.runtime.query("op(500, xfy, foo)")

    def test_dcg_support(self):
        """DCG（文法規則）サポートのテスト"""
        with pytest.raises(PrologError):
            self.runtime.query("phrase(rule, [a])")

    def test_debugging_support(self):
        """デバッグサポートのテスト"""
        with pytest.raises(PrologError):
            self.runtime.query("trace")

    def test_profiling_support(self):
        """プロファイリングサポートのテスト"""
        with pytest.raises(PrologError):
            self.runtime.query("profile")

    def test_multi_threading(self):
        """マルチスレッドのテスト"""
        stats = self.runtime.io_manager.get_input_statistics()
        assert stats["threading_enabled"] is True
        assert stats["handler_configured"] is True

    def test_garbage_collection(self):
        """ガベージコレクションのテスト"""
        results = self.runtime.query("X is 1")
        assert results[0].get(Variable("X")) == Number(1)
        results = self.runtime.query("X is 2")
        assert results[0].get(Variable("X")) == Number(2)

    def test_foreign_interface(self):
        """外部インターフェースのテスト"""
        with pytest.raises(PrologError):
            self.runtime.query("foreign_call(foo)")

    def test_serialization(self):
        """シリアル化のテスト"""
        with pytest.raises(PrologError):
            self.runtime.query("serialize(state)")

    def test_incremental_compilation(self):
        """インクリメンタルコンパイルのテスト"""
        self._add_rules("new_fact :- fail.")
        assert len(self.runtime.query("new_fact")) == 0
        self._add_rules("new_fact.")
        assert len(self.runtime.query("new_fact")) == 1

    def test_optimization(self):
        """最適化のテスト"""
        for i in range(20):
            assert self.runtime.add_rule(f"opt({i}).")
        results = self.runtime.query("opt(X)")
        assert len(results) == 20

    def test_stress_scenarios(self):
        """ストレステストシナリオ"""
        for i in range(100):
            assert self.runtime.add_rule(f"stress({i}).")
        results = self.runtime.query("stress(X)")
        assert len(results) == 100

    def test_edge_case_integration(self):
        """境界ケース統合テスト"""
        self._add_rules("edge(a).")
        assert len(self.runtime.query("edge(a), fail")) == 0
        assert len(self.runtime.query("edge(a); edge(b)")) == 1

    def test_medical_diagnosis_japanese(self):
        """日本語医療診断KBのエンドツーエンドテスト"""
        kb_path = "tests/data/medical_diagnosis_kb_japanese.pl"
        consult_success = self.runtime.consult(kb_path)
        assert consult_success, f"Failed to consult the knowledge base: {kb_path}"

        # --- Test basic write/1 and nl/0 ---
        output = StringStream()
        self.runtime.io_manager.set_output_stream(output)
        write_solutions = self.runtime.query("test_write")
        assert write_solutions is not None, "test_write query returned None."
        # test_write should succeed once if it's found and write/nl work.
        assert len(write_solutions) >= 1, (
            "test_write query failed (or produced unexpected results)."
        )
        assert "Hello from Prolog write" in output.get_output_string()
        # --- End Test basic write/1 and nl/0 ---

        # --- Basic KB Integrity Check ---
        simple_fact_query = "疾患症状(風邪, 発熱, 0.8)"
        simple_solutions = self.runtime.query(simple_fact_query)
        assert simple_solutions is not None, "Simple fact query returned None."
        assert len(simple_solutions) > 0, (
            "Simple fact query '疾患症状(風邪, 発熱, 0.8).' failed. KB might not be loaded correctly or basic fact retrieval is broken."
        )
        # --- End Basic KB Integrity Check ---

        # Query 1: 患者診断([発熱, 咳], 30, [], [], Result). - Added empty list for Lifestyles for arity 5
        query1_str = "患者診断([発熱, 咳], 30, [], [], Result)"
        solutions1 = self.runtime.query(query1_str)

        assert solutions1 is not None, (
            "Query 1 returned None instead of a list of solutions."
        )
        assert len(solutions1) > 0, (
            "Query 1 '患者診断([発熱, 咳], 30, [], [], Result).' returned no solutions."
        )

        result_var1 = Variable("Result")
        solution1 = solutions1[0]
        assert result_var1 in solution1, (
            "Variable 'Result' not found in solution1 for Query 1."
        )
        result_value1 = solution1[result_var1]
        assert isinstance(result_value1, Term) and result_value1.functor.name == ".", (
            "Result from Query 1 should be a Prolog list."
        )

        # Query 2: 患者診断([息切れ, 発熱], 70, [糖尿病], [], Result). - Added empty list for Lifestyles for arity 5
        query2_str = "患者診断([息切れ, 発熱], 70, [糖尿病], [], Result)"
        solutions2 = self.runtime.query(query2_str)
        assert solutions2 is not None, "Query 2 returned None."
        assert len(solutions2) > 0, (
            "Query 2 '患者診断([息切れ, 発熱], 70, [糖尿病], [], Result).' returned no solutions."
        )
        result_var2 = Variable("Result")
        solution2 = solutions2[0]
        assert result_var2 in solution2, (
            "Variable 'Result' not found in solution2 for Query 2."
        )
        result_value2 = solution2[result_var2]
        assert isinstance(result_value2, Term) and result_value2.functor.name == ".", (
            "Result from Query 2 should be a Prolog list."
        )

        # Query 3: 診断([発熱, 咳, のどの痛み], 45, [喫煙], DiagnosisList). - This uses 診断/4 which correctly calls 患者診断/5
        query3_str = "診断([発熱, 咳, のどの痛み], 45, [喫煙], DiagnosisList)"
        solutions3 = self.runtime.query(query3_str)
        assert solutions3 is not None, "Query 3 returned None."
        assert len(solutions3) > 0, (
            "Query 3 '診断([発熱, 咳, のどの痛み], 45, [喫煙], DiagnosisList).' returned no solutions."
        )
        result_var3 = Variable("DiagnosisList")
        solution3 = solutions3[0]
        assert result_var3 in solution3, (
            "Variable 'DiagnosisList' not found in solution3 for Query 3."
        )
        result_value3 = solution3[result_var3]
        assert isinstance(result_value3, Term) and result_value3.functor.name == ".", (
            "DiagnosisList from Query 3 should be a Prolog list."
        )

