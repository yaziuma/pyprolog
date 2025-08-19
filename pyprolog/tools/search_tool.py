"""
Search ツールの実装

Prologルールと事実の検索機能を提供するためのツールです。
"""

from typing import Dict, Any, Tuple
from pyprolog.runtime.interpreter import Runtime
from pyprolog.search.search_engine import SearchEngine
from pyprolog.util.logger import get_logger

logger = get_logger(__name__)


class SearchTool:
    """Prologルールと事実の検索を提供するツール"""

    def __init__(self, runtime: Runtime):
        self.runtime = runtime
        self.search_engine = SearchEngine(runtime)

    def search_query(
        self, pattern: str, search_type: str = "predicate", limit: int = 100
    ) -> Dict[str, Any]:
        """
        検索クエリを実行します

        Args:
            pattern: 検索パターン
            search_type: 検索タイプ ("predicate", "argument", "full_text")
            limit: 結果数制限

        Returns:
            検索結果を含む辞書
        """
        try:
            logger.debug(
                f"検索実行: pattern='{pattern}', type={search_type}, limit={limit}"
            )

            # 検索を実行
            results = self.search_engine.search(pattern, search_type, limit)

            # 結果を辞書形式に変換
            result_dicts = []
            for result in results:
                result_dict = {
                    "rule": str(result.rule_or_fact),
                    "file_path": result.file_path,
                    "line_number": result.line_number,
                    "matched_text": result.matched_text,
                    "match_type": result.match_type,
                    "confidence": result.confidence,
                }
                result_dicts.append(result_dict)

            return {
                "pattern": pattern,
                "search_type": search_type,
                "results": result_dicts,
                "result_count": len(results),
                "limit": limit,
                "success": True,
            }

        except Exception as e:
            logger.error(f"検索エラー '{pattern}': {e}")
            return {
                "pattern": pattern,
                "search_type": search_type,
                "error": str(e),
                "success": False,
            }

    def parse_search_command(self, search_command: str) -> Tuple[str, str, int]:
        """
        search(pattern, type, limit) コマンドをパースします

        Args:
            search_command: search形式のコマンド文字列

        Returns:
            (pattern, search_type, limit) のタプル
        """
        try:
            # "search(" と ")." を除去
            if search_command.startswith("search(") and search_command.endswith(")."):
                inner = search_command[7:-2]  # "search(" と ")." を除去
            else:
                raise ValueError("無効なsearchコマンド形式")

            # パラメータを分割（簡易的な実装）
            parts = []
            current = ""
            paren_level = 0
            in_quotes = False

            for char in inner:
                if char == '"' and not in_quotes:
                    in_quotes = True
                elif char == '"' and in_quotes:
                    in_quotes = False
                elif char == "(" and not in_quotes:
                    paren_level += 1
                elif char == ")" and not in_quotes:
                    paren_level -= 1
                elif char == "," and paren_level == 0 and not in_quotes:
                    parts.append(current.strip())
                    current = ""
                    continue

                current += char

            if current.strip():
                parts.append(current.strip())

            # デフォルト値を設定
            pattern = parts[0] if len(parts) > 0 else ""
            search_type = parts[1] if len(parts) > 1 else "predicate"
            limit = int(parts[2]) if len(parts) > 2 and parts[2].isdigit() else 100

            # クォートを除去
            if search_type.startswith('"') and search_type.endswith('"'):
                search_type = search_type[1:-1]
            if pattern.startswith('"') and pattern.endswith('"'):
                pattern = pattern[1:-1]

            return pattern, search_type, limit

        except Exception as e:
            logger.warning(f"searchコマンド解析エラー '{search_command}': {e}")
            return search_command, "predicate", 100

    def format_results(
        self, search_result: Dict[str, Any], format_type: str = "text"
    ) -> str:
        """
        検索結果をフォーマットします

        Args:
            search_result: 検索結果辞書
            format_type: 出力形式 ("text", "json", "table")

        Returns:
            フォーマットされた結果文字列
        """
        try:
            if not search_result.get("success"):
                return f"検索エラー: {search_result.get('error', '不明なエラー')}"

            results = search_result.get("results", [])

            if not results:
                return f"パターン '{search_result['pattern']}' に一致する結果が見つかりませんでした。"

            if format_type == "json":
                import json

                return json.dumps(search_result, ensure_ascii=False, indent=2)

            elif format_type == "table":
                return self._format_table(search_result)

            else:  # text format
                return self._format_text(search_result)

        except Exception as e:
            logger.error(f"結果フォーマットエラー: {e}")
            return f"フォーマットエラー: {e}"

    def _format_text(self, search_result: Dict[str, Any]) -> str:
        """テキスト形式でフォーマット"""
        lines = []
        lines.append("=== 検索結果 ===")
        lines.append(f"パターン: {search_result['pattern']}")
        lines.append(f"検索タイプ: {search_result['search_type']}")
        lines.append(f"結果数: {search_result['result_count']} 件")
        lines.append("")

        for i, result in enumerate(search_result["results"], 1):
            lines.append(
                f"{i}. {result['match_type']}マッチ (信頼度: {result['confidence']:.2f})"
            )
            lines.append(f"   ルール: {result['rule']}")
            if result.get("file_path"):
                lines.append(f"   場所: {result['file_path']}:{result['line_number']}")
            lines.append(f"   マッチ箇所: {result['matched_text']}")
            lines.append("")

        return "\n".join(lines)

    def _format_table(self, search_result: Dict[str, Any]) -> str:
        """テーブル形式でフォーマット"""
        lines = []
        lines.append(
            f"検索結果: {search_result['pattern']} ({search_result['result_count']} 件)"
        )
        lines.append("─" * 80)
        lines.append(f"{'No.':<4} {'タイプ':<10} {'信頼度':<8} {'ルール'}")
        lines.append("─" * 80)

        for i, result in enumerate(search_result["results"], 1):
            rule_text = result["rule"]
            if len(rule_text) > 50:
                rule_text = rule_text[:47] + "..."

            lines.append(
                f"{i:<4} {result['match_type']:<10} {result['confidence']:<8.2f} {rule_text}"
            )

        lines.append("─" * 80)
        return "\n".join(lines)

    def get_search_statistics(self) -> Dict[str, Any]:
        """検索エンジンの統計情報を取得"""
        return self.search_engine.get_statistics()

    def rebuild_index(self) -> bool:
        """検索インデックスを再構築"""
        try:
            self.search_engine.invalidate_cache()
            self.search_engine.build_index()
            return True
        except Exception as e:
            logger.error(f"インデックス再構築エラー: {e}")
            return False
