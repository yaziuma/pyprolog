# API設計仕様

## 4.1 利用者向けAPI

### 4.1.1 基本利用パターン

**パターン1: 既存コード（修正不要）**
```python
# 完全に無修正で動作
from pyprolog.runtime.interpreter import Runtime

runtime = Runtime()
results = runtime.query("get_char(X).")
print(results)  # [{'X': 'a'}] など
```

**パターン2: 統一ハンドラ設定**
```python
from pyprolog.runtime.interpreter import Runtime
from pyprolog.runtime.unified_input_system import InputHandler, InputEvent

class SimpleInputHandler(InputHandler):
    def handle_input_request(self, event: InputEvent) -> Optional[str]:
        if event.input_type == "char":
            return "a"  # 固定文字返却
        elif event.input_type == "line":
            return "hello world"  # 固定行返却
        return None  # EOF

runtime = Runtime()
runtime.io_manager.set_input_handler(SimpleInputHandler())

# 全ての入力述語が統一ハンドラ経由で処理される
results1 = runtime.query("get_char(X).")      # X = "a"
results2 = runtime.query("read_line(Y).")     # Y = "hello world"
```

**パターン3: GUI統合**
```python
import tkinter as tk
from tkinter import simpledialog

class GUIInputHandler(InputHandler):
    def __init__(self, parent_window):
        self.parent = parent_window
    
    def handle_input_request(self, event: InputEvent) -> Optional[str]:
        if event.input_type == "char":
            result = simpledialog.askstring(
                "文字入力", 
                "1文字入力してください:",
                parent=self.parent
            )
            return result[0] if result else None
        
        elif event.input_type == "line":
            return simpledialog.askstring(
                "行入力",
                "1行入力してください:",
                parent=self.parent
            )
        
        return None

# GUI アプリケーションでの使用
root = tk.Tk()
handler = GUIInputHandler(root)

runtime = Runtime()
runtime.io_manager.set_input_handler(handler)
```

### 4.1.2 InputHandler実装ガイド

**基本テンプレート:**
```python
from pyprolog.runtime.unified_input_system import InputHandler, InputEvent
from typing import Optional

class CustomInputHandler(InputHandler):
    def __init__(self):
        # 初期化処理
        self.input_sources = {}
    
    def handle_input_request(self, event: InputEvent) -> Optional[str]:
        """
        必須実装メソッド
        
        Args:
            event: 入力要求イベント
            
        Returns:
            入力値（文字列）またはNone（EOF）
        """
        try:
            # 入力タイプ別処理
            if event.input_type == "char":
                return self._handle_char_input(event)
            elif event.input_type == "line":
                return self._handle_line_input(event)
            else:
                # 未対応タイプ
                return None
        
        except Exception as e:
            # エラー時の処理
            self._log_error(f"Input failed: {e}")
            return None
    
    def _handle_char_input(self, event: InputEvent) -> Optional[str]:
        """文字入力処理の実装例"""
        # 実装する
        pass
    
    def _handle_line_input(self, event: InputEvent) -> Optional[str]:
        """行入力処理の実装例"""
        # 実装する
        pass
    
    def _log_error(self, message: str):
        """エラーログ処理"""
        print(f"[ERROR] {message}")
```

**高度なテンプレート:**
```python
class AdvancedInputHandler(InputHandler):
    def __init__(self):
        self.config = {}
        self.state = {}
    
    def handle_input_request(self, event: InputEvent) -> Optional[str]:
        # パラメータ解析
        prompt = event.get_arg("prompt", "入力: ")
        timeout = event.get_arg("timeout_seconds", 30)
        default = event.get_arg("default_value")
        
        # コンテキスト情報活用
        if event.context:
            user_id = event.context.get("user_id")
            session = event.context.get("session")
        
        # 入力タイプ別処理
        handler_method = getattr(
            self, 
            f"_handle_{event.input_type}_input", 
            self._handle_unknown_input
        )
        
        return handler_method(event, prompt, timeout, default)
    
    def _handle_char_input(self, event, prompt, timeout, default):
        # 文字入力の詳細実装
        pass
    
    def _handle_line_input(self, event, prompt, timeout, default):
        # 行入力の詳細実装
        pass
    
    def _handle_password_input(self, event, prompt, timeout, default):
        # パスワード入力の実装
        pass
    
    def _handle_unknown_input(self, event, prompt, timeout, default):
        # 未知の入力タイプに対する処理
        return None
    
    def get_supported_input_types(self):
        """サポート入力タイプの明示"""
        return {"char", "line", "password", "multiline"}
```

### 4.1.3 設定・カスタマイズAPI

**システム設定:**
```python
# 統一入力ハンドラ設定
runtime.io_manager.set_input_handler(my_handler)

# フォールバックストリーム設定
from pyprolog.runtime.io_streams import StringStream
fallback = StringStream("default input\n")
runtime.io_manager.set_input_stream(fallback)

# 設定組み合わせ
runtime.io_manager.configure_input_system({
    "handler": my_handler,
    "fallback_stream": fallback,
    "enable_history": True,
    "max_history": 200
})
```

**ハンドラ切り替え:**
```python
# 実行時ハンドラ切り替え
runtime.io_manager.set_input_handler(gui_handler)
results1 = runtime.query("get_char(X).")  # GUI経由

runtime.io_manager.set_input_handler(console_handler)
results2 = runtime.query("get_char(Y).")  # コンソール経由

runtime.io_manager.set_input_handler(None)
results3 = runtime.query("get_char(Z).")  # フォールバック使用
```

### 4.1.4 デバッグ・監視API

**ステータス確認:**
```python
# 入力システム状態確認
status = runtime.io_manager.get_input_system_status()
print(f"Handler configured: {status['unified_system']['handler_configured']}")
print(f"Total events: {status['unified_system']['total_events']}")

# イベント履歴取得
history = runtime.io_manager.unified_input.get_event_history(limit=10)
for event in history:
    print(f"{event.timestamp}: {event.get_display_name()}")

# 統計情報取得
stats = runtime.io_manager.unified_input.get_statistics()
print(f"Input type distribution: {stats['input_type_distribution']}")
```

**デバッグハンドラ:**
```python
from pyprolog.runtime.unified_input_system import DebugInputHandler

# 既存ハンドラをデバッグラップ
original_handler = MyInputHandler()
debug_handler = DebugInputHandler(original_handler, debug_level=2)
runtime.io_manager.set_input_handler(debug_handler)

# ログ出力有効化
import logging
logging.basicConfig(level=logging.DEBUG)
```

## 4.2 内部API

### 4.2.1 コンポーネント間通信API

**IOManager → UnifiedInputSystem:**
```python
class IOManager:
    def request_input(self, input_type: str, predicate_name: str, **kwargs) -> Optional[str]:
        """内部通信API"""
        return self.unified_input.request_input(input_type, predicate_name, **kwargs)
```

**UnifiedInputSystem → InputHandler:**
```python
class UnifiedInputSystem:
    def _execute_handler(self, event: InputEvent) -> Optional[str]:
        """内部ハンドラ実行API"""
        with self._handler_lock:
            current_handler = self._handler
        
        if current_handler:
            return current_handler.handle_input_request(event)
        return None
```

### 4.2.2 拡張ポイントAPI

**カスタム入力タイプ登録:**
```python
class InputTypeRegistry:
    """入力タイプ登録管理"""
    
    _custom_types: Set[str] = set()
    
    @classmethod
    def register_input_type(cls, input_type: str, description: str = ""):
        """カスタム入力タイプ登録"""
        if not input_type.startswith("custom_"):
            raise ValueError("Custom input types must start with 'custom_'")
        
        cls._custom_types.add(input_type)
    
    @classmethod
    def is_registered_type(cls, input_type: str) -> bool:
        """登録済みタイプの確認"""
        return input_type in cls._custom_types
```

**イベントミドルウェア:**
```python
class InputEventMiddleware:
    """入力イベントの前処理・後処理"""
    
    def before_request(self, event: InputEvent) -> InputEvent:
        """要求前処理（イベント変更可能）"""
        return event
    
    def after_request(self, event: InputEvent, result: Optional[str]) -> Optional[str]:
        """要求後処理（結果変更可能）"""
        return result

class UnifiedInputSystem:
    def __init__(self):
        self.middlewares: List[InputEventMiddleware] = []
    
    def add_middleware(self, middleware: InputEventMiddleware):
        """ミドルウェア追加"""
        self.middlewares.append(middleware)
```

### 4.2.3 テスト支援API

**モックハンドラ:**
```python
class MockInputHandler(InputHandler):
    """テスト用モックハンドラ"""
    
    def __init__(self, responses: Dict[str, str]):
        self.responses = responses
        self.call_history: List[InputEvent] = []
    
    def handle_input_request(self, event: InputEvent) -> Optional[str]:
        self.call_history.append(event)
        
        key = f"{event.input_type}:{event.predicate_name}"
        return self.responses.get(key)
    
    def get_call_count(self, input_type: str = None) -> int:
        """呼び出し回数取得"""
        if input_type is None:
            return len(self.call_history)
        return sum(1 for e in self.call_history if e.input_type == input_type)

# 使用例
mock_handler = MockInputHandler({
    "char:get_char": "a",
    "line:read_line": "test input"
})

runtime.io_manager.set_input_handler(mock_handler)
runtime.query("get_char(X).")

assert mock_handler.get_call_count("char") == 1
```

**テストヘルパー:**
```python
class InputSystemTestHelper:
    """入力システムテスト支援"""
    
    def __init__(self, runtime: Runtime):
        self.runtime = runtime
        self.original_handler = None
    
    def setup_mock_inputs(self, inputs: Dict[str, str]):
        """モック入力設定"""
        self.original_handler = self.runtime.io_manager.get_input_handler()
        mock_handler = MockInputHandler(inputs)
        self.runtime.io_manager.set_input_handler(mock_handler)
        return mock_handler
    
    def teardown(self):
        """テスト後片付け"""
        self.runtime.io_manager.set_input_handler(self.original_handler)
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.teardown()

# 使用例
with InputSystemTestHelper(runtime) as helper:
    mock = helper.setup_mock_inputs({
        "char:get_char": "x",
        "line:read_line": "hello"
    })
    
    result = runtime.query("get_char(C), read_line(L).")
    assert result[0]["C"] == "x"
    assert result[0]["L"] == "hello"
    assert mock.get_call_count() == 2
```

## 4.3 互換性API

### 4.3.1 レガシーAPI維持仕様

**IOManager レガシーメソッド:**
```python
class IOManager:
    # すべて維持（非推奨化は将来実施）
    
    def read_char_from_current(self) -> str:
        """レガシー: 文字読み取り"""
        result = self.request_input("char", "legacy_read_char")
        return result if result is not None else ""
    
    def read_line_from_current(self) -> Optional[str]:
        """レガシー: 行読み取り"""
        return self.request_input("line", "legacy_read_line")
    
    def set_input_stream(self, stream: IOStream) -> None:
        """レガシー: 入力ストリーム設定"""
        self.current_input_stream = stream
        self.unified_input.set_fallback_stream(stream)
    
    def get_input_stream(self) -> IOStream:
        """レガシー: 入力ストリーム取得"""
        return self.current_input_stream
```

**IOStream インターフェース:**
```python
# 既存のIOStreamインターフェースは完全維持
class IOStream(ABC):
    @abstractmethod
    def read_char(self) -> str: pass
    
    @abstractmethod
    def read_line(self) -> Optional[str]: pass
    
    # その他既存メソッドも完全維持
```

### 4.3.2 段階的移行支援

**移行支援API:**
```python
class MigrationHelper:
    """レガシーコードの段階的移行支援"""
    
    @staticmethod
    def wrap_legacy_stream(stream: IOStream) -> InputHandler:
        """既存IOStreamを統一ハンドラに変換"""
        class StreamWrapperHandler(InputHandler):
            def __init__(self, wrapped_stream: IOStream):
                self.stream = wrapped_stream
            
            def handle_input_request(self, event: InputEvent) -> Optional[str]:
                if event.input_type == "char":
                    return self.stream.read_char()
                elif event.input_type == "line":
                    return self.stream.read_line()
                return None
        
        return StreamWrapperHandler(stream)
    
    @staticmethod
    def create_compatibility_handler(old_functions: Dict[str, Callable]) -> InputHandler:
        """既存関数群を統一ハンドラに変換"""
        class CompatibilityHandler(InputHandler):
            def handle_input_request(self, event: InputEvent) -> Optional[str]:
                func = old_functions.get(event.input_type)
                if func:
                    return func(event)
                return None
        
        return CompatibilityHandler()

# 使用例
# 既存IOStreamの統一ハンドラ化
legacy_stream = StringStream("input data\n")
handler = MigrationHelper.wrap_legacy_stream(legacy_stream)
runtime.io_manager.set_input_handler(handler)

# 既存関数群の統一ハンドラ化
def my_char_input(event):
    return input("Enter char: ")

def my_line_input(event):
    return input("Enter line: ")

handler = MigrationHelper.create_compatibility_handler({
    "char": my_char_input,
    "line": my_line_input
})
```

### 4.3.3 非推奨化戦略

**段階的非推奨化:**
```python
import warnings

class IOManager:
    def read_char_from_current(self) -> str:
        # Phase 1: 警告なし（現在）
        # Phase 2: 非推奨警告（バージョン1.0）
        # Phase 3: 削除（バージョン2.0）
        
        # 将来実装予定:
        # warnings.warn(
        #     "read_char_from_current() is deprecated. Use request_input() instead.",
        #     DeprecationWarning,
        #     stacklevel=2
        # )
        
        result = self.request_input("char", "legacy_read_char")
        return result if result is not None else ""
```

**移行パス明確化:**
```python
class IOManager:
    def get_migration_info(self) -> Dict[str, str]:
        """API移行情報の提供"""
        return {
            "read_char_from_current": "Use request_input('char', 'your_predicate')",
            "read_line_from_current": "Use request_input('line', 'your_predicate')",
            "set_input_stream": "Use set_input_handler() with wrapped handler",
        }
```