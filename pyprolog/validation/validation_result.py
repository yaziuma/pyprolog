"""
検証結果クラス

Prologルールと事実の静的解析結果を格納・管理します。
"""
import json
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Union, Any
from pyprolog.core.rule import Rule
from pyprolog.core.fact import Fact


@dataclass
class ValidationIssue:
    """検証で発見された問題を表すクラス"""
    issue_type: str  # "conflict", "unreachable", "undefined"
    severity: str    # "error", "warning", "info"
    message: str
    rule_or_fact: Optional[Union[Rule, Fact]]
    file_path: Optional[str]
    line_number: int
    column_number: int
    suggested_fix: Optional[str] = None
    related_items: List['ValidationIssue'] = field(default_factory=list)
    
    def __str__(self) -> str:
        """文字列表現"""
        severity_symbol = "❌" if self.severity == "error" else "⚠️" if self.severity == "warning" else "ℹ️"
        location = f"{self.file_path}:{self.line_number}" if self.file_path else f"line {self.line_number}"
        return f"{severity_symbol} [{self.issue_type}] {self.message} ({location})"
    
    def to_dict(self) -> Dict[str, Any]:
        """辞書形式に変換"""
        return {
            "issue_type": self.issue_type,
            "severity": self.severity,
            "message": self.message,
            "rule_or_fact": str(self.rule_or_fact) if self.rule_or_fact else None,
            "file_path": self.file_path,
            "line_number": self.line_number,
            "column_number": self.column_number,
            "suggested_fix": self.suggested_fix,
            "related_items_count": len(self.related_items)
        }


@dataclass
class ValidationResult:
    """検証結果全体を表すクラス"""
    issues: List[ValidationIssue]
    total_rules_analyzed: int
    analysis_duration: float
    summary: Dict[str, int] = field(default_factory=dict)  # issue_type -> count
    
    def __post_init__(self):
        """初期化後の処理"""
        if not self.summary:
            self.summary = self._calculate_summary()
    
    def has_errors(self) -> bool:
        """エラーが存在するかチェック"""
        return any(issue.severity == "error" for issue in self.issues)
    
    def has_warnings(self) -> bool:
        """警告が存在するかチェック"""
        return any(issue.severity == "warning" for issue in self.issues)
    
    def filter_by_type(self, issue_type: str) -> List[ValidationIssue]:
        """指定されたタイプの問題のみを抽出"""
        return [issue for issue in self.issues if issue.issue_type == issue_type]
    
    def filter_by_severity(self, severity: str) -> List[ValidationIssue]:
        """指定された重要度の問題のみを抽出"""
        return [issue for issue in self.issues if issue.severity == severity]
    
    def to_json(self) -> str:
        """JSON形式で出力"""
        result_dict = {
            "total_rules_analyzed": self.total_rules_analyzed,
            "analysis_duration": self.analysis_duration,
            "summary": self.summary,
            "issues": [issue.to_dict() for issue in self.issues],
            "has_errors": self.has_errors(),
            "has_warnings": self.has_warnings()
        }
        return json.dumps(result_dict, indent=2, ensure_ascii=False)
    
    def _calculate_summary(self) -> Dict[str, int]:
        """問題の種類別サマリーを計算"""
        summary = {}
        for issue in self.issues:
            if issue.issue_type not in summary:
                summary[issue.issue_type] = 0
            summary[issue.issue_type] += 1
        return summary
    
    def get_error_count(self) -> int:
        """エラー数を取得"""
        return len(self.filter_by_severity("error"))
    
    def get_warning_count(self) -> int:
        """警告数を取得"""
        return len(self.filter_by_severity("warning"))
    
    def get_info_count(self) -> int:
        """情報数を取得"""
        return len(self.filter_by_severity("info"))