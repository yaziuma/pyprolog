"""
Prologプログラムバリデーター

静的解析と検証機能の中心となるクラスです。
"""
import time
from typing import List, Dict, Set, Union, Optional, Any
from pyprolog.runtime.interpreter import Runtime
from pyprolog.validation.symbol_table import SymbolTable, predicate_key
from pyprolog.validation.dependency_graph import DependencyGraph
from pyprolog.validation.validation_result import ValidationResult, ValidationIssue
from pyprolog.validation.analyzers.conflict_analyzer import ConflictAnalyzer
from pyprolog.validation.analyzers.reachability_analyzer import ReachabilityAnalyzer
from pyprolog.validation.analyzers.undefined_analyzer import UndefinedAnalyzer
from pyprolog.core.types import Rule, Fact, Term
from pyprolog.util.logger import get_logger

logger = get_logger(__name__)


class Validator:
    """Prologプログラムの静的解析・検証クラス"""
    
    def __init__(self, runtime: Runtime):
        self.runtime = runtime
        self.symbol_table = SymbolTable()
        self.dependency_graph = DependencyGraph()
        self.analyzers = {
            'conflicts': ConflictAnalyzer(),
            'unreachable': ReachabilityAnalyzer(),
            'undefined': UndefinedAnalyzer()
        }
    
    def validate(self, check_type: str = "all", detailed: bool = False) -> ValidationResult:
        """
        検証を実行
        
        Args:
            check_type: 検証タイプ ("all", "conflicts", "unreachable", "undefined")
            detailed: 詳細な解析を行うか
            
        Returns:
            検証結果
        """
        logger.info(f"バリデーション開始: type={check_type}, detailed={detailed}")
        start_time = time.time()
        
        try:
            # シンボルテーブルと依存関係グラフを構築
            self.build_symbol_table()
            self.build_dependency_graph()
            
            # 解析を実行
            all_issues = []
            
            if check_type == "all" or check_type == "conflicts":
                issues = self.analyzers['conflicts'].analyze(self.symbol_table, self.dependency_graph)
                all_issues.extend(issues)
                logger.debug(f"矛盾解析: {len(issues)} 個の問題")
            
            if check_type == "all" or check_type == "unreachable":
                issues = self.analyzers['unreachable'].analyze(self.symbol_table, self.dependency_graph)
                all_issues.extend(issues)
                logger.debug(f"到達可能性解析: {len(issues)} 個の問題")
            
            if check_type == "all" or check_type == "undefined":
                issues = self.analyzers['undefined'].analyze(self.symbol_table, self.dependency_graph)
                all_issues.extend(issues)
                logger.debug(f"未定義述語解析: {len(issues)} 個の問題")
            
            # 詳細解析
            if detailed:
                all_issues.extend(self._perform_detailed_analysis())
            
            # 結果を構築
            analysis_duration = time.time() - start_time
            result = ValidationResult(
                issues=all_issues,
                total_rules_analyzed=len(self.runtime.rules) if self.runtime else 0,
                analysis_duration=analysis_duration
            )
            
            logger.info(f"バリデーション完了: {len(all_issues)} 個の問題, {analysis_duration:.2f}秒")
            return result
            
        except Exception as e:
            logger.error(f"バリデーションエラー: {e}")
            analysis_duration = time.time() - start_time
            error_issue = ValidationIssue(
                issue_type="system",
                severity="error",
                message=f"バリデーションシステムエラー: {e}",
                rule_or_fact=None,
                file_path=None,
                line_number=0,
                column_number=0
            )
            
            return ValidationResult(
                issues=[error_issue],
                total_rules_analyzed=0,
                analysis_duration=analysis_duration
            )
    
    def build_symbol_table(self) -> None:
        """シンボルテーブルを構築"""
        logger.debug("シンボルテーブル構築開始")
        
        if not self.runtime or not self.runtime.rules:
            logger.warning("ランタイムまたはルールが存在しません")
            return
        
        # 全ルールを解析
        for i, rule_or_fact in enumerate(self.runtime.rules):
            self._analyze_rule_or_fact(rule_or_fact, None, i + 1)
        
        stats = self.symbol_table.get_statistics()
        logger.info(f"シンボルテーブル構築完了: {stats}")
    
    def build_dependency_graph(self) -> None:
        """依存関係グラフを構築"""
        logger.debug("依存関係グラフ構築開始")
        
        # 全ての述語をノードとして追加
        for key in self.symbol_table.predicates.keys():
            self.dependency_graph.add_node(key)
        
        for key in self.symbol_table.builtins:
            self.dependency_graph.add_node(key)
        
        # ルールから依存関係を抽出
        for rule_or_fact in self.runtime.rules:
            if isinstance(rule_or_fact, Rule):
                head_term = rule_or_fact.head
                caller_key = self._get_predicate_key(head_term)
                
                # ボディから依存先を抽出
                body_terms = self._extract_terms_from_body(rule_or_fact.body)
                for body_term in body_terms:
                    callee_key = self._get_predicate_key(body_term)
                    if caller_key != callee_key:  # 自己参照以外
                        self.dependency_graph.add_edge(caller_key, callee_key)
        
        stats = self.dependency_graph.get_statistics()
        logger.info(f"依存関係グラフ構築完了: {stats}")
    
    def _analyze_rule_or_fact(self, rule_or_fact: Union[Rule, Fact], 
                             file_path: Optional[str], line_number: int) -> None:
        """ルールまたは事実を解析してシンボルテーブルに追加"""
        if isinstance(rule_or_fact, Fact):
            # 事実のヘッドを定義として登録
            name, arity = self._extract_predicate_info(rule_or_fact.head)
            self.symbol_table.add_predicate(name, arity, rule_or_fact, file_path, line_number)
            
        elif isinstance(rule_or_fact, Rule):
            # ルールのヘッドを定義として登録
            name, arity = self._extract_predicate_info(rule_or_fact.head)
            self.symbol_table.add_predicate(name, arity, rule_or_fact, file_path, line_number)
            
            # ボディの述語を参照として登録
            body_terms = self._extract_terms_from_body(rule_or_fact.body)
            for term in body_terms:
                ref_name, ref_arity = self._extract_predicate_info(term)
                self.symbol_table.add_reference(ref_name, ref_arity, rule_or_fact, 
                                              file_path, line_number, "body")
    
    def _extract_predicate_info(self, term: Any) -> tuple:
        """項から述語名とアリティを抽出"""
        if hasattr(term, 'functor'):
            functor = term.functor
            name = functor.name if hasattr(functor, 'name') else str(functor)
            arity = len(term.args) if hasattr(term, 'args') and term.args else 0
        elif hasattr(term, 'name'):
            name = term.name
            arity = 0
        else:
            name = str(term)
            arity = 0
        
        return name, arity
    
    def _get_predicate_key(self, term: Any) -> str:
        """項から述語キーを生成"""
        name, arity = self._extract_predicate_info(term)
        return predicate_key(name, arity)
    
    def _extract_terms_from_body(self, body: Any) -> List[Any]:
        """ルールのボディから全ての項を抽出"""
        terms = []
        
        if hasattr(body, 'functor'):
            functor_name = body.functor.name if hasattr(body.functor, 'name') else str(body.functor)
            if functor_name == ',':  # 連言
                if hasattr(body, 'args') and len(body.args) >= 2:
                    terms.extend(self._extract_terms_from_body(body.args[0]))
                    terms.extend(self._extract_terms_from_body(body.args[1]))
            elif functor_name == ';':  # 選言
                if hasattr(body, 'args') and len(body.args) >= 2:
                    terms.extend(self._extract_terms_from_body(body.args[0]))
                    terms.extend(self._extract_terms_from_body(body.args[1]))
            else:
                terms.append(body)
        else:
            terms.append(body)
        
        return terms
    
    def _perform_detailed_analysis(self) -> List[ValidationIssue]:
        """詳細な解析を実行"""
        logger.debug("詳細解析開始")
        issues = []
        
        # 複雑度の解析
        issues.extend(self._analyze_complexity())
        
        # 命名規則のチェック
        issues.extend(self._check_naming_conventions())
        
        # パフォーマンス問題の検出
        issues.extend(self._check_performance_issues())
        
        logger.debug(f"詳細解析完了: {len(issues)} 個の問題")
        return issues
    
    def _analyze_complexity(self) -> List[ValidationIssue]:
        """複雑度を解析"""
        issues = []
        
        for predicate_infos in self.symbol_table.predicates.values():
            for predicate_info in predicate_infos:
                if isinstance(predicate_info.definition, Rule):
                    complexity = self._calculate_rule_complexity(predicate_info.definition)
                    if complexity > 10:  # 閾値
                        issue = ValidationIssue(
                            issue_type="complexity",
                            severity="warning",
                            message=f"高い複雑度: {predicate_info.name}/{predicate_info.arity} (複雑度: {complexity})",
                            rule_or_fact=predicate_info.definition,
                            file_path=predicate_info.file_path,
                            line_number=predicate_info.line_number,
                            column_number=0,
                            suggested_fix="ルールを単純化するか、複数のルールに分割してください"
                        )
                        issues.append(issue)
        
        return issues
    
    def _check_naming_conventions(self) -> List[ValidationIssue]:
        """命名規則をチェック"""
        issues = []
        
        for predicate_infos in self.symbol_table.predicates.values():
            for predicate_info in predicate_infos:
                name = predicate_info.name
                
                # 命名規則のチェック
                if not self._follows_naming_convention(name):
                    issue = ValidationIssue(
                        issue_type="style",
                        severity="info",
                        message=f"命名規則違反: {name}/{predicate_info.arity}",
                        rule_or_fact=predicate_info.definition,
                        file_path=predicate_info.file_path,
                        line_number=predicate_info.line_number,
                        column_number=0,
                        suggested_fix="スネークケース（lower_case_with_underscores）を使用してください"
                    )
                    issues.append(issue)
        
        return issues
    
    def _check_performance_issues(self) -> List[ValidationIssue]:
        """パフォーマンス問題をチェック"""
        issues = []
        
        # 左再帰の検出
        cycles = self.dependency_graph.detect_cycles()
        for cycle in cycles:
            if len(cycle) == 1:  # 自己再帰
                predicate_key_str = cycle[0]
                name, arity = predicate_key_str.split('/')
                predicate_infos = self.symbol_table.get_predicate_info(name, int(arity))
                
                if predicate_infos:
                    for predicate_info in predicate_infos:
                        if isinstance(predicate_info.definition, Rule):
                            if self._has_left_recursion(predicate_info.definition):
                                issue = ValidationIssue(
                                    issue_type="performance",
                                    severity="warning",
                                    message=f"左再帰の可能性: {name}/{arity}",
                                    rule_or_fact=predicate_info.definition,
                                    file_path=predicate_info.file_path,
                                    line_number=predicate_info.line_number,
                                    column_number=0,
                                    suggested_fix="右再帰に変更するか、累積パラメータを使用してください"
                                )
                                issues.append(issue)
        
        return issues
    
    def _calculate_rule_complexity(self, rule: Rule) -> int:
        """ルールの複雑度を計算"""
        complexity = 1  # 基本複雑度
        
        # ボディの項数をカウント
        body_terms = self._extract_terms_from_body(rule.body)
        complexity += len(body_terms)
        
        # 条件分岐（選言）をカウント
        def count_disjunctions(term):
            if hasattr(term, 'functor'):
                functor_name = term.functor.name if hasattr(term.functor, 'name') else str(term.functor)
                if functor_name == ';':
                    return 1 + count_disjunctions(term.args[0]) + count_disjunctions(term.args[1])
            return 0
        
        complexity += count_disjunctions(rule.body)
        
        return complexity
    
    def _follows_naming_convention(self, name: str) -> bool:
        """命名規則に従っているかチェック"""
        # Prologの一般的な命名規則: 小文字で始まり、アンダースコアで区切る
        import re
        return re.match(r'^[a-z][a-z0-9_]*$', name) is not None
    
    def _has_left_recursion(self, rule: Rule) -> bool:
        """左再帰があるかチェック"""
        body_terms = self._extract_terms_from_body(rule.body)
        if not body_terms:
            return False
        
        # 最初の項が同じ述語を呼んでいるかチェック
        first_term = body_terms[0]
        head_key = self._get_predicate_key(rule.head)
        first_key = self._get_predicate_key(first_term)
        
        return head_key == first_key
    
    def get_entry_points(self) -> Set[str]:
        """エントリーポイントを取得"""
        return self.analyzers['unreachable']._get_entry_points(self.symbol_table)