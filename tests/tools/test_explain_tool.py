"""
ExplainToolのテスト

クエリの実行過程を説明する機能のテストです。
"""
import pytest
from unittest.mock import Mock, patch
from pyprolog.tools.explain_tool import ExplainTool
from pyprolog.runtime.interpreter import Runtime
from pyprolog.runtime.tracer import TraceEvent
from pyprolog.parser.parser import Parser
from pyprolog.parser.scanner import Scanner
from pyprolog.core.types import Fact, Rule, Term, Atom


class TestExplainTool:
    """ExplainToolのテストクラス"""
    
    def setup_method(self):
        """各テストの前に実行される初期化"""
        # テスト用の簡単なルールを作成
        rules = [
            Fact(Term(Atom("parent"), [Atom("tom"), Atom("mary")])),
            Fact(Term(Atom("parent"), [Atom("mary"), Atom("john")])),
            Rule(
                Term(Atom("grandparent"), [Atom("X"), Atom("Z")]),
                Term(Atom(","), [
                    Term(Atom("parent"), [Atom("X"), Atom("Y")]),
                    Term(Atom("parent"), [Atom("Y"), Atom("Z")])
                ])
            )
        ]
        
        self.runtime = Runtime(rules)
        self.explain_tool = ExplainTool(self.runtime)
    
    def test_explain_tool_initialization(self):
        """ExplainToolの初期化テスト"""
        assert self.explain_tool.runtime is not None
        assert hasattr(self.explain_tool, 'runtime')
    
    def test_explain_simple_fact_query(self):
        """単純な事実クエリの説明テスト"""
        result = self.explain_tool.explain_query("parent(tom, mary)", "text")
        
        assert result["success"] is True
        assert "parent(tom, mary)" in result["query"]
        assert len(result["solutions"]) >= 1
        assert result["event_count"] >= 1
        assert "trace" in result
        assert isinstance(result["trace"], str)
    
    def test_explain_rule_query(self):
        """ルールクエリの説明テスト"""
        result = self.explain_tool.explain_query("grandparent(tom, john)", "text")
        
        assert result["success"] is True
        assert "grandparent(tom, john)" in result["query"]
        assert "trace" in result
        # grandparentルールが実行されるので複数のイベントが期待される
        assert result["event_count"] > 1
    
    def test_explain_with_tree_format(self):
        """ツリー形式での説明テスト"""
        result = self.explain_tool.explain_query("parent(tom, mary)", "tree")
        
        assert result["success"] is True
        assert "trace" in result
        # ツリー形式の特徴的な文字が含まれているかチェック
        trace_text = result["trace"]
        assert any(char in trace_text for char in ["├", "└", "│", "─"])
    
    def test_explain_with_json_format(self):
        """JSON形式での説明テスト"""
        result = self.explain_tool.explain_query("parent(tom, mary)", "json")
        
        assert result["success"] is True
        assert "trace" in result
        # JSON形式なので文字列としてJSONが含まれているはず
        import json
        try:
            parsed_json = json.loads(result["trace"])
            assert isinstance(parsed_json, (list, dict))
        except json.JSONDecodeError:
            pytest.fail("JSON形式の出力が無効です")
    
    def test_explain_with_depth_limit(self):
        """深度制限付きの説明テスト"""
        result = self.explain_tool.explain_query("grandparent(tom, john)", "text", 2)
        
        assert result["success"] is True
        assert "trace" in result
        # 深度制限により、イベント数が制限されているかは実装依存
        # 少なくともエラーが発生しないことを確認
    
    def test_explain_nonexistent_predicate(self):
        """存在しない述語の説明テスト"""
        result = self.explain_tool.explain_query("nonexistent(X)", "text")
        
        # 存在しない述語でもエラーにならず、解が見つからないだけであることを確認
        assert result["success"] is True
        assert len(result["solutions"]) == 0
    
    def test_explain_invalid_query(self):
        """無効なクエリの説明テスト"""
        result = self.explain_tool.explain_query("invalid syntax here", "text")
        
        # パースエラーが発生するはず
        assert result["success"] is False
        assert "error" in result
    
    def test_explain_with_invalid_format(self):
        """無効な形式指定の説明テスト"""
        result = self.explain_tool.explain_query("parent(tom, mary)", "invalid_format")
        
        # 無効な形式でもデフォルト形式で処理されるはず
        assert result["success"] is True
        assert "trace" in result
    
    def test_format_trace_events_text(self):
        """トレースイベントのテキスト形式フォーマットテスト"""
        # モックイベントを作成
        events = [
            TraceEvent("goal_start", {"goal": "test", "depth": 0}),
            TraceEvent("goal_success", {"goal": "test", "depth": 0})
        ]
        
        formatted = self.explain_tool._format_trace_events(events, "text")
        assert isinstance(formatted, str)
        assert "test" in formatted
    
    def test_format_trace_events_tree(self):
        """トレースイベントのツリー形式フォーマットテスト"""
        events = [
            TraceEvent("goal_start", {"goal": "test", "depth": 0}),
            TraceEvent("goal_success", {"goal": "test", "depth": 0})
        ]
        
        formatted = self.explain_tool._format_trace_events(events, "tree")
        assert isinstance(formatted, str)
    
    def test_format_trace_events_json(self):
        """トレースイベントのJSON形式フォーマットテスト"""
        events = [
            TraceEvent("goal_start", {"goal": "test", "depth": 0}),
            TraceEvent("goal_success", {"goal": "test", "depth": 0})
        ]
        
        formatted = self.explain_tool._format_trace_events(events, "json")
        assert isinstance(formatted, str)
        # JSON形式として解析可能かチェック
        import json
        parsed = json.loads(formatted)
        assert isinstance(parsed, list)
        assert len(parsed) == 2