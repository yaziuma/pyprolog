"""
矛盾検出アナライザー

Prologプログラムの論理的矛盾や競合する定義を検出します。
"""

from typing import List, Set, Any
from pyprolog.validation.validation_result import ValidationIssue
from pyprolog.validation.symbol_table import SymbolTable, PredicateInfo
from pyprolog.validation.dependency_graph import DependencyGraph
from pyprolog.core.types import Rule, Fact, Atom
from pyprolog.util.logger import get_logger

logger = get_logger(__name__)


class ConflictAnalyzer:
    """矛盾・競合検出アナライザー"""

    def analyze(
        self, symbol_table: SymbolTable, dependency_graph: DependencyGraph
    ) -> List[ValidationIssue]:
        """矛盾分析を実行"""
        issues = []

        logger.debug("矛盾分析開始")

        # 同じ述語の複数定義をチェック
        issues.extend(self._check_multiple_definitions(symbol_table))

        # 論理的矛盾をチェック
        issues.extend(self._check_logical_conflicts(symbol_table))

        # 型の不整合をチェック
        issues.extend(self._check_type_inconsistencies(symbol_table))

        # 無限再帰の可能性をチェック
        issues.extend(self._check_infinite_recursion(symbol_table, dependency_graph))

        logger.info(f"矛盾分析完了: {len(issues)} 個の問題を発見")
        return issues

    def _check_multiple_definitions(
        self, symbol_table: SymbolTable
    ) -> List[ValidationIssue]:
        """複数定義のチェック"""
        issues = []

        multiple_defs = symbol_table.get_multiple_definitions()

        for predicate_key, predicate_infos in multiple_defs.items():
            facts = [p for p in predicate_infos if isinstance(p.definition, Fact)]
            rules = [p for p in predicate_infos if isinstance(p.definition, Rule)]

            # 事実と事実の競合チェック
            for i, fact1_info in enumerate(facts):
                for fact2_info in facts[i + 1 :]:
                    if self._facts_potentially_conflict(
                        fact1_info.definition, fact2_info.definition
                    ):
                        issue = ValidationIssue(
                            issue_type="conflict",
                            severity="warning",
                            message=f"潜在的な競合事実: {predicate_key}",
                            rule_or_fact=fact1_info.definition,
                            file_path=fact1_info.file_path,
                            line_number=fact1_info.line_number,
                            column_number=0,
                            suggested_fix="事実の定義を見直し、論理的整合性を確認してください",
                        )
                        issues.append(issue)

            # ルール間の競合チェック
            if len(rules) > 1:
                # 同じヘッドを持つルールの重複チェック
                for i, rule1_info in enumerate(rules):
                    for rule2_info in rules[i + 1 :]:
                        if self._rules_potentially_conflict(
                            rule1_info.definition, rule2_info.definition
                        ):
                            issue = ValidationIssue(
                                issue_type="conflict",
                                severity="info",
                                message=f"重複するルール定義: {predicate_key}",
                                rule_or_fact=rule1_info.definition,
                                file_path=rule1_info.file_path,
                                line_number=rule1_info.line_number,
                                column_number=0,
                                suggested_fix="ルールの条件を明確化して区別してください",
                            )
                            issues.append(issue)

        return issues

    def _check_logical_conflicts(
        self, symbol_table: SymbolTable
    ) -> List[ValidationIssue]:
        """論理的矛盾のチェック"""
        issues = []

        # 対照的な述語名の検出
        conflicting_pairs = [
            ("is_true", "is_false"),
            ("is_on", "is_off"),
            ("is_open", "is_closed"),
            ("is_fast", "is_slow"),
            ("exists", "not_exists"),
            ("valid", "invalid"),
            ("active", "inactive"),
            ("enabled", "disabled"),
        ]

        all_predicates = symbol_table.get_all_predicates()

        for pos_pred, neg_pred in conflicting_pairs:
            pos_predicates = [p for p in all_predicates if pos_pred in p.name.lower()]
            neg_predicates = [p for p in all_predicates if neg_pred in p.name.lower()]

            for pos_p in pos_predicates:
                for neg_p in neg_predicates:
                    if pos_p.arity == neg_p.arity:
                        # 同じ引数で対照的な述語が定義されている可能性
                        if self._check_conflicting_arguments(pos_p, neg_p):
                            issue = ValidationIssue(
                                issue_type="conflict",
                                severity="warning",
                                message=f"対照的な述語の潜在的競合: {pos_p.name}/{pos_p.arity} vs {neg_p.name}/{neg_p.arity}",
                                rule_or_fact=pos_p.definition,
                                file_path=pos_p.file_path,
                                line_number=pos_p.line_number,
                                column_number=0,
                                suggested_fix="対照的な述語の使用時は排他的な条件を確認してください",
                            )
                            issues.append(issue)

        return issues

    def _check_type_inconsistencies(
        self, symbol_table: SymbolTable
    ) -> List[ValidationIssue]:
        """型の不整合チェック"""
        issues = []

        # 同じ述語で異なる引数型の使用パターンを検出
        for predicate_key, predicate_infos in symbol_table.predicates.items():
            if len(predicate_infos) > 1:
                # 引数の型パターンを分析
                type_patterns = self._analyze_argument_types(predicate_infos)

                if len(type_patterns) > 1:
                    issue = ValidationIssue(
                        issue_type="conflict",
                        severity="info",
                        message=f"異なる引数型パターン: {predicate_key}",
                        rule_or_fact=predicate_infos[0].definition,
                        file_path=predicate_infos[0].file_path,
                        line_number=predicate_infos[0].line_number,
                        column_number=0,
                        suggested_fix="引数の型使用を統一してください",
                    )
                    issues.append(issue)

        return issues

    def _check_infinite_recursion(
        self, symbol_table: SymbolTable, dependency_graph: DependencyGraph
    ) -> List[ValidationIssue]:
        """無限再帰の可能性をチェック"""
        issues = []

        cycles = dependency_graph.detect_cycles()

        for cycle in cycles:
            if len(cycle) > 1:  # 自己再帰以外の循環
                # 循環内の各述語をチェック
                for predicate_key in cycle:
                    predicate_infos = symbol_table.get_predicate_info(
                        *predicate_key.split("/")
                    )
                    if predicate_infos:
                        for predicate_info in predicate_infos:
                            issue = ValidationIssue(
                                issue_type="conflict",
                                severity="warning",
                                message=f"循環依存による無限再帰の可能性: {predicate_key}",
                                rule_or_fact=predicate_info.definition,
                                file_path=predicate_info.file_path,
                                line_number=predicate_info.line_number,
                                column_number=0,
                                suggested_fix="ベースケースや終了条件を追加してください",
                            )
                            issues.append(issue)
            elif len(cycle) == 1:  # 自己再帰
                predicate_key = cycle[0]
                predicate_infos = symbol_table.get_predicate_info(
                    *predicate_key.split("/")
                )
                if predicate_infos:
                    for predicate_info in predicate_infos:
                        # 自己再帰のルールで終了条件があるかチェック
                        if isinstance(predicate_info.definition, Rule):
                            if not self._has_base_case(predicate_info, symbol_table):
                                issue = ValidationIssue(
                                    issue_type="conflict",
                                    severity="error",
                                    message=f"終了条件のない自己再帰: {predicate_key}",
                                    rule_or_fact=predicate_info.definition,
                                    file_path=predicate_info.file_path,
                                    line_number=predicate_info.line_number,
                                    column_number=0,
                                    suggested_fix="ベースケース（終了条件）を追加してください",
                                )
                                issues.append(issue)

        return issues

    def _facts_potentially_conflict(self, fact1: Fact, fact2: Fact) -> bool:
        """2つの事実が潜在的に競合するかチェック"""
        try:
            head1_str = str(fact1.head).lower()
            head2_str = str(fact2.head).lower()

            # 基本的な対照語彙チェック
            conflicting_words = [
                ("true", "false"),
                ("yes", "no"),
                ("on", "off"),
                ("open", "closed"),
                ("active", "inactive"),
                ("valid", "invalid"),
                ("enabled", "disabled"),
            ]

            for pos_word, neg_word in conflicting_words:
                if pos_word in head1_str and neg_word in head2_str:
                    return self._same_argument_structure(fact1.head, fact2.head)
                if neg_word in head1_str and pos_word in head2_str:
                    return self._same_argument_structure(fact1.head, fact2.head)

            return False
        except Exception as e:
            logger.debug(f"事実競合チェックエラー: {e}")
            return False

    def _rules_potentially_conflict(self, rule1: Rule, rule2: Rule) -> bool:
        """2つのルールが潜在的に競合するかチェック"""
        try:
            # ヘッドが同じ構造かチェック
            return self._same_argument_structure(rule1.head, rule2.head)
        except Exception as e:
            logger.debug(f"ルール競合チェックエラー: {e}")
            return False

    def _same_argument_structure(self, term1: Any, term2: Any) -> bool:
        """2つの項が同じ引数構造かチェック"""
        try:
            if not hasattr(term1, "args") or not hasattr(term2, "args"):
                return str(term1) == str(term2)

            args1 = term1.args if term1.args else []
            args2 = term2.args if term2.args else []

            if len(args1) != len(args2):
                return False

            for arg1, arg2 in zip(args1, args2):
                if str(arg1) == str(arg2):
                    continue
                # 変数やワイルドカードの場合は構造が同じとみなす
                if self._is_variable_or_wildcard(
                    str(arg1)
                ) or self._is_variable_or_wildcard(str(arg2)):
                    continue
                return False

            return True
        except Exception:
            return False

    def _is_variable_or_wildcard(self, arg_str: str) -> bool:
        """引数が変数またはワイルドカードかチェック"""
        arg_str = arg_str.strip()
        return (
            arg_str.startswith("_") or arg_str in ["X", "Y", "Z"] or arg_str.isupper()
        )

    def _check_conflicting_arguments(
        self, pred1: PredicateInfo, pred2: PredicateInfo
    ) -> bool:
        """対照的な述語の引数が競合するかチェック"""
        try:
            if isinstance(pred1.definition, Fact) and isinstance(
                pred2.definition, Fact
            ):
                return self._same_argument_structure(
                    pred1.definition.head, pred2.definition.head
                )
            return False
        except Exception:
            return False

    def _analyze_argument_types(self, predicate_infos: List[PredicateInfo]) -> Set[str]:
        """引数の型パターンを分析"""
        type_patterns = set()

        for predicate_info in predicate_infos:
            try:
                if hasattr(predicate_info.definition, "head"):
                    head = predicate_info.definition.head
                    if hasattr(head, "args") and head.args:
                        pattern = []
                        for arg in head.args:
                            if isinstance(arg, Atom):
                                pattern.append("atom")
                            elif str(arg).isdigit():
                                pattern.append("number")
                            elif str(arg).startswith("["):
                                pattern.append("list")
                            else:
                                pattern.append("variable")
                        type_patterns.add(tuple(pattern))
            except Exception as e:
                logger.debug(f"引数型分析エラー: {e}")
                continue

        return type_patterns

    def _has_base_case(
        self, predicate_info: PredicateInfo, symbol_table: SymbolTable
    ) -> bool:
        """述語にベースケースがあるかチェック"""
        predicate_key = f"{predicate_info.name}/{predicate_info.arity}"
        predicate_infos = symbol_table.predicates.get(predicate_key, [])

        # 同じ述語に事実（ベースケース）が存在するかチェック
        for info in predicate_infos:
            if isinstance(info.definition, Fact):
                return True

        return False
