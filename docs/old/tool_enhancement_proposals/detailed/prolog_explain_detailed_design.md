# `prolog_explain` 詳細設計書

## 1. アーキテクチャ設計

### 1.1 コンポーネント構成

```
pyprolog/
├── runtime/
│   ├── tracer.py              # 新規: トレース機能
│   ├── trace_formatter.py     # 新規: 出力フォーマッタ
│   └── interpreter.py         # 既存: トレース対応追加
├── tools/
│   └── explain_tool.py        # 新規: explain ツール実装
└── cli/
    └── prolog.py              # 既存: explain オプション追加
```

### 1.2 クラス設計

#### 1.2.1 TraceEvent クラス
```python
@dataclass
class TraceEvent:
    event_type: str  # "CALL", "EXIT", "FAIL", "REDO"
    goal: Term
    depth: int
    bindings: BindingEnvironment
    timestamp: float
    rule_ref: Optional[Union[Rule, Fact]] = None
```

#### 1.2.2 Tracer クラス
```python
class Tracer:
    def __init__(self, max_depth: Optional[int] = None):
        self.events: List[TraceEvent] = []
        self.max_depth = max_depth
        self.current_depth = 0
        self.enabled = False
    
    def start_trace(self) -> None
    def stop_trace(self) -> None
    def record_call(self, goal: Term, bindings: BindingEnvironment) -> None
    def record_exit(self, goal: Term, bindings: BindingEnvironment, rule: Union[Rule, Fact]) -> None
    def record_fail(self, goal: Term) -> None
    def record_redo(self, goal: Term) -> None
    def get_events(self) -> List[TraceEvent]
    def clear_events(self) -> None
```

#### 1.2.3 TraceFormatter クラス
```python
class TraceFormatter:
    @staticmethod
    def format_text(events: List[TraceEvent]) -> str
    
    @staticmethod
    def format_tree(events: List[TraceEvent]) -> str
    
    @staticmethod
    def format_json(events: List[TraceEvent], query: str, solutions: List[Dict]) -> str
```

## 2. 実装詳細

### 2.1 Runtime クラスの拡張

既存の`Runtime`クラスにトレース機能を統合：

```python
class Runtime:
    def __init__(self, ...):
        # 既存の初期化
        self.tracer = Tracer()
    
    def query_with_trace(self, query_str: str, max_depth: Optional[int] = None) -> Tuple[List[Dict], List[TraceEvent]]:
        """トレース付きでクエリを実行"""
        self.tracer = Tracer(max_depth)
        self.tracer.start_trace()
        
        try:
            solutions = list(self.query(query_str))
            return solutions, self.tracer.get_events()
        finally:
            self.tracer.stop_trace()
```

### 2.2 LogicInterpreter のトレース対応

`LogicInterpreter.solve_goal`メソッドにトレースフックを追加：

```python
def solve_goal(self, goal: Term, bindings: BindingEnvironment) -> Iterator[BindingEnvironment]:
    if self.runtime.tracer.enabled:
        self.runtime.tracer.record_call(goal, bindings)
    
    try:
        found_solution = False
        for rule in self.runtime.rules:
            # 既存のマッチング処理
            if matches:
                if self.runtime.tracer.enabled:
                    self.runtime.tracer.record_exit(goal, new_bindings, rule)
                yield new_bindings
                found_solution = True
                
                if self.runtime.tracer.enabled:
                    self.runtime.tracer.record_redo(goal)
        
        if not found_solution and self.runtime.tracer.enabled:
            self.runtime.tracer.record_fail(goal)
            
    except Exception as e:
        if self.runtime.tracer.enabled:
            self.runtime.tracer.record_fail(goal)
        raise
```

### 2.3 出力フォーマッタの実装

#### 2.3.1 テキスト形式
```python
def format_text(events: List[TraceEvent]) -> str:
    result = []
    for event in events:
        indent = "  " * event.depth
        if event.event_type == "CALL":
            result.append(f"{indent}CALL: {event.goal}")
        elif event.event_type == "EXIT":
            bindings_str = _format_bindings(event.bindings)
            result.append(f"{indent}EXIT: {event.goal} {bindings_str}")
        elif event.event_type == "FAIL":
            result.append(f"{indent}FAIL: {event.goal}")
        elif event.event_type == "REDO":
            result.append(f"{indent}REDO: {event.goal}")
    
    return "\n".join(result)
```

#### 2.3.2 ツリー形式
```python
def format_tree(events: List[TraceEvent]) -> str:
    # 階層構造を維持しながら、成功/失敗の状態を表示
    tree_nodes = _build_tree_structure(events)
    return _render_tree(tree_nodes)
```

#### 2.3.3 JSON形式
```python
def format_json(events: List[TraceEvent], query: str, solutions: List[Dict]) -> str:
    trace_data = []
    for event in events:
        trace_data.append({
            "event": event.event_type,
            "goal": str(event.goal),
            "depth": event.depth,
            "bindings": _serialize_bindings(event.bindings),
            "timestamp": event.timestamp
        })
    
    result = {
        "query": query,
        "status": "SUCCESS" if solutions else "FAIL",
        "solutions": solutions,
        "trace": trace_data
    }
    
    return json.dumps(result, indent=2, ensure_ascii=False)
```

## 3. CLI統合

### 3.1 コマンドライン引数の追加

```python
# pyprolog/cli/prolog.py
def main():
    parser = argparse.ArgumentParser()
    # 既存の引数
    parser.add_argument('--explain', action='store_true', 
                       help='Enable query explanation mode')
    parser.add_argument('--trace-depth', type=int, 
                       help='Maximum trace depth')
    parser.add_argument('--trace-format', choices=['text', 'tree', 'json'],
                       default='text', help='Trace output format')
```

### 3.2 対話モードでの統合

```python
def interactive_mode(runtime: Runtime, args):
    while True:
        query = input("?- ")
        if query.startswith("explain(") and query.endswith(")."):
            # explain(query, format, depth) の解析
            explain_query(runtime, query, args)
        else:
            # 通常のクエリ処理
            normal_query(runtime, query)

def explain_query(runtime: Runtime, explain_command: str, args):
    # explain(member(X, [1,2,3]), text, 5) のようなコマンドをパース
    inner_query, format_type, depth = parse_explain_command(explain_command)
    
    solutions, trace_events = runtime.query_with_trace(inner_query, depth)
    
    if format_type == "text":
        print(TraceFormatter.format_text(trace_events))
    elif format_type == "tree":
        print(TraceFormatter.format_tree(trace_events))
    elif format_type == "json":
        print(TraceFormatter.format_json(trace_events, inner_query, solutions))
```

## 4. パフォーマンス考慮事項

### 4.1 トレース有効時のオーバーヘッド

- イベント記録は最小限のオーバーヘッドで実装
- 大きなBindingEnvironmentのコピーを避けるため、必要な情報のみ記録
- `max_depth`制限により、深い再帰での性能問題を回避

### 4.2 メモリ使用量

```python
class Tracer:
    def __init__(self, max_depth: Optional[int] = None, max_events: int = 10000):
        self.max_events = max_events
    
    def record_event(self, event: TraceEvent):
        if len(self.events) >= self.max_events:
            # 古いイベントを削除してメモリ使用量を制限
            self.events = self.events[1000:]  # 最新の9000イベントを保持
        self.events.append(event)
```

## 5. テスト設計

### 5.1 単体テスト

```python
# tests/runtime/test_tracer.py
class TestTracer:
    def test_basic_tracing(self):
        tracer = Tracer()
        tracer.start_trace()
        # テストケース実装
    
    def test_depth_limit(self):
        tracer = Tracer(max_depth=3)
        # 深さ制限のテスト
    
    def test_trace_formatting(self):
        # 各フォーマットのテスト
```

### 5.2 統合テスト

```python
# tests/integration/test_explain_tool.py
class TestExplainTool:
    def test_simple_query_explanation(self):
        # 基本的なクエリの説明テスト
    
    def test_backtracking_explanation(self):
        # バックトラッキングが発生するクエリのテスト
    
    def test_failed_query_explanation(self):
        # 失敗するクエリの説明テスト
```

## 6. エラーハンドリング

### 6.1 トレース中の例外処理

```python
def record_call(self, goal: Term, bindings: BindingEnvironment) -> None:
    try:
        if self.current_depth >= self.max_depth:
            return
        
        event = TraceEvent(
            event_type="CALL",
            goal=goal,
            depth=self.current_depth,
            bindings=bindings.copy(),  # 安全なコピー
            timestamp=time.time()
        )
        self.record_event(event)
        self.current_depth += 1
        
    except Exception as e:
        logger.warning(f"Failed to record trace event: {e}")
        # トレースエラーはメインの実行を妨げない
```

### 6.2 フォーマット時のエラー

```python
def format_text(events: List[TraceEvent]) -> str:
    try:
        return _safe_format_text(events)
    except Exception as e:
        return f"Error formatting trace: {e}\nRaw events: {events}"
```

## 7. 設定可能な項目

```python
# pyprolog/config/trace_config.py
@dataclass
class TraceConfig:
    max_depth: Optional[int] = None
    max_events: int = 10000
    include_builtin_predicates: bool = False
    include_timestamps: bool = True
    minimal_output: bool = False  # 最小限の出力モード
```

この設計により、既存のPyPrologアーキテクチャに最小限の変更でトレース機能を統合し、ユーザーが求める推論過程の可視化を実現できます。