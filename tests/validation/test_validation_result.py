"""
ValidationResultとValidationIssueのテスト

検証結果クラスのテストです。
"""

from pyprolog.validation.validation_result import ValidationResult, ValidationIssue
from pyprolog.core.types import Fact, Term, Atom


class TestValidationIssue:
    """ValidationIssueのテストクラス"""

    def test_validation_issue_creation(self):
        """ValidationIssueの作成テスト"""
        test_fact = Fact(Term(Atom("test"), [Atom("arg")]))

        issue = ValidationIssue(
            issue_type="test_type",
            severity="error",
            message="テストメッセージ",
            rule_or_fact=test_fact,
            file_path="/test/path.pl",
            line_number=10,
            column_number=5,
            suggested_fix="修正提案",
        )

        assert issue.issue_type == "test_type"
        assert issue.severity == "error"
        assert issue.message == "テストメッセージ"
        assert issue.rule_or_fact == test_fact
        assert issue.file_path == "/test/path.pl"
        assert issue.line_number == 10
        assert issue.column_number == 5
        assert issue.suggested_fix == "修正提案"

    def test_validation_issue_to_dict(self):
        """ValidationIssueの辞書変換テスト"""
        test_fact = Fact(Term(Atom("test"), [Atom("arg")]))

        issue = ValidationIssue(
            issue_type="test_type",
            severity="warning",
            message="警告メッセージ",
            rule_or_fact=test_fact,
            file_path="/test/path.pl",
            line_number=20,
            column_number=10,
        )

        issue_dict = issue.to_dict()

        assert isinstance(issue_dict, dict)
        assert issue_dict["issue_type"] == "test_type"
        assert issue_dict["severity"] == "warning"
        assert issue_dict["message"] == "警告メッセージ"
        assert issue_dict["file_path"] == "/test/path.pl"
        assert issue_dict["line_number"] == 20
        assert issue_dict["column_number"] == 10
        assert "rule_or_fact" in issue_dict

    def test_validation_issue_without_optional_fields(self):
        """オプションフィールドなしのValidationIssueテスト"""
        issue = ValidationIssue(
            issue_type="minimal",
            severity="info",
            message="最小限のissue",
            rule_or_fact=None,
            file_path=None,
            line_number=0,
            column_number=0,
        )

        assert issue.issue_type == "minimal"
        assert issue.severity == "info"
        assert issue.rule_or_fact is None
        assert issue.file_path is None
        assert issue.suggested_fix is None

    def test_validation_issue_severity_validation(self):
        """重要度の検証テスト"""
        valid_severities = ["error", "warning", "info"]

        for severity in valid_severities:
            issue = ValidationIssue(
                issue_type="test",
                severity=severity,
                message="テスト",
                rule_or_fact=None,
                file_path=None,
                line_number=0,
                column_number=0,
            )
            assert issue.severity == severity


class TestValidationResult:
    """ValidationResultのテストクラス"""

    def test_validation_result_creation(self):
        """ValidationResultの作成テスト"""
        test_fact = Fact(Term(Atom("test"), [Atom("arg")]))

        issues = [
            ValidationIssue(
                "error_type", "error", "エラーメッセージ", test_fact, None, 1, 0
            ),
            ValidationIssue(
                "warning_type", "warning", "警告メッセージ", test_fact, None, 2, 0
            ),
            ValidationIssue(
                "info_type", "info", "情報メッセージ", test_fact, None, 3, 0
            ),
        ]

        result = ValidationResult(
            issues=issues, total_rules_analyzed=10, analysis_duration=1.5
        )

        assert len(result.issues) == 3
        assert result.total_rules_analyzed == 10
        assert result.analysis_duration == 1.5

    def test_validation_result_empty(self):
        """空のValidationResultテスト"""
        result = ValidationResult(
            issues=[], total_rules_analyzed=0, analysis_duration=0.1
        )

        assert len(result.issues) == 0
        assert result.total_rules_analyzed == 0
        assert result.analysis_duration == 0.1

    def test_has_errors_method(self):
        """has_errors()メソッドのテスト"""
        # エラーありのケース
        error_issues = [
            ValidationIssue("error_type", "error", "エラー", None, None, 1, 0),
            ValidationIssue("warning_type", "warning", "警告", None, None, 2, 0),
        ]

        result_with_errors = ValidationResult(error_issues, 5, 1.0)
        assert result_with_errors.has_errors() is True

        # エラーなしのケース
        warning_issues = [
            ValidationIssue("warning_type", "warning", "警告", None, None, 1, 0),
            ValidationIssue("info_type", "info", "情報", None, None, 2, 0),
        ]

        result_without_errors = ValidationResult(warning_issues, 5, 1.0)
        assert result_without_errors.has_errors() is False

        # 問題なしのケース
        empty_result = ValidationResult([], 5, 1.0)
        assert empty_result.has_errors() is False

    def test_has_warnings_method(self):
        """has_warnings()メソッドのテスト"""
        # 警告ありのケース
        warning_issues = [
            ValidationIssue("warning_type", "warning", "警告", None, None, 1, 0),
            ValidationIssue("info_type", "info", "情報", None, None, 2, 0),
        ]

        result_with_warnings = ValidationResult(warning_issues, 5, 1.0)
        assert result_with_warnings.has_warnings() is True

        # 警告なしのケース
        info_issues = [ValidationIssue("info_type", "info", "情報", None, None, 1, 0)]

        result_without_warnings = ValidationResult(info_issues, 5, 1.0)
        assert result_without_warnings.has_warnings() is False

    def test_get_error_count_method(self):
        """get_error_count()メソッドのテスト"""
        mixed_issues = [
            ValidationIssue("error1", "error", "エラー1", None, None, 1, 0),
            ValidationIssue("error2", "error", "エラー2", None, None, 2, 0),
            ValidationIssue("warning1", "warning", "警告1", None, None, 3, 0),
            ValidationIssue("info1", "info", "情報1", None, None, 4, 0),
        ]

        result = ValidationResult(mixed_issues, 10, 1.0)
        assert result.get_error_count() == 2

    def test_get_warning_count_method(self):
        """get_warning_count()メソッドのテスト"""
        mixed_issues = [
            ValidationIssue("error1", "error", "エラー1", None, None, 1, 0),
            ValidationIssue("warning1", "warning", "警告1", None, None, 2, 0),
            ValidationIssue("warning2", "warning", "警告2", None, None, 3, 0),
            ValidationIssue("info1", "info", "情報1", None, None, 4, 0),
        ]

        result = ValidationResult(mixed_issues, 10, 1.0)
        assert result.get_warning_count() == 2

    def test_get_info_count_method(self):
        """get_info_count()メソッドのテスト"""
        mixed_issues = [
            ValidationIssue("error1", "error", "エラー1", None, None, 1, 0),
            ValidationIssue("warning1", "warning", "警告1", None, None, 2, 0),
            ValidationIssue("info1", "info", "情報1", None, None, 3, 0),
            ValidationIssue("info2", "info", "情報2", None, None, 4, 0),
            ValidationIssue("info3", "info", "情報3", None, None, 5, 0),
        ]

        result = ValidationResult(mixed_issues, 10, 1.0)
        assert result.get_info_count() == 3

    def test_summary_property(self):
        """summaryプロパティのテスト"""
        mixed_issues = [
            ValidationIssue("conflict", "error", "矛盾", None, None, 1, 0),
            ValidationIssue("conflict", "error", "矛盾2", None, None, 2, 0),
            ValidationIssue("unreachable", "warning", "到達不能", None, None, 3, 0),
            ValidationIssue("undefined", "info", "未定義", None, None, 4, 0),
        ]

        result = ValidationResult(mixed_issues, 10, 1.0)
        summary = result.summary

        assert isinstance(summary, dict)
        assert summary.get("conflict", 0) == 2
        assert summary.get("unreachable", 0) == 1
        assert summary.get("undefined", 0) == 1

    def test_validation_result_with_large_dataset(self):
        """大量データでのValidationResultテスト"""
        # 大量の問題を作成
        large_issues = []
        for i in range(1000):
            issue_type = ["error", "warning", "info"][i % 3]
            large_issues.append(
                ValidationIssue(
                    f"type_{i % 10}", issue_type, f"メッセージ{i}", None, None, i, 0
                )
            )

        result = ValidationResult(large_issues, 1000, 5.0)

        assert len(result.issues) == 1000
        assert (
            result.get_error_count()
            + result.get_warning_count()
            + result.get_info_count()
            == 1000
        )

        # 性能テスト：サマリー生成が適切に動作するか
        summary = result.summary
        assert isinstance(summary, dict)
        assert len(summary) <= 10  # type_0からtype_9まで
