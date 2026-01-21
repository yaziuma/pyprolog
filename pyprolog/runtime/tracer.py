"""
トレース機能の実装

Prologクエリの実行過程を記録・可視化するためのトレース機能を提供します。
"""

import time
from dataclasses import dataclass
from typing import List, Optional, Union
from pyprolog.core.types import Term, Rule, Fact
from pyprolog.core.binding_environment import BindingEnvironment
from pyprolog.util.logger import get_logger

logger = get_logger(__name__)


@dataclass
class TraceEvent:
    """トレースイベントを表すクラス"""

    event_type: str  # "CALL", "EXIT", "FAIL", "REDO"
    goal: Term
    depth: int
    bindings: BindingEnvironment
    timestamp: float
    rule_ref: Optional[Union[Rule, Fact]] = None


class Tracer:
    """クエリ実行のトレース機能を提供するクラス"""

    def __init__(self, max_depth: Optional[int] = None, max_events: int = 10000):
        self.events: List[TraceEvent] = []
        self.max_depth = max_depth
        self.max_events = max_events
        self.current_depth = 0
        self.enabled = False

    def start_trace(self) -> None:
        """トレースを開始します"""
        self.enabled = True
        self.current_depth = 0
        self.events.clear()
        logger.debug("Tracing started")

    def stop_trace(self) -> None:
        """トレースを停止します"""
        self.enabled = False
        logger.debug("Tracing stopped. Recorded %d events", len(self.events))

    def record_call(self, goal: Term, bindings: BindingEnvironment) -> None:
        """ゴール呼び出しを記録します"""
        if not self.enabled:
            return

        try:
            if self.max_depth is not None and self.current_depth >= self.max_depth:
                return

            event = TraceEvent(
                event_type="CALL",
                goal=goal,
                depth=self.current_depth,
                bindings=bindings.copy() if bindings else BindingEnvironment(),
                timestamp=time.time(),
            )
            self._record_event(event)
            self.current_depth += 1

        except Exception as e:
            logger.warning("Failed to record call event: %s", e)

    def record_exit(
        self, goal: Term, bindings: BindingEnvironment, rule: Union[Rule, Fact]
    ) -> None:
        """ゴール成功を記録します"""
        if not self.enabled:
            return

        try:
            if self.current_depth > 0:
                self.current_depth -= 1

            event = TraceEvent(
                event_type="EXIT",
                goal=goal,
                depth=self.current_depth,
                bindings=bindings.copy() if bindings else BindingEnvironment(),
                timestamp=time.time(),
                rule_ref=rule,
            )
            self._record_event(event)

        except Exception as e:
            logger.warning("Failed to record exit event: %s", e)

    def record_fail(self, goal: Term) -> None:
        """ゴール失敗を記録します"""
        if not self.enabled:
            return

        try:
            if self.current_depth > 0:
                self.current_depth -= 1

            event = TraceEvent(
                event_type="FAIL",
                goal=goal,
                depth=self.current_depth,
                bindings=BindingEnvironment(),
                timestamp=time.time(),
            )
            self._record_event(event)

        except Exception as e:
            logger.warning("Failed to record fail event: %s", e)

    def record_redo(self, goal: Term) -> None:
        """バックトラッキングを記録します"""
        if not self.enabled:
            return

        try:
            event = TraceEvent(
                event_type="REDO",
                goal=goal,
                depth=self.current_depth,
                bindings=BindingEnvironment(),
                timestamp=time.time(),
            )
            self._record_event(event)
            self.current_depth += 1

        except Exception as e:
            logger.warning("Failed to record redo event: %s", e)

    def get_events(self) -> List[TraceEvent]:
        """記録されたイベントのリストを取得します"""
        return self.events.copy()

    def clear_events(self) -> None:
        """記録されたイベントをクリアします"""
        self.events.clear()
        logger.debug("Trace events cleared")

    def _record_event(self, event: TraceEvent) -> None:
        """イベントを記録します（メモリ管理あり）"""
        if len(self.events) >= self.max_events:
            # 古いイベントを削除してメモリ使用量を制限
            self.events = self.events[1000:]  # 最新の events を保持

        self.events.append(event)
