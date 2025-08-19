"""
未定義述語アナライザー

Prologプログラムで参照されているが定義されていない述語を検出します。
"""

from typing import List, Set, Dict
from pyprolog.validation.validation_result import ValidationIssue
from pyprolog.validation.symbol_table import SymbolTable, predicate_key
from pyprolog.validation.dependency_graph import DependencyGraph
from pyprolog.util.logger import get_logger

logger = get_logger(__name__)


class UndefinedAnalyzer:
    """未定義述語検出アナライザー"""

    def analyze(
        self, symbol_table: SymbolTable, dependency_graph: DependencyGraph
    ) -> List[ValidationIssue]:
        """未定義述語分析を実行"""
        issues = []

        logger.debug("未定義述語分析開始")

        # 参照されているが定義されていない述語を検出
        issues.extend(self._check_undefined_predicates(symbol_table))

        # スペルミスの可能性をチェック
        issues.extend(self._check_potential_typos(symbol_table))

        # 削除された述語の参照をチェック
        issues.extend(self._check_missing_imports(symbol_table, dependency_graph))

        logger.info(f"未定義述語分析完了: {len(issues)} 個の問題を発見")
        return issues

    def _check_undefined_predicates(
        self, symbol_table: SymbolTable
    ) -> List[ValidationIssue]:
        """未定義述語のチェック"""
        issues = []

        # 全ての述語参照を調査
        referenced_predicates = self._collect_all_references(symbol_table)

        for predicate_key, references in referenced_predicates.items():
            name, arity = predicate_key.split("/")
            arity = int(arity)

            # ビルトイン述語はスキップ
            if symbol_table.is_builtin(name, arity):
                continue

            # 定義されているかチェック
            if not symbol_table.is_defined(name, arity):
                # 未定義述語を発見
                for reference in references:
                    severity = self._determine_severity(name, arity)
                    suggested_fix = self._suggest_fix(name, arity, symbol_table)

                    issue = ValidationIssue(
                        issue_type="undefined",
                        severity=severity,
                        message=f"未定義述語: {name}/{arity}",
                        rule_or_fact=reference.referenced_in,
                        file_path=reference.file_path,
                        line_number=reference.line_number,
                        column_number=0,
                        suggested_fix=suggested_fix,
                    )
                    issues.append(issue)

        return issues

    def _check_potential_typos(
        self, symbol_table: SymbolTable
    ) -> List[ValidationIssue]:
        """スペルミスの可能性をチェック"""
        issues = []

        referenced_predicates = self._collect_all_references(symbol_table)
        defined_predicates = set(symbol_table.predicates.keys())

        for undefined_key in referenced_predicates.keys():
            name, arity = undefined_key.split("/")
            arity = int(arity)

            if symbol_table.is_defined(name, arity) or symbol_table.is_builtin(
                name, arity
            ):
                continue

            # 似ている定義済み述語を検索
            similar_predicates = self._find_similar_predicates(
                name, arity, defined_predicates
            )

            if similar_predicates:
                references = referenced_predicates[undefined_key]
                for reference in references:
                    similar_list = ", ".join(similar_predicates)
                    issue = ValidationIssue(
                        issue_type="undefined",
                        severity="warning",
                        message=f"未定義述語（スペルミスの可能性）: {name}/{arity}",
                        rule_or_fact=reference.referenced_in,
                        file_path=reference.file_path,
                        line_number=reference.line_number,
                        column_number=0,
                        suggested_fix=f"類似の述語が存在します: {similar_list}",
                    )
                    issues.append(issue)

        return issues

    def _check_missing_imports(
        self, symbol_table: SymbolTable, dependency_graph: DependencyGraph
    ) -> List[ValidationIssue]:
        """欠落したインポートや依存関係をチェック"""
        issues = []

        # ライブラリ述語と思われる未定義述語を検出
        referenced_predicates = self._collect_all_references(symbol_table)

        library_patterns = {
            "lists": ["append", "member", "length", "reverse", "sort", "permutation"],
            "arithmetic": ["plus", "minus", "times", "div", "mod", "abs", "max", "min"],
            "io": ["read", "write", "get", "put", "open", "close", "stream"],
            "strings": ["atom_chars", "atom_codes", "string_concat", "sub_string"],
            "meta": ["call", "findall", "bagof", "setof", "forall"],
        }

        for undefined_key in referenced_predicates.keys():
            name, arity = undefined_key.split("/")
            arity = int(arity)

            if symbol_table.is_defined(name, arity) or symbol_table.is_builtin(
                name, arity
            ):
                continue

            # ライブラリ述語かチェック
            for library, predicates in library_patterns.items():
                if any(name.lower().startswith(pred) for pred in predicates):
                    references = referenced_predicates[undefined_key]
                    for reference in references:
                        issue = ValidationIssue(
                            issue_type="undefined",
                            severity="info",
                            message=f"未定義述語（ライブラリ述語の可能性）: {name}/{arity}",
                            rule_or_fact=reference.referenced_in,
                            file_path=reference.file_path,
                            line_number=reference.line_number,
                            column_number=0,
                            suggested_fix=f"{library}ライブラリの使用を確認してください",
                        )
                        issues.append(issue)
                    break

        return issues

    def _collect_all_references(self, symbol_table: SymbolTable) -> Dict[str, List]:
        """全ての述語参照を収集"""
        all_references = {}

        for predicate_infos in symbol_table.predicates.values():
            for predicate_info in predicate_infos:
                for reference in predicate_info.references:
                    ref_key = predicate_key(reference.name, reference.arity)
                    if ref_key not in all_references:
                        all_references[ref_key] = []
                    all_references[ref_key].append(reference)

        return all_references

    def _determine_severity(self, name: str, arity: int) -> str:
        """未定義述語の重要度を決定"""
        # クリティカルな述語名
        critical_patterns = ["main", "start", "init", "run"]
        if any(name.lower().startswith(pattern) for pattern in critical_patterns):
            return "error"

        # テスト関連は警告レベル
        if name.lower().startswith("test_"):
            return "warning"

        # デフォルトはエラー
        return "error"

    def _suggest_fix(self, name: str, arity: int, symbol_table: SymbolTable) -> str:
        """修正提案を生成"""
        # 類似の述語を探す
        defined_predicates = set(symbol_table.predicates.keys())
        similar = self._find_similar_predicates(name, arity, defined_predicates)

        if similar:
            return f"述語 {name}/{arity} を定義するか、類似の述語を確認: {', '.join(similar)}"
        else:
            return f"述語 {name}/{arity} を定義してください"

    def _find_similar_predicates(
        self, name: str, arity: int, defined_predicates: Set[str]
    ) -> List[str]:
        """類似の述語を検索"""
        similar = []
        name_lower = name.lower()

        for pred_key in defined_predicates:
            pred_name, pred_arity = pred_key.split("/")
            pred_arity = int(pred_arity)
            pred_name_lower = pred_name.lower()

            # 同じアリティで名前が類似
            if pred_arity == arity:
                if self._is_similar_name(name_lower, pred_name_lower):
                    similar.append(pred_key)

            # アリティが近く、名前が同じ
            elif abs(pred_arity - arity) <= 1:
                if pred_name_lower == name_lower:
                    similar.append(pred_key)

        return similar[:3]  # 最大3つまで

    def _is_similar_name(self, name1: str, name2: str) -> bool:
        """名前の類似性をチェック"""
        # レーベンシュタイン距離の簡易版
        if len(name1) == 0:
            return len(name2) <= 2
        if len(name2) == 0:
            return len(name1) <= 2

        # 1文字の違い
        if abs(len(name1) - len(name2)) <= 1:
            differences = 0
            min_len = min(len(name1), len(name2))

            for i in range(min_len):
                if name1[i] != name2[i]:
                    differences += 1
                    if differences > 2:
                        return False

            differences += abs(len(name1) - len(name2))
            return differences <= 2

        # 部分一致
        if name1 in name2 or name2 in name1:
            return True

        return False
