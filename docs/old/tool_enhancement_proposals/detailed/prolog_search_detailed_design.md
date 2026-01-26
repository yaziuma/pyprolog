# `prolog_search` 詳細設計書

## 1. アーキテクチャ設計

### 1.1 コンポーネント構成

```
pyprolog/
├── search/
│   ├── __init__.py
│   ├── search_engine.py        # 新規: 検索エンジン本体
│   ├── indexer.py             # 新規: インデックス構築
│   ├── pattern_matcher.py     # 新規: パターンマッチング
│   └── search_result.py       # 新規: 検索結果クラス
├── tools/
│   └── search_tool.py         # 新規: search ツール実装
└── cli/
    └── prolog.py              # 既存: search オプション追加
```

### 1.2 クラス設計

#### 1.2.1 SearchResult クラス
```python
@dataclass
class SearchResult:
    rule_or_fact: Union[Rule, Fact]
    file_path: Optional[str]
    line_number: int
    matched_text: str
    match_type: str  # "predicate", "argument", "full_text"
    context_lines: List[str]  # 前後の行
    confidence: float  # マッチ度（0.0-1.0）
```

#### 1.2.2 SearchIndex クラス
```python
class SearchIndex:
    def __init__(self):
        self.predicate_index: Dict[str, List[SearchResult]] = {}
        self.argument_index: Dict[str, List[SearchResult]] = {}
        self.text_index: Dict[str, List[SearchResult]] = {}
        self.file_mapping: Dict[str, List[Union[Rule, Fact]]] = {}
    
    def build_index(self, rules: List[Union[Rule, Fact]], file_path: Optional[str] = None) -> None
    def search_predicates(self, pattern: str) -> List[SearchResult]
    def search_arguments(self, pattern: str) -> List[SearchResult]
    def search_full_text(self, pattern: str) -> List[SearchResult]
```

#### 1.2.3 PatternMatcher クラス
```python
class PatternMatcher:
    @staticmethod
    def match_predicate_name(pattern: str, term: Term) -> bool
    
    @staticmethod
    def match_argument_pattern(pattern: str, term: Term) -> Tuple[bool, float]
    
    @staticmethod
    def parse_argument_pattern(pattern: str) -> Term
    
    @staticmethod
    def unify_patterns(pattern_term: Term, target_term: Term) -> Tuple[bool, float]
```

#### 1.2.4 SearchEngine クラス
```python
class SearchEngine:
    def __init__(self, runtime: Runtime):
        self.runtime = runtime
        self.index = SearchIndex()
        self.is_indexed = False
    
    def build_index(self) -> None
    def search(self, pattern: str, search_type: str = "predicate", limit: int = 100) -> List[SearchResult]
    def _search_predicate(self, pattern: str, limit: int) -> List[SearchResult]
    def _search_argument(self, pattern: str, limit: int) -> List[SearchResult]
    def _search_full_text(self, pattern: str, limit: int) -> List[SearchResult]
```

## 2. 実装詳細

### 2.1 インデックス構築

#### 2.1.1 述語名インデックス
```python
def build_predicate_index(self, rules: List[Union[Rule, Fact]], file_path: Optional[str] = None):
    for i, rule_or_fact in enumerate(rules):
        if isinstance(rule_or_fact, Fact):
            predicate_name = rule_or_fact.head.functor if hasattr(rule_or_fact.head, 'functor') else str(rule_or_fact.head)
        elif isinstance(rule_or_fact, Rule):
            predicate_name = rule_or_fact.head.functor if hasattr(rule_or_fact.head, 'functor') else str(rule_or_fact.head)
        
        # インデックスに追加
        if predicate_name not in self.predicate_index:
            self.predicate_index[predicate_name] = []
        
        search_result = SearchResult(
            rule_or_fact=rule_or_fact,
            file_path=file_path,
            line_number=i + 1,  # ファイル情報が利用可能な場合は実際の行番号を使用
            matched_text=predicate_name,
            match_type="predicate",
            context_lines=[],
            confidence=1.0
        )
        self.predicate_index[predicate_name].append(search_result)
```

#### 2.1.2 引数パターンインデックス
```python
def build_argument_index(self, rules: List[Union[Rule, Fact]], file_path: Optional[str] = None):
    for i, rule_or_fact in enumerate(rules):
        # 全ての項（head, body内の各項）を再帰的に解析
        terms_to_index = []
        if isinstance(rule_or_fact, Fact):
            terms_to_index.append(rule_or_fact.head)
        elif isinstance(rule_or_fact, Rule):
            terms_to_index.append(rule_or_fact.head)
            terms_to_index.extend(self._extract_terms_from_body(rule_or_fact.body))
        
        for term in terms_to_index:
            # 引数の組み合わせをインデックス化
            if hasattr(term, 'args') and term.args:
                for j, arg in enumerate(term.args):
                    pattern_key = f"{term.functor}/{len(term.args)}/{j}/{self._serialize_argument(arg)}"
                    
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
```

#### 2.1.3 全文検索インデックス
```python
def build_text_index(self, rules: List[Union[Rule, Fact]], file_path: Optional[str] = None):
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

def _tokenize_text(self, text: str) -> List[str]:
    """テキストをトークンに分割（アルファベット、数字、日本語文字を考慮）"""
    import re
    # 英数字、日本語文字、アンダースコアを単語として抽出
    tokens = re.findall(r'[a-zA-Z0-9_\u3040-\u309F\u30A0-\u30FF\u4E00-\u9FAF]+', text)
    return [token.lower() for token in tokens if len(token) > 1]
```

### 2.2 パターンマッチング

#### 2.2.1 述語名マッチング
```python
def match_predicate_name(pattern: str, term: Term) -> bool:
    if hasattr(term, 'functor'):
        functor_name = term.functor
    else:
        functor_name = str(term)
    
    # 完全一致
    if pattern == functor_name:
        return True
    
    # 部分一致（大文字小文字を無視）
    if pattern.lower() in functor_name.lower():
        return True
    
    # 正規表現マッチング（パターンが正規表現として有効な場合）
    try:
        import re
        if re.search(pattern, functor_name, re.IGNORECASE):
            return True
    except re.error:
        pass
    
    return False
```

#### 2.2.2 引数パターンマッチング
```python
def match_argument_pattern(pattern: str, term: Term) -> Tuple[bool, float]:
    """
    引数パターンマッチング
    例: "location(_, office)" は location(desk, office) にマッチ
    """
    try:
        # パターンをパースしてTermに変換
        pattern_term = self.parse_argument_pattern(pattern)
        
        # 単一化を試行
        is_match, confidence = self.unify_patterns(pattern_term, term)
        return is_match, confidence
        
    except Exception as e:
        logger.warning(f"Failed to match argument pattern '{pattern}': {e}")
        return False, 0.0

def parse_argument_pattern(pattern: str) -> Term:
    """文字列パターンをTermオブジェクトに変換"""
    from pyprolog.parser.scanner import Scanner
    from pyprolog.parser.parser import Parser
    
    scanner = Scanner(pattern)
    tokens = scanner.scan_tokens()
    parser = Parser(tokens)
    
    # パターンは単一の項として解析
    term = parser.parse_term()
    return term

def unify_patterns(pattern_term: Term, target_term: Term) -> Tuple[bool, float]:
    """パターン項と対象項の単一化を試行し、マッチ度を計算"""
    from pyprolog.core.binding_environment import BindingEnvironment
    from pyprolog.runtime.logic_interpreter import LogicInterpreter
    
    bindings = BindingEnvironment()
    logic_interpreter = LogicInterpreter(None)  # Runtimeは後で設定
    
    try:
        unified_bindings = logic_interpreter.unify(pattern_term, target_term, bindings)
        if unified_bindings is not None:
            # マッチ度を計算（完全一致なら1.0、部分一致なら比率に応じて）
            confidence = self._calculate_unification_confidence(pattern_term, target_term, unified_bindings)
            return True, confidence
        else:
            return False, 0.0
    except Exception:
        return False, 0.0

def _calculate_unification_confidence(pattern: Term, target: Term, bindings: BindingEnvironment) -> float:
    """単一化の信頼度を計算"""
    if str(pattern) == str(target):
        return 1.0
    
    # 変数の数と具体的な値の数を比較
    pattern_vars = self._count_variables(pattern)
    target_vars = self._count_variables(target)
    
    if pattern_vars == 0 and target_vars == 0:
        return 1.0  # 完全一致
    
    # 変数が多いほど信頼度は低下
    confidence = max(0.1, 1.0 - (pattern_vars * 0.2))
    return confidence
```

### 2.3 検索エンジンの実装

#### 2.3.1 統合検索メソッド
```python
def search(self, pattern: str, search_type: str = "predicate", limit: int = 100) -> List[SearchResult]:
    if not self.is_indexed:
        self.build_index()
    
    results = []
    
    if search_type == "predicate":
        results = self._search_predicate(pattern, limit)
    elif search_type == "argument":
        results = self._search_argument(pattern, limit)
    elif search_type == "full_text":
        results = self._search_full_text(pattern, limit)
    else:
        raise ValueError(f"Unknown search type: {search_type}")
    
    # 信頼度順にソート
    results.sort(key=lambda x: x.confidence, reverse=True)
    
    return results[:limit]

def _search_predicate(self, pattern: str, limit: int) -> List[SearchResult]:
    results = []
    
    for predicate_name, search_results in self.index.predicate_index.items():
        if PatternMatcher.match_predicate_name(pattern, Term(predicate_name)):
            results.extend(search_results)
    
    return results

def _search_argument(self, pattern: str, limit: int) -> List[SearchResult]:
    results = []
    
    for rule_or_fact in self.runtime.rules:
        terms_to_check = []
        if isinstance(rule_or_fact, Fact):
            terms_to_check.append(rule_or_fact.head)
        elif isinstance(rule_or_fact, Rule):
            terms_to_check.append(rule_or_fact.head)
            terms_to_check.extend(self._extract_terms_from_body(rule_or_fact.body))
        
        for term in terms_to_check:
            is_match, confidence = PatternMatcher.match_argument_pattern(pattern, term)
            if is_match:
                search_result = SearchResult(
                    rule_or_fact=rule_or_fact,
                    file_path=None,  # ファイル情報があれば設定
                    line_number=0,   # 行番号情報があれば設定
                    matched_text=str(term),
                    match_type="argument",
                    context_lines=[],
                    confidence=confidence
                )
                results.append(search_result)
                
                if len(results) >= limit:
                    break
    
    return results

def _search_full_text(self, pattern: str, limit: int) -> List[SearchResult]:
    results = []
    pattern_lower = pattern.lower()
    
    for rule_or_fact in self.runtime.rules:
        rule_text = str(rule_or_fact)
        if pattern_lower in rule_text.lower():
            confidence = self._calculate_text_relevance(pattern, rule_text)
            search_result = SearchResult(
                rule_or_fact=rule_or_fact,
                file_path=None,
                line_number=0,
                matched_text=rule_text,
                match_type="full_text",
                context_lines=[],
                confidence=confidence
            )
            results.append(search_result)
            
            if len(results) >= limit:
                break
    
    return results
```

### 2.4 CLI統合

#### 2.4.1 コマンドライン引数
```python
# pyprolog/cli/prolog.py
def add_search_arguments(parser):
    parser.add_argument('--search', action='store_true',
                       help='Enable search mode')
    parser.add_argument('--search-pattern', type=str,
                       help='Search pattern')
    parser.add_argument('--search-type', choices=['predicate', 'argument', 'full_text'],
                       default='predicate', help='Search type')
    parser.add_argument('--search-limit', type=int, default=100,
                       help='Maximum number of search results')
```

#### 2.4.2 対話モードでの統合
```python
def interactive_search_mode(runtime: Runtime):
    search_engine = SearchEngine(runtime)
    
    while True:
        command = input("search> ").strip()
        
        if command.startswith("search(") and command.endswith(")."):
            # search(pattern, type, limit) のパース
            pattern, search_type, limit = parse_search_command(command)
            
            results = search_engine.search(pattern, search_type, limit)
            
            if results:
                print(f"Found {len(results)} results:")
                for i, result in enumerate(results, 1):
                    print(f"{i}. {result.matched_text} (confidence: {result.confidence:.2f})")
                    if result.file_path:
                        print(f"   File: {result.file_path}:{result.line_number}")
                    print()
            else:
                print("No results found.")
        
        elif command == "exit":
            break
        else:
            print("Use: search(pattern, type, limit) or 'exit'")
            print("Example: search(location, predicate, 10)")
```

## 3. パフォーマンス最適化

### 3.1 レイジーインデックス構築
```python
class SearchEngine:
    def __init__(self, runtime: Runtime):
        self.runtime = runtime
        self.index = None
        self._index_cache_valid = False
    
    def _ensure_index(self):
        if not self._index_cache_valid or self.index is None:
            self.build_index()
            self._index_cache_valid = True
    
    def invalidate_cache(self):
        """ルールが変更された時にキャッシュを無効化"""
        self._index_cache_valid = False
```

### 3.2 検索結果のキャッシュ
```python
from functools import lru_cache

class SearchEngine:
    @lru_cache(maxsize=128)
    def _cached_search(self, pattern: str, search_type: str, limit: int) -> tuple:
        results = self.search(pattern, search_type, limit)
        # LRUキャッシュはハッシュ可能なオブジェクトが必要なのでtupleに変換
        return tuple((r.matched_text, r.confidence, r.match_type) for r in results)
```

## 4. テスト設計

### 4.1 単体テスト
```python
# tests/search/test_search_engine.py
class TestSearchEngine:
    def test_predicate_search(self):
        # 述語名検索のテスト
        pass
    
    def test_argument_search(self):
        # 引数パターン検索のテスト
        pass
    
    def test_full_text_search(self):
        # 全文検索のテスト
        pass
    
    def test_search_limit(self):
        # 結果数制限のテスト
        pass

# tests/search/test_pattern_matcher.py
class TestPatternMatcher:
    def test_predicate_matching(self):
        assert PatternMatcher.match_predicate_name("location", Term("location"))
        assert PatternMatcher.match_predicate_name("loc", Term("location"))
    
    def test_argument_pattern_matching(self):
        # location(_, office) パターンのテスト
        pass
```

### 4.2 統合テスト
```python
# tests/integration/test_search_tool.py
class TestSearchTool:
    def test_cli_search_integration(self):
        # CLI統合のテスト
        pass
    
    def test_interactive_search_mode(self):
        # 対話モードでの検索テスト
        pass
```

## 5. エラーハンドリング

### 5.1 パターン解析エラー
```python
def parse_argument_pattern(pattern: str) -> Term:
    try:
        scanner = Scanner(pattern)
        tokens = scanner.scan_tokens()
        parser = Parser(tokens)
        return parser.parse_term()
    except Exception as e:
        raise ValueError(f"Invalid argument pattern '{pattern}': {e}")
```

### 5.2 検索タイムアウト
```python
import signal

class SearchTimeoutError(Exception):
    pass

def search_with_timeout(self, pattern: str, search_type: str, limit: int, timeout: int = 30) -> List[SearchResult]:
    def timeout_handler(signum, frame):
        raise SearchTimeoutError(f"Search timed out after {timeout} seconds")
    
    signal.signal(signal.SIGALRM, timeout_handler)
    signal.alarm(timeout)
    
    try:
        return self.search(pattern, search_type, limit)
    finally:
        signal.alarm(0)  # タイムアウトをクリア
```

この設計により、効率的で柔軟な検索機能をPyPrologに統合できます。