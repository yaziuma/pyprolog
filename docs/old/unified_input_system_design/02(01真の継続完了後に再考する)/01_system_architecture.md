# システム全体設計

## 1.1 アーキテクチャ詳細

### システム構成図

```
┌─────────────────────────────────────────────────────────────┐
│                    PyProlog Runtime                        │
├─────────────────────────────────────────────────────────────┤
│ 入力述語群                                                   │
│ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐           │
│ │GetCharPred  │ │ReadLinePred │ │PeekCharPred │ ...       │
│ └─────┬───────┘ └─────┬───────┘ └─────┬───────┘           │
│       │               │               │                   │
│       └───────────────┼───────────────┘                   │
│                       │                                   │
├───────────────────────┼───────────────────────────────────┤
│ IOManager             │                                   │
│ ┌─────────────────────▼─────────────────────┐             │
│ │ request_input(type, predicate, **kwargs) │             │
│ └─────────────────────┬─────────────────────┘             │
│                       │                                   │
├───────────────────────┼───────────────────────────────────┤
│ UnifiedInputSystem    │                                   │
│ ┌─────────────────────▼─────────────────────┐             │
│ │ handle_input_request(InputEvent)          │             │
│ │                                           │             │
│ │ ┌─────────────┐    ┌─────────────────┐   │             │
│ │ │EventRouter  │ -> │FallbackHandler  │   │             │
│ │ └─────────────┘    └─────────────────┘   │             │
│ └─────────────────────┬─────────────────────┘             │
│                       │                                   │
├───────────────────────┼───────────────────────────────────┤
│ User Implementation   │                                   │
│ ┌─────────────────────▼─────────────────────┐             │
│ │ InputHandler.handle_input_request()       │             │
│ │                                           │             │
│ │ ┌─────────┐ ┌─────────┐ ┌─────────────┐   │             │
│ │ │GUI Input│ │Web API  │ │File/DB/etc  │   │             │
│ │ └─────────┘ └─────────┘ └─────────────┘   │             │
│ └───────────────────────────────────────────┘             │
└─────────────────────────────────────────────────────────────┘
```

### レイヤー構成

**Layer 1: 述語レイヤー**
- 役割: Prolog述語の実行ロジック
- 責務: 入力要求の発行、結果の処理

**Layer 2: 管理レイヤー (IOManager)**
- 役割: 入力要求の統一インターフェース
- 責務: 要求の標準化、ルーティング

**Layer 3: 制御レイヤー (UnifiedInputSystem)**
- 役割: 入力イベントの制御・管理
- 責務: イベント処理、フォールバック、エラーハンドリング

**Layer 4: 実装レイヤー (InputHandler)**
- 役割: 実際の入力処理実装
- 責務: 入力ソースからの値取得

## 1.2 データフロー設計

### 標準入力フロー

```
1. 述語実行開始
   GetCharPredicate.execute() が呼び出される

2. 入力要求発行
   runtime.io_manager.request_input("char", "get_char")

3. イベント生成
   UnifiedInputSystem が InputEvent を生成
   event = InputEvent(
       input_type="char",
       predicate_name="get_char", 
       timestamp=now()
   )

4. ハンドラ実行
   user_handler.handle_input_request(event)

5. 結果返却
   user_handler -> UnifiedInputSystem -> IOManager -> Predicate

6. 述語処理
   GetCharPredicate が結果を処理して Term に変換
```

### フォールバックフロー

```
1-3. 標準フローと同様

4. ハンドラ実行失敗
   user_handler.handle_input_request(event) が例外 or None

5. フォールバック実行
   UnifiedInputSystem.fallback_stream.read_char()

6. 結果返却
   fallback_stream -> UnifiedInputSystem -> IOManager -> Predicate
```

## 1.3 コンポーネント間相互作用

### 依存関係

```
InputPredicate ---> IOManager
                        |
                        v
               UnifiedInputSystem
                        |
                        v
                  InputHandler (User)
                        |
                        v
                  IOStream (Fallback)
```

### 通信プロトコル

**述語 → IOManager**
```python
result = runtime.io_manager.request_input(
    input_type: str,        # "char", "line", "term"
    predicate_name: str,    # "get_char", "read_line"
    **kwargs               # 追加パラメータ
) -> Optional[str]
```

**IOManager → UnifiedInputSystem**
```python
event = InputEvent(input_type, predicate_name, kwargs)
result = unified_system.handle_input_request(event)
```

**UnifiedInputSystem → InputHandler**
```python
result = input_handler.handle_input_request(event)
```

## 1.4 並行処理・スレッドセーフティ設計

### スレッドセーフティ要件

**読み取り専用操作 (Thread-Safe)**
- `InputEvent` の読み取り
- `InputHandler` の実行（利用者実装依存）
- フォールバックストリームの読み取り

**変更操作 (要同期化)**
- `InputHandler` の設定変更
- フォールバックストリームの設定変更

### 同期化戦略

```python
class UnifiedInputSystem:
    def __init__(self):
        self._handler_lock = threading.RLock()
        self._handler: Optional[InputHandler] = None
        self._fallback_stream: Optional[IOStream] = None
    
    def set_input_handler(self, handler: InputHandler):
        with self._handler_lock:
            self._handler = handler
    
    def request_input(self, input_type: str, predicate_name: str, **kwargs):
        with self._handler_lock:
            current_handler = self._handler
            
        # ロック外でハンドラ実行（デッドロック回避）
        if current_handler:
            return current_handler.handle_input_request(event)
```

### 並行アクセス考慮事項

**利用者責務**
- `InputHandler.handle_input_request()` のスレッドセーフティ
- 外部リソース（GUI、Web API等）のアクセス制御

**システム責務**
- ハンドラ設定の同期化
- イベント生成の一意性保証

## 1.5 エラー伝播モデル

### エラー分類

**システムエラー**
- 設定エラー: ハンドラ未設定、フォールバック未設定
- 実装エラー: 不正なパラメータ、型エラー

**利用者エラー**  
- ハンドラ実装エラー: 例外発生、不正な戻り値
- 外部システムエラー: 接続失敗、タイムアウト

**リソースエラー**
- EOF: 入力終端到達
- 中断: ユーザーキャンセル、システム停止

### エラー処理方針

```
┌─────────────────┐
│ InputHandler    │ → 例外発生
│ 実行エラー      │
└─────────┬───────┘
          │
          v
┌─────────────────┐
│ UnifiedInput    │ → ログ記録 + フォールバック実行
│ System          │
└─────────┬───────┘
          │
          v (フォールバック成功)
┌─────────────────┐
│ IOManager       │ → 正常値を返却
└─────────┬───────┘
          │
          v
┌─────────────────┐
│ Predicate       │ → 通常処理継続
└─────────────────┘
```

### 例外階層

```
InputSystemError (基底)
├── InputHandlerError (ハンドラ関連)
│   ├── HandlerNotSetError
│   ├── HandlerExecutionError  
│   └── HandlerTimeoutError
├── InputEventError (イベント関連)
│   ├── InvalidInputTypeError
│   └── InvalidParameterError
└── FallbackError (フォールバック関連)
    ├── FallbackNotSetError
    └── FallbackExecutionError
```