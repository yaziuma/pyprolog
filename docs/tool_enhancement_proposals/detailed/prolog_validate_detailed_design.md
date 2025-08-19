# `prolog_validate` 詳細設計書

## 1. アーキテクチャ設計

### 1.1 コンポーネント構成

```
pyprolog/
├── validation/
│   ├── __init__.py
│   ├── validator.py           # 新規: 検証エンジン本体
│   ├── analyzers/
│   │   ├── __init__.py
│   │   ├── conflict_analyzer.py    # 新規: 矛盾検出
│   │   ├── reachability_analyzer.py # 新規: 到達可能性解析
│   │   └── undefined_analyzer.py   # 新規: 未定義述語検出
│   ├── dependency_graph.py    # 新規: 依存関係グラフ
│   ├── symbol_table.py        # 新規: シンボルテーブル
│   └── validation_result.py   # 新規: 検証結果クラス
├── tools/
│   └── validate_tool.py       # 新規: validate ツール実装
└── cli/
    └── prolog.py              # 既存: validate オプション追加
```

### 1.2 クラス設計

#### 1.2.1 ValidationIssue クラス
```python
@dataclass
class ValidationIssue:
    issue_type: str  # "conflict", "unreachable", "undefined"
    severity: str    # "error", "warning", "info"
    message: str
    rule_or_fact: Optional[Union[Rule, Fact]]
    file_path: Optional[str]
    line_number: int
    column_number: int
    suggested_fix: Optional[str] = None
    related_items: List['ValidationIssue'] = field(default_factory=list)
```

#### 1.2.2 ValidationResult クラス
```python
@dataclass
class ValidationResult:
    issues: List[ValidationIssue]
    total_rules_analyzed: int
    analysis_duration: float
    summary: Dict[str, int]  # issue_type -> count
    
    def has_errors(self) -> bool:
        return any(issue.severity == "error" for issue in self.issues)
    
    def has_warnings(self) -> bool:
        return any(issue.severity == "warning" for issue in self.issues)
    
    def filter_by_type(self, issue_type: str) -> List[ValidationIssue]:
        return [issue for issue in self.issues if issue.issue_type == issue_type]
    
    def to_json(self) -> str:
        return json.dumps(asdict(self), indent=2, ensure_ascii=False)
```

#### 1.2.3 SymbolTable クラス
```python
class SymbolTable:
    def __init__(self):
        self.predicates: Dict[str, List[PredicateInfo]] = {}
        self.builtins: Set[str] = set()
        self.user_defined: Set[str] = set()
    
    def add_predicate(self, name: str, arity: int, rule_or_fact: Union[Rule, Fact], 
                     file_path: Optional[str] = None, line_number: int = 0) -> None
    
    def get_predicate_info(self, name: str, arity: int) -> Optional[PredicateInfo]
    
    def is_defined(self, name: str, arity: int) -> bool
    
    def get_all_predicates(self) -> List[PredicateInfo]
    
    def get_undefined_references(self) -> List[PredicateReference]

@dataclass
class PredicateInfo:
    name: str
    arity: int
    definition: Union[Rule, Fact]
    file_path: Optional[str]
    line_number: int
    is_builtin: bool = False
    references: List['PredicateReference'] = field(default_factory=list)

@dataclass
class PredicateReference:
    name: str
    arity: int
    referenced_in: Union[Rule, Fact]
    file_path: Optional[str]
    line_number: int
    context: str  # "head" or "body"
```

#### 1.2.4 DependencyGraph クラス
```python
class DependencyGraph:
    def __init__(self):
        self.nodes: Set[str] = set()  # predicate/arity
        self.edges: Dict[str, Set[str]] = {}  # caller -> callees
        self.reverse_edges: Dict[str, Set[str]] = {}  # callee -> callers
    
    def add_node(self, predicate_key: str) -> None
    
    def add_edge(self, caller: str, callee: str) -> None
    
    def get_reachable_from(self, start_nodes: Set[str]) -> Set[str]
    
    def get_unreachable_nodes(self, entry_points: Set[str]) -> Set[str]
    
    def detect_cycles(self) -> List[List[str]]
    
    def topological_sort(self) -> List[str]

def predicate_key(name: str, arity: int) -> str:
    return f"{name}/{arity}"
```

#### 1.2.5 Validator クラス
```python
class Validator:
    def __init__(self, runtime: Runtime):
        self.runtime = runtime
        self.symbol_table = SymbolTable()
        self.dependency_graph = DependencyGraph()
        self.analyzers = {
            'conflicts': ConflictAnalyzer(),
            'unreachable': ReachabilityAnalyzer(),
            'undefined': UndefinedAnalyzer()
        }
    
    def validate(self, check_type: str = "all", detailed: bool = False) -> ValidationResult
    
    def build_symbol_table(self) -> None
    
    def build_dependency_graph(self) -> None
    
    def get_entry_points(self) -> Set[str]
```

## 2. 実装詳細

### 2.1 シンボルテーブル構築

```python
def build_symbol_table(self) -> None:
    # ビルトイン述語の登録
    builtin_predicates = [
        "var/1", "atom/1", "number/1", "functor/3", "arg/3", "=../2",
        "asserta/1", "assertz/1", "retract/1", "member/2", "append/3",
        "findall/3", "get_char/1", "write/1", "nl/0", "is/2",
        "=/2", "=:=/2", "=\\=/2", "</2", "=</2", ">/2", ">=/2"
    ]
    
    for predicate in builtin_predicates:
        name, arity_str = predicate.split('/')
        arity = int(arity_str)
        self.symbol_table.builtins.add(predicate_key(name, arity))
    
    # ユーザー定義述語の登録
    for i, rule_or_fact in enumerate(self.runtime.rules):
        self._analyze_rule_or_fact(rule_or_fact, None, i + 1)

def _analyze_rule_or_fact(self, rule_or_fact: Union[Rule, Fact], 
                         file_path: Optional[str], line_number: int) -> None:
    if isinstance(rule_or_fact, Fact):
        self._register_predicate(rule_or_fact.head, rule_or_fact, file_path, line_number)
    elif isinstance(rule_or_fact, Rule):
        # ヘッドの述語を定義として登録
        self._register_predicate(rule_or_fact.head, rule_or_fact, file_path, line_number)
        
        # ボディの述語を参照として登録
        body_terms = self._extract_terms_from_body(rule_or_fact.body)
        for term in body_terms:
            self._register_reference(term, rule_or_fact, file_path, line_number)

def _register_predicate(self, term: Term, rule_or_fact: Union[Rule, Fact],
                       file_path: Optional[str], line_number: int) -> None:
    name = term.functor if hasattr(term, 'functor') else str(term)
    arity = len(term.args) if hasattr(term, 'args') and term.args else 0
    
    predicate_info = PredicateInfo(
        name=name,
        arity=arity,
        definition=rule_or_fact,
        file_path=file_path,
        line_number=line_number
    )
    
    key = predicate_key(name, arity)
    if key not in self.symbol_table.predicates:
        self.symbol_table.predicates[key] = []
    
    self.symbol_table.predicates[key].append(predicate_info)
    self.symbol_table.user_defined.add(key)

def _register_reference(self, term: Term, rule_or_fact: Union[Rule, Fact],
                       file_path: Optional[str], line_number: int) -> None:
    name = term.functor if hasattr(term, 'functor') else str(term)
    arity = len(term.args) if hasattr(term, 'args') and term.args else 0
    
    reference = PredicateReference(
        name=name,
        arity=arity,
        referenced_in=rule_or_fact,
        file_path=file_path,
        line_number=line_number,
        context="body"
    )
    
    key = predicate_key(name, arity)
    if key in self.symbol_table.predicates:
        for predicate_info in self.symbol_table.predicates[key]:
            predicate_info.references.append(reference)
```

### 2.2 依存関係グラフ構築

```python
def build_dependency_graph(self) -> None:
    # 全ての述語をノードとして追加
    for key in self.symbol_table.predicates.keys():
        self.dependency_graph.add_node(key)
    
    for key in self.symbol_table.builtins:
        self.dependency_graph.add_node(key)
    
    # 依存関係をエッジとして追加
    for rule_or_fact in self.runtime.rules:
        if isinstance(rule_or_fact, Rule):
            head_term = rule_or_fact.head
            caller_key = predicate_key(
                head_term.functor if hasattr(head_term, 'functor') else str(head_term),
                len(head_term.args) if hasattr(head_term, 'args') and head_term.args else 0
            )
            
            body_terms = self._extract_terms_from_body(rule_or_fact.body)
            for body_term in body_terms:
                callee_key = predicate_key(
                    body_term.functor if hasattr(body_term, 'functor') else str(body_term),
                    len(body_term.args) if hasattr(body_term, 'args') and body_term.args else 0
                )
                self.dependency_graph.add_edge(caller_key, callee_key)

def _extract_terms_from_body(self, body: Term) -> List[Term]:
    """ルールのボディから全ての項を抽出"""
    terms = []
    
    if hasattr(body, 'functor'):
        if body.functor == ',':  # 連言
            if hasattr(body, 'args') and len(body.args) >= 2:
                terms.extend(self._extract_terms_from_body(body.args[0]))
                terms.extend(self._extract_terms_from_body(body.args[1]))
        elif body.functor == ';':  # 選言
            if hasattr(body, 'args') and len(body.args) >= 2:
                terms.extend(self._extract_terms_from_body(body.args[0]))
                terms.extend(self._extract_terms_from_body(body.args[1]))
        else:
            terms.append(body)
    else:
        terms.append(body)
    
    return terms
```

### 2.3 各アナライザーの実装

#### 2.3.1 ConflictAnalyzer
```python
class ConflictAnalyzer:
    def analyze(self, symbol_table: SymbolTable, dependency_graph: DependencyGraph) -> List[ValidationIssue]:
        issues = []
        
        # 同じ述語の複数定義をチェック
        for key, predicate_infos in symbol_table.predicates.items():
            if len(predicate_infos) > 1:
                # 複数の定義が存在する場合、潜在的な競合を検出
                issues.extend(self._check_predicate_conflicts(predicate_infos))
        
        # 論理的矛盾をチェック
        issues.extend(self._check_logical_conflicts(symbol_table))
        
        return issues
    
    def _check_predicate_conflicts(self, predicate_infos: List[PredicateInfo]) -> List[ValidationIssue]:
        issues = []
        facts = [p for p in predicate_infos if isinstance(p.definition, Fact)]
        rules = [p for p in predicate_infos if isinstance(p.definition, Rule)]
        
        # 事実と事実の競合チェック
        for i, fact1 in enumerate(facts):
            for fact2 in facts[i+1:]:
                if self._facts_conflict(fact1.definition, fact2.definition):
                    issue = ValidationIssue(
                        issue_type="conflict",
                        severity="warning",
                        message=f"Potentially conflicting facts for {fact1.name}/{fact1.arity}",
                        rule_or_fact=fact1.definition,
                        file_path=fact1.file_path,
                        line_number=fact1.line_number,
                        column_number=0,
                        suggested_fix="Review fact definitions for logical consistency"
                    )
                    issues.append(issue)
        
        return issues
    
    def _facts_conflict(self, fact1: Fact, fact2: Fact) -> bool:
        """2つの事実が論理的に矛盾するかチェック"""
        # 基本的な例: 同じ引数で異なる述語（is_true(X), is_false(X)など）
        # より高度な分析では、制約やルールとの矛盾もチェック可能
        
        head1_str = str(fact1.head)
        head2_str = str(fact2.head)
        
        # 簡易的な矛盾検出：対照的な述語名
        conflicting_pairs = [
            ("is_true", "is_false"),
            ("is_on", "is_off"),
            ("is_open", "is_closed"),
            ("is_fast", "is_slow")
        ]
        
        for pos_pred, neg_pred in conflicting_pairs:
            if (pos_pred in head1_str and neg_pred in head2_str) or \
               (neg_pred in head1_str and pos_pred in head2_str):
                # 引数が同じかチェック
                if self._same_arguments(fact1.head, fact2.head):
                    return True
        
        return False
    
    def _same_arguments(self, term1: Term, term2: Term) -> bool:
        """2つの項の引数が同じかチェック"""
        if not (hasattr(term1, 'args') and hasattr(term2, 'args')):
            return False
        
        if len(term1.args) != len(term2.args):
            return False
        
        for arg1, arg2 in zip(term1.args, term2.args):
            if str(arg1) != str(arg2):
                return False
        
        return True
```

#### 2.3.2 ReachabilityAnalyzer
```python
class ReachabilityAnalyzer:
    def analyze(self, symbol_table: SymbolTable, dependency_graph: DependencyGraph) -> List[ValidationIssue]:
        issues = []
        
        # エントリーポイントを特定
        entry_points = self._get_entry_points(symbol_table)
        
        # 到達可能な述語を計算
        reachable = dependency_graph.get_reachable_from(entry_points)
        
        # 到達不能な述語を特定
        all_user_defined = symbol_table.user_defined
        unreachable = all_user_defined - reachable
        
        for predicate_key in unreachable:
            predicate_infos = symbol_table.predicates.get(predicate_key, [])
            for predicate_info in predicate_infos:
                issue = ValidationIssue(
                    issue_type="unreachable",
                    severity="warning",
                    message=f"Unreachable predicate: {predicate_info.name}/{predicate_info.arity}",
                    rule_or_fact=predicate_info.definition,
                    file_path=predicate_info.file_path,
                    line_number=predicate_info.line_number,
                    column_number=0,
                    suggested_fix="Consider removing unused predicate or adding entry point"
                )
                issues.append(issue)
        
        return issues
    
    def _get_entry_points(self, symbol_table: SymbolTable) -> Set[str]:
        """エントリーポイントとなる述語を特定"""
        entry_points = set()
        
        # トップレベルクエリで使用される可能性のある述語
        # 実際の実装では、メイン述語や外部から呼び出される述語を特定
        for key, predicate_infos in symbol_table.predicates.items():
            for predicate_info in predicate_infos:
                # 事実は通常エントリーポイントとして扱う
                if isinstance(predicate_info.definition, Fact):
                    entry_points.add(key)
                # 特定の命名規則に従う述語（例：test_*, main_*）
                elif predicate_info.name.startswith(('test_', 'main_', 'query_')):
                    entry_points.add(key)
        
        return entry_points
```

#### 2.3.3 UndefinedAnalyzer
```python
class UndefinedAnalyzer:
    def analyze(self, symbol_table: SymbolTable, dependency_graph: DependencyGraph) -> List[ValidationIssue]:
        issues = []
        
        # 参照されているが定義されていない述語を検出
        undefined_references = symbol_table.get_undefined_references()
        
        for reference in undefined_references:
            key = predicate_key(reference.name, reference.arity)
            
            # ビルトイン述語はスキップ
            if key in symbol_table.builtins:
                continue
            
            issue = ValidationIssue(
                issue_type="undefined",
                severity="error",
                message=f"Undefined predicate: {reference.name}/{reference.arity}",
                rule_or_fact=reference.referenced_in,
                file_path=reference.file_path,
                line_number=reference.line_number,
                column_number=0,
                suggested_fix=f"Define predicate {reference.name}/{reference.arity} or check spelling"
            )
            issues.append(issue)
        
        return issues
```

### 2.4 CLI統合

#### 2.4.1 コマンドライン引数
```python
# pyprolog/cli/prolog.py
def add_validation_arguments(parser):
    parser.add_argument('--validate', action='store_true',
                       help='Enable validation mode')
    parser.add_argument('--check-type', 
                       choices=['all', 'conflicts', 'unreachable', 'undefined'],
                       default='all', help='Type of validation checks')
    parser.add_argument('--detailed', action='store_true',
                       help='Generate detailed validation report')
    parser.add_argument('--validation-output', choices=['text', 'json'],
                       default='text', help='Validation output format')
```

#### 2.4.2 検証モード実行
```python
def run_validation(runtime: Runtime, args) -> None:
    validator = Validator(runtime)
    
    start_time = time.time()
    result = validator.validate(args.check_type, args.detailed)
    
    if args.validation_output == 'json':
        print(result.to_json())
    else:
        print_validation_report(result)
    
    # 終了コード設定
    if result.has_errors():
        sys.exit(1)
    elif result.has_warnings():
        sys.exit(2)
    else:
        sys.exit(0)

def print_validation_report(result: ValidationResult) -> None:
    print(f"Validation Report")
    print(f"================")
    print(f"Analyzed {result.total_rules_analyzed} rules in {result.analysis_duration:.2f}s")
    print()
    
    if not result.issues:
        print("✅ No issues found!")
        return
    
    # 重要度順にソート
    sorted_issues = sorted(result.issues, key=lambda x: (x.severity == "info", x.severity == "warning", x.issue_type))
    
    for issue in sorted_issues:
        icon = "❌" if issue.severity == "error" else "⚠️" if issue.severity == "warning" else "ℹ️"
        print(f"{icon} {issue.message}")
        if issue.file_path:
            print(f"   📁 {issue.file_path}:{issue.line_number}")
        if issue.suggested_fix:
            print(f"   💡 {issue.suggested_fix}")
        print()
    
    # サマリー
    print("Summary:")
    for issue_type, count in result.summary.items():
        print(f"  {issue_type}: {count}")
```

## 3. パフォーマンス考慮事項

### 3.1 大規模知識ベース対応
```python
class Validator:
    def __init__(self, runtime: Runtime, batch_size: int = 1000):
        self.runtime = runtime
        self.batch_size = batch_size
    
    def validate_large_kb(self, check_type: str = "all") -> ValidationResult:
        """大規模知識ベース用の分割処理"""
        all_issues = []
        total_analyzed = 0
        
        for i in range(0, len(self.runtime.rules), self.batch_size):
            batch = self.runtime.rules[i:i + self.batch_size]
            batch_validator = Validator(Runtime(batch))
            batch_result = batch_validator.validate(check_type)
            
            all_issues.extend(batch_result.issues)
            total_analyzed += batch_result.total_rules_analyzed
        
        return ValidationResult(
            issues=all_issues,
            total_rules_analyzed=total_analyzed,
            analysis_duration=0.0,  # 実際の処理時間を記録
            summary=self._calculate_summary(all_issues)
        )
```

### 3.2 インクリメンタル検証
```python
class IncrementalValidator:
    def __init__(self, validator: Validator):
        self.validator = validator
        self.cached_results: Dict[str, ValidationResult] = {}
        self.last_modification_time = 0
    
    def validate_if_modified(self, check_type: str = "all") -> Optional[ValidationResult]:
        current_time = time.time()
        if current_time - self.last_modification_time > 1.0:  # 1秒以上の変更がない場合
            cache_key = f"{check_type}_{len(self.validator.runtime.rules)}"
            if cache_key not in self.cached_results:
                result = self.validator.validate(check_type)
                self.cached_results[cache_key] = result
                self.last_modification_time = current_time
                return result
            else:
                return self.cached_results[cache_key]
        return None
```

## 4. テスト設計

### 4.1 単体テスト
```python
# tests/validation/test_validator.py
class TestValidator:
    def test_symbol_table_building(self):
        # シンボルテーブル構築のテスト
        pass
    
    def test_dependency_graph_building(self):
        # 依存関係グラフ構築のテスト
        pass

# tests/validation/test_analyzers.py
class TestAnalyzers:
    def test_conflict_detection(self):
        # 矛盾検出のテスト
        pass
    
    def test_unreachable_detection(self):
        # 到達不能述語検出のテスト
        pass
    
    def test_undefined_detection(self):
        # 未定義述語検出のテスト
        pass
```

### 4.2 統合テスト
```python
# tests/integration/test_validation_tool.py
class TestValidationTool:
    def test_full_validation_workflow(self):
        # 完全な検証ワークフローのテスト
        pass
    
    def test_cli_validation_integration(self):
        # CLI統合のテスト
        pass
```

この設計により、PyPrologの知識ベースの品質保証と静的解析機能を実現できます。