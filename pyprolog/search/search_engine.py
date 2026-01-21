"""
検索エンジンの実装

Prologルールと事実の効率的な検索機能を提供します。
"""

from typing import List, Dict, Any
from pyprolog.runtime.interpreter import Runtime
from pyprolog.search.indexer import SearchIndex
from pyprolog.search.pattern_matcher import PatternMatcher
from pyprolog.search.search_result import SearchResult
from pyprolog.util.logger import get_logger

logger = get_logger(__name__)


class SearchEngine:
    """Prologクエリの検索エンジン"""

    def __init__(self, runtime: Runtime):
        self.runtime = runtime
        self.index = SearchIndex()
        self.is_indexed = False
        self._index_cache_valid = False

    def build_index(self) -> None:
        """検索インデックスを構築"""
        logger.debug("検索インデックス構築開始")

        if not self.runtime or not self.runtime.rules:
            logger.warning("ランタイムまたはルールが存在しません")
            return

        self.index.build_index(self.runtime.rules)
        self.is_indexed = True
        self._index_cache_valid = True

        logger.info("検索インデックス構築完了: %d ルール処理", len(self.runtime.rules))

    def search(
        self, pattern: str, search_type: str = "predicate", limit: int = 100
    ) -> List[SearchResult]:
        """
        検索を実行

        Args:
            pattern: 検索パターン
            search_type: 検索タイプ ("predicate", "argument", "full_text")
            limit: 結果数制限

        Returns:
            検索結果のリスト
        """
        self._ensure_index()

        logger.debug(
            f"検索実行: pattern='{pattern}', type={search_type}, limit={limit}"
        )

        results = []

        try:
            if search_type == "predicate":
                results = self._search_predicate(pattern, limit)
            elif search_type == "argument":
                results = self._search_argument(pattern, limit)
            elif search_type == "full_text":
                results = self._search_full_text(pattern, limit)
            else:
                raise ValueError(f"不明な検索タイプ: {search_type}")

            # 信頼度順にソート
            results.sort(key=lambda x: x.confidence, reverse=True)

            # 結果数制限を適用
            results = results[:limit]

            logger.debug("検索完了: %d 件の結果", len(results))
            return results

        except Exception as e:
            logger.error("検索エラー: %s", e)
            return []

    def _search_predicate(self, pattern: str, limit: int) -> List[SearchResult]:
        """述語名検索"""
        results = []

        # インデックスから検索
        index_results = self.index.search_predicates(pattern)
        results.extend(index_results)

        # パターンマッチングでの追加検索
        for rule_or_fact in self.runtime.rules:
            head_term = None
            if hasattr(rule_or_fact, "head"):
                head_term = rule_or_fact.head

            if head_term and PatternMatcher.match_predicate_name(pattern, head_term):
                # 重複チェック
                already_exists = any(
                    r.rule_or_fact == rule_or_fact and r.match_type == "predicate"
                    for r in results
                )

                if not already_exists:
                    search_result = SearchResult(
                        rule_or_fact=rule_or_fact,
                        file_path=None,
                        line_number=0,
                        matched_text=str(head_term),
                        match_type="predicate",
                        context_lines=[],
                        confidence=1.0,
                    )
                    results.append(search_result)

        return results

    def _search_argument(self, pattern: str, limit: int) -> List[SearchResult]:
        """引数パターン検索"""
        results = []

        # インデックスから基本検索
        index_results = self.index.search_arguments(pattern)
        results.extend(index_results)

        # パターンマッチングでの詳細検索
        for rule_or_fact in self.runtime.rules:
            terms_to_check = []

            if hasattr(rule_or_fact, "head"):
                terms_to_check.append(rule_or_fact.head)

            if hasattr(rule_or_fact, "body"):
                body_terms = self._extract_terms_from_body(rule_or_fact.body)
                terms_to_check.extend(body_terms)

            for term in terms_to_check:
                try:
                    is_match, confidence = PatternMatcher.match_argument_pattern(
                        pattern, term
                    )
                    if is_match:
                        search_result = SearchResult(
                            rule_or_fact=rule_or_fact,
                            file_path=None,
                            line_number=0,
                            matched_text=str(term),
                            match_type="argument",
                            context_lines=[],
                            confidence=confidence,
                        )
                        results.append(search_result)

                        if len(results) >= limit:
                            break
                except Exception as e:
                    logger.debug("引数マッチングエラー: %s", e)
                    continue

        return results

    def _search_full_text(self, pattern: str, limit: int) -> List[SearchResult]:
        """全文検索"""
        results = []

        # インデックスから検索
        index_results = self.index.search_full_text(pattern)
        results.extend(index_results)

        # 直接テキスト検索での補完
        pattern_lower = pattern.lower()

        for rule_or_fact in self.runtime.rules:
            rule_text = str(rule_or_fact)
            if pattern_lower in rule_text.lower():
                # 重複チェック
                already_exists = any(
                    r.rule_or_fact == rule_or_fact and r.match_type == "full_text"
                    for r in results
                )

                if not already_exists:
                    confidence = self._calculate_text_relevance(pattern, rule_text)
                    search_result = SearchResult(
                        rule_or_fact=rule_or_fact,
                        file_path=None,
                        line_number=0,
                        matched_text=rule_text,
                        match_type="full_text",
                        context_lines=[],
                        confidence=confidence,
                    )
                    results.append(search_result)

                    if len(results) >= limit:
                        break

        return results

    def _ensure_index(self) -> None:
        """インデックスが構築されていることを確認"""
        if not self._index_cache_valid or not self.is_indexed:
            self.build_index()

    def invalidate_cache(self) -> None:
        """インデックスキャッシュを無効化"""
        self._index_cache_valid = False
        self.is_indexed = False
        logger.debug("検索インデックスキャッシュが無効化されました")

    def _extract_terms_from_body(self, body) -> List:
        """ルールのボディから項を抽出"""
        terms = []

        if hasattr(body, "functor"):
            functor_name = (
                body.functor.name
                if hasattr(body.functor, "name")
                else str(body.functor)
            )
            if functor_name == ",":  # 連言
                if hasattr(body, "args") and len(body.args) >= 2:
                    terms.extend(self._extract_terms_from_body(body.args[0]))
                    terms.extend(self._extract_terms_from_body(body.args[1]))
            elif functor_name == ";":  # 選言
                if hasattr(body, "args") and len(body.args) >= 2:
                    terms.extend(self._extract_terms_from_body(body.args[0]))
                    terms.extend(self._extract_terms_from_body(body.args[1]))
            else:
                terms.append(body)
        else:
            terms.append(body)

        return terms

    def _calculate_text_relevance(self, pattern: str, full_text: str) -> float:
        """テキストの関連度を計算"""
        pattern_lower = pattern.lower()
        text_lower = full_text.lower()

        # 出現回数による重み付け
        count = text_lower.count(pattern_lower)
        if count == 0:
            return 0.0

        # 文字列の長さに対する比率
        text_length = len(full_text)
        pattern_length = len(pattern)

        if text_length == 0:
            return 0.0

        # 関連度計算（出現回数と文字列長の比率を考慮）
        relevance = min(1.0, (count * pattern_length) / text_length * 5)
        return relevance

    def get_statistics(self) -> Dict[str, Any]:
        """検索エンジンの統計情報を取得"""
        return {
            "indexed": self.is_indexed,
            "total_rules": len(self.runtime.rules) if self.runtime else 0,
            "predicate_index_size": len(self.index.predicate_index),
            "argument_index_size": len(self.index.argument_index),
            "text_index_size": len(self.index.text_index),
            "cache_valid": self._index_cache_valid,
        }
