"""
到達可能性アナライザー

Prologプログラムの到達不可能な述語（デッドコード）を検出します。
"""

from pyprolog.util.logger import get_logger
from pyprolog.validation.dependency_graph import DependencyGraph
from pyprolog.validation.symbol_table import SymbolTable
from pyprolog.validation.validation_result import ValidationIssue

logger = get_logger(__name__)


class ReachabilityAnalyzer:
    """到達可能性分析アナライザー"""

    def analyze(
        self, symbol_table: SymbolTable, dependency_graph: DependencyGraph
    ) -> list[ValidationIssue]:
        """到達可能性分析を実行"""
        issues = []

        logger.debug("到達可能性分析開始")

        # エントリーポイントを特定
        entry_points = self._get_entry_points(symbol_table)
        logger.debug("エントリーポイント: %d 個", len(entry_points))

        # 到達可能な述語を計算
        reachable = dependency_graph.get_reachable_from(entry_points)

        # 到達不能な述語を特定
        all_user_defined = symbol_table.user_defined
        unreachable = all_user_defined - reachable

        # 到達不能な述語に対して警告を生成
        for predicate_key in unreachable:
            predicate_infos = symbol_table.predicates.get(predicate_key, [])
            for predicate_info in predicate_infos:
                # ただし、特定のパターンは除外
                if self._should_ignore_unreachable(predicate_info.name):
                    continue

                issue = ValidationIssue(
                    issue_type="unreachable",
                    severity="warning",
                    message=f"到達不可能な述語: {predicate_info.name}/{predicate_info.arity}",
                    rule_or_fact=predicate_info.definition,
                    file_path=predicate_info.file_path,
                    line_number=predicate_info.line_number,
                    column_number=0,
                    suggested_fix="使用されていない述語を削除するか、エントリーポイントから呼び出してください",
                )
                issues.append(issue)

        # 孤立したコンポーネントの検出
        issues.extend(self._check_isolated_components(symbol_table, dependency_graph))

        logger.info("到達可能性分析完了: %d 個の問題を発見", len(issues))
        return issues

    def _get_entry_points(self, symbol_table: SymbolTable) -> set[str]:
        """エントリーポイントとなる述語を特定"""
        entry_points = set()

        for predicate_key, predicate_infos in symbol_table.predicates.items():
            for predicate_info in predicate_infos:
                # エントリーポイントとなる条件
                if self._is_entry_point(predicate_info.name, predicate_info):
                    entry_points.add(predicate_key)

        # エントリーポイントが見つからない場合は全ての事実をエントリーポイントとする
        if not entry_points:
            logger.warning(
                "明示的なエントリーポイントが見つからないため、全ての事実をエントリーポイントとします"
            )
            from pyprolog.core.types import Fact

            for predicate_key, predicate_infos in symbol_table.predicates.items():
                for predicate_info in predicate_infos:
                    if isinstance(predicate_info.definition, Fact):
                        entry_points.add(predicate_key)

        return entry_points

    def _is_entry_point(self, predicate_name: str, predicate_info) -> bool:
        """述語がエントリーポイントかどうかを判定"""
        from pyprolog.core.types import Fact

        # 事実は通常エントリーポイント
        if isinstance(predicate_info.definition, Fact):
            return True

        # 特定の命名規則に従う述語
        entry_patterns = [
            "main_",
            "test_",
            "query_",
            "demo_",
            "example_",
            "run_",
            "start_",
            "init_",
            "setup_",
        ]

        predicate_lower = predicate_name.lower()
        for pattern in entry_patterns:
            if predicate_lower.startswith(pattern):
                return True

        # 引数なしの述語（しばしばエントリーポイント）
        if predicate_info.arity == 0:
            return True

        # 外部から参照される可能性の高い述語
        common_entry_names = [
            "solve",
            "find",
            "search",
            "check",
            "verify",
            "compute",
            "calculate",
            "process",
            "analyze",
        ]

        if predicate_lower in common_entry_names:
            return True

        return False

    def _should_ignore_unreachable(self, predicate_name: str) -> bool:
        """到達不可能として無視すべき述語かどうかを判定"""
        ignore_patterns = [
            # ヘルパー関数やユーティリティ
            "helper_",
            "util_",
            "aux_",
            "internal_",
            # テスト関連（別途テストから呼ばれる可能性）
            "test_",
            "check_",
            "verify_",
            # デバッグ用
            "debug_",
            "trace_",
            "print_",
            # 将来の拡張用
            "future_",
            "todo_",
            "planned_",
        ]

        predicate_lower = predicate_name.lower()
        for pattern in ignore_patterns:
            if predicate_lower.startswith(pattern):
                return True

        return False

    def _check_isolated_components(
        self, symbol_table: SymbolTable, dependency_graph: DependencyGraph
    ) -> list[ValidationIssue]:
        """孤立したコンポーネントをチェック"""
        issues = []

        # 強連結成分を取得
        components = dependency_graph.get_strongly_connected_components()

        # エントリーポイントを含まない成分は孤立している可能性
        entry_points = self._get_entry_points(symbol_table)

        for component in components:
            if len(component) > 1:  # 複数の述語からなる成分
                has_entry_point = any(
                    predicate_key in entry_points for predicate_key in component
                )

                if not has_entry_point:
                    # この成分は外部から到達不可能
                    for predicate_key in component:
                        predicate_infos = symbol_table.predicates.get(predicate_key, [])
                        for predicate_info in predicate_infos:
                            if not self._should_ignore_unreachable(predicate_info.name):
                                issue = ValidationIssue(
                                    issue_type="unreachable",
                                    severity="info",
                                    message=f"孤立したコンポーネントの述語: {predicate_info.name}/{predicate_info.arity}",
                                    rule_or_fact=predicate_info.definition,
                                    file_path=predicate_info.file_path,
                                    line_number=predicate_info.line_number,
                                    column_number=0,
                                    suggested_fix="この述語群は相互に依存していますが外部からアクセスできません",
                                )
                                issues.append(issue)

        return issues
