# MCP統合シーケンス図

## 概要

改修後のpyprologを使用してprolog_mcpで`addition_calculator.pl`の`detailed_interaction`述語を実行する際の、統一入力システムの動作フローを示します。

## シーケンス図

```mermaid
sequenceDiagram
    participant Client as MCPクライアント
    participant MCP as prolog_mcp<br/>サーバー
    participant Runtime as pyprolog<br/>Runtime
    participant IOManager as IOManager
    participant UnifiedInput as UnifiedInput<br/>System
    participant Handler as MCPInputHandler<br/>(MCP統合ハンドラ)
    participant ReadLine as ReadLine<br/>Predicate

    Note over Client,Handler: クエリ実行フェーズ
    Client->>MCP: prolog_query("detailed_interaction.")
    MCP->>Runtime: runtime.query("detailed_interaction.")
    
    Note over Runtime,Handler: 1回目の入力（名前入力）
    Runtime->>ReadLine: execute()
    ReadLine->>IOManager: request_input("line", "read_line")
    IOManager->>UnifiedInput: request_input("line", "read_line")
    
    Note over UnifiedInput: InputEvent生成
    UnifiedInput->>UnifiedInput: create_event(<br/>"line", "read_line", {})
    
    UnifiedInput->>Handler: handle_input_request(event)
    Note over Handler: 入力待ち検知
    Handler->>MCP: PrologInputRequiredException<br/>("あなたの名前を入力してください: ")
    MCP-->>Client: ツール一時停止<br/>input_required: "名前を入力してください"
    
    Client->>MCP: provide_prolog_input("Alice")
    MCP->>Handler: resume_with_input("Alice")
    Handler-->>UnifiedInput: "Alice"
    UnifiedInput-->>IOManager: "Alice"
    IOManager-->>ReadLine: "Alice"
    ReadLine-->>Runtime: unified with Variable

    Note over Runtime,Handler: 2回目の入力（数値1入力）
    Runtime->>ReadLine: execute()
    ReadLine->>IOManager: request_input("line", "read_line")
    IOManager->>UnifiedInput: request_input("line", "read_line")
    UnifiedInput->>UnifiedInput: create_event(<br/>"line", "read_line", {})
    UnifiedInput->>Handler: handle_input_request(event)
    Handler->>MCP: PrologInputRequiredException<br/>("1つ目の数値を入力: ")
    MCP-->>Client: ツール一時停止<br/>input_required: "1つ目の数値を入力"
    
    Client->>MCP: provide_prolog_input("10")
    MCP->>Handler: resume_with_input("10")
    Handler-->>UnifiedInput: "10"
    UnifiedInput-->>IOManager: "10"
    IOManager-->>ReadLine: "10"
    ReadLine-->>Runtime: unified with Variable

    Note over Runtime,Handler: 3回目の入力（数値2入力）
    Runtime->>ReadLine: execute()
    ReadLine->>IOManager: request_input("line", "read_line")
    IOManager->>UnifiedInput: request_input("line", "read_line")
    UnifiedInput->>UnifiedInput: create_event(<br/>"line", "read_line", {})
    UnifiedInput->>Handler: handle_input_request(event)
    Handler->>MCP: PrologInputRequiredException<br/>("2つ目の数値を入力: ")
    MCP-->>Client: ツール一時停止<br/>input_required: "2つ目の数値を入力"
    
    Client->>MCP: provide_prolog_input("20")
    MCP->>Handler: resume_with_input("20")
    Handler-->>UnifiedInput: "20"
    UnifiedInput-->>IOManager: "20"
    IOManager-->>ReadLine: "20"
    ReadLine-->>Runtime: unified with Variable

    Note over Runtime,Handler: 4回目の入力（保存確認）
    Runtime->>ReadLine: execute()
    ReadLine->>IOManager: request_input("line", "read_line")
    IOManager->>UnifiedInput: request_input("line", "read_line")
    UnifiedInput->>UnifiedInput: create_event(<br/>"line", "read_line", {})
    UnifiedInput->>Handler: handle_input_request(event)
    Handler->>MCP: PrologInputRequiredException<br/>("結果を保存しますか？ (yes/no): ")
    MCP-->>Client: ツール一時停止<br/>input_required: "結果を保存しますか？"
    
    Client->>MCP: provide_prolog_input("yes")
    MCP->>Handler: resume_with_input("yes")
    Handler-->>UnifiedInput: "yes"
    UnifiedInput-->>IOManager: "yes"
    IOManager-->>ReadLine: "yes"
    ReadLine-->>Runtime: unified with Variable

    Note over Runtime,Handler: クエリ完了
    Runtime-->>MCP: [{"Name": "Alice", "Num1": "10", "Num2": "20", "Save": "yes"}]
    MCP-->>Client: ツール実行完了（出力含む）
```

## 詳細な動作説明

### クエリ実行フェーズ

**MCP統合での入力処理フロー:**
1. `detailed_interaction`述語が実行される
2. 各`read_line/1`呼び出しで以下が発生：
   - ReadLinePredicateがIOManagerに入力要求
   - IOManagerがUnifiedInputSystemに転送
   - InputEventが生成される（入力タイプ、述語名、タイムスタンプ等）
   - MCPInputHandlerが入力待ちを検知し、`PrologInputRequiredException`を発生
   - prolog_mcpサーバーが例外をキャッチし、MCPクライアントに入力要求を通知
   - MCPクライアントがユーザーから入力を取得し、`provide_prolog_input`で返送
   - ハンドラが入力値を受け取り、統一入力システム経由でProlog実行を再開

**MCP統合の重要な特徴:**
- **非同期的な対話**: 入力待ちで実行が一時停止し、クライアントからの入力で再開
- **例外ベースの制御**: `PrologInputRequiredException`で入力待ち状態を表現
- **MCPツール分離**: `provide_prolog_input`専用ツールで入力値を供給
- **統一的な処理**: 全ての入力タイプ（char、line等）が同一メカニズムで処理

## MCP統合ハンドラ実装例

```python
class MCPInputHandler(InputHandler):
    """MCP統合用の入力ハンドラ"""
    
    def __init__(self):
        self.pending_input = None
        self.input_event = threading.Event()
    
    def handle_input_request(self, event: InputEvent) -> Optional[str]:
        """入力要求を検知してMCPクライアントに通知"""
        # プロンプトメッセージの抽出（Prologの出力から）
        prompt = self._extract_prompt_from_context(event)
        
        # prolog_mcpサーバーに入力要求例外を発生
        raise PrologInputRequiredException(
            input_type=event.input_type,
            predicate_name=event.predicate_name, 
            prompt=prompt,
            event_id=event.request_id
        )
    
    def resume_with_input(self, input_value: str) -> str:
        """MCPクライアントから入力値を受け取って再開"""
        self.pending_input = input_value
        self.input_event.set()
        return input_value
    
    def _extract_prompt_from_context(self, event: InputEvent) -> str:
        """実行コンテキストからプロンプト文字列を抽出"""
        # Prologの出力バッファからプロンプトを取得
        # または event.context から取得
        return event.get_arg("prompt", "入力してください: ")

# prolog_mcpサーバーでの使用
class PrologInputRequiredException(Exception):
    """入力要求例外 - MCPクライアントに通知するため"""
    def __init__(self, input_type: str, predicate_name: str, prompt: str, event_id: str):
        self.input_type = input_type
        self.predicate_name = predicate_name
        self.prompt = prompt
        self.event_id = event_id
        super().__init__(f"Input required: {prompt}")

# MCP サーバー側での処理
try:
    results = runtime.query("detailed_interaction.")
except PrologInputRequiredException as e:
    # MCPクライアントに入力要求を通知
    return {
        "status": "input_required",
        "input_type": e.input_type,
        "prompt": e.prompt,
        "event_id": e.event_id
    }
```

## MCP統合の利点

この統一入力システム + MCP統合により：

1. **真の対話的実行**: MCPクライアント（Claude Desktop等）でユーザーが実際に入力
2. **統一的な制御**: 全ての入力述語が同一の仕組みで処理
3. **拡張性**: 新しい入力タイプも自動的にMCP対応
4. **デバッグ支援**: 入力要求の履歴・統計情報が統一管理