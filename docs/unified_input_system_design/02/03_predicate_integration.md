# 入力述語統合設計

## 3.1 既存述語クラス改修仕様

### 3.1.1 GetCharPredicate 改修

**改修前:**
```python
class GetCharPredicate(BuiltinPredicate):
    def execute(self, runtime: "Runtime", env: BindingEnvironment) -> Iterator[BindingEnvironment]:
        # 直接IOStreamを呼び出し
        char_str = runtime.io_manager.read_char_from_current()
        
        # 処理ロジック...
```

**改修後:**
```python
class GetCharPredicate(BuiltinPredicate):
    def execute(self, runtime: "Runtime", env: BindingEnvironment) -> Iterator[BindingEnvironment]:
        # 統一入力システムを使用
        char_str = runtime.io_manager.request_input(
            input_type="char",
            predicate_name="get_char"
        )
        
        # 処理ロジックは変更なし
        target_term: PrologType
        if char_str == "" or char_str is None:
            target_term = Atom("end_of_file")
        elif len(char_str) == 1:
            if char_str.isdigit():
                target_term = Number(int(char_str))
            else:
                target_term = Atom(char_str)
        # ...
```

**変更点:**
- `read_char_from_current()` → `request_input("char", "get_char")`
- 処理ロジック、戻り値形式は完全に維持

### 3.1.2 ReadLinePredicate 改修

**改修前:**
```python
class ReadLinePredicate(BuiltinPredicate):
    def execute(self, runtime: "Runtime", env: BindingEnvironment) -> Iterator[BindingEnvironment]:
        line_str = runtime.io_manager.read_line_from_current()
        # 処理ロジック...
```

**改修後:**
```python
class ReadLinePredicate(BuiltinPredicate):
    def execute(self, runtime: "Runtime", env: BindingEnvironment) -> Iterator[BindingEnvironment]:
        line_str = runtime.io_manager.request_input(
            input_type="line",
            predicate_name="read_line"
        )
        
        # 処理ロジックは変更なし
        target_term: PrologType
        if line_str is None:
            target_term = Atom("end_of_file")
        else:
            # 数値変換試行
            number_value = try_convert_atom_to_number(line_str)
            if number_value is not None:
                target_term = Number(number_value)
            else:
                target_term = Atom(line_str)
        # ...
```

### 3.1.3 PeekCharPredicate 改修

**改修前:**
```python
class PeekCharPredicate(BuiltinPredicate):
    def execute(self, runtime: "Runtime", env: BindingEnvironment) -> Iterator[BindingEnvironment]:
        try:
            char_str = runtime.io_manager.current_input_stream.peek_char()
        except StreamOperationError:
            # フォールバック処理
```

**改修後:**
```python
class PeekCharPredicate(BuiltinPredicate):
    def execute(self, runtime: "Runtime", env: BindingEnvironment) -> Iterator[BindingEnvironment]:
        # peek操作は特殊なため、現在はフォールバックストリーム使用
        # 将来的には統一入力システムでpeek対応を検討
        try:
            char_str = runtime.io_manager.request_input(
                input_type="peek_char",
                predicate_name="peek_char"
            )
        except UnsupportedInputTypeError:
            # フォールバック: 従来のpeek_char()を使用
            char_str = runtime.io_manager.current_input_stream.peek_char()
        # ...
```

### 3.1.4 その他入力述語改修

**AtEndOfStreamPredicate:**
```python
class AtEndOfStreamPredicate(BuiltinPredicate):
    def execute(self, runtime: "Runtime", env: BindingEnvironment) -> Iterator[BindingEnvironment]:
        # EOF状態確認も統一入力システム経由
        try:
            result = runtime.io_manager.request_input(
                input_type="check_eof",
                predicate_name="at_end_of_stream"
            )
            is_eof = (result is None)
        except UnsupportedInputTypeError:
            # フォールバック
            is_eof = runtime.io_manager.current_input_stream.at_end_of_stream()
        
        if is_eof:
            yield env  # 成功
        # 失敗時は何も yield しない
```

## 3.2 新述語対応パターン

### 3.2.1 新述語追加手順

**ステップ1: 入力タイプ定義**
```python
# pyprolog/runtime/unified_input_system.py に追加
class InputType:
    # 既存
    CHAR = "char"
    LINE = "line"
    
    # 新規追加
    PASSWORD = "password"      # パスワード入力
    MULTILINE = "multiline"    # 複数行入力
    FILE_PATH = "file_path"    # ファイルパス入力
```

**ステップ2: 述語クラス実装**
```python
class ReadPasswordPredicate(BuiltinPredicate):
    """read_password/1 - パスワード入力述語"""
    
    def __init__(self, arg: "PrologType"):
        super().__init__(arg)
    
    def execute(self, runtime: "Runtime", env: BindingEnvironment) -> Iterator[BindingEnvironment]:
        # 統一入力システム使用
        password_str = runtime.io_manager.request_input(
            input_type="password",
            predicate_name="read_password",
            mask_char="*",          # パラメータ例
            min_length=4           # パラメータ例
        )
        
        # 標準的な処理パターン
        if password_str is None:
            target_term = Atom("end_of_file")
        else:
            target_term = Atom(password_str)
        
        # 統一化
        unified, final_env = runtime.logic_interpreter.unify(
            self.args[0], target_term, env
        )
        if unified:
            yield final_env
```

**ステップ3: ランタイム登録**
```python
# pyprolog/runtime/interpreter.py の __init__ に追加
from pyprolog.runtime.builtins import ReadPasswordPredicate

# 述語登録処理に追加
self._builtin_predicates["read_password"] = ReadPasswordPredicate
```

### 3.2.2 入力タイプ拡張方式

**標準タイプ拡張:**
```python
class InputType:
    # 基本タイプ
    CHAR = "char"
    LINE = "line"
    TERM = "term"
    
    # 数値系
    INTEGER = "integer"
    FLOAT = "float"
    
    # 文字列系
    PASSWORD = "password"
    MULTILINE = "multiline"
    
    # ファイル系
    FILE_PATH = "file_path"
    DIRECTORY_PATH = "directory_path"
    
    # 選択系
    MENU_CHOICE = "menu_choice"
    YES_NO = "yes_no"
```

**カスタムタイプ:**
```python
# 利用者定義カスタムタイプ
CUSTOM_JSON = "custom_json_input"
CUSTOM_XML = "custom_xml_input"

# カスタムタイプ検証
def is_custom_type(input_type: str) -> bool:
    return input_type.startswith("custom_")
```

### 3.2.3 パラメータ渡し規約

**基本パラメータ:**
```python
runtime.io_manager.request_input(
    input_type="password",
    predicate_name="read_password",
    
    # 表示系パラメータ
    prompt="パスワードを入力: ",
    title="認証",
    
    # 検証系パラメータ
    min_length=4,
    max_length=20,
    required=True,
    
    # 表示制御パラメータ
    mask_char="*",
    show_length=False,
    
    # タイムアウト系パラメータ
    timeout_seconds=30,
    
    # コンテキスト系パラメータ
    context={"user_id": "12345", "session": "abc"}
)
```

**パラメータ命名規約:**
- `prompt`: ユーザー向けプロンプト文字列
- `title`: ダイアログ等のタイトル
- `min_length`, `max_length`: 入力長制限
- `timeout_seconds`: タイムアウト時間
- `required`: 必須入力フラグ
- `default_value`: デフォルト値
- `validation_pattern`: 検証用正規表現
- `context`: 追加コンテキスト情報

## 3.3 述語実行フロー

### 3.3.1 従来フロー vs 新フロー

**従来フロー:**
```
1. GetCharPredicate.execute()
2. runtime.io_manager.read_char_from_current()
3. runtime.io_manager.current_input_stream.read_char()
4. ConsoleStream.read_char() または StringStream.read_char()
5. 結果返却
6. GetCharPredicate で処理・統一化
```

**新フロー:**
```
1. GetCharPredicate.execute()
2. runtime.io_manager.request_input("char", "get_char")
3. unified_input_system.request_input()
4. InputEvent 生成
5. input_handler.handle_input_request(event) 
   または fallback_stream.read_char()
6. 結果返却
7. GetCharPredicate で処理・統一化
```

**変更の影響:**
- GetCharPredicate の実装: 1行のみ変更
- 処理結果: 完全に同一
- パフォーマンス: 微小なオーバーヘッド（イベント生成）
- 機能性: 大幅な向上（柔軟な入力制御）

### 3.3.2 デバッグ・トレース対応

**イベントトレース:**
```python
class InputTracer:
    """入力イベントのトレース機能"""
    
    def __init__(self, enabled: bool = False):
        self.enabled = enabled
        self.traces: List[Dict[str, Any]] = []
    
    def trace_event(self, event: InputEvent, result: Optional[str], duration: float):
        """イベント実行のトレース記録"""
        if not self.enabled:
            return
        
        trace_entry = {
            "timestamp": event.timestamp,
            "event": event.to_dict(),
            "result": result,
            "duration_ms": duration * 1000,
            "success": result is not None,
        }
        self.traces.append(trace_entry)
    
    def get_trace_summary(self) -> Dict[str, Any]:
        """トレース要約取得"""
        if not self.traces:
            return {"total_events": 0}
        
        total = len(self.traces)
        successful = sum(1 for t in self.traces if t["success"])
        avg_duration = sum(t["duration_ms"] for t in self.traces) / total
        
        return {
            "total_events": total,
            "successful_events": successful,
            "success_rate": successful / total,
            "average_duration_ms": avg_duration,
            "input_types": list(set(t["event"]["input_type"] for t in self.traces)),
        }
```

**デバッグハンドラ:**
```python
class DebugInputHandler(InputHandler):
    """デバッグ用入力ハンドラ"""
    
    def __init__(self, base_handler: InputHandler, debug_level: int = 1):
        self.base_handler = base_handler
        self.debug_level = debug_level
        self.logger = logging.getLogger(__name__ + ".DebugInputHandler")
    
    def handle_input_request(self, event: InputEvent) -> Optional[str]:
        if self.debug_level >= 1:
            self.logger.info(f"INPUT REQUEST: {event.get_display_name()}")
        
        if self.debug_level >= 2:
            self.logger.debug(f"Event details: {event.to_dict()}")
        
        start_time = time.time()
        try:
            result = self.base_handler.handle_input_request(event)
            duration = time.time() - start_time
            
            if self.debug_level >= 1:
                self.logger.info(f"INPUT RESULT: {result} (took {duration:.3f}s)")
            
            return result
        
        except Exception as e:
            duration = time.time() - start_time
            self.logger.error(f"INPUT ERROR: {e} (after {duration:.3f}s)")
            raise
```

**利用例:**
```python
# デバッグ有効化
base_handler = MyInputHandler()
debug_handler = DebugInputHandler(base_handler, debug_level=2)
runtime.io_manager.set_input_handler(debug_handler)

# トレース有効化
tracer = InputTracer(enabled=True)
runtime.io_manager.unified_input.set_tracer(tracer)

# 実行後の分析
summary = tracer.get_trace_summary()
print(f"Success rate: {summary['success_rate']:.2%}")
print(f"Average duration: {summary['average_duration_ms']:.1f}ms")
```