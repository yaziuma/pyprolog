"""
Explain ツールの実装

Prologクエリの実行過程を説明・可視化するためのツールです。
"""
from typing import Dict, List, Optional, Any
from pyprolog.runtime.interpreter import Runtime
from pyprolog.runtime.trace_formatter import TraceFormatter
from pyprolog.util.logger import get_logger

logger = get_logger(__name__)


class ExplainTool:
    """Prologクエリの実行説明を提供するツール"""
    
    def __init__(self, runtime: Runtime):
        self.runtime = runtime
    
    def explain_query(self, query_str: str, format_type: str = "text", max_depth: Optional[int] = None) -> Dict[str, Any]:
        """
        クエリの実行過程を説明します
        
        Args:
            query_str: 実行するクエリ
            format_type: 出力形式 ("text", "tree", "json")
            max_depth: トレースの最大深度
            
        Returns:
            説明結果を含む辞書
        """
        try:
            logger.debug(f"Explaining query: {query_str} with format: {format_type}")
            
            # トレース付きでクエリを実行
            solutions, trace_events = self.runtime.query_with_trace(query_str, max_depth)
            
            # 結果をフォーマット
            if format_type == "text":
                trace_output = TraceFormatter.format_text(trace_events)
            elif format_type == "tree":
                trace_output = TraceFormatter.format_tree(trace_events)
            elif format_type == "json":
                trace_output = TraceFormatter.format_json(trace_events, query_str, solutions)
            else:
                raise ValueError(f"Unknown format type: {format_type}")
            
            return {
                "query": query_str,
                "solutions": solutions,
                "trace": trace_output,
                "format": format_type,
                "event_count": len(trace_events),
                "success": len(solutions) > 0
            }
            
        except Exception as e:
            logger.error(f"Error explaining query '{query_str}': {e}")
            return {
                "query": query_str,
                "error": str(e),
                "success": False
            }
    
    def parse_explain_command(self, explain_command: str) -> tuple:
        """
        explain(query, format, depth) コマンドをパースします
        
        Args:
            explain_command: explain形式のコマンド文字列
            
        Returns:
            (query, format_type, depth) のタプル
        """
        try:
            # "explain(" と ")." を除去
            if explain_command.startswith("explain(") and explain_command.endswith(")."):
                inner = explain_command[8:-2]  # "explain(" と ")." を除去
            else:
                raise ValueError("Invalid explain command format")
            
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
                elif char == '(' and not in_quotes:
                    paren_level += 1
                elif char == ')' and not in_quotes:
                    paren_level -= 1
                elif char == ',' and paren_level == 0 and not in_quotes:
                    parts.append(current.strip())
                    current = ""
                    continue
                
                current += char
            
            if current.strip():
                parts.append(current.strip())
            
            # デフォルト値を設定
            query = parts[0] if len(parts) > 0 else ""
            format_type = parts[1] if len(parts) > 1 else "text"
            depth = int(parts[2]) if len(parts) > 2 and parts[2].isdigit() else None
            
            # クォートを除去
            if format_type.startswith('"') and format_type.endswith('"'):
                format_type = format_type[1:-1]
            
            return query, format_type, depth
            
        except Exception as e:
            logger.warning(f"Error parsing explain command '{explain_command}': {e}")
            return explain_command, "text", None