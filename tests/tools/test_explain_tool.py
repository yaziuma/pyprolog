"""
ExplainToolのテスト

クエリの実行過程を説明する機能のテストです。
"""

import pytest
from pyprolog.tools.explain_tool import ExplainTool
from pyprolog.runtime.interpreter import Runtime
from pyprolog.core.types import Fact, Rule, Term, Atom, Variable


class TestExplainTool:
    """ExplainToolのテストクラス"""

    def setup_method(self):
        """各テストの前に実行される初期化"""
        # テスト用の簡単なルールを作成
        rules = [
            Fact(Term(Atom("parent"), [Atom("tom"), Atom("mary")])),
            Fact(Term(Atom("parent"), [Atom("mary"), Atom("john")])),
            Rule(
                Term(Atom("grandparent"), [Variable("X"), Variable("Z")]),
                Term(
                    Atom(","),
                    [
                        Term(Atom("parent"), [Variable("X"), Variable("Y")]),
                        Term(Atom("parent"), [Variable("Y"), Variable("Z")]),
                    ],
                ),
            ),
        ]

        self.runtime = Runtime(rules)
        self.explain_tool = ExplainTool(self.runtime)

    def test_explain_tool_initialization(self):
        """ExplainToolの初期化テスト"""
        assert self.explain_tool.runtime is not None
        assert hasattr(self.explain_tool, "runtime")

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

        # 存在しない述語は解が見つからないので success は False になる
        assert result["success"] is False
        assert "error" in result
        assert len(result["solutions"]) == 0

    def test_explain_invalid_query(self):
        """無効なクエリの説明テスト"""
        result = self.explain_tool.explain_query("invalid syntax here", "text")

        assert result["success"] is False
        assert "error" in result

    def test_explain_with_invalid_format(self):
        """無効な形式指定の説明テスト"""
        result = self.explain_tool.explain_query("parent(tom, mary)", "invalid_format")

        # 無効な形式は ValueError を発生させ、explain_toolがそれを捕捉して success: False を返す
        assert result["success"] is False
        assert "error" in result
        assert "Unknown format type" in result["error"]

    # --- Tests for parse_explain_command ---

    def test_parse_full_command(self):
        """'parse_explain_command' with all arguments"""
        command = 'explain("grandparent(X, Y)", "tree", 5).'
        query, format_type, depth = self.explain_tool.parse_explain_command(command)
        assert query == '"grandparent(X, Y)"'
        assert format_type == "tree"
        assert depth == 5

    def test_parse_command_with_default_depth(self):
        """'parse_explain_command' with default depth"""
        command = 'explain("parent(X, Y)", "json").'
        query, format_type, depth = self.explain_tool.parse_explain_command(command)
        assert query == '"parent(X, Y)"'
        assert format_type == "json"
        assert depth is None

    def test_parse_command_with_default_format_and_depth(self):
        """'parse_explain_command' with default format and depth"""
        command = 'explain("some_query(A)").'
        query, format_type, depth = self.explain_tool.parse_explain_command(command)
        assert query == '"some_query(A)"'
        assert format_type == "text"
        assert depth is None

    def test_parse_command_with_unquoted_format(self):
        """'parse_explain_command' with unquoted format type"""
        command = "explain(simple, tree, 10)."
        # The parser is simple, so it will treat `simple` as the query string
        query, format_type, depth = self.explain_tool.parse_explain_command(command)
        assert query == "simple"
        assert format_type == "tree"
        assert depth == 10

    def test_parse_invalid_command_format(self):
        """'parse_explain_command' with an invalid format"""
        command = 'splain("bad format").'
        # The parser should return the original command as query and defaults for others
        query, format_type, depth = self.explain_tool.parse_explain_command(command)
        assert query == 'splain("bad format").'
        assert format_type == "text"
        assert depth is None
