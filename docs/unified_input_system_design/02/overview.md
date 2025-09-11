# PyProlog 統一入力システム 概要設計書

## 1. 概要

### 1.1 目的

PyPrologライブラリの入力処理を統一し、利用者側の修正不要で全ての入力述語を制御可能にする。

### 1.2 背景と課題

**現在の問題:**
- 新しい入力述語追加時、利用者がIOStreamクラスでメソッドオーバーライド必要
- 入力処理が分散（`read_char()`, `read_line()` 等が個別実装）
- 開放閉鎖原則に違反（拡張のために既存コード変更が必要）

**目標:**
- 利用者側の修正を一切不要にする
- 全入力操作を単一ハンドラで統一制御
- 新述語追加時の影響を最小化

## 2. システム概要

### 2.1 アーキテクチャ方針

**イベントドリブン統一入力システム**
- 全入力要求をイベントとして抽象化
- 単一のInputHandlerで全入力タイプを処理
- 従来互換性を完全保持

### 2.2 コンポーネント構成

```
┌─────────────────┐
│ 入力述語群      │  get_char/1, read_line/1, etc.
│ (Predicate)     │
└─────────┬───────┘
          │ request_input()
┌─────────▼───────┐
│ IOManager       │  統一入力要求の管理
└─────────┬───────┘
          │ handle_input_request()
┌─────────▼───────┐
│ UnifiedInput    │  イベント処理・ルーティング
│ System          │
└─────────┬───────┘
          │ InputEvent
┌─────────▼───────┐
│ InputHandler    │  利用者実装の統一ハンドラ
│ (User Defined)  │
└─────────────────┘
```

## 3. コアコンポーネント設計

### 3.1 InputEvent

**役割:** 入力要求情報の標準化

```python
@dataclass
class InputEvent:
    input_type: str       # "char", "line", "term", "number"
    predicate_name: str   # "get_char", "read_line" 
    args: Dict[str, Any]  # 追加パラメータ
    timestamp: float      # 要求時刻
    context: Optional[Dict] = None  # 実行コンテキスト
```

### 3.2 InputHandler (Abstract)

**役割:** 利用者実装の統一入力ハンドラインターフェース

```python
class InputHandler(ABC):
    @abstractmethod
    def handle_input_request(self, event: InputEvent) -> Optional[str]:
        """
        統一入力要求処理
        
        Returns:
            入力値 or None(EOF)
        """
        pass
```

### 3.3 UnifiedInputSystem

**役割:** 入力要求の中央管理・ルーティング

**主要機能:**
- イベント生成・配信
- カスタムハンドラ管理
- フォールバック処理
- エラーハンドリング

```python
class UnifiedInputSystem:
    def __init__(self):
        self.input_handler: Optional[InputHandler] = None
        self.fallback_stream: Optional[IOStream] = None
    
    def request_input(self, input_type: str, predicate_name: str, **kwargs) -> Optional[str]:
        # InputEvent生成
        # カスタムハンドラ実行
        # フォールバック処理
        pass
```

### 3.4 IOManager (改修)

**役割:** 統一入力システムとの統合

**変更点:**
- `UnifiedInputSystem`インスタンス管理
- 統一入力API提供
- 従来互換性維持

## 4. 利用者インターフェース

### 4.1 基本利用（修正不要）

```python
# 既存コードは無修正で動作
runtime = Runtime()
results = runtime.query("get_char(X).")
```

### 4.2 統一ハンドラ設定

```python
class MyInputHandler(InputHandler):
    def handle_input_request(self, event: InputEvent) -> Optional[str]:
        if event.input_type == "char":
            return self.get_char_from_gui()
        elif event.input_type == "line":
            return self.get_line_from_api()
        return None

runtime = Runtime()
runtime.io_manager.set_input_handler(MyInputHandler())
```

## 5. 設計原則

### 5.1 互換性保証

- **完全後方互換:** 既存コードは無修正で動作
- **段階的移行:** 従来方式と新方式の併存
- **API継続性:** 既存IOManager APIを維持

### 5.2 拡張性

- **開放閉鎖原則準拠:** 新述語追加時に既存コード変更不要
- **プラグイン設計:** InputHandler動的交換可能
- **マルチソース対応:** 複数入力源の統一管理

### 5.3 保守性

- **責任分離:** 各コンポーネントの役割明確化
- **テスト容易性:** モックハンドラによるテスト支援
- **ログ統一:** 全入力操作の一元ログ記録

## 6. 実装段階

### Phase 1: コアシステム実装

**対象:**
- `InputEvent`, `InputHandler`クラス定義
- `UnifiedInputSystem`基本実装
- `IOManager`統合

**成果物:**
- 統一入力システムの基盤
- 基本的な利用者API

### Phase 2: 既存述語統合

**対象:**
- `GetCharPredicate`, `ReadLinePredicate`の移行
- 従来互換性検証
- テストスイート整備

**成果物:**
- 既存述語の統一入力システム対応
- 完全互換性保証

### Phase 3: 機能拡張

**対象:**
- 高度なイベント情報（コンテキスト、スタックトレース）
- 入力キャッシュ・バッファリング
- 非同期入力サポート

**成果物:**
- 高度な入力制御機能
- エンタープライズ対応機能

## 7. 品質保証

### 7.1 テスト戦略

- **互換性テスト:** 既存コードでの動作確認
- **統合テスト:** 統一ハンドラによる動作検証
- **パフォーマンステスト:** オーバーヘッド測定

### 7.2 検証項目

- [ ] 既存コード無修正での動作
- [ ] 全入力述語の統一ハンドラ対応
- [ ] 新述語追加時の利用者影響ゼロ
- [ ] フォールバック機能の動作
- [ ] エラーハンドリングの適切性

## 8. MCP統合設計

### 8.1 MCP統合の課題

**基本設計では実現困難な項目:**
- **実行コンテキスト保存・復元**: 例外発生後の実行再開メカニズム
- **出力キャプチャとプロンプト検出**: Prologの`write()`出力からプロンプト抽出
- **継続実行メカニズム**: MCPクライアントからの入力で実行を再開する仕組み
- **スレッド間通信制御**: 非同期的な入力待ち・再開の制御

### 8.2 追加設計要素

#### 8.2.1 実行コンテキスト管理

```python
class SuspendableInputSystem(UnifiedInputSystem):
    """実行中断・再開対応の統一入力システム"""
    
    def __init__(self):
        super().__init__()
        self.suspended_contexts = {}  # 中断されたコンテキスト
    
    def request_input_suspendable(self, input_type: str, predicate_name: str, **kwargs):
        """中断可能な入力要求"""
        event = self._create_event(input_type, predicate_name, kwargs)
        
        try:
            return self._handler.handle_input_request(event)
        except PrologInputRequiredException as e:
            # 実行コンテキスト保存
            self.suspended_contexts[e.event_id] = {
                'event': event,
                'thread_id': threading.get_ident(),
                'continuation_token': self._create_continuation_token()
            }
            raise  # MCPサーバーに伝播
    
    def resume_execution(self, event_id: str, input_value: str):
        """保存されたコンテキストで実行再開"""
        context = self.suspended_contexts.pop(event_id)
        return input_value  # 継続実行
```

#### 8.2.2 出力キャプチャ機能

```python
class OutputCapturingIOManager(IOManager):
    """出力キャプチャ対応IOManager"""
    
    def __init__(self):
        super().__init__()
        self.output_buffer = []
        self.prompt_detector = PromptDetector()
    
    def write_char_to_current(self, char: str):
        super().write_char_to_current(char)
        self.output_buffer.append(char)
        
        # リアルタイムプロンプト検出
        if self.prompt_detector.is_prompt_char(char):
            prompt = self.prompt_detector.extract_prompt(self.output_buffer)
            self._last_detected_prompt = prompt
    
    def get_last_prompt(self) -> str:
        """最後に検出されたプロンプトを取得"""
        return getattr(self, '_last_detected_prompt', "入力してください: ")
```

#### 8.2.3 MCP統合レイヤー（prolog_mcp側実装）

**配置:** `prolog_mcp/mcp_integration_layer.py`

```python
class MCPIntegrationLayer:
    """MCP特有の実行制御レイヤー - prolog_mcpプロジェクト内で実装"""
    
    def __init__(self, runtime: Runtime):
        self.runtime = runtime
        self.continuation_tokens = {}
    
    def execute_query_with_input_support(self, query: str):
        """入力対応Prolog実行"""
        try:
            # 通常実行
            return {
                "status": "completed",
                "results": self.runtime.query(query)
            }
        except PrologInputRequiredException as e:
            # 入力待ち状態をMCPクライアントに通知
            continuation_token = self._create_continuation_token(e)
            return {
                "status": "input_required",
                "input_type": e.input_type,
                "prompt": e.prompt,
                "event_id": e.event_id,
                "continuation_token": continuation_token
            }
    
    def continue_with_input(self, continuation_token: str, input_value: str):
        """入力値で実行継続"""
        context = self.continuation_tokens.pop(continuation_token)
        
        # 保存されたコンテキストで実行再開
        event_id = context['event_id']
        result = self.runtime.io_manager.unified_input.resume_execution(event_id, input_value)
        
        # 実行継続または完了
        try:
            return {
                "status": "completed", 
                "results": context['suspended_execution'].resume()
            }
        except PrologInputRequiredException as e:
            # さらなる入力が必要
            return self._handle_next_input_request(e)

# MCP統合用例外（prolog_mcp側で定義）
class PrologInputRequiredException(Exception):
    """入力要求例外 - MCPクライアントに通知するため"""
    def __init__(self, input_type: str, predicate_name: str, prompt: str, event_id: str):
        self.input_type = input_type
        self.predicate_name = predicate_name
        self.prompt = prompt
        self.event_id = event_id
        super().__init__(f"Input required: {prompt}")
```

### 8.3 MCP統合の実装段階

#### Phase 1: 基本統一入力システム
- 標準的なInputHandler統合
- 例外ベースの入力要求検知

#### Phase 2: 実行制御拡張
- 実行コンテキスト保存・復元
- 継続実行メカニズム

#### Phase 3: MCP完全統合
- 出力キャプチャとプロンプト検出
- MCPクライアント連携

### 8.4 制約事項

**技術的制約:**
- Pythonの継続実行の限界（真の継続はサポートされない）
- スレッド間での実行状態共有の複雑さ
- 例外ベース制御のパフォーマンスオーバーヘッド

**設計上の制約:**
- プロンプト検出の精度（ヒューリスティック依存）
- MCPプロトコルの同期的性質との整合性
- 既存コードとの互換性維持

## 9. 期待効果

### 9.1 利用者メリット

- **開発効率向上:** 入力処理の一元管理
- **保守性向上:** 修正箇所の最小化
- **テスト効率化:** 統一的なモック・テスト環境
- **MCP統合:** 真の対話的Prolog実行

### 9.2 ライブラリメリット

- **拡張性向上:** 新機能追加の容易さ
- **設計品質向上:** 開放閉鎖原則準拠
- **利用者体験向上:** 学習コスト削減
- **エコシステム統合:** MCP対応による利用範囲拡大