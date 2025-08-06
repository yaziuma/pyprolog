# PyProlog 非ブロッキング入力述語 詳細設計書

## 目次

1. [アーキテクチャ設計](#1-アーキテクチャ設計)
2. [IOStreamインターフェース拡張](#2-iostreamインターフェース拡張)
3. [実装クラス詳細設計](#3-実装クラス詳細設計)
4. [BuiltinPredicate実装設計](#4-builtinpredicate実装設計)
5. [エラーハンドリング設計](#5-エラーハンドリング設計)
6. [パフォーマンス設計](#6-パフォーマンス設計)
7. [互換性・移行設計](#7-互換性移行設計)
8. [実装ガイドライン](#8-実装ガイドライン)

---

## 1. アーキテクチャ設計

### 1.1 モジュール構成

```
pyprolog/runtime/
├── io_streams.py           # IOStreamインターフェース拡張
├── io_manager.py           # IOManager機能追加
├── builtins.py             # peek_char/at_end_of_stream述語
└── stream_buffer.py        # 新規: バッファ管理クラス

pyprolog/core/
└── stream_errors.py        # 新規: ストリーム専用例外
```

### 1.2 クラス依存関係

```
IOManager
├── IOStream (Abstract)
│   ├── StringStream (既存拡張)
│   ├── ConsoleStream (既存拡張)  
│   └── BufferedConsoleStream (新規)
│
├── StreamBuffer (新規)
│   ├── CircularBuffer
│   └── NonBlockingReader
│
└── BuiltinPredicate (拡張)
    ├── PeekCharPredicate (新規)
    └── AtEndOfStreamPredicate (新規)
```

### 1.3 データフロー設計

```
1. クエリ実行開始
   ↓
2. IOManager.get_input_stream()
   ↓
3. Stream.supports_peek_operations() 確認
   ↓
4. 非ブロッキング操作実行
   ├── バッファあり → 即座に結果返却
   ├── バッファ空 → select()でチェック
   └── EOF → end_of_fileアトム返却
   ↓
5. Unification & 結果返却
```

---

## 2. IOStreamインターフェース拡張

### 2.1 抽象基底クラス拡張

```python
# 新規追加メソッド仕様
class IOStream(ABC):
    
    @abstractmethod
    def peek_char(self) -> str:
        """
        次の文字を非破壊的に取得
        
        Returns:
            str: 次の文字 (EOF時は空文字列)
        
        Raises:
            StreamOperationError: ストリームが操作をサポートしない
            StreamBufferError: バッファエラー
        """
        pass
    
    @abstractmethod
    def at_end_of_stream(self) -> bool:
        """
        EOF状態を非破壊的に確認
        
        Returns:
            bool: True=EOF到達, False=データあり
        
        Raises:
            StreamOperationError: ストリーム状態取得不可
        """
        pass
    
    @abstractmethod
    def supports_peek_operations(self) -> bool:
        """
        peek系操作のサポート状況確認
        
        Returns:
            bool: True=サポート, False=非サポート
        """
        pass
    
    @abstractmethod
    def get_stream_status(self) -> StreamStatus:
        """
        詳細なストリーム状態取得
        
        Returns:
            StreamStatus: 状態情報オブジェクト
        """
        pass
```

### 2.2 StreamStatusクラス設計

```python
@dataclass
class StreamStatus:
    """ストリーム状態情報"""
    
    # 基本状態
    at_eof: bool
    has_data_available: bool
    supports_peek: bool
    
    # バッファ情報
    buffer_size: int
    buffered_chars: int
    buffer_position: int
    
    # メタデータ
    stream_type: str
    encoding: str
    last_operation: str
    
    # エラー状態
    has_errors: bool
    error_message: Optional[str]
```

---

## 3. 実装クラス詳細設計

### 3.1 StringStream拡張実装

```python
class StringStream(IOStream):
    """
    メモリベースストリーム（完全機能実装）
    - 全ての操作が非ブロッキング
    - peek操作フルサポート
    - 高パフォーマンス
    """
    
    def peek_char(self) -> str:
        """実装方針: read_positionを変更せずに文字取得"""
        if self.read_position < len(self.input_string):
            return self.input_string[self.read_position]
        return ""  # EOF
    
    def at_end_of_stream(self) -> bool:
        """実装方針: 位置と長さの比較のみ"""
        return self.read_position >= len(self.input_string)
    
    def supports_peek_operations(self) -> bool:
        return True  # 完全サポート
    
    def get_stream_status(self) -> StreamStatus:
        return StreamStatus(
            at_eof=self.at_end_of_stream(),
            has_data_available=not self.at_end_of_stream(),
            supports_peek=True,
            buffer_size=len(self.input_string),
            buffered_chars=len(self.input_string) - self.read_position,
            buffer_position=self.read_position,
            stream_type="StringStream",
            encoding="utf-8",
            last_operation=getattr(self, '_last_op', 'init'),
            has_errors=False,
            error_message=None
        )
```

### 3.2 BufferedConsoleStream新規実装（クロスプラットフォーム対応）

```python
import platform

class BufferedConsoleStream(IOStream):
    """
    バッファ付きコンソールストリーム（新規実装）
    - クロスプラットフォーム非ブロッキング読み取り
    - 循環バッファによる効率的なデータ管理
    - Windows/Unix両対応
    """
    
    def __init__(self, buffer_size: int = 1024):
        self.buffer = StreamBuffer(buffer_size)
        self.eof_reached = False
        self._last_operation = "init"
        self._platform_handler = self._create_platform_handler()
    
    def _create_platform_handler(self):
        """プラットフォーム固有ハンドラー作成"""
        if platform.system() == 'Windows':
            return WindowsInputHandler()
        else:
            return UnixInputHandler()
    
    def _fill_buffer_non_blocking(self) -> bool:
        """
        非ブロッキングでバッファを充填
        
        Returns:
            bool: 新しいデータを読み込めた場合True
        """
        if self.eof_reached:
            return False
            
        try:
            if self._platform_handler.is_input_available():
                char = self._platform_handler.read_char_nonblocking()
                if char:
                    self.buffer.put(char)
                    return True
                else:
                    self.eof_reached = True
                    return False
            return False  # 入力なし
            
        except Exception as e:
            raise StreamOperationError(f"Buffer fill failed: {e}")
    
    def peek_char(self) -> str:
        """実装方針: バッファから非破壊的読み取り"""
        # バッファに文字があるかチェック
        if not self.buffer.is_empty():
            return self.buffer.peek()
        
        # バッファ充填を試行
        if self._fill_buffer_non_blocking():
            return self.buffer.peek()
        
        # EOFまたは入力なし
        return ""
    
    def at_end_of_stream(self) -> bool:
        """実装方針: バッファ状態とEOFフラグの組み合わせ"""
        if not self.buffer.is_empty():
            return False
        
        # バッファが空の場合、充填を試行
        self._fill_buffer_non_blocking()
        return self.eof_reached and self.buffer.is_empty()
    
    def read_char(self) -> str:
        """バッファ優先の文字読み取り"""
        if not self.buffer.is_empty():
            return self.buffer.get()
        
        # バッファが空の場合はプラットフォーム固有の読み取り
        return self._platform_handler.read_char_blocking()
    
    def supports_peek_operations(self) -> bool:
        return True
```

### 3.3 プラットフォーム固有ハンドラー

```python
from abc import ABC, abstractmethod

class InputHandler(ABC):
    """入力ハンドラー抽象基底クラス"""
    
    @abstractmethod
    def is_input_available(self) -> bool:
        """入力が利用可能かチェック"""
        pass
    
    @abstractmethod
    def read_char_nonblocking(self) -> str:
        """非ブロッキング文字読み込み"""
        pass
    
    @abstractmethod
    def read_char_blocking(self) -> str:
        """ブロッキング文字読み込み"""
        pass

class UnixInputHandler(InputHandler):
    """Unix系システム用入力ハンドラー"""
    
    def is_input_available(self) -> bool:
        """select()による入力判定"""
        import select
        import sys
        ready, _, _ = select.select([sys.stdin], [], [], 0.0)
        return bool(ready)
    
    def read_char_nonblocking(self) -> str:
        """非ブロッキング読み込み"""
        if self.is_input_available():
            import sys
            return sys.stdin.read(1)
        return ""
    
    def read_char_blocking(self) -> str:
        """通常のブロッキング読み込み"""
        import sys
        return sys.stdin.read(1)

class WindowsInputHandler(InputHandler):
    """Windows用入力ハンドラー"""
    
    def __init__(self):
        try:
            import msvcrt
            self._msvcrt = msvcrt
        except ImportError:
            raise StreamCapabilityError("Windows input handler requires msvcrt")
    
    def is_input_available(self) -> bool:
        """msvcrt.kbhit()による入力判定"""
        return self._msvcrt.kbhit()
    
    def read_char_nonblocking(self) -> str:
        """非ブロッキング読み込み"""
        if self.is_input_available():
            return self._msvcrt.getch().decode('utf-8', errors='ignore')
        return ""
    
    def read_char_blocking(self) -> str:
        """ブロッキング読み込み"""
        return self._msvcrt.getch().decode('utf-8', errors='ignore')

### 3.4 StreamBufferクラス実装（シングルスレッド用）

```python
from collections import deque
from typing import Optional

class StreamBuffer:
    """
    効率的な文字バッファ管理（シングルスレッド用）
    - dequeによる効率的なデータ管理
    - peek操作の高速化
    - シンプルなインタフェース
    """
    
    def __init__(self, capacity: int = 1024):
        self._buffer = deque(maxlen=capacity)
        self._capacity = capacity
    
    def peek(self) -> Optional[str]:
        """先頭文字をpeek（位置変更なし）"""
        try:
            return self._buffer[0]
        except IndexError:
            return None
    
    def get(self) -> Optional[str]:
        """先頭文字を読み取り（除去）"""
        try:
            return self._buffer.popleft()
        except IndexError:
            return None
    
    def put(self, char: str) -> bool:
        """文字をバッファに追加"""
        try:
            self._buffer.append(char)
            return True
        except:
            return False
    
    def is_empty(self) -> bool:
        """バッファが空かチェック"""
        return len(self._buffer) == 0
    
    def size(self) -> int:
        """現在のバッファサイズ"""
        return len(self._buffer)
    
    def clear(self) -> None:
        """バッファクリア"""
        self._buffer.clear()
                return char
            return ""
    
    def write(self, data: str) -> int:
        """データを書き込み"""
        with self._lock:
            written = 0
            for char in data:
                if self.data_count < self.size:
                    self.buffer[self.write_pos] = char
                    self.write_pos = (self.write_pos + 1) % self.size
                    self.data_count += 1
                    written += 1
                else:
                    break  # バッファフル
            return written
```

---

## 4. BuiltinPredicate実装設計

### 4.1 PeekCharPredicate詳細設計

```python
class PeekCharPredicate(BuiltinPredicate):
    """
    peek_char/1述語実装
    - 引数バリデーション
    - ストリーム能力チェック
    - エラーハンドリング
    - パフォーマンス最適化
    """
    
    def __init__(self, *args):
        super().__init__(*args)
        self._validate_arguments()
    
    def _validate_arguments(self):
        """引数検証"""
        arg_count = len(self.args)
        if arg_count == 0:
            raise PrologError("peek_char requires at least 1 argument")
        elif arg_count > 2:
            raise PrologError(f"peek_char takes 1-2 arguments, got {arg_count}")
    
    def execute(self, runtime: "Runtime", env: BindingEnvironment) -> Iterator[BindingEnvironment]:
        """メイン実行ロジック"""
        try:
            # ストリーム取得
            stream = self._get_target_stream(runtime, env)
            
            # 能力チェック
            if not stream.supports_peek_operations():
                raise StreamOperationError(
                    f"Stream {type(stream).__name__} does not support peek_char/1"
                )
            
            # peek操作実行
            char_str = stream.peek_char()
            target_atom = self._convert_to_atom(char_str)
            
            # unification
            char_arg = self.args[-1]  # 最後の引数が文字変数
            unified, next_env = runtime.logic_interpreter.unify(
                char_arg, target_atom, env
            )
            
            if unified:
                yield next_env
                
        except StreamOperationError as e:
            # ストリーム操作エラーは予期される例外
            logger.warning(f"peek_char/1 stream operation failed: {e}")
            return  # 失敗として処理
            
        except Exception as e:
            # 予期しない例外は再発生
            logger.error(f"Unexpected error in peek_char/1: {e}", exc_info=True)
            raise PrologError(f"peek_char/1 execution failed: {e}") from e
    
    def _get_target_stream(self, runtime: "Runtime", env: BindingEnvironment) -> IOStream:
        """対象ストリームの特定"""
        if len(self.args) == 1:
            # peek_char(-Char) 形式
            return runtime.io_manager.get_input_stream()
        else:
            # peek_char(+Stream, -Char) 形式
            stream_arg = self.args[0]
            # ストリーム引数の解決ロジック（将来実装）
            raise NotImplementedError("Stream argument not yet supported")
    
    def _convert_to_atom(self, char_str: str) -> Atom:
        """文字列からAtomへの変換"""
        if char_str == "":
            return Atom("end_of_file")
        elif len(char_str) == 1:
            return Atom(char_str)
        else:
            # マルチバイト文字などの処理
            return Atom(char_str[0])  # 最初の文字のみ
```

### 4.2 AtEndOfStreamPredicate詳細設計

```python
class AtEndOfStreamPredicate(BuiltinPredicate):
    """
    at_end_of_stream/0述語実装
    - 引数なしまたはストリーム指定
    - EOF状態の確実な判定
    - 高速化のためのキャッシュ機能
    """
    
    def __init__(self, *args):
        super().__init__(*args)
        if len(self.args) > 1:
            raise PrologError(f"at_end_of_stream takes 0-1 arguments, got {len(self.args)}")
    
    def execute(self, runtime: "Runtime", env: BindingEnvironment) -> Iterator[BindingEnvironment]:
        """メイン実行ロジック"""
        try:
            # ストリーム取得
            stream = self._get_target_stream(runtime, env)
            
            # EOF状態確認
            if stream.at_end_of_stream():
                yield env  # 成功
            # else: 失敗（何もyieldしない）
            
        except StreamOperationError as e:
            logger.warning(f"at_end_of_stream stream operation failed: {e}")
            return  # 失敗として処理
            
        except Exception as e:
            logger.error(f"Unexpected error in at_end_of_stream: {e}", exc_info=True)
            raise PrologError(f"at_end_of_stream execution failed: {e}") from e
    
    def _get_target_stream(self, runtime: "Runtime", env: BindingEnvironment) -> IOStream:
        """対象ストリームの特定"""
        if len(self.args) == 0:
            return runtime.io_manager.get_input_stream()
        else:
            # at_end_of_stream(+Stream) 形式（将来実装）
            raise NotImplementedError("Stream argument not yet supported")
```

---

## 5. エラーハンドリング設計

### 5.1 例外クラス階層

```python
# pyprolog/core/stream_errors.py

class StreamError(PrologError):
    """ストリーム関連エラーの基底クラス"""
    pass

class StreamOperationError(StreamError):
    """ストリーム操作エラー"""
    def __init__(self, message: str, stream_type: str = None):
        super().__init__(message)
        self.stream_type = stream_type

class StreamBufferError(StreamError):
    """バッファ関連エラー"""
    pass

class StreamCapabilityError(StreamError):
    """ストリーム能力不足エラー"""
    def __init__(self, operation: str, stream_type: str):
        super().__init__(f"Operation '{operation}' not supported by {stream_type}")
        self.operation = operation
        self.stream_type = stream_type
```

### 5.2 エラーハンドリング戦略

```python
# レベル1: 予期される操作失敗
def handle_expected_failure(operation_name: str, error: Exception):
    """
    予期される失敗の処理
    - ログ出力（WARNING レベル）
    - 述語失敗として処理
    - 例外は再発生させない
    """
    logger.warning(f"{operation_name} failed as expected: {error}")
    return  # 空のイテレーターを返す

# レベル2: 回復可能なエラー
def handle_recoverable_error(operation_name: str, error: Exception, fallback_action):
    """
    回復可能なエラーの処理
    - ログ出力（INFO レベル）
    - フォールバック処理実行
    - 部分的成功を目指す
    """
    logger.info(f"{operation_name} error, attempting fallback: {error}")
    return fallback_action()

# レベル3: 致命的エラー
def handle_fatal_error(operation_name: str, error: Exception):
    """
    致命的エラーの処理
    - 詳細ログ出力（ERROR レベル）
    - PrologErrorとして再発生
    - スタックトレース保持
    """
    logger.error(f"Fatal error in {operation_name}: {error}", exc_info=True)
    raise PrologError(f"{operation_name} execution failed: {error}") from error
```

---

## 6. パフォーマンス設計

### 6.1 最適化戦略

**1. バッファサイズ最適化**
```python
# 用途別バッファサイズ設定
BUFFER_SIZES = {
    'interactive': 256,    # 対話的使用（小バッファ）
    'batch': 4096,         # バッチ処理（大バッファ）
    'streaming': 1024,     # ストリーミング（中バッファ）
}
```

**2. 操作キャッシュ**
```python
class CachedStreamOperations:
    """頻繁な操作の結果をキャッシュ"""
    
    def __init__(self):
        self._eof_cache = {}
        self._peek_cache = {}
        self._cache_timeout = 0.1  # 100ms
    
    def cached_at_end_of_stream(self, stream_id: str, stream: IOStream) -> bool:
        now = time.time()
        cache_entry = self._eof_cache.get(stream_id)
        
        if cache_entry and (now - cache_entry['timestamp']) < self._cache_timeout:
            return cache_entry['result']
        
        result = stream.at_end_of_stream()
        self._eof_cache[stream_id] = {
            'result': result,
            'timestamp': now
        }
        return result
```

**3. 遅延初期化**
```python
class LazyBufferedStream:
    """必要時のみバッファを初期化"""
    
    def __init__(self):
        self._buffer = None
        self._initialized = False
    
    def _ensure_initialized(self):
        if not self._initialized:
            self._buffer = StreamBuffer(self._get_optimal_buffer_size())
            self._initialized = True
    
    def peek_char(self) -> str:
        self._ensure_initialized()
        return self._buffer.peek_char()
```

### 6.2 パフォーマンス監視

```python
class PerformanceMonitor:
    """パフォーマンス監視とメトリクス収集"""
    
    def __init__(self):
        self.metrics = {
            'peek_operations': 0,
            'buffer_fills': 0,
            'cache_hits': 0,
            'cache_misses': 0,
            'total_execution_time': 0.0
        }
    
    def record_operation(self, operation_name: str, execution_time: float):
        self.metrics[f'{operation_name}_count'] = self.metrics.get(f'{operation_name}_count', 0) + 1
        self.metrics['total_execution_time'] += execution_time
    
    def get_performance_report(self) -> dict:
        return {
            'operations_per_second': self.metrics.get('peek_operations', 0) / max(0.001, self.metrics['total_execution_time']),
            'average_operation_time': self.metrics['total_execution_time'] / max(1, self.metrics.get('peek_operations', 1)),
            'cache_hit_ratio': self.metrics.get('cache_hits', 0) / max(1, self.metrics.get('cache_hits', 0) + self.metrics.get('cache_misses', 0)),
            **self.metrics
        }
```

---

## 7. 互換性・移行設計

### 7.1 後方互換性保証

**既存コードへの影響ゼロ**
```python
# 既存のIOStreamクラス拡張時の互換性保証
class IOStream(ABC):
    # 新規メソッドにはデフォルト実装を提供
    def peek_char(self) -> str:
        """デフォルト実装: サポートしない旨を明示"""
        raise StreamCapabilityError("peek_char", type(self).__name__)
    
    def supports_peek_operations(self) -> bool:
        """デフォルト実装: 保守的にFalseを返す"""
        return False
```

**段階的移行サポート**
```python
class StreamFactory:
    """peek機能対応ストリームの作成"""
    
    @staticmethod
    def create_console_stream() -> IOStream:
        """非ブロッキングコンソールストリームの作成"""
        import logging
        logger = logging.getLogger(__name__)
        
        logger.info("Creating BufferedConsoleStream for peek support")
        return BufferedConsoleStream()
    
    @staticmethod
    def create_string_stream(content: str = "") -> IOStream:
        """peek機能付き文字列ストリームの作成"""
        return StringStream(content)
    
    @staticmethod
    def get_optimal_stream(stream_type: str) -> IOStream:
        """最適なストリーム実装を取得"""
        if stream_type == "string":
            return StreamFactory.create_string_stream()
        elif stream_type == "console":
            return StreamFactory.create_console_stream()
        else:
            raise ValueError(f"Unsupported stream type: {stream_type}")

def create_peek_capable_stream(stream_type: str = 'console') -> IOStream:
    """peek機能対応ストリームの作成"""
    return StreamFactory.get_optimal_stream(stream_type)
```

### 7.2 IOManager統合

```python
# pyprolog/runtime/io_manager.pyの拡張

class IOManager:
    """拡張されたIOManager（peek機能サポート）"""
    
    def __init__(self):
        self._input_stream = None
        self._output_stream = None
    
    def initialize_with_peek_support(self):
        """peek機能サポート付きでIOManagerを初期化"""
        import logging
        logger = logging.getLogger(__name__)
        
        logger.info("Initializing IOManager with peek support")
        self._input_stream = BufferedConsoleStream()
        self._output_stream = ConsoleStream()  # 出力は既存で十分
    
    def get_input_stream(self) -> IOStream:
        """peek機能対応入力ストリーム取得"""
        if self._input_stream is None:
            self._input_stream = BufferedConsoleStream()
        return self._input_stream
    
    def set_string_input(self, content: str):
        """文字列入力ストリームを設定（テスト用）"""
        self._input_stream = StringStream(content)
    
    def upgrade_input_stream(self):
        """入力ストリームをpeek対応にアップグレード"""
        current = self._input_stream
        if not hasattr(current, 'peek_char') or not current.supports_peek_operations():
            self._input_stream = BufferedConsoleStream()
            import logging
            logger = logging.getLogger(__name__)
            logger.info("Input stream upgraded to BufferedConsoleStream")
```

---

## 8. 実装ガイドライン

### 8.1 開発の優先順位

**Phase 1: 基盤実装（必須）**
1. StreamStatus, StreamError例外クラス
2. IOStreamインターフェース拡張
3. StringStreamの機能拡張
4. 基本テストスイート

**Phase 2: コア機能（重要）**
1. PeekCharPredicate実装
2. AtEndOfStreamPredicate実装
3. IOManagerの統合
4. エラーハンドリング

**Phase 3: 高度な機能（推奨）**
1. BufferedConsoleStream実装
2. StreamBuffer実装
3. パフォーマンス最適化
4. 包括的テスト

**Phase 4: 拡張機能（オプション）**
1. 設定ベース機能切り替え
2. パフォーマンス監視
3. 移行ヘルパー
4. ドキュメント整備

### 8.2 コーディング標準

**命名規則**
```python
# クラス名: CamelCase
class BufferedConsoleStream:
    pass

# メソッド名: snake_case
def peek_char(self) -> str:
    pass

# 定数: UPPER_SNAKE_CASE
DEFAULT_BUFFER_SIZE = 1024

# プライベートメソッド: _prefix
def _fill_buffer_non_blocking(self):
    pass
```

**エラーハンドリング規則**
```python
# 1. 具体的な例外タイプを使用
try:
    result = stream.peek_char()
except StreamOperationError as e:
    handle_stream_error(e)
except StreamBufferError as e:
    handle_buffer_error(e)

# 2. ログ出力を必ず行う
logger.warning(f"Operation failed: {e}")

# 3. 元の例外を保持
raise PrologError("Operation failed") from e
```

**テスト規則**
```python
# 1. 各メソッドに対応するテストクラス
class TestPeekCharPredicate:
    def test_peek_char_with_string_stream(self):
        pass
    
    def test_peek_char_with_eof(self):
        pass
    
    def test_peek_char_unsupported_stream(self):
        pass

# 2. エッジケースを含む包括的テスト
def test_peek_char_with_multibyte_characters(self):
    """マルチバイト文字の処理をテスト"""
    pass

# 3. パフォーマンステスト
def test_peek_char_performance(self):
    """大量操作のパフォーマンステスト"""
    pass
```

### 8.3 品質保証指針

**コードレビューチェックリスト**
- [ ] 全ての新規メソッドにdocstringがある
- [ ] エラーハンドリングが適切に実装されている
- [ ] 既存コードとの互換性が保たれている
- [ ] パフォーマンスへの配慮がされている
- [ ] テストカバレッジが十分である

**パフォーマンス要件**
- peek_char操作: < 1ms (95%ile)
- at_end_of_stream操作: < 0.5ms (95%ile)  
- バッファ充填: < 10ms (95%ile)
- メモリ使用量: base + 1MB以下

---

**作成者**: Claude Code  
**日時**: 2025年8月6日  
**バージョン**: 1.0