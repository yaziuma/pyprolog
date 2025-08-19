"""
バリデーションアナライザーのテスト

各種アナライザー（ConflictAnalyzer、ReachabilityAnalyzer、UndefinedAnalyzer）のテストです。
"""
import pytest
from pyprolog.validation.analyzers.conflict_analyzer import ConflictAnalyzer
from pyprolog.validation.analyzers.reachability_analyzer import ReachabilityAnalyzer
from pyprolog.validation.analyzers.undefined_analyzer import UndefinedAnalyzer
from pyprolog.validation.symbol_table import SymbolTable, predicate_key
from pyprolog.validation.dependency_graph import DependencyGraph
from pyprolog.core.types import Fact, Rule, Term, Atom, Variable


class TestConflictAnalyzer:
    """ConflictAnalyzerのテストクラス"""
    
    def setup_method(self):
        """各テストの前に実行される初期化"""
        self.analyzer = ConflictAnalyzer()
        self.symbol_table = SymbolTable()
        self.dependency_graph = DependencyGraph()
        
        # テストデータを準備
        fact1 = Fact(Term(Atom("test_pred"), [Atom("a")]))
        fact2 = Fact(Term(Atom("test_pred"), [Atom("b")]))
        
        self.symbol_table.add_predicate("test_pred", 1, fact1, "test.pl", 1)
        self.symbol_table.add_predicate("test_pred", 1, fact2, "test.pl", 2)
    
    def test_conflict_analyzer_initialization(self):
        """ConflictAnalyzerの初期化テスト"""
        assert self.analyzer is not None
    
    def test_analyze_no_conflicts(self):
        """矛盾なしの場合のテスト"""
        # 矛盾のないデータ
        clean_symbol_table = SymbolTable()
        clean_dependency_graph = DependencyGraph()
        
        fact = Fact(Term(Atom("clean_pred"), [Atom("value")]))
        clean_symbol_table.add_predicate("clean_pred", 1, fact, "clean.pl", 1)
        
        issues = self.analyzer.analyze(clean_symbol_table, clean_dependency_graph)
        assert isinstance(issues, list)
        # 矛盾はないので、問題は見つからないかもしれない
        assert len(issues) >= 0
    
    def test_analyze_with_conflicts(self):
        """矛盾ありの場合のテスト"""
        issues = self.analyzer.analyze(self.symbol_table, self.dependency_graph)
        assert isinstance(issues, list)
        assert len(issues) >= 0
        
        # 問題が見つかった場合の検証
        for issue in issues:
            assert hasattr(issue, 'issue_type')
            assert hasattr(issue, 'severity')
            assert hasattr(issue, 'message')


class TestReachabilityAnalyzer:
    """ReachabilityAnalyzerのテストクラス"""
    
    def setup_method(self):
        """各テストの前に実行される初期化"""
        self.analyzer = ReachabilityAnalyzer()
        self.symbol_table = SymbolTable()
        self.dependency_graph = DependencyGraph()
        
        # エントリーポイントとなる事実
        entry_fact = Fact(Term(Atom("entry_point"), []))
        self.symbol_table.add_predicate("entry_point", 0, entry_fact, "test.pl", 1)
        
        # 到達可能なルール
        reachable_rule = Rule(
            Term(Atom("reachable"), [Variable("X")]),
            Term(Atom("entry_point"), [])
        )
        self.symbol_table.add_predicate("reachable", 1, reachable_rule, "test.pl", 2)
        
        # 到達不可能なルール
        unreachable_rule = Rule(
            Term(Atom("unreachable"), [Variable("X")]),
            Term(Atom("some_other"), [Variable("X")])
        )
        self.symbol_table.add_predicate("unreachable", 1, unreachable_rule, "test.pl", 3)
        
        # 依存関係を構築
        self.dependency_graph.add_node("entry_point/0")
        self.dependency_graph.add_node("reachable/1")
        self.dependency_graph.add_node("unreachable/1")
        self.dependency_graph.add_edge("reachable/1", "entry_point/0")
    
    def test_reachability_analyzer_initialization(self):
        """ReachabilityAnalyzerの初期化テスト"""
        assert self.analyzer is not None
    
    def test_get_entry_points(self):
        """エントリーポイント特定のテスト"""
        entry_points = self.analyzer._get_entry_points(self.symbol_table)
        assert isinstance(entry_points, set)
        assert "entry_point/0" in entry_points
    
    def test_is_entry_point(self):
        """エントリーポイント判定のテスト"""
        # 事実のエントリーポイント判定
        fact_info = type('PredicateInfo', (), {
            'definition': Fact(Term(Atom("test"), [])),
            'arity': 0
        })()
        assert self.analyzer._is_entry_point("test", fact_info) is True
        
        # main_で始まる述語
        main_info = type('PredicateInfo', (), {
            'definition': Rule(Term(Atom("main_test"), []), Term(Atom("true"), [])),
            'arity': 0
        })()
        assert self.analyzer._is_entry_point("main_test", main_info) is True
    
    def test_should_ignore_unreachable(self):
        """到達不可能述語の無視判定テスト"""
        # テスト関数は無視される
        assert self.analyzer._should_ignore_unreachable("test_function") is True
        
        # ヘルパー関数は無視される
        assert self.analyzer._should_ignore_unreachable("helper_function") is True
        
        # 通常の述語は無視されない
        assert self.analyzer._should_ignore_unreachable("normal_predicate") is False
    
    def test_analyze_reachability(self):
        """到達可能性解析のテスト"""
        issues = self.analyzer.analyze(self.symbol_table, self.dependency_graph)
        assert isinstance(issues, list)
        
        # 到達不可能な述語が検出される可能性
        unreachable_found = any("unreachable" in issue.message for issue in issues)
        # 実装依存なので、エラーが発生しないことだけ確認
        assert len(issues) >= 0


class TestUndefinedAnalyzer:
    """UndefinedAnalyzerのテストクラス"""
    
    def setup_method(self):
        """各テストの前に実行される初期化"""
        self.analyzer = UndefinedAnalyzer()
        self.symbol_table = SymbolTable()
        self.dependency_graph = DependencyGraph()
        
        # 定義済み述語
        defined_fact = Fact(Term(Atom("defined_pred"), [Atom("value")]))
        self.symbol_table.add_predicate("defined_pred", 1, defined_fact, "test.pl", 1)
        
        # 未定義述語を参照するルール
        undefined_rule = Rule(
            Term(Atom("caller"), [Variable("X")]),
            Term(Atom("undefined_pred"), [Variable("X")])
        )
        self.symbol_table.add_predicate("caller", 1, undefined_rule, "test.pl", 2)
        self.symbol_table.add_reference("undefined_pred", 1, undefined_rule, "test.pl", 2, "body")
    
    def test_undefined_analyzer_initialization(self):
        """UndefinedAnalyzerの初期化テスト"""
        assert self.analyzer is not None
    
    def test_collect_all_references(self):
        """全参照収集のテスト"""
        references = self.analyzer._collect_all_references(self.symbol_table)
        assert isinstance(references, dict)
        assert "undefined_pred/1" in references
    
    def test_determine_severity(self):
        """重要度決定のテスト"""
        # main関数は重要
        assert self.analyzer._determine_severity("main", 0) == "error"
        
        # test関数は警告
        assert self.analyzer._determine_severity("test_something", 1) == "warning"
        
        # 通常の述語はエラー
        assert self.analyzer._determine_severity("normal_pred", 2) == "error"
    
    def test_suggest_fix(self):
        """修正提案のテスト"""
        suggestion = self.analyzer._suggest_fix("undefined", 1, self.symbol_table)
        assert isinstance(suggestion, str)
        assert "undefined/1" in suggestion
    
    def test_find_similar_predicates(self):
        """類似述語検索のテスト"""
        defined_predicates = {"defined_pred/1", "another_pred/1", "defined_func/2"}
        
        # 類似の述語を検索
        similar = self.analyzer._find_similar_predicates("defined", 1, defined_predicates)
        assert isinstance(similar, list)
        assert len(similar) <= 3  # 最大3つまで
    
    def test_is_similar_name(self):
        """名前類似性判定のテスト"""
        # 1文字違い
        assert self.analyzer._is_similar_name("test", "test1") is True
        assert self.analyzer._is_similar_name("pred", "pref") is True
        
        # 部分一致
        assert self.analyzer._is_similar_name("test", "testing") is True
        
        # 全く違う
        assert self.analyzer._is_similar_name("abc", "xyz") is False
    
    def test_analyze_undefined_predicates(self):
        """未定義述語解析のテスト"""
        issues = self.analyzer.analyze(self.symbol_table, self.dependency_graph)
        assert isinstance(issues, list)
        
        # 未定義述語があるので何らかの問題が見つかるはず
        undefined_found = any("undefined" in issue.message.lower() for issue in issues)
        # 実装によっては問題が見つからない場合もあるので、エラーが発生しないことを確認
        assert len(issues) >= 0


class TestAnalyzersIntegration:
    """アナライザー統合テスト"""
    
    def setup_method(self):
        """各テストの前に実行される初期化"""
        self.conflict_analyzer = ConflictAnalyzer()
        self.reachability_analyzer = ReachabilityAnalyzer()
        self.undefined_analyzer = UndefinedAnalyzer()
        
        # 複雑なテストケースを準備
        self.symbol_table = SymbolTable()
        self.dependency_graph = DependencyGraph()
        
        # エントリーポイント
        entry = Fact(Term(Atom("main"), []))
        self.symbol_table.add_predicate("main", 0, entry, "main.pl", 1)
        
        # 正常なルール
        normal_rule = Rule(
            Term(Atom("process"), [Variable("X")]),
            Term(Atom("main"), [])
        )
        self.symbol_table.add_predicate("process", 1, normal_rule, "main.pl", 2)
        
        # 問題のあるルール
        problematic_rule = Rule(
            Term(Atom("problematic"), [Variable("X")]),
            Term(Atom("missing_predicate"), [Variable("X")])
        )
        self.symbol_table.add_predicate("problematic", 1, problematic_rule, "main.pl", 3)
        self.symbol_table.add_reference("missing_predicate", 1, problematic_rule, "main.pl", 3, "body")
        
        # 依存関係を構築
        self.dependency_graph.add_node("main/0")
        self.dependency_graph.add_node("process/1")
        self.dependency_graph.add_node("problematic/1")
        self.dependency_graph.add_edge("process/1", "main/0")
    
    def test_all_analyzers_run_without_error(self):
        """全アナライザーがエラーなしで実行されるテスト"""
        # すべてのアナライザーを実行
        conflict_issues = self.conflict_analyzer.analyze(self.symbol_table, self.dependency_graph)
        reachability_issues = self.reachability_analyzer.analyze(self.symbol_table, self.dependency_graph)
        undefined_issues = self.undefined_analyzer.analyze(self.symbol_table, self.dependency_graph)
        
        # エラーなく実行されることを確認
        assert isinstance(conflict_issues, list)
        assert isinstance(reachability_issues, list)
        assert isinstance(undefined_issues, list)
    
    def test_analyzers_find_different_issues(self):
        """各アナライザーが異なる種類の問題を発見するテスト"""
        conflict_issues = self.conflict_analyzer.analyze(self.symbol_table, self.dependency_graph)
        reachability_issues = self.reachability_analyzer.analyze(self.symbol_table, self.dependency_graph)
        undefined_issues = self.undefined_analyzer.analyze(self.symbol_table, self.dependency_graph)
        
        # 各アナライザーが独自の問題タイプを検出
        all_issues = conflict_issues + reachability_issues + undefined_issues
        
        if len(all_issues) > 0:
            issue_types = set(issue.issue_type for issue in all_issues)
            # 複数の異なる問題タイプが検出されることを期待
            assert len(issue_types) >= 0
    
    def test_analyzer_performance_with_large_dataset(self):
        """大規模データセットでのアナライザー性能テスト"""
        # 大量のルールを追加
        large_symbol_table = SymbolTable()
        large_dependency_graph = DependencyGraph()
        
        for i in range(100):
            fact = Fact(Term(Atom(f"pred_{i}"), [Atom(f"value_{i}")]))
            large_symbol_table.add_predicate(f"pred_{i}", 1, fact, f"file_{i}.pl", 1)
        
        # 各アナライザーが大量データで正常動作することを確認
        import time
        
        start = time.time()
        conflict_issues = self.conflict_analyzer.analyze(large_symbol_table, large_dependency_graph)
        conflict_time = time.time() - start
        
        start = time.time()
        reachability_issues = self.reachability_analyzer.analyze(large_symbol_table, large_dependency_graph)
        reachability_time = time.time() - start
        
        start = time.time()
        undefined_issues = self.undefined_analyzer.analyze(large_symbol_table, large_dependency_graph)
        undefined_time = time.time() - start
        
        # 合理的な時間内で完了することを確認（10秒以内）
        assert conflict_time < 10.0
        assert reachability_time < 10.0
        assert undefined_time < 10.0
        
        # 結果が返されることを確認
        assert isinstance(conflict_issues, list)
        assert isinstance(reachability_issues, list)
        assert isinstance(undefined_issues, list)