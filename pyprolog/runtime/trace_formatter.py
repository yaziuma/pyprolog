"""
トレース結果のフォーマッタ

トレースイベントを様々な形式（テキスト、ツリー、JSON）で出力するためのフォーマッタを提供します。
"""

import json
from typing import Any

from pyprolog.core.binding_environment import BindingEnvironment
from pyprolog.runtime.tracer import TraceEvent
from pyprolog.util.logger import get_logger

logger = get_logger(__name__)


class TraceFormatter:
    """トレース結果の出力フォーマットを提供するクラス"""

    @staticmethod
    def format_text(events: list[TraceEvent]) -> str:
        """トレースイベントをテキスト形式で出力"""
        try:
            return TraceFormatter._safe_format_text(events)
        except Exception as e:
            logger.error("Error formatting trace as text: %s", e)
            return f"Error formatting trace: {e}\nRaw events: {len(events)} events recorded"

    @staticmethod
    def _safe_format_text(events: list[TraceEvent]) -> str:
        """安全なテキスト形式フォーマット"""
        if not events:
            return "No trace events recorded."

        result = []
        result.append("=== Execution Trace ===")

        for event in events:
            indent = "  " * event.depth

            if event.event_type == "CALL":
                result.append(f"{indent}CALL: {event.goal}")
            elif event.event_type == "EXIT":
                bindings_str = TraceFormatter._format_bindings(event.bindings)
                rule_info = (
                    f" (via {type(event.rule_ref).__name__})" if event.rule_ref else ""
                )
                result.append(f"{indent}EXIT: {event.goal}{bindings_str}{rule_info}")
            elif event.event_type == "FAIL":
                result.append(f"{indent}FAIL: {event.goal}")
            elif event.event_type == "REDO":
                result.append(f"{indent}REDO: {event.goal}")

        result.append("=== End of Trace ===")
        return "\n".join(result)

    @staticmethod
    def format_tree(events: list[TraceEvent]) -> str:
        """トレースイベントをツリー形式で出力"""
        try:
            return TraceFormatter._safe_format_tree(events)
        except Exception as e:
            logger.error("Error formatting trace as tree: %s", e)
            return f"Error formatting trace tree: {e}"

    @staticmethod
    def _safe_format_tree(events: list[TraceEvent]) -> str:
        """安全なツリー形式フォーマット"""
        if not events:
            return "No trace events recorded."

        # 階層構造を構築
        tree_nodes = TraceFormatter._build_tree_structure(events)

        # ツリーをレンダリング
        result = []
        result.append("=== Execution Tree ===")
        result.extend(TraceFormatter._render_tree(tree_nodes))
        result.append("=== End of Tree ===")

        return "\n".join(result)

    @staticmethod
    def format_json(events: list[TraceEvent], query: str, solutions: list[dict]) -> str:
        """トレースイベントをJSON形式で出力"""
        try:
            return TraceFormatter._safe_format_json(events, query, solutions)
        except Exception as e:
            logger.error("Error formatting trace as JSON: %s", e)
            return json.dumps(
                {"error": f"Error formatting trace: {e}", "event_count": len(events)},
                indent=2,
                ensure_ascii=False,
            )

    @staticmethod
    def _safe_format_json(
        events: list[TraceEvent], query: str, solutions: list[dict]
    ) -> str:
        """安全なJSON形式フォーマット"""
        trace_data = []

        for event in events:
            event_data = {
                "event": event.event_type,
                "goal": str(event.goal),
                "depth": event.depth,
                "bindings": TraceFormatter._serialize_bindings(event.bindings),
                "timestamp": event.timestamp,
            }

            if event.rule_ref:
                event_data["rule_type"] = type(event.rule_ref).__name__
                event_data["rule_text"] = str(event.rule_ref)

            trace_data.append(event_data)

        result = {
            "query": query,
            "status": "SUCCESS" if solutions else "FAIL",
            "solutions": solutions,
            "trace": {
                "events": trace_data,
                "event_count": len(trace_data),
                "max_depth": max((event.depth for event in events), default=0),
            },
        }

        return json.dumps(result, indent=2, ensure_ascii=False)

    @staticmethod
    def _format_bindings(bindings: BindingEnvironment) -> str:
        """バインディング環境を文字列として整形"""
        if not bindings or not bindings.bindings:
            return ""

        binding_strs = []
        for var_name, value in bindings.bindings.items():
            binding_strs.append(f"{var_name}={value}")

        return f" [{', '.join(binding_strs)}]"

    @staticmethod
    def _serialize_bindings(bindings: BindingEnvironment) -> dict[str, Any]:
        """バインディング環境をシリアライズ"""
        if not bindings or not bindings.bindings:
            return {}

        result = {}
        for var_name, value in bindings.bindings.items():
            try:
                # 値を文字列として記録
                result[var_name] = str(value)
            except Exception as e:
                result[var_name] = f"<serialization error: {e}>"

        return result

    @staticmethod
    def _build_tree_structure(events: list[TraceEvent]) -> list[dict]:
        """イベントから階層構造を構築"""
        nodes = []
        stack = []  # 現在の呼び出しスタック

        for event in events:
            if event.event_type == "CALL":
                node = {
                    "goal": str(event.goal),
                    "depth": event.depth,
                    "status": "pending",
                    "children": [],
                    "bindings": TraceFormatter._serialize_bindings(event.bindings),
                }

                if event.depth == 0:
                    nodes.append(node)
                else:
                    # 親ノードを見つけて子として追加
                    if stack and len(stack) > event.depth:
                        stack[event.depth - 1]["children"].append(node)

                # スタックを調整
                while len(stack) <= event.depth:
                    stack.append(None)
                stack[event.depth] = node

            elif event.event_type == "EXIT":
                # 対応するCALLノードのステータスを更新
                if event.depth < len(stack) and stack[event.depth]:
                    stack[event.depth]["status"] = "success"
                    stack[event.depth]["bindings"] = TraceFormatter._serialize_bindings(
                        event.bindings
                    )
                    if event.rule_ref:
                        stack[event.depth]["rule"] = str(event.rule_ref)

            elif event.event_type == "FAIL":
                # 対応するCALLノードのステータスを更新
                if event.depth < len(stack) and stack[event.depth]:
                    stack[event.depth]["status"] = "failed"

        return nodes

    @staticmethod
    def _render_tree(nodes: list[dict], prefix: str = "") -> list[str]:
        """ツリーノードをテキスト表現でレンダリング"""
        result = []

        for i, node in enumerate(nodes):
            is_last = i == len(nodes) - 1

            # ノードの記号
            symbol = "└─" if is_last else "├─"
            status_symbol = (
                "✓"
                if node["status"] == "success"
                else "✗"
                if node["status"] == "failed"
                else "●"
            )

            # ノード情報
            bindings_str = ""
            if node.get("bindings"):
                bindings_items = [f"{k}={v}" for k, v in node["bindings"].items()]
                if bindings_items:
                    bindings_str = f" [{', '.join(bindings_items)}]"

            result.append(
                f"{prefix}{symbol} {status_symbol} {node['goal']}{bindings_str}"
            )

            # 子ノードの描画
            if node["children"]:
                child_prefix = prefix + ("  " if is_last else "│ ")
                result.extend(
                    TraceFormatter._render_tree(node["children"], child_prefix)
                )

        return result
