"""
Validate ツールの実装

Prologルールと事実の静的解析・検証機能を提供するためのツールです。
"""

from typing import Dict, Any
from pyprolog.runtime.interpreter import Runtime
from pyprolog.validation.validator import Validator
from pyprolog.util.logger import get_logger

logger = get_logger(__name__)


class ValidateTool:
    """Prologルールと事実の検証を提供するツール"""

    def __init__(self, runtime: Runtime):
        self.runtime = runtime
        self.validator = Validator(runtime)

    def validate_query(
        self, check_type: str = "all", detailed: bool = False
    ) -> Dict[str, Any]:
        """
        検証を実行します

        Args:
            check_type: 検証タイプ ("all", "conflicts", "unreachable", "undefined")
            detailed: 詳細な解析を行うか

        Returns:
            検証結果を含む辞書
        """
        try:
            logger.debug("検証実行: type=%s, detailed=%s", check_type, detailed)

            # 検証を実行
            result = self.validator.validate(check_type, detailed)

            return {
                "check_type": check_type,
                "detailed": detailed,
                "total_rules_analyzed": result.total_rules_analyzed,
                "analysis_duration": result.analysis_duration,
                "issues": [issue.to_dict() for issue in result.issues],
                "summary": result.summary,
                "has_errors": result.has_errors(),
                "has_warnings": result.has_warnings(),
                "error_count": result.get_error_count(),
                "warning_count": result.get_warning_count(),
                "info_count": result.get_info_count(),
                "success": True,
            }

        except Exception as e:
            logger.error("検証エラー: %s", e)
            return {
                "check_type": check_type,
                "detailed": detailed,
                "error": str(e),
                "success": False,
            }

    def format_results(
        self, validation_result: Dict[str, Any], format_type: str = "text"
    ) -> str:
        """
        検証結果をフォーマットします

        Args:
            validation_result: 検証結果辞書
            format_type: 出力形式 ("text", "json", "detailed")

        Returns:
            フォーマットされた結果文字列
        """
        try:
            if not validation_result.get("success"):
                return f"検証エラー: {validation_result.get('error', '不明なエラー')}"

            if format_type == "json":
                import json

                return json.dumps(validation_result, ensure_ascii=False, indent=2)

            elif format_type == "detailed":
                return self._format_detailed(validation_result)

            else:  # text format
                return self._format_text(validation_result)

        except Exception as e:
            logger.error("結果フォーマットエラー: %s", e)
            return f"フォーマットエラー: {e}"

    def _format_text(self, validation_result: Dict[str, Any]) -> str:
        """テキスト形式でフォーマット"""
        lines = []

        # ヘッダー
        lines.append("=" * 60)
        lines.append("📋 Prologプログラム検証結果")
        lines.append("=" * 60)

        # サマリー情報
        lines.append(f"検証タイプ: {validation_result['check_type']}")
        lines.append(f"解析ルール数: {validation_result['total_rules_analyzed']}")
        lines.append(f"解析時間: {validation_result['analysis_duration']:.2f}秒")

        # 問題サマリー
        error_count = validation_result.get("error_count", 0)
        warning_count = validation_result.get("warning_count", 0)
        info_count = validation_result.get("info_count", 0)

        lines.append("")
        lines.append("📊 問題サマリー:")
        lines.append(f"  ❌ エラー: {error_count}")
        lines.append(f"  ⚠️ 警告: {warning_count}")
        lines.append(f"  ℹ️ 情報: {info_count}")

        # 種類別サマリー
        if validation_result.get("summary"):
            lines.append("")
            lines.append("🔍 種類別問題数:")
            for issue_type, count in validation_result["summary"].items():
                lines.append(f"  {issue_type}: {count}")

        # 個別問題
        issues = validation_result.get("issues", [])
        if issues:
            lines.append("")
            lines.append("🔍 詳細問題:")
            lines.append("-" * 60)

            # 重要度順にソート
            sorted_issues = sorted(
                issues,
                key=lambda x: (
                    x["severity"] == "info",
                    x["severity"] == "warning",
                    x["issue_type"],
                ),
            )

            for i, issue in enumerate(sorted_issues, 1):
                severity_symbol = (
                    "❌"
                    if issue["severity"] == "error"
                    else "⚠️"
                    if issue["severity"] == "warning"
                    else "ℹ️"
                )

                lines.append(
                    f"{i}. {severity_symbol} [{issue['issue_type']}] {issue['message']}"
                )

                if issue.get("file_path"):
                    lines.append(
                        f"   📁 場所: {issue['file_path']}:{issue['line_number']}"
                    )
                elif issue.get("line_number"):
                    lines.append(f"   📍 行: {issue['line_number']}")

                if issue.get("rule_or_fact"):
                    rule_text = str(issue["rule_or_fact"])
                    if len(rule_text) > 100:
                        rule_text = rule_text[:97] + "..."
                    lines.append(f"   📝 ルール: {rule_text}")

                if issue.get("suggested_fix"):
                    lines.append(f"   💡 提案: {issue['suggested_fix']}")

                lines.append("")

        # フッター
        if error_count == 0 and warning_count == 0:
            lines.append("✅ 問題は見つかりませんでした！")
        else:
            lines.append("🔧 上記の問題を確認して修正してください。")

        lines.append("=" * 60)

        return "\n".join(lines)

    def _format_detailed(self, validation_result: Dict[str, Any]) -> str:
        """詳細形式でフォーマット"""
        lines = []

        # 基本情報
        lines.append("🔍 Prolog検証詳細レポート")
        lines.append("=" * 80)

        # 解析統計
        lines.append("📈 解析統計:")
        lines.append(f"  • 検証タイプ: {validation_result['check_type']}")
        lines.append(
            f"  • 詳細解析: {'はい' if validation_result.get('detailed') else 'いいえ'}"
        )
        lines.append(f"  • 解析ルール数: {validation_result['total_rules_analyzed']}")
        lines.append(f"  • 解析時間: {validation_result['analysis_duration']:.3f}秒")
        lines.append("")

        # 問題の詳細分析
        issues = validation_result.get("issues", [])
        if issues:
            # 種類別グループ化
            issues_by_type = {}
            for issue in issues:
                issue_type = issue["issue_type"]
                if issue_type not in issues_by_type:
                    issues_by_type[issue_type] = []
                issues_by_type[issue_type].append(issue)

            for issue_type, type_issues in issues_by_type.items():
                lines.append(f"🔷 {issue_type.upper()} ({len(type_issues)} 件)")
                lines.append("-" * 40)

                for issue in type_issues:
                    severity_icon = {"error": "🚨", "warning": "⚠️", "info": "💡"}
                    icon = severity_icon.get(issue["severity"], "❓")

                    lines.append(f"{icon} {issue['message']}")

                    if issue.get("file_path"):
                        lines.append(
                            f"   📂 {issue['file_path']}:{issue['line_number']}"
                        )

                    if issue.get("suggested_fix"):
                        lines.append(f"   🔧 修正提案: {issue['suggested_fix']}")

                    lines.append("")

                lines.append("")

        # 品質スコア（仮想的な計算）
        total_issues = len(issues)
        total_rules = validation_result["total_rules_analyzed"]

        if total_rules > 0:
            quality_score = max(0, 100 - (total_issues * 10))  # 簡易スコア
            lines.append("🎯 品質評価:")
            lines.append(f"  スコア: {quality_score}/100")

            if quality_score >= 90:
                lines.append("  評価: 優秀 ✨")
            elif quality_score >= 70:
                lines.append("  評価:良好 👍")
            elif quality_score >= 50:
                lines.append("  評価: 要改善 ⚠️")
            else:
                lines.append("  評価: 要大幅改善 🚨")

            lines.append("")

        # 推奨事項
        lines.append("📝 推奨事項:")
        if validation_result.get("error_count", 0) > 0:
            lines.append("  1. エラーを最優先で修正してください")
        if validation_result.get("warning_count", 0) > 0:
            lines.append("  2. 警告も可能な限り対応してください")
        lines.append("  3. 定期的な検証を実行してください")
        lines.append("  4. コードレビュー時にこのツールを活用してください")

        return "\n".join(lines)

    def get_validation_statistics(self) -> Dict[str, Any]:
        """検証エンジンの統計情報を取得"""
        try:
            symbol_stats = self.validator.symbol_table.get_statistics()
            graph_stats = self.validator.dependency_graph.get_statistics()

            return {
                "symbol_table": symbol_stats,
                "dependency_graph": graph_stats,
                "total_rules": len(self.runtime.rules) if self.runtime else 0,
            }
        except Exception as e:
            logger.error("統計情報取得エラー: %s", e)
            return {"error": str(e)}

    def rebuild_analysis(self) -> bool:
        """解析データを再構築"""
        try:
            self.validator.symbol_table = self.validator.symbol_table.__class__()
            self.validator.dependency_graph = (
                self.validator.dependency_graph.__class__()
            )
            logger.info("解析データを再構築しました")
            return True
        except Exception as e:
            logger.error("解析データ再構築エラー: %s", e)
            return False
