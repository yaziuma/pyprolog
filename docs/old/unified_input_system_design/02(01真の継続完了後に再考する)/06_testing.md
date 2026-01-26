# テスト設計

## 6.1 単体テスト設計

### 6.1.1 コンポーネント別テスト

**InputEvent テスト:**
```python
import pytest
from pyprolog.runtime.unified_input_system import InputEvent, InputType
import time

class TestInputEvent:
    def test_event_creation(self):
        """InputEvent 基本生成テスト"""
        event = InputEvent(
            input_type=InputType.CHAR,
            predicate_name="get_char",
            timestamp=time.time()
        )
        
        assert event.input_type == InputType.CHAR
        assert event.predicate_name == "get_char"
        assert event.timestamp > 0
        assert event.request_id is not None
    
    def test_event_with_args(self):
        """引数付きInputEvent テスト"""
        args = {"prompt": "Enter char:", "timeout": 30}
        context = {"user": "test_user"}
        
        event = InputEvent(
            input_type=InputType.LINE,
            predicate_name="read_line",
            timestamp=time.time(),
            args=args,
            context=context
        )
        
        assert event.get_arg("prompt") == "Enter char:"
        assert event.get_arg("timeout") == 30
        assert event.get_arg("missing", "default") == "default"
        assert event.has_arg("prompt") is True
        assert event.has_arg("missing") is False
    
    def test_event_immutability(self):
        """InputEvent 不変性テスト"""
        event = InputEvent(
            input_type=InputType.CHAR,
            predicate_name="get_char",
            timestamp=time.time()
        )
        
        # frozen=True によりAttributeError が発生するはず
        with pytest.raises(AttributeError):
            event.input_type = "modified"
    
    def test_display_name(self):
        """表示名生成テスト"""
        event = InputEvent(
            input_type=InputType.LINE,
            predicate_name="read_line",
            timestamp=time.time()
        )
        
        assert event.get_display_name() == "read_line(line)"
    
    def test_age_calculation(self):
        """経過時間計算テスト"""
        past_time = time.time() - 5.0
        event = InputEvent(
            input_type=InputType.CHAR,
            predicate_name="get_char",
            timestamp=past_time
        )
        
        age = event.get_age_seconds()
        assert 4.5 <= age <= 5.5  # 約5秒（若干の誤差許容）
```

**InputHandler テスト:**
```python
class TestInputHandler:
    def test_abstract_handler(self):
        """抽象基底クラステスト"""
        from pyprolog.runtime.unified_input_system import InputHandler
        
        # 抽象クラスは直接インスタンス化できない
        with pytest.raises(TypeError):
            InputHandler()
    
    def test_concrete_handler_implementation(self):
        """具象ハンドラ実装テスト"""
        class TestHandler(InputHandler):
            def handle_input_request(self, event):
                if event.input_type == "char":
                    return "a"
                elif event.input_type == "line":
                    return "test line"
                return None
        
        handler = TestHandler()
        
        # 文字入力テスト
        char_event = InputEvent("char", "get_char", time.time())
        assert handler.handle_input_request(char_event) == "a"
        
        # 行入力テスト
        line_event = InputEvent("line", "read_line", time.time())
        assert handler.handle_input_request(line_event) == "test line"
        
        # 未サポートタイプテスト
        unknown_event = InputEvent("unknown", "unknown_pred", time.time())
        assert handler.handle_input_request(unknown_event) is None
```

**UnifiedInputSystem テスト:**
```python
class TestUnifiedInputSystem:
    def setup_method(self):
        """テストメソッド前の初期化"""
        from pyprolog.runtime.unified_input_system import UnifiedInputSystem
        self.system = UnifiedInputSystem()
    
    def test_handler_management(self):
        """ハンドラ管理機能テスト"""
        assert self.system.has_input_handler() is False
        
        # モックハンドラ設定
        mock_handler = MockInputHandler({"char:get_char": "x"})
        self.system.set_input_handler(mock_handler)
        
        assert self.system.has_input_handler() is True
        assert self.system.get_input_handler() is mock_handler
        
        # ハンドラクリア
        self.system.set_input_handler(None)
        assert self.system.has_input_handler() is False
    
    def test_request_input_with_handler(self):
        """ハンドラ経由の入力要求テスト"""
        mock_handler = MockInputHandler({
            "char:get_char": "a",
            "line:read_line": "hello"
        })
        self.system.set_input_handler(mock_handler)
        
        # 文字入力
        result = self.system.request_input("char", "get_char")
        assert result == "a"
        
        # 行入力
        result = self.system.request_input("line", "read_line")
        assert result == "hello"
        
        # 呼び出し履歴確認
        assert mock_handler.get_call_count() == 2
        assert mock_handler.get_call_count("char") == 1
        assert mock_handler.get_call_count("line") == 1
    
    def test_fallback_execution(self):
        """フォールバック実行テスト"""
        from pyprolog.runtime.io_streams import StringStream
        
        # フォールバックストリーム設定
        fallback_stream = StringStream("test\nline\n")
        self.system.set_fallback_stream(fallback_stream)
        
        # ハンドラ未設定でのフォールバック
        result = self.system.request_input("line", "read_line")
        assert result == "test"
        
        result = self.system.request_input("line", "read_line")
        assert result == "line"
```

### 6.1.2 モック・スタブ設計

**MockInputHandler:**
```python
class MockInputHandler(InputHandler):
    """テスト用モックハンドラ"""
    
    def __init__(self, responses: Dict[str, str] = None):
        self.responses = responses or {}
        self.call_history: List[InputEvent] = []
        self.call_count = 0
        self.last_event = None
    
    def handle_input_request(self, event: InputEvent) -> Optional[str]:
        self.call_history.append(event)
        self.call_count += 1
        self.last_event = event
        
        # キー生成: "input_type:predicate_name"
        key = f"{event.input_type}:{event.predicate_name}"
        return self.responses.get(key)
    
    def set_response(self, input_type: str, predicate_name: str, response: str):
        """動的レスポンス設定"""
        key = f"{input_type}:{predicate_name}"
        self.responses[key] = response
    
    def get_call_count(self, input_type: str = None) -> int:
        """呼び出し回数取得"""
        if input_type is None:
            return self.call_count
        return sum(1 for e in self.call_history if e.input_type == input_type)
    
    def get_last_event(self) -> Optional[InputEvent]:
        """最後のイベント取得"""
        return self.last_event
    
    def clear_history(self):
        """履歴クリア"""
        self.call_history.clear()
        self.call_count = 0
        self.last_event = None
```

**StubIOStream:**
```python
class StubIOStream(IOStream):
    """テスト用IOStreamスタブ"""
    
    def __init__(self, char_responses: List[str] = None, line_responses: List[str] = None):
        self.char_responses = char_responses or []
        self.line_responses = line_responses or []
        self.char_index = 0
        self.line_index = 0
    
    def read_char(self) -> str:
        if self.char_index < len(self.char_responses):
            result = self.char_responses[self.char_index]
            self.char_index += 1
            return result
        return ""  # EOF
    
    def read_line(self) -> Optional[str]:
        if self.line_index < len(self.line_responses):
            result = self.line_responses[self.line_index]
            self.line_index += 1
            return result
        return None  # EOF
    
    def write_char(self, char: str) -> None:
        pass  # スタブなので何もしない
    
    def read_term(self):
        raise NotImplementedError
    
    def write_term(self, term):
        raise NotImplementedError
```

**TestFixtures:**
```python
@pytest.fixture
def mock_runtime():
    """テスト用Runtimeフィクスチャ"""
    from pyprolog.runtime.interpreter import Runtime
    return Runtime()

@pytest.fixture
def mock_input_handler():
    """テスト用InputHandlerフィクスチャ"""
    return MockInputHandler({
        "char:get_char": "a",
        "line:read_line": "test input",
        "char:peek_char": "p"
    })

@pytest.fixture
def stub_io_stream():
    """テスト用IOStreamフィクスチャ"""
    return StubIOStream(
        char_responses=["a", "b", "c"],
        line_responses=["line1", "line2", "line3"]
    )

@pytest.fixture
def unified_system():
    """テスト用UnifiedInputSystemフィクスチャ"""
    from pyprolog.runtime.unified_input_system import UnifiedInputSystem
    return UnifiedInputSystem()
```

### 6.1.3 カバレッジ要件

**カバレッジ目標:**
- コード行カバレッジ: 90%以上
- ブランチカバレッジ: 85%以上
- 関数カバレッジ: 95%以上

**カバレッジ測定:**
```bash
# カバレッジ測定実行
uvx pytest --cov=pyprolog.runtime.unified_input_system tests/

# 詳細レポート生成
uvx pytest --cov=pyprolog.runtime.unified_input_system --cov-report=html tests/

# ブランチカバレッジ測定
uvx pytest --cov=pyprolog.runtime.unified_input_system --cov-branch tests/
```

**カバレッジ対象外の除外:**
```python
# .coveragerc設定例
[run]
source = pyprolog.runtime.unified_input_system
omit = 
    */tests/*
    */test_*.py
    */__init__.py

[report]
exclude_lines =
    pragma: no cover
    def __repr__
    raise AssertionError
    raise NotImplementedError
    if __name__ == .__main__.:
```

## 6.2 統合テスト設計

### 6.2.1 コンポーネント間連携テスト

**Runtime ↔ IOManager ↔ UnifiedInputSystem 連携:**
```python
class TestInputSystemIntegration:
    def test_end_to_end_char_input(self):
        """文字入力エンドツーエンドテスト"""
        from pyprolog.runtime.interpreter import Runtime
        
        # Runtime 作成
        runtime = Runtime()
        
        # モックハンドラ設定
        mock_handler = MockInputHandler({"char:get_char": "x"})
        runtime.io_manager.set_input_handler(mock_handler)
        
        # Prolog クエリ実行
        results = runtime.query("get_char(C).")
        
        # 結果検証
        assert len(results) == 1
        assert results[0]["C"] == "x"
        
        # ハンドラ呼び出し確認
        assert mock_handler.get_call_count() == 1
        last_event = mock_handler.get_last_event()
        assert last_event.input_type == "char"
        assert last_event.predicate_name == "get_char"
    
    def test_end_to_end_line_input(self):
        """行入力エンドツーエンドテスト"""
        runtime = Runtime()
        
        mock_handler = MockInputHandler({"line:read_line": "hello world"})
        runtime.io_manager.set_input_handler(mock_handler)
        
        results = runtime.query("read_line(L).")
        
        assert len(results) == 1
        assert results[0]["L"] == "hello world"
    
    def test_fallback_integration(self):
        """フォールバック連携テスト"""
        from pyprolog.runtime.io_streams import StringStream
        
        runtime = Runtime()
        
        # フォールバックストリーム設定（ハンドラは未設定）
        fallback_stream = StringStream("fallback\n")
        runtime.io_manager.set_input_stream(fallback_stream)
        
        results = runtime.query("read_line(L).")
        
        assert len(results) == 1
        assert results[0]["L"] == "fallback"
    
    def test_handler_failure_fallback(self):
        """ハンドラ失敗時のフォールバック動作テスト"""
        from pyprolog.runtime.io_streams import StringStream
        
        runtime = Runtime()
        
        # 例外発生ハンドラ
        class FailingHandler(InputHandler):
            def handle_input_request(self, event):
                raise Exception("Handler failed")
        
        # フォールバック設定
        fallback_stream = StringStream("fallback_result\n")
        runtime.io_manager.set_input_handler(FailingHandler())
        runtime.io_manager.set_input_stream(fallback_stream)
        
        results = runtime.query("read_line(L).")
        
        assert len(results) == 1
        assert results[0]["L"] == "fallback_result"
```

### 6.2.2 エンドツーエンドテスト

**複数述語統合テスト:**
```python
class TestMultiplePredicatesIntegration:
    def test_mixed_input_types(self):
        """複数入力タイプの混在テスト"""
        runtime = Runtime()
        
        # 複数レスポンス設定
        mock_handler = MockInputHandler({
            "char:get_char": "a",
            "line:read_line": "test line",
            "char:get_char": "b"  # 2回目の文字入力
        })
        runtime.io_manager.set_input_handler(mock_handler)
        
        # 複合Prologプログラム
        program = """
        test_input_sequence(C1, L, C2) :-
            get_char(C1),
            read_line(L), 
            get_char(C2).
        """
        runtime.consult_string(program)
        
        results = runtime.query("test_input_sequence(C1, L, C2).")
        
        assert len(results) == 1
        result = results[0]
        assert result["C1"] == "a"
        assert result["L"] == "test line"
        # 注意: 同じキーのため最後の値が適用される
        assert result["C2"] == "b"
    
    def test_input_with_prolog_logic(self):
        """Prologロジックと統合した入力テスト"""
        runtime = Runtime()
        
        # 数値文字列の自動変換テスト
        mock_handler = MockInputHandler({
            "line:read_line": "42"  # 数値文字列
        })
        runtime.io_manager.set_input_handler(mock_handler)
        
        program = """
        read_and_calculate(Result) :-
            read_line(X),
            Result is X + 10.
        """
        runtime.consult_string(program)
        
        results = runtime.query("read_and_calculate(R).")
        
        assert len(results) == 1
        assert results[0]["R"] == 52  # 42 + 10
```

### 6.2.3 互換性テスト

**レガシーAPI互換性テスト:**
```python
class TestLegacyCompatibility:
    def test_legacy_io_stream_usage(self):
        """従来のIOStream使用パターンテスト"""
        from pyprolog.runtime.io_streams import StringStream
        
        runtime = Runtime()
        
        # 従来方式: IOStream直接設定
        input_stream = StringStream("legacy_char\nlegacy_line\n")
        runtime.io_manager.set_input_stream(input_stream)
        
        # レガシーメソッド経由での入力
        char_result = runtime.io_manager.read_char_from_current()
        assert char_result == "l"  # "legacy_char" の最初の文字
        
        line_result = runtime.io_manager.read_line_from_current()
        assert line_result == "egacy_char"  # 残りの文字
    
    def test_legacy_predicate_execution(self):
        """レガシー述語実行の互換性テスト"""
        from pyprolog.runtime.io_streams import StringStream
        
        runtime = Runtime()
        
        # 従来方式でストリーム設定
        input_stream = StringStream("x\nhello\n")
        runtime.io_manager.set_input_stream(input_stream)
        
        # 述語は統一入力システム経由で処理されるが、
        # フォールバックとして従来ストリームが使用される
        char_results = runtime.query("get_char(C).")
        line_results = runtime.query("read_line(L).")
        
        assert len(char_results) == 1
        assert char_results[0]["C"] == "x"
        
        assert len(line_results) == 1
        assert line_results[0]["L"] == "hello"
    
    def test_migration_path(self):
        """移行パステスト"""
        from pyprolog.runtime.io_streams import StringStream
        
        runtime = Runtime()
        
        # ステップ1: 従来方式（フォールバック使用）
        legacy_stream = StringStream("step1\n")
        runtime.io_manager.set_input_stream(legacy_stream)
        
        result1 = runtime.query("read_line(L).")
        assert result1[0]["L"] == "step1"
        
        # ステップ2: 統一ハンドラ導入
        mock_handler = MockInputHandler({"line:read_line": "step2"})
        runtime.io_manager.set_input_handler(mock_handler)
        
        result2 = runtime.query("read_line(L).")
        assert result2[0]["L"] == "step2"
        
        # ステップ3: ハンドラ削除でフォールバック復帰
        runtime.io_manager.set_input_handler(None)
        # 新しいフォールバックストリーム設定
        new_stream = StringStream("step3\n")
        runtime.io_manager.set_input_stream(new_stream)
        
        result3 = runtime.query("read_line(L).")
        assert result3[0]["L"] == "step3"
```

**パフォーマンス互換性テスト:**
```python
class TestPerformanceCompatibility:
    def test_overhead_measurement(self):
        """統一入力システムのオーバーヘッド測定"""
        import time
        from pyprolog.runtime.io_streams import StringStream
        
        runtime = Runtime()
        
        # 大量の入力データ準備
        large_input = "test\n" * 1000
        
        # 従来方式での測定
        legacy_stream = StringStream(large_input)
        runtime.io_manager.set_input_stream(legacy_stream)
        
        start_time = time.time()
        for _ in range(100):
            runtime.io_manager.read_line_from_current()
        legacy_time = time.time() - start_time
        
        # 統一入力システム方式での測定
        mock_handler = MockInputHandler({"line:legacy_read_line": "test"})
        runtime.io_manager.set_input_handler(mock_handler)
        
        start_time = time.time()
        for _ in range(100):
            runtime.io_manager.read_line_from_current()
        unified_time = time.time() - start_time
        
        # オーバーヘッドが許容範囲内（例：20%以内）であることを確認
        overhead_ratio = unified_time / legacy_time
        assert overhead_ratio < 1.2, f"Overhead too high: {overhead_ratio:.2f}"
```