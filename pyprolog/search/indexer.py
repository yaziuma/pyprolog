"""
検索インデックス構築機能

Prologルールと事実の効率的な検索のためのインデックス構築を提供します。
"""
from typing import Dict, List, Set, Union, Optional, Any
from pyprolog.core.types import Rule, Fact, Term, Atom
from pyprolog.search.search_result import SearchResult
from pyprolog.util.logger import get_logger
import re

logger = get_logger(__name__)


class SearchIndex:
    """検索インデックスを管理するクラス"""
    
    def __init__(self):
        self.predicate_index: Dict[str, List[SearchResult]] = {}
        self.argument_index: Dict[str, List[SearchResult]] = {}
        self.text_index: Dict[str, List[SearchResult]] = {}
        self.file_mapping: Dict[str, List[Union[Rule, Fact]]] = {}
    
    def build_index(self, rules: List[Union[Rule, Fact]], file_path: Optional[str] = None) -> None:
        """
        ルールリストからインデックスを構築
        
        Args:
            rules: インデックス化するルールと事実のリスト
            file_path: ファイルパス（オプション）
        """
        logger.debug(f"インデックス構築開始: {len(rules)} ルール")
        
        # インデックスをクリア
        self.predicate_index.clear()
        self.argument_index.clear()
        self.text_index.clear()
        
        # 各インデックスを構築
        self._build_predicate_index(rules, file_path)
        self._build_argument_index(rules, file_path)
        self._build_text_index(rules, file_path)
        
        # ファイルマッピングを保存
        if file_path:
            self.file_mapping[file_path] = rules
        
        logger.info(f"インデックス構築完了: 述語={len(self.predicate_index)}, "
                   f"引数={len(self.argument_index)}, テキスト={len(self.text_index)}")
    
    def _build_predicate_index(self, rules: List[Union[Rule, Fact]], file_path: Optional[str]) -> None:
        """述語名インデックスを構築"""
        for i, rule_or_fact in enumerate(rules):
            predicate_name = self._extract_predicate_name(rule_or_fact)
            
            if predicate_name not in self.predicate_index:
                self.predicate_index[predicate_name] = []
            
            search_result = SearchResult(
                rule_or_fact=rule_or_fact,
                file_path=file_path,
                line_number=i + 1,
                matched_text=predicate_name,
                match_type="predicate",
                context_lines=[],
                confidence=1.0
            )
            self.predicate_index[predicate_name].append(search_result)
    
    def _build_argument_index(self, rules: List[Union[Rule, Fact]], file_path: Optional[str]) -> None:
        """引数パターンインデックスを構築"""
        for i, rule_or_fact in enumerate(rules):
            terms_to_index = self._extract_all_terms(rule_or_fact)
            
            for term in terms_to_index:
                if isinstance(term, Term) and hasattr(term, 'args') and term.args:
                    for j, arg in enumerate(term.args):
                        pattern_key = f"{self._get_functor_name(term)}/{len(term.args)}/{j}/{self._serialize_argument(arg)}"
                        
                        if pattern_key not in self.argument_index:
                            self.argument_index[pattern_key] = []
                        
                        search_result = SearchResult(
                            rule_or_fact=rule_or_fact,
                            file_path=file_path,
                            line_number=i + 1,
                            matched_text=str(term),
                            match_type="argument",
                            context_lines=[],
                            confidence=1.0
                        )
                        self.argument_index[pattern_key].append(search_result)
    
    def _build_text_index(self, rules: List[Union[Rule, Fact]], file_path: Optional[str]) -> None:
        """全文検索インデックスを構築"""
        for i, rule_or_fact in enumerate(rules):
            rule_text = str(rule_or_fact)
            words = self._tokenize_text(rule_text)
            
            for word in words:
                if word not in self.text_index:
                    self.text_index[word] = []
                
                search_result = SearchResult(
                    rule_or_fact=rule_or_fact,
                    file_path=file_path,
                    line_number=i + 1,
                    matched_text=rule_text,
                    match_type="full_text",
                    context_lines=[],
                    confidence=self._calculate_text_relevance(word, rule_text)
                )
                self.text_index[word].append(search_result)
    
    def search_predicates(self, pattern: str) -> List[SearchResult]:
        """述語名で検索"""
        results = []
        
        for predicate_name, search_results in self.predicate_index.items():
            if self._matches_predicate_pattern(pattern, predicate_name):
                results.extend(search_results)
        
        return results
    
    def search_arguments(self, pattern: str) -> List[SearchResult]:
        """引数パターンで検索"""
        results = []
        
        # 簡易的な引数パターン検索
        for pattern_key, search_results in self.argument_index.items():
            if pattern.lower() in pattern_key.lower():
                results.extend(search_results)
        
        return results
    
    def search_full_text(self, pattern: str) -> List[SearchResult]:
        """全文検索"""
        results = []
        
        # トークン化して検索
        pattern_tokens = self._tokenize_text(pattern)
        
        for token in pattern_tokens:
            if token in self.text_index:
                results.extend(self.text_index[token])
        
        # パターン文字列での直接検索も追加
        pattern_lower = pattern.lower()
        for word, search_results in self.text_index.items():
            if pattern_lower in word.lower():
                for result in search_results:
                    if result not in results:
                        results.append(result)
        
        return results
    
    def _extract_predicate_name(self, rule_or_fact: Union[Rule, Fact]) -> str:
        """ルールまたは事実から述語名を抽出"""
        if isinstance(rule_or_fact, Fact):
            return self._get_functor_name(rule_or_fact.head)
        elif isinstance(rule_or_fact, Rule):
            return self._get_functor_name(rule_or_fact.head)
        else:
            return str(rule_or_fact)
    
    def _extract_all_terms(self, rule_or_fact: Union[Rule, Fact]) -> List[Term]:
        """ルールまたは事実からすべての項を抽出"""
        terms = []
        
        if isinstance(rule_or_fact, Fact):
            terms.append(rule_or_fact.head)
        elif isinstance(rule_or_fact, Rule):
            terms.append(rule_or_fact.head)
            terms.extend(self._extract_terms_from_body(rule_or_fact.body))
        
        return terms
    
    def _extract_terms_from_body(self, body: Any) -> List[Term]:
        """ルールのボディから項を抽出"""
        terms = []
        
        if isinstance(body, Term):
            if hasattr(body, 'functor'):
                functor_name = self._get_functor_name(body)
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
        else:
            # bodyがTermでない場合の処理
            if hasattr(body, '__iter__') and not isinstance(body, str):
                for item in body:
                    terms.extend(self._extract_terms_from_body(item))
            else:
                # 単一の項として扱う
                terms.append(body)
        
        return terms
    
    def _get_functor_name(self, term: Any) -> str:
        """項からファンクター名を取得"""
        if hasattr(term, 'functor'):
            functor = term.functor
            if hasattr(functor, 'name'):
                return functor.name
            else:
                return str(functor)
        elif hasattr(term, 'name'):
            return term.name
        else:
            return str(term)
    
    def _serialize_argument(self, arg: Any) -> str:
        """引数をシリアライズ"""
        if arg is None:
            return "null"
        return str(arg)
    
    def _tokenize_text(self, text: str) -> List[str]:
        """テキストをトークンに分割（日本語対応）"""
        # 英数字、日本語文字、アンダースコアを単語として抽出
        tokens = re.findall(r'[a-zA-Z0-9_\u3040-\u309F\u30A0-\u30FF\u4E00-\u9FAF]+', text)
        return [token.lower() for token in tokens if len(token) > 1]
    
    def _matches_predicate_pattern(self, pattern: str, predicate_name: str) -> bool:
        """述語パターンマッチング"""
        # 完全一致
        if pattern == predicate_name:
            return True
        
        # 部分一致
        if pattern.lower() in predicate_name.lower():
            return True
        
        # 正規表現マッチング
        try:
            if re.search(pattern, predicate_name, re.IGNORECASE):
                return True
        except re.error:
            pass
        
        return False
    
    def _calculate_text_relevance(self, word: str, full_text: str) -> float:
        """テキストの関連度を計算"""
        word_count = full_text.lower().count(word.lower())
        text_length = len(full_text.split())
        
        if text_length == 0:
            return 0.0
        
        # TF（Term Frequency）的な計算
        relevance = min(1.0, word_count / max(1, text_length) * 10)
        return relevance