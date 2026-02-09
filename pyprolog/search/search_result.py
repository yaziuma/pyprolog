"""
検索結果を表すクラス

Prologルールと事実の検索結果を格納・管理します。
"""

from dataclasses import dataclass, field

from pyprolog.core.types import Fact, Rule


@dataclass
class SearchResult:
    """検索結果を表すクラス"""

    rule_or_fact: Rule | Fact
    file_path: str | None
    line_number: int
    matched_text: str
    match_type: str  # "predicate", "argument", "full_text"
    context_lines: list[str] = field(default_factory=list)  # 前後の行
    confidence: float = 1.0  # マッチ度（0.0-1.0）

    def __str__(self) -> str:
        """文字列表現"""
        location = (
            f"{self.file_path}:{self.line_number}"
            if self.file_path
            else f"line {self.line_number}"
        )
        return f"{self.match_type}マッチ [{location}] {self.matched_text} (信頼度: {self.confidence:.2f})"

    def to_dict(self) -> dict:
        """辞書形式に変換"""
        return {
            "rule_or_fact": str(self.rule_or_fact),
            "file_path": self.file_path,
            "line_number": self.line_number,
            "matched_text": self.matched_text,
            "match_type": self.match_type,
            "context_lines": self.context_lines,
            "confidence": self.confidence,
        }
