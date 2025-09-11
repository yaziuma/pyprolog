# コアコンポーネント詳細設計

## 2.1 InputEvent クラス

### 2.1.1 クラス定義と属性

```python
@dataclass(frozen=True)
class InputEvent:
    """入力要求イベント（不変オブジェクト）"""
    
    # 必須属性
    input_type: str                    # 入力タイプ
    predicate_name: str               # 呼び出し元述語名
    timestamp: float                  # 生成時刻（Unix timestamp）
    
    # オプション属性
    args: Dict[str, Any] = field(default_factory=dict)  # 追加パラメータ
    context: Optional[Dict[str, Any]] = None             # 実行コンテキスト
    request_id: str = field(default_factory=lambda: str(uuid.uuid4()))  # 一意ID
```

### 2.1.2 メソッド仕様

```python
class InputEvent:
    def get_display_name(self) -> str:
        """表示用名称を取得"""
        return f"{self.predicate_name}({self.input_type})"
    
    def get_age_seconds(self) -> float:
        """イベント生成からの経過時間（秒）"""
        return time.time() - self.timestamp
    
    def has_arg(self, key: str) -> bool:
        """指定されたパラメータの存在確認"""
        return key in self.args
    
    def get_arg(self, key: str, default=None) -> Any:
        """パラメータ値の取得"""
        return self.args.get(key, default)
    
    def to_dict(self) -> Dict[str, Any]:
        """辞書形式への変換（ログ出力用）"""
        return asdict(self)
```

### 2.1.3 イベントタイプ定義

```python
class InputType:
    """標準入力タイプ定義"""
    CHAR = "char"           # 1文字入力
    LINE = "line"           # 1行入力  
    TERM = "term"           # Prolog項入力
    NUMBER = "number"       # 数値入力
    
    # 拡張用
    CUSTOM_PREFIX = "custom_"  # カスタムタイプの接頭辞

# 入力タイプ検証
def validate_input_type(input_type: str) -> bool:
    """入力タイプの妥当性検証"""
    standard_types = {InputType.CHAR, InputType.LINE, InputType.TERM, InputType.NUMBER}
    return (input_type in standard_types or 
            input_type.startswith(InputType.CUSTOM_PREFIX))
```

### 2.1.4 コンテキスト情報設計

```python
class ExecutionContext:
    """実行コンテキスト情報"""
    
    @staticmethod
    def create_context() -> Dict[str, Any]:
        """現在の実行コンテキストを生成"""
        return {
            "thread_id": threading.get_ident(),
            "stack_depth": len(traceback.extract_stack()),
            "current_rule": None,  # 現在実行中のルール（将来拡張）
            "query_depth": 0,      # クエリのネスト深度（将来拡張）
        }
```

### 2.1.5 シリアライゼーション仕様

```python
class InputEventSerializer:
    """InputEvent のシリアライゼーション"""
    
    @staticmethod
    def to_json(event: InputEvent) -> str:
        """JSON文字列への変換"""
        data = asdict(event)
        return json.dumps(data, default=str, ensure_ascii=False)
    
    @staticmethod
    def from_json(json_str: str) -> InputEvent:
        """JSON文字列からの復元"""
        data = json.loads(json_str)
        return InputEvent(**data)
```

## 2.2 InputHandler インターフェース

### 2.2.1 抽象基底クラス定義

```python
from abc import ABC, abstractmethod

class InputHandler(ABC):
    """統一入力ハンドラインターフェース"""
    
    @abstractmethod
    def handle_input_request(self, event: InputEvent) -> Optional[str]:
        """
        入力要求の処理
        
        Args:
            event: 入力要求イベント
            
        Returns:
            入力値（文字列）、またはNone（EOF）
            
        Raises:
            InputHandlerError: 処理エラー時
        """
        pass
    
    def get_handler_info(self) -> Dict[str, Any]:
        """ハンドラ情報の取得（オプション）"""
        return {
            "handler_type": self.__class__.__name__,
            "supported_types": self.get_supported_input_types(),
        }
    
    def get_supported_input_types(self) -> Set[str]:
        """サポートする入力タイプ一覧（オプション）"""
        return {InputType.CHAR, InputType.LINE}  # デフォルト
```

### 2.2.2 メソッドシグネチャ仕様

```python
# 戻り値の型と意味
ReturnType = Optional[str]

# 戻り値の解釈
None        # EOF到達
""          # 空文字列入力
"valid"     # 通常の入力値
```

### 2.2.3 戻り値規約

**文字入力 (input_type="char")**
```python
"a"         # 1文字
"1"         # 数字文字
" "         # 空白文字
None        # EOF
```

**行入力 (input_type="line")**
```python
"hello"     # 通常の行
""          # 空行
None        # EOF
```

### 2.2.4 例外処理規約

```python
class InputHandlerError(Exception):
    """ハンドラ関連エラーの基底クラス"""
    def __init__(self, message: str, event: InputEvent, cause: Exception = None):
        super().__init__(message)
        self.event = event
        self.cause = cause

# 利用者が発生させるべき例外
class InputTimeoutError(InputHandlerError):
    """入力タイムアウトエラー"""
    pass

class InputCancelledError(InputHandlerError):
    """入力キャンセルエラー"""
    pass

class InputSourceError(InputHandlerError):
    """入力ソースエラー（ネットワーク、ファイル等）"""
    pass
```

### 2.2.5 ライフサイクル管理

```python
class InputHandler(ABC):
    def initialize(self) -> None:
        """ハンドラ初期化（オプション）"""
        pass
    
    def cleanup(self) -> None:
        """ハンドラ終了処理（オプション）"""
        pass
    
    def __enter__(self):
        self.initialize()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.cleanup()
```

## 2.3 UnifiedInputSystem クラス

### 2.3.1 クラス設計と責務

```python
class UnifiedInputSystem:
    """統一入力システム - 入力要求の中央制御"""
    
    def __init__(self):
        # ハンドラ管理
        self._handler_lock = threading.RLock()
        self._handler: Optional[InputHandler] = None
        
        # フォールバック管理
        self._fallback_stream: Optional[IOStream] = None
        
        # 監視・ログ
        self._logger = logging.getLogger(__name__ + ".UnifiedInputSystem")
        self._event_history: List[InputEvent] = []
        self._max_history = 100
```

### 2.3.2 コンストラクタ仕様

```python
def __init__(self, 
             default_handler: Optional[InputHandler] = None,
             fallback_stream: Optional[IOStream] = None,
             enable_history: bool = True,
             max_history: int = 100):
    """
    Args:
        default_handler: デフォルトハンドラ
        fallback_stream: フォールバックストリーム
        enable_history: イベント履歴の有効化
        max_history: 履歴保持件数
    """
```

### 2.3.3 request_input() メソッド詳細

```python
def request_input(self, input_type: str, predicate_name: str, **kwargs) -> Optional[str]:
    """
    統一入力要求処理
    
    Args:
        input_type: 入力タイプ
        predicate_name: 呼び出し元述語名
        **kwargs: 追加パラメータ
        
    Returns:
        入力値、またはNone（EOF）
        
    Raises:
        InputSystemError: システムエラー
    """
    # 1. イベント生成
    event = self._create_event(input_type, predicate_name, kwargs)
    
    # 2. 履歴記録
    self._record_event(event)
    
    # 3. ハンドラ実行
    try:
        result = self._execute_handler(event)
        if result is not None:
            return result
    except Exception as e:
        self._logger.warning(f"Handler failed: {e}")
    
    # 4. フォールバック実行
    return self._execute_fallback(event)
```

### 2.3.4 ハンドラ管理機能

```python
def set_input_handler(self, handler: Optional[InputHandler]) -> None:
    """入力ハンドラの設定"""
    with self._handler_lock:
        if self._handler:
            self._handler.cleanup()
        
        self._handler = handler
        
        if handler:
            handler.initialize()

def get_input_handler(self) -> Optional[InputHandler]:
    """現在のハンドラ取得"""
    with self._handler_lock:
        return self._handler

def has_input_handler(self) -> bool:
    """ハンドラ設定状況の確認"""
    with self._handler_lock:
        return self._handler is not None
```

### 2.3.5 フォールバック機構

```python
def _execute_fallback(self, event: InputEvent) -> Optional[str]:
    """フォールバック入力実行"""
    if not self._fallback_stream:
        raise FallbackNotSetError("No fallback stream configured")
    
    try:
        if event.input_type == InputType.CHAR:
            return self._fallback_stream.read_char()
        elif event.input_type == InputType.LINE:
            return self._fallback_stream.read_line()
        else:
            raise UnsupportedInputTypeError(f"Fallback doesn't support: {event.input_type}")
    
    except Exception as e:
        raise FallbackExecutionError(f"Fallback failed: {e}", event, e)
```

### 2.3.6 キャッシュ・バッファリング

```python
class InputCache:
    """入力結果のキャッシュ（将来拡張用）"""
    
    def __init__(self, max_size: int = 50):
        self._cache: Dict[str, str] = {}
        self._max_size = max_size
    
    def get_cache_key(self, event: InputEvent) -> str:
        """キャッシュキー生成"""
        return f"{event.input_type}:{event.predicate_name}"
    
    def get(self, event: InputEvent) -> Optional[str]:
        """キャッシュから取得"""
        key = self.get_cache_key(event)
        return self._cache.get(key)
    
    def put(self, event: InputEvent, value: str) -> None:
        """キャッシュに保存"""
        if len(self._cache) >= self._max_size:
            # LRU削除（簡易実装）
            oldest_key = next(iter(self._cache))
            del self._cache[oldest_key]
        
        key = self.get_cache_key(event)
        self._cache[key] = value
```

### 2.3.7 ログ・監視機能

```python
def _record_event(self, event: InputEvent) -> None:
    """イベント履歴記録"""
    if not self._enable_history:
        return
    
    self._event_history.append(event)
    
    # 履歴サイズ制限
    if len(self._event_history) > self._max_history:
        self._event_history.pop(0)

def get_event_history(self, limit: int = None) -> List[InputEvent]:
    """イベント履歴取得"""
    if limit is None:
        return self._event_history.copy()
    return self._event_history[-limit:]

def get_statistics(self) -> Dict[str, Any]:
    """統計情報取得"""
    total_events = len(self._event_history)
    type_counts = {}
    predicate_counts = {}
    
    for event in self._event_history:
        type_counts[event.input_type] = type_counts.get(event.input_type, 0) + 1
        predicate_counts[event.predicate_name] = predicate_counts.get(event.predicate_name, 0) + 1
    
    return {
        "total_events": total_events,
        "input_type_distribution": type_counts,
        "predicate_distribution": predicate_counts,
        "handler_configured": self.has_input_handler(),
        "fallback_configured": self._fallback_stream is not None,
    }
```

## 2.4 IOManager クラス改修

### 2.4.1 既存構造と変更点

**改修前:**
```python
class IOManager:
    def __init__(self):
        self.current_input_stream: IOStream = ConsoleStream()
        self.current_output_stream: IOStream = ConsoleStream()
    
    def read_char_from_current(self) -> str:
        return self.current_input_stream.read_char()
    
    def read_line_from_current(self) -> Optional[str]:
        return self.current_input_stream.read_line()
```

**改修後:**
```python
class IOManager:
    def __init__(self):
        # 新システム
        self.unified_input = UnifiedInputSystem()
        
        # 出力系（変更なし）
        self.current_output_stream: IOStream = ConsoleStream()
        
        # 互換性維持
        self.current_input_stream: IOStream = ConsoleStream()
        self.unified_input.set_fallback_stream(self.current_input_stream)
```

### 2.4.2 統一入力システム統合

```python
# 新しい統一API
def request_input(self, input_type: str, predicate_name: str, **kwargs) -> Optional[str]:
    """統一入力要求API"""
    return self.unified_input.request_input(input_type, predicate_name, **kwargs)

def set_input_handler(self, handler: InputHandler) -> None:
    """統一入力ハンドラ設定"""
    self.unified_input.set_input_handler(handler)

def get_input_handler(self) -> Optional[InputHandler]:
    """現在のハンドラ取得"""
    return self.unified_input.get_input_handler()
```

### 2.4.3 互換性レイヤー設計

```python
# 従来API（互換性維持）
def read_char_from_current(self) -> str:
    """レガシー文字読み取りAPI"""
    result = self.request_input("char", "legacy_read_char")
    return result if result is not None else ""

def read_line_from_current(self) -> Optional[str]:
    """レガシー行読み取りAPI"""
    return self.request_input("line", "legacy_read_line")

def set_input_stream(self, stream: IOStream) -> None:
    """レガシーストリーム設定API"""
    self.current_input_stream = stream
    self.unified_input.set_fallback_stream(stream)

def get_input_stream(self) -> IOStream:
    """レガシーストリーム取得API"""
    return self.current_input_stream
```

### 2.4.4 レガシーメソッド維持

```python
class IOManager:
    """
    互換性のため、既存のpublicメソッドはすべて維持
    内部実装のみ統一入力システムを使用するよう変更
    """
    
    # すべての既存パブリックメソッドを維持
    # 非推奨化は将来のバージョンで段階的に実施
```

### 2.4.5 設定管理機能

```python
def configure_input_system(self, config: Dict[str, Any]) -> None:
    """統一入力システムの設定"""
    if "handler" in config:
        self.set_input_handler(config["handler"])
    
    if "fallback_stream" in config:
        self.unified_input.set_fallback_stream(config["fallback_stream"])
    
    if "enable_history" in config:
        self.unified_input._enable_history = config["enable_history"]

def get_input_system_status(self) -> Dict[str, Any]:
    """入力システム状態取得"""
    return {
        "unified_system": self.unified_input.get_statistics(),
        "fallback_stream": type(self.current_input_stream).__name__,
        "legacy_mode": not self.unified_input.has_input_handler(),
    }
```