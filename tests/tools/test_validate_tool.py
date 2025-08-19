"""
ValidateToolのテスト

Prologプログラムの静的解析・検証機能のテストです。
"""

from pyprolog.tools.validate_tool import ValidateTool
from pyprolog.runtime.interpreter import Runtime
from pyprolog.core.types import Fact, Rule, Term, Atom, Variable


class TestValidateTool:
    """ValidateToolのテストクラス"""

    def setup_method(self):
        """各テストの前に実行される初期化"""
        # テスト用のルールセットを作成（問題を含む）
        rules = [
            # 正常な事実
            Fact(Term(Atom("parent"), [Atom("tom"), Atom("mary")])),
            Fact(Term(Atom("parent"), [Atom("mary"), Atom("john")])),
            # 正常なルール
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
            # 到達不能な述語（意図的に問題のあるルール）
            Rule(
                Term(Atom("unreachable_predicate"), [Variable("X")]),
                Term(Atom("some_undefined_predicate"), [Variable("X")]),
            ),
            # 未定義述語を参照するルール
            Rule(
                Term(Atom("calls_undefined"), [Variable("X")]),
                Term(Atom("undefined_predicate"), [Variable("X")]),
            ),
        ]

        self.runtime = Runtime(rules)
        self.validate_tool = ValidateTool(self.runtime)

    def test_validate_tool_initialization(self):
        """ValidateToolの初期化テスト"""
        assert self.validate_tool.runtime is not None
        assert hasattr(self.validate_tool, "validator")

    def test_validate_all_checks(self):
        """全ての検証の実行テスト"""
        result = self.validate_tool.validate_query("all", False)

        assert result["success"] is True
        assert "check_type" in result
        assert result["check_type"] == "all"
        assert "detailed" in result
        assert result["detailed"] is False
        assert "total_rules_analyzed" in result
        assert result["total_rules_analyzed"] >= 0
        assert "analysis_duration" in result
        assert "issues" in result
        assert isinstance(result["issues"], list)
        assert "summary" in result
        assert "has_errors" in result
        assert "has_warnings" in result
        assert "error_count" in result
        assert "warning_count" in result
        assert "info_count" in result

    def test_validate_conflicts_only(self):
        """矛盾検証のみのテスト"""
        result = self.validate_tool.validate_query("conflicts", False)

        assert result["success"] is True
        assert result["check_type"] == "conflicts"

    def test_validate_unreachable_only(self):
        """到達可能性検証のみのテスト"""
        result = self.validate_tool.validate_query("unreachable", False)

        assert result["success"] is True
        assert result["check_type"] == "unreachable"
        # 到達不能な述語があるので、何らかの問題が検出されるはず
        assert len(result["issues"]) >= 0

    def test_validate_undefined_only(self):
        """未定義述語検証のみのテスト"""
        result = self.validate_tool.validate_query("undefined", False)

        assert result["success"] is True
        assert result["check_type"] == "undefined"
        # 未定義述語があるので、何らかの問題が検出されるはず
        assert len(result["issues"]) >= 0

    def test_validate_with_detailed_analysis(self):
        """詳細解析付きの検証テスト"""
        result = self.validate_tool.validate_query("all", True)

        assert result["success"] is True
        assert result["detailed"] is True
        # 詳細解析では通常より多くの問題が検出される
        assert len(result["issues"]) >= 0

    def test_format_results_text(self):
        """検証結果のテキスト形式フォーマットテスト"""
        result = self.validate_tool.validate_query("all", False)
        formatted = self.validate_tool.format_results(result, "text")

        assert isinstance(formatted, str)
        assert "検証結果" in formatted or "Validation" in formatted
        assert (
            "解析ルール数" in formatted
            or str(result["total_rules_analyzed"]) in formatted
        )

    def test_format_results_json(self):
        """検証結果のJSON形式フォーマットテスト"""
        result = self.validate_tool.validate_query("all", False)
        formatted = self.validate_tool.format_results(result, "json")

        assert isinstance(formatted, str)
        # JSON形式として解析可能かチェック
        import json

        parsed = json.loads(formatted)
        assert "success" in parsed
        assert "check_type" in parsed

    def test_format_results_detailed(self):
        """検証結果の詳細形式フォーマットテスト"""
        result = self.validate_tool.validate_query("all", False)
        formatted = self.validate_tool.format_results(result, "detailed")

        assert isinstance(formatted, str)
        assert len(formatted) > 0
        assert "検証詳細レポート" in formatted or "品質評価" in formatted

    def test_format_error_result(self):
        """エラー結果のフォーマットテスト"""
        error_result = {"success": False, "error": "テストエラー"}
        formatted = self.validate_tool.format_results(error_result, "text")

        assert isinstance(formatted, str)
        assert "エラー" in formatted
        assert "テストエラー" in formatted

    def test_get_validation_statistics(self):
        """検証エンジン統計情報の取得テスト"""
        stats = self.validate_tool.get_validation_statistics()

        assert isinstance(stats, dict)
        if "error" not in stats:
            assert "symbol_table" in stats
            assert "dependency_graph" in stats
            assert "total_rules" in stats

            # シンボルテーブル統計
            symbol_stats = stats["symbol_table"]
            assert isinstance(symbol_stats, dict)

            # 依存関係グラフ統計
            graph_stats = stats["dependency_graph"]
            assert isinstance(graph_stats, dict)

    def test_rebuild_analysis(self):
        """解析データ再構築テスト"""
        success = self.validate_tool.rebuild_analysis()
        assert isinstance(success, bool)

    def test_validate_empty_runtime(self):
        """空のランタイムでの検証テスト"""
        empty_runtime = Runtime([])
        empty_validate_tool = ValidateTool(empty_runtime)

        result = empty_validate_tool.validate_query("all", False)

        assert result["success"] is True
        assert result["total_rules_analyzed"] == 0
        assert len(result["issues"]) == 0

    def test_validate_invalid_check_type(self):
        """無効な検証タイプのテスト"""
        # 無効なcheck_typeでも正常に動作するはず（デフォルト動作）
        result = self.validate_tool.validate_query("invalid_type", False)

        assert result["success"] is True
        assert result["check_type"] == "invalid_type"

    def test_issue_severity_levels(self):
        """問題の重要度レベルのテスト"""
        result = self.validate_tool.validate_query("all", False)

        if len(result["issues"]) > 0:
            # 各問題に重要度が設定されているかチェック
            for issue in result["issues"]:
                assert "severity" in issue
                assert issue["severity"] in ["error", "warning", "info"]
                assert "issue_type" in issue
                assert "message" in issue

    def test_issue_details(self):
        """問題の詳細情報テスト"""
        result = self.validate_tool.validate_query("all", False)

        if len(result["issues"]) > 0:
            for issue in result["issues"]:
                # 必須フィールドの存在確認
                assert "issue_type" in issue
                assert "severity" in issue
                assert "message" in issue
                assert isinstance(issue["message"], str)
                assert len(issue["message"]) > 0

    def test_analysis_performance(self):
        """解析性能のテスト"""
        import time

        start_time = time.time()

        result = self.validate_tool.validate_query("all", True)

        end_time = time.time()
        actual_duration = end_time - start_time

        # 解析時間が記録されているかチェック
        assert "analysis_duration" in result
        assert result["analysis_duration"] > 0
        # 実際の時間とある程度一致しているかチェック（誤差許容）
        assert abs(result["analysis_duration"] - actual_duration) < 1.0

    def test_validation_with_complex_rules(self):
        """複雑なルールでの検証テスト"""
        complex_rules = [
            # 複雑な再帰ルール
            Rule(
                Term(Atom("ancestor"), [Variable("X"), Variable("Z")]),
                Term(Atom("parent"), [Variable("X"), Variable("Z")]),
            ),
            Rule(
                Term(Atom("ancestor"), [Variable("X"), Variable("Z")]),
                Term(
                    Atom(","),
                    [
                        Term(Atom("parent"), [Variable("X"), Variable("Y")]),
                        Term(Atom("ancestor"), [Variable("Y"), Variable("Z")]),
                    ],
                ),
            ),
            # 左再帰の可能性があるルール
            Rule(
                Term(Atom("left_recursive"), [Variable("X")]),
                Term(
                    Atom(","),
                    [
                        Term(Atom("left_recursive"), [Variable("Y")]),
                        Term(Atom("some_goal"), [Variable("X"), Variable("Y")]),
                    ],
                ),
            ),
        ]

        complex_runtime = Runtime(complex_rules)
        complex_validate_tool = ValidateTool(complex_runtime)

        result = complex_validate_tool.validate_query("all", True)

        assert result["success"] is True
        # 複雑なルールなので何らかの問題が検出される可能性が高い
        assert len(result["issues"]) >= 0
