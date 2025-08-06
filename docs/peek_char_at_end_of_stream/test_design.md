# PyProlog 非ブロッキング入力述語 テスト設計書

## 目次

1. [テスト戦略](#1-テスト戦略)
2. [単体テスト設計](#2-単体テスト設計)
3. [統合テスト設計](#3-統合テスト設計)
4. [パフォーマンステスト設計](#4-パフォーマンステスト設計)
5. [エラーケーステスト](#5-エラーケーステスト)
6. [互換性テスト](#6-互換性テスト)
7. [テストデータ設計](#7-テストデータ設計)

---

## 1. テスト戦略

### 1.1 テストピラミッド構成

```
                    E2E Tests
                   (10% - 20件)
                  /            \
            Integration Tests
           (30% - 60件)
          /                    \
    Unit Tests
   (60% - 120件)
```

**カバレッジ目標:**
- 行カバレッジ: 95%以上
- ブランチカバレッジ: 90%以上
- 機能カバレッジ: 100%

### 1.2 テストカテゴリ

**1. 機能テスト (Functional Tests)**
- peek_char/1の基本動作
- at_end_of_stream/0の基本動作
- ストリーム間の一貫性

**2. 非機能テスト (Non-Functional Tests)**
- パフォーマンス
- メモリ使用量
- 同時実行性

**3. 境界値テスト (Boundary Tests)**
- EOF境界
- バッファ境界
- 文字エンコーディング境界

**4. エラーテスト (Error Tests)**
- 例外処理
- 不正入力
- リソース不足

---

## 2. 単体テスト設計

### 2.1 StringStreamテスト

```python
class TestStringStream:
    """StringStreamのpeek機能テスト"""
    
    @pytest.fixture
    def stream(self):
        return StringStream("hello\nworld")
    
    def test_peek_char_basic(self, stream):
        """基本的なpeek_char動作"""
        # 最初の文字をpeek
        assert stream.peek_char() == "h"
        
        # 位置が変わらないことを確認
        assert stream.peek_char() == "h"
        
        # 実際に読み取った後
        assert stream.read_char() == "h"
        assert stream.peek_char() == "e"
    
    def test_peek_char_at_eof(self, stream):
        """EOF時のpeek_char動作"""
        # 全ての文字を読み取り
        while not stream.at_end_of_stream():
            stream.read_char()
        
        # EOF時のpeek
        assert stream.peek_char() == ""
        assert stream.at_end_of_stream() is True
    
    def test_peek_char_multibyte(self):
        """マルチバイト文字のpeek"""
        stream = StringStream("こんにちは")
        assert stream.peek_char() == "こ"
        assert stream.read_char() == "こ"
        assert stream.peek_char() == "ん"
    
    def test_at_end_of_stream_progression(self, stream):
        """at_end_of_streamの状態変化"""
        assert stream.at_end_of_stream() is False
        
        # 1文字ずつ読み取りながら確認
        while stream.peek_char():
            assert stream.at_end_of_stream() is False
            stream.read_char()
        
        assert stream.at_end_of_stream() is True
    
    def test_stream_status(self, stream):
        """ストリーム状態情報の取得"""
        status = stream.get_stream_status()
        
        assert status.at_eof is False
        assert status.has_data_available is True
        assert status.supports_peek is True
        assert status.stream_type == "StringStream"
        assert status.has_errors is False
```

### 2.2 BufferedConsoleStreamテスト

```python
class TestBufferedConsoleStream:
    """BufferedConsoleStreamのテスト"""
    
    @pytest.fixture
    def mock_stdin(self, monkeypatch):
        """stdinをモック化"""
        mock_data = io.StringIO("test input\n")
        monkeypatch.setattr('sys.stdin', mock_data)
        return mock_data
    
    @pytest.fixture
    def stream(self, mock_stdin):
        return BufferedConsoleStream(buffer_size=10)
    
    def test_peek_char_with_buffer_fill(self, stream, mock_stdin):
        """バッファ充填を伴うpeek操作"""
        # 最初はバッファが空
        # peek操作でバッファが充填される
        char = stream.peek_char()
        assert char == "t"
        
        # 同じ文字がもう一度取得できる
        char2 = stream.peek_char()
        assert char2 == "t"
    
    @pytest.mark.timeout(1)
    def test_peek_char_non_blocking(self, stream):
        """非ブロッキング動作の確認"""
        # 入力がない状態でのpeek（即座に返ること）
        start_time = time.time()
        char = stream.peek_char()
        end_time = time.time()
        
        # 100ms以内に返ること
        assert (end_time - start_time) < 0.1
        assert char == ""  # 入力なしでEOF
    
    def test_buffer_overflow_handling(self):
        """バッファオーバーフロー処理"""
        large_input = "a" * 2000  # バッファサイズを超える入力
        mock_stdin = io.StringIO(large_input)
        
        with patch('sys.stdin', mock_stdin):
            stream = BufferedConsoleStream(buffer_size=100)
            
            # バッファサイズ分だけ処理されること
            chars_read = 0
            while stream.peek_char() and chars_read < 150:
                stream.read_char()
                chars_read += 1
            
            assert chars_read == 100  # バッファサイズに制限される
```

### 2.3 PeekCharPredicateテスト

```python
class TestPeekCharPredicate:
    """PeekCharPredicate述語のテスト"""
    
    @pytest.fixture
    def runtime(self):
        runtime = Runtime()
        runtime.io_manager.set_input_stream(StringStream("abc"))
        return runtime
    
    def test_peek_char_unification_success(self, runtime):
        """peek_char/1の成功ケース"""
        solutions = runtime.query("peek_char(X)")
        
        assert len(solutions) == 1
        assert solutions[0][Variable("X")] == Atom("a")
        
        # 再度実行しても同じ結果
        solutions2 = runtime.query("peek_char(Y)")
        assert solutions2[0][Variable("Y")] == Atom("a")
    
    def test_peek_char_unification_failure(self, runtime):
        """peek_char/1の失敗ケース"""
        solutions = runtime.query("peek_char(z)")  # 'a'と'z'は一致しない
        
        assert len(solutions) == 0
    
    def test_peek_char_eof(self, runtime):
        """EOF時のpeek_char/1"""
        runtime.io_manager.set_input_stream(StringStream(""))
        solutions = runtime.query("peek_char(X)")
        
        assert len(solutions) == 1
        assert solutions[0][Variable("X")] == Atom("end_of_file")
    
    def test_peek_char_unsupported_stream(self, runtime):
        """サポートしないストリームでのエラー"""
        # 古いConsoleStreamをモック
        unsupported_stream = Mock()
        unsupported_stream.supports_peek_operations.return_value = False
        runtime.io_manager.set_input_stream(unsupported_stream)
        
        with pytest.raises(PrologError) as excinfo:
            runtime.query("peek_char(X)")
        
        assert "does not support peek_char" in str(excinfo.value)
    
    def test_peek_char_argument_validation(self):
        """引数検証テスト"""
        with pytest.raises(PrologError) as excinfo:
            PeekCharPredicate()  # 引数なし
        
        assert "requires at least 1 argument" in str(excinfo.value)
        
        with pytest.raises(PrologError) as excinfo:
            PeekCharPredicate(Variable("X"), Variable("Y"), Variable("Z"))  # 引数過多
        
        assert "takes 1-2 arguments" in str(excinfo.value)
```

### 2.4 AtEndOfStreamPredicateテスト

```python
class TestAtEndOfStreamPredicate:
    """AtEndOfStreamPredicate述語のテスト"""
    
    @pytest.fixture
    def runtime(self):
        return Runtime()
    
    def test_at_end_of_stream_false(self, runtime):
        """データがある場合の動作"""
        runtime.io_manager.set_input_stream(StringStream("data"))
        solutions = runtime.query("at_end_of_stream")
        
        assert len(solutions) == 0  # 失敗
    
    def test_at_end_of_stream_true(self, runtime):
        """EOFの場合の動作"""
        runtime.io_manager.set_input_stream(StringStream(""))
        solutions = runtime.query("at_end_of_stream")
        
        assert len(solutions) == 1  # 成功
    
    def test_at_end_of_stream_progression(self, runtime):
        """読み取り進行中のEOF状態変化"""
        stream = StringStream("a")
        runtime.io_manager.set_input_stream(stream)
        
        # データがあるときは失敗
        solutions1 = runtime.query("at_end_of_stream")
        assert len(solutions1) == 0
        
        # 文字を読み取り
        runtime.query("get_char(X)")
        
        # EOF到達後は成功
        solutions2 = runtime.query("at_end_of_stream")
        assert len(solutions2) == 1
```

---

## 3. 統合テスト設計

### 3.1 IOManager統合テスト

```python
class TestIOManagerIntegration:
    """IOManagerとの統合テスト"""
    
    def test_stream_switching(self):
        """ストリーム切り替えテスト"""
        runtime = Runtime()
        
        # 最初のストリーム
        stream1 = StringStream("first")
        runtime.io_manager.set_input_stream(stream1)
        
        solutions1 = runtime.query("peek_char(X)")
        assert solutions1[0][Variable("X")] == Atom("f")
        
        # ストリーム切り替え
        stream2 = StringStream("second")
        runtime.io_manager.set_input_stream(stream2)
        
        solutions2 = runtime.query("peek_char(Y)")
        assert solutions2[0][Variable("Y")] == Atom("s")
    
    def test_mixed_operations(self):
        """peek_charとget_charの混在操作"""
        runtime = Runtime()
        stream = StringStream("abcde")
        runtime.io_manager.set_input_stream(stream)
        
        # peek -> get -> peek -> get のパターン
        peek1 = runtime.query("peek_char(X1)")  # 'a'
        get1 = runtime.query("get_char(Y1)")    # 'a' (消費)
        peek2 = runtime.query("peek_char(X2)")  # 'b'
        get2 = runtime.query("get_char(Y2)")    # 'b' (消費)
        
        assert peek1[0][Variable("X1")] == Atom("a")
        assert get1[0][Variable("Y1")] == Atom("a")
        assert peek2[0][Variable("X2")] == Atom("b")
        assert get2[0][Variable("Y2")] == Atom("b")
```

### 3.2 複合クエリテスト

```python
class TestComplexQueries:
    """複合クエリでの動作テスト"""
    
    def test_conditional_reading(self):
        """条件付き読み取りパターン"""
        runtime = Runtime()
        
        # 数字判定ルールを追加
        runtime.add_rule("""
        read_if_digit(Char) :-
            peek_char(Next),
            Next >= '0',
            Next =< '9',
            get_char(Char).
        """)
        
        # テストケース1: 数字がある場合
        runtime.io_manager.set_input_stream(StringStream("5abc"))
        solutions = runtime.query("read_if_digit(X)")
        assert len(solutions) == 1
        assert solutions[0][Variable("X")] == Atom("5")
        
        # テストケース2: 数字がない場合
        runtime.io_manager.set_input_stream(StringStream("abc"))
        solutions = runtime.query("read_if_digit(Y)")
        assert len(solutions) == 0
    
    def test_lookahead_parsing(self):
        """先読み解析パターン"""
        runtime = Runtime()
        
        # トークン判定ルール
        runtime.add_rule("""
        next_token_type(number) :-
            peek_char(C),
            C >= '0',
            C =< '9'.
            
        next_token_type(letter) :-
            peek_char(C),
            C >= 'a',
            C =< 'z'.
            
        next_token_type(eof) :-
            at_end_of_stream.
        """)
        
        # 数字の場合
        runtime.io_manager.set_input_stream(StringStream("1abc"))
        solutions = runtime.query("next_token_type(Type)")
        assert solutions[0][Variable("Type")] == Atom("number")
        
        # 文字の場合
        runtime.io_manager.set_input_stream(StringStream("abc"))
        solutions = runtime.query("next_token_type(Type)")
        assert solutions[0][Variable("Type")] == Atom("letter")
        
        # EOFの場合
        runtime.io_manager.set_input_stream(StringStream(""))
        solutions = runtime.query("next_token_type(Type)")
        assert solutions[0][Variable("Type")] == Atom("eof")
```

---

## 4. パフォーマンステスト設計

### 4.1 ベンチマーク定義

```python
class TestPerformance:
    """パフォーマンステスト"""
    
    @pytest.mark.benchmark
    def test_peek_char_performance(self):
        """peek_char操作のパフォーマンス"""
        stream = StringStream("a" * 10000)
        
        start_time = time.perf_counter()
        for _ in range(1000):
            stream.peek_char()
        end_time = time.perf_counter()
        
        avg_time = (end_time - start_time) / 1000
        assert avg_time < 0.001  # 1ms以下
    
    @pytest.mark.benchmark
    def test_at_end_of_stream_performance(self):
        """at_end_of_stream操作のパフォーマンス"""
        stream = StringStream("data")
        
        start_time = time.perf_counter()
        for _ in range(1000):
            stream.at_end_of_stream()
        end_time = time.perf_counter()
        
        avg_time = (end_time - start_time) / 1000
        assert avg_time < 0.0005  # 0.5ms以下
    
    @pytest.mark.benchmark
    def test_buffer_efficiency(self):
        """バッファ効率テスト"""
        # 大量データでのメモリ使用量確認
        large_data = "x" * 1000000  # 1MB
        stream = StringStream(large_data)
        
        memory_before = self._get_memory_usage()
        
        # 多数のpeek操作
        for _ in range(10000):
            stream.peek_char()
        
        memory_after = self._get_memory_usage()
        memory_increase = memory_after - memory_before
        
        # メモリ増加量が1MB以下であること
        assert memory_increase < 1024 * 1024
    
    def _get_memory_usage(self) -> int:
        """現在のメモリ使用量を取得"""
        import psutil
        process = psutil.Process()
        return process.memory_info().rss
```

### 4.2 負荷テスト

```python
class TestLoadHandling:
    """負荷テスト"""
    
    def test_concurrent_peek_operations(self):
        """同時peek操作テスト"""
        import threading
        import concurrent.futures
        
        stream = StringStream("concurrent test data")
        results = []
        errors = []
        
        def peek_operation():
            try:
                for _ in range(100):
                    char = stream.peek_char()
                    results.append(char)
            except Exception as e:
                errors.append(e)
        
        # 10個のスレッドで同時実行
        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(peek_operation) for _ in range(10)]
            concurrent.futures.wait(futures)
        
        # エラーがないこと
        assert len(errors) == 0
        
        # 全ての結果が同じ文字であること（最初の文字）
        unique_results = set(results)
        assert len(unique_results) == 1
        assert list(unique_results)[0] == "c"
    
    def test_large_stream_handling(self):
        """大容量ストリーム処理テスト"""
        # 10MBのデータ
        large_data = "0123456789" * 1000000
        stream = StringStream(large_data)
        
        # 順次peek操作（メモリリークがないことを確認）
        start_memory = self._get_memory_usage()
        
        for i in range(0, len(large_data), 1000):
            stream.read_position = i
            char = stream.peek_char()
            assert char == large_data[i]
        
        end_memory = self._get_memory_usage()
        memory_growth = end_memory - start_memory
        
        # メモリ増加が1MB以下であること
        assert memory_growth < 1024 * 1024
```

---

## 5. エラーケーステスト

### 5.1 例外処理テスト

```python
class TestErrorHandling:
    """エラーハンドリングテスト"""
    
    def test_stream_operation_error(self):
        """StreamOperationErrorの処理"""
        runtime = Runtime()
        
        # peek操作をサポートしないモックストリーム
        mock_stream = Mock()
        mock_stream.supports_peek_operations.return_value = False
        runtime.io_manager.set_input_stream(mock_stream)
        
        # 適切な例外が発生することを確認
        with pytest.raises(PrologError) as excinfo:
            runtime.query("peek_char(X)")
        
        assert "not support" in str(excinfo.value).lower()
    
    def test_buffer_error_handling(self):
        """バッファエラーの処理"""
        # バッファ操作でエラーが発生するモック
        mock_buffer = Mock()
        mock_buffer.peek_char.side_effect = StreamBufferError("Buffer corruption")
        
        stream = BufferedConsoleStream()
        stream._buffer = mock_buffer
        
        with pytest.raises(StreamOperationError):
            stream.peek_char()
    
    def test_resource_exhaustion(self):
        """リソース枯渇時の処理"""
        # メモリ不足をシミュレート
        def memory_error_side_effect(*args, **kwargs):
            raise MemoryError("Out of memory")
        
        with patch('pyprolog.runtime.io_streams.StreamBuffer.__init__', 
                   side_effect=memory_error_side_effect):
            with pytest.raises(StreamOperationError) as excinfo:
                BufferedConsoleStream()
            
            assert "memory" in str(excinfo.value).lower()
    
    def test_encoding_error_handling(self):
        """エンコーディングエラーの処理"""
        # 不正なバイトシーケンス
        invalid_data = b'\xff\xfe\xfd'
        
        with patch('sys.stdin.read', return_value=invalid_data.decode('latin-1')):
            stream = BufferedConsoleStream()
            
            # エラーが適切に処理されることを確認
            try:
                char = stream.peek_char()
                # エラーハンドリングが正常に動作すれば到達
                assert True
            except UnicodeDecodeError:
                pytest.fail("Encoding error was not handled properly")
```

### 5.2 境界値テスト

```python
class TestBoundaryConditions:
    """境界値テスト"""
    
    def test_empty_stream(self):
        """空ストリームの処理"""
        stream = StringStream("")
        
        assert stream.peek_char() == ""
        assert stream.at_end_of_stream() is True
        
        # 複数回呼び出しても安定していること
        for _ in range(10):
            assert stream.peek_char() == ""
            assert stream.at_end_of_stream() is True
    
    def test_single_char_stream(self):
        """1文字のみのストリーム"""
        stream = StringStream("a")
        
        # EOF前
        assert stream.peek_char() == "a"
        assert stream.at_end_of_stream() is False
        
        # 読み取り後
        stream.read_char()
        assert stream.peek_char() == ""
        assert stream.at_end_of_stream() is True
    
    def test_buffer_boundary(self):
        """バッファ境界でのpeek操作"""
        buffer_size = 10
        test_data = "a" * buffer_size + "b" * buffer_size
        
        mock_stdin = io.StringIO(test_data)
        with patch('sys.stdin', mock_stdin):
            stream = BufferedConsoleStream(buffer_size=buffer_size)
            
            # バッファサイズちょうどの位置でのpeek
            for i in range(buffer_size):
                char = stream.peek_char()
                assert char == "a"
                stream.read_char()
            
            # バッファ境界を跨いだpeek
            char = stream.peek_char()
            assert char == "b"  # 次のバッファから正常に読み取れること
    
    def test_unicode_boundary(self):
        """Unicode文字境界での処理"""
        # マルチバイト文字を含む文字列
        unicode_data = "Hello世界🌍"
        stream = StringStream(unicode_data)
        
        expected_chars = list(unicode_data)
        for expected_char in expected_chars:
            peeked_char = stream.peek_char()
            assert peeked_char == expected_char
            
            read_char = stream.read_char()
            assert read_char == expected_char
        
        # 最後はEOF
        assert stream.peek_char() == ""
        assert stream.at_end_of_stream() is True
```

---

## 6. 互換性テスト

### 6.1 既存機能との互換性

```python
class TestBackwardCompatibility:
    """既存機能との互換性テスト"""
    
    def test_existing_get_char_behavior(self):
        """既存のget_char/1の動作に影響がないこと"""
        runtime = Runtime()
        stream = StringStream("test")
        runtime.io_manager.set_input_stream(stream)
        
        # get_char/1の既存動作
        solutions = runtime.query("get_char(X)")
        assert solutions[0][Variable("X")] == Atom("t")
        
        # 2回目は次の文字
        solutions = runtime.query("get_char(Y)")
        assert solutions[0][Variable("Y")] == Atom("e")
    
    def test_legacy_stream_wrapper(self):
        """レガシーストリームラッパーのテスト"""
        # peek機能のないストリームをエミュレート
        legacy_stream = Mock(spec=IOStream)
        legacy_stream.read_char.side_effect = ["a", "b", ""]
        legacy_stream.supports_peek_operations.return_value = False
        
        # ラッパーで機能を提供
        wrapped_stream = LegacyStreamWrapper(legacy_stream)
        
        # 制限付きだが基本的なpeek機能が使えること
        char1 = wrapped_stream.peek_char()
        char2 = wrapped_stream.peek_char()  # 同じ文字が返る
        assert char1 == char2 == "a"
        
        # 実際の読み取り
        read_char = wrapped_stream.read_char()
        assert read_char == "a"
    
    def test_configuration_compatibility(self):
        """設定による機能切り替えテスト"""
        # 互換モード
        compat_config = StreamConfiguration(
            enable_peek_operations=False,
            strict_compatibility_mode=True
        )
        
        # peek機能が無効化されることを確認
        stream = create_stream_with_config("console", compat_config)
        assert not stream.supports_peek_operations()
        
        # 通常モード
        normal_config = StreamConfiguration(
            enable_peek_operations=True,
            strict_compatibility_mode=False
        )
        
        stream = create_stream_with_config("console", normal_config)
        assert stream.supports_peek_operations()
```

---

## 7. テストデータ設計

### 7.1 標準テストデータセット

```python
class TestDataSets:
    """標準的なテストデータセット"""
    
    # 基本文字セット
    ASCII_CHARS = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"
    SPECIAL_CHARS = " !@#$%^&*()_+-=[]{}|;':\",./<>?"
    
    # Unicode文字セット
    UNICODE_CHARS = "こんにちは世界🌍🎉"
    MIXED_UNICODE = "Hello世界🌍Test"
    
    # 制御文字
    CONTROL_CHARS = "\n\r\t"
    
    # 境界値データ
    EMPTY_STRING = ""
    SINGLE_CHAR = "x"
    LARGE_DATA = "x" * 10000
    
    # エラーテスト用データ
    BINARY_DATA = bytes([0x00, 0x01, 0x02, 0xFF])
    
    @staticmethod
    def get_test_cases():
        """テストケースのジェネレーター"""
        return [
            ("empty", TestDataSets.EMPTY_STRING),
            ("single", TestDataSets.SINGLE_CHAR),
            ("ascii", TestDataSets.ASCII_CHARS),
            ("special", TestDataSets.SPECIAL_CHARS),
            ("unicode", TestDataSets.UNICODE_CHARS),
            ("mixed", TestDataSets.MIXED_UNICODE),
            ("control", TestDataSets.CONTROL_CHARS),
            ("large", TestDataSets.LARGE_DATA[:100]),  # テスト用に短縮
        ]
```

### 7.2 パラメータ化テスト

```python
@pytest.mark.parametrize("test_name,test_data", TestDataSets.get_test_cases())
def test_peek_char_with_various_data(test_name, test_data):
    """様々なデータでのpeek_char動作テスト"""
    stream = StringStream(test_data)
    
    if test_data:
        expected_first_char = test_data[0]
        assert stream.peek_char() == expected_first_char
        assert stream.at_end_of_stream() is False
    else:
        assert stream.peek_char() == ""
        assert stream.at_end_of_stream() is True

@pytest.mark.parametrize("buffer_size", [1, 10, 100, 1000])
def test_buffered_stream_with_various_sizes(buffer_size):
    """様々なバッファサイズでのテスト"""
    test_data = "a" * (buffer_size * 2)  # バッファサイズの2倍のデータ
    
    mock_stdin = io.StringIO(test_data)
    with patch('sys.stdin', mock_stdin):
        stream = BufferedConsoleStream(buffer_size=buffer_size)
        
        # バッファサイズに関係なく正常に動作すること
        assert stream.peek_char() == "a"
        
        # 全てのデータを読み取れること
        chars_read = 0
        while not stream.at_end_of_stream():
            stream.read_char()
            chars_read += 1
        
        assert chars_read == len(test_data)
```

---

## 8. テスト実行コマンド

```bash
# 基本テスト実行
uvx pytest tests/runtime/test_peek_char.py --timeout=30

# カバレッジ付きテスト
uvx pytest tests/runtime/test_peek_char.py --timeout=30 --cov=pyprolog.runtime --cov-report=html

# パフォーマンステスト
uvx pytest tests/performance/test_peek_performance.py --timeout=120 --benchmark-only

# 特定のテストケースのみ（詳細表示）
uvx pytest tests/runtime/test_peek_char.py::TestPeekCharPredicate::test_peek_char_unification_success --timeout=10 -v

# デバッグ用詳細テスト
uvx pytest tests/runtime/test_peek_char.py --timeout=30 -v -s

# すべてのpeek関連テスト
uvx pytest tests/ -k "peek" --timeout=60
```

---

**作成者**: Claude Code  
**日時**: 2025年8月6日  
**バージョン**: 1.0