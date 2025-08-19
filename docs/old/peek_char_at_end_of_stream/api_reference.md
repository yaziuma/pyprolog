# PyProlog 非ブロッキング入力述語 APIリファレンス

## 目次

1. [述語リファレンス](#1-述語リファレンス)
2. [IOStreamインターフェース](#2-iostreamインターフェース)
3. [例外クラス](#3-例外クラス)
4. [設定クラス](#4-設定クラス)
5. [ユーティリティクラス](#5-ユーティリティクラス)
6. [使用例](#6-使用例)
7. [移行ガイド](#7-移行ガイド)
8. [トラブルシューティング](#8-トラブルシューティング)

---

## 1. 述語リファレンス

### 1.1 peek_char/1

**形式:**
```prolog
peek_char(-Char)
peek_char(+Stream, -Char)
```

**説明:**
入力ストリームから次の文字を非破壊的に読み取る。ストリームの位置は変更されない。

**引数:**
- `Stream` (Optional, Input): 対象入力ストリーム。省略時は現在のストリーム
- `Char` (Output): 読み取った文字のAtom

**成功条件:**
- ストリームが読み取り可能
- peek操作をサポートするストリーム

**失敗条件:**
- ストリームがpeek操作をサポートしない
- ストリームアクセスエラー

**戻り値:**
- 通常文字: `'a'`, `'1'`, `' '`, `'あ'` など
- EOF: `'end_of_file'`

**使用例:**
```prolog
?- peek_char(X).
X = 'h'.

?- peek_char(Y).    % 同じ文字が返る
Y = 'h'.

?- get_char(Z).     % 実際に消費
Z = 'h'.

?- peek_char(W).    % 次の文字
W = 'e'.
```

**エラー:**
- `StreamOperationError`: ストリーム操作失敗
- `PrologError`: 引数エラーまたは実行エラー

---

### 1.2 at_end_of_stream/0

**形式:**
```prolog
at_end_of_stream
at_end_of_stream(+Stream)
```

**説明:**
入力ストリームがEOF（End of File）に到達しているかを非破壊的に確認する。

**引数:**
- `Stream` (Optional, Input): 対象入力ストリーム

**成功条件:**
- ストリームがEOF位置に到達している

**失敗条件:**
- ストリームにまだデータが残っている

**使用例:**
```prolog
?- at_end_of_stream.
false.                  % データあり

?- get_char(_), get_char(_).  % 文字を消費
true.

?- at_end_of_stream.
true.                   % EOF到達
```

**エラー:**
- `StreamOperationError`: ストリーム状態取得失敗
- `PrologError`: 実行エラー

---

## 2. IOStreamインターフェース

### 2.1 IOStream抽象基底クラス

```python
class IOStream(ABC):
    """Prolog I/Oストリームの抽象基底クラス"""
```

#### 2.1.1 peek_char() -> str

**説明:** 次の文字を非破壊的に取得

**戻り値:**
- `str`: 次の文字（EOF時は空文字列）

**例外:**
- `StreamOperationError`: 操作がサポートされていない
- `StreamBufferError`: バッファエラー

**使用例:**
```python
stream = StringStream("hello")
char = stream.peek_char()  # 'h'
same_char = stream.peek_char()  # 'h' (同じ文字)
```

#### 2.1.2 at_end_of_stream() -> bool

**説明:** EOF状態を非破壊的に確認

**戻り値:**
- `bool`: True=EOF到達, False=データあり

**例外:**
- `StreamOperationError`: ストリーム状態取得不可

**使用例:**
```python
stream = StringStream("")
is_eof = stream.at_end_of_stream()  # True
```

#### 2.1.3 supports_peek_operations() -> bool

**説明:** peek系操作のサポート状況確認

**戻り値:**
- `bool`: True=サポート, False=非サポート

**使用例:**
```python
if stream.supports_peek_operations():
    char = stream.peek_char()
else:
    print("Peek operations not supported")
```

#### 2.1.4 get_stream_status() -> StreamStatus

**説明:** 詳細なストリーム状態取得

**戻り値:**
- `StreamStatus`: 状態情報オブジェクト

**使用例:**
```python
status = stream.get_stream_status()
print(f"EOF: {status.at_eof}")
print(f"Buffer size: {status.buffer_size}")
```

---

### 2.2 StringStream

```python
class StringStream(IOStream):
    """メモリベースの文字列ストリーム"""
    
    def __init__(self, initial_input: str = "", output_buffer: List[str] = None):
        """
        Args:
            initial_input: 初期入力文字列
            output_buffer: 出力バッファ（オプション）
        """
```

**特徴:**
- 全てのpeek操作をサポート
- 非ブロッキング動作
- 高パフォーマンス

**メソッド:**
- `peek_char()`: O(1)で実行
- `at_end_of_stream()`: O(1)で実行
- `supports_peek_operations()`: 常にTrue

---

### 2.3 BufferedConsoleStream

```python
class BufferedConsoleStream(IOStream):
    """バッファ付きコンソールストリーム"""
    
    def __init__(self, buffer_size: int = 1024, read_timeout: float = 0.0):
        """
        Args:
            buffer_size: バッファサイズ（バイト）
            read_timeout: 読み取りタイムアウト（秒）
        """
```

**特徴:**
- `select()`による非ブロッキング実装
- 循環バッファによる効率的なデータ管理
- タイムアウト対応

**メソッド:**
- `peek_char()`: バッファから非破壊的取得
- `at_end_of_stream()`: バッファ状態とEOFフラグで判定
- `supports_peek_operations()`: 常にTrue

---

## 3. 例外クラス

### 3.1 StreamError

```python
class StreamError(PrologError):
    """ストリーム関連エラーの基底クラス"""
```

### 3.2 StreamOperationError

```python
class StreamOperationError(StreamError):
    """ストリーム操作エラー"""
    
    def __init__(self, message: str, stream_type: str = None):
        """
        Args:
            message: エラーメッセージ
            stream_type: ストリームタイプ（オプション）
        """
```

**使用場面:**
- peek操作がサポートされていない
- ストリームアクセス失敗
- 読み取り権限不足

### 3.3 StreamBufferError

```python
class StreamBufferError(StreamError):
    """バッファ関連エラー"""
```

**使用場面:**
- バッファオーバーフロー
- バッファ破損
- メモリ不足

### 3.4 StreamCapabilityError

```python
class StreamCapabilityError(StreamError):
    """ストリーム能力不足エラー"""
    
    def __init__(self, operation: str, stream_type: str):
        """
        Args:
            operation: 失敗した操作名
            stream_type: ストリームタイプ
        """
```

**使用場面:**
- 未サポート操作の実行
- 機能制限による失敗

---

## 4. 設定クラス

### 4.1 StreamConfiguration

```python
@dataclass
class StreamConfiguration:
    """ストリーム機能の設定"""
    
    enable_peek_operations: bool = True
    enable_buffering: bool = True
    default_buffer_size: int = 1024
    enable_performance_monitoring: bool = False
    strict_compatibility_mode: bool = False
    
    @classmethod
    def from_dict(cls, config_dict: dict) -> 'StreamConfiguration':
        """辞書から設定オブジェクトを作成"""
```

**設定項目:**
- `enable_peek_operations`: peek機能の有効化
- `enable_buffering`: バッファ機能の有効化  
- `default_buffer_size`: デフォルトバッファサイズ
- `enable_performance_monitoring`: パフォーマンス監視の有効化
- `strict_compatibility_mode`: 厳密互換モードの有効化

**使用例:**
```python
config = StreamConfiguration(
    enable_peek_operations=True,
    default_buffer_size=2048
)

stream = create_stream_with_config("console", config)
```

---

### 4.2 StreamStatus

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

**使用例:**
```python
status = stream.get_stream_status()

if status.has_errors:
    print(f"Stream error: {status.error_message}")
elif status.at_eof:
    print("Stream has reached EOF")
else:
    print(f"Available characters: {status.buffered_chars}")
```

---

## 5. ユーティリティクラス

### 5.1 StreamBuffer

```python
class StreamBuffer:
    """効率的な文字バッファ管理"""
    
    def __init__(self, size: int):
        """
        Args:
            size: バッファサイズ
        """
    
    def peek_char(self) -> str:
        """先頭文字をpeek（位置変更なし）"""
    
    def read_char(self) -> str:
        """先頭文字を読み取り（位置を進める）"""
    
    def write(self, data: str) -> int:
        """データを書き込み"""
    
    def has_data(self) -> bool:
        """データ有無確認"""
    
    def available_space(self) -> int:
        """利用可能スペース取得"""
```

### 5.2 LegacyStreamWrapper

```python
class LegacyStreamWrapper(IOStream):
    """レガシーストリームのラッパー"""
    
    def __init__(self, wrapped_stream: IOStream):
        """
        Args:
            wrapped_stream: ラップ対象のストリーム
        """
```

**機能:**
- レガシーストリームに制限付きpeek機能を提供
- 1文字の先読みバッファを内部で管理
- 既存コードの移行を支援

---

## 6. 使用例

### 6.1 基本的な使用パターン

```python
# ランタイム初期化
from pyprolog.runtime.interpreter import Runtime
from pyprolog.runtime.io_streams import StringStream
from pyprolog.core.types import Variable

runtime = Runtime()

# ストリーム設定
input_data = "hello world"
stream = StringStream(input_data)
runtime.io_manager.set_input_stream(stream)

# peek_char使用
peek_result = runtime.query("peek_char(X)")
print(f"Next character: {peek_result[0][Variable('X')]}")  # 'h'

# 同じ文字がもう一度取得される
peek_again = runtime.query("peek_char(Y)")
print(f"Same character: {peek_again[0][Variable('Y')]}")  # 'h'

# 実際に文字を消費
consume_result = runtime.query("get_char(Z)")
print(f"Consumed: {consume_result[0][Variable('Z')]}")  # 'h'

# EOF確認
eof_result = runtime.query("at_end_of_stream")
print(f"At EOF: {len(eof_result) > 0}")  # False（まだデータあり）
```

### 6.2 条件付き読み取りパターン

```python
# 数字判定ルール
runtime.add_rule("""
read_if_digit(Char) :-
    peek_char(Next),
    Next >= '0',
    Next =< '9',
    get_char(Char).

read_if_letter(Char) :-
    peek_char(Next),
    Next >= 'a',
    Next =< 'z',
    get_char(Char).
""")

# テストデータ
runtime.io_manager.set_input_stream(StringStream("5abc"))

# 数字の場合のみ読み取り
digit_result = runtime.query("read_if_digit(D)")
if digit_result:
    print(f"Read digit: {digit_result[0][Variable('D')]}")  # '5'

# 文字の場合のみ読み取り
letter_result = runtime.query("read_if_letter(L)")
if letter_result:
    print(f"Read letter: {letter_result[0][Variable('L')]}")  # 'a'
```

### 6.3 パーサー実装パターン

```python
# トークン解析ルール
runtime.add_rule("""
% 数値トークン
parse_number(Num) :-
    peek_char(First),
    First >= '0', First =< '9',
    collect_digits(Digits),
    atom_codes(Num, Digits).

% 数字収集（再帰）
collect_digits([D|Ds]) :-
    peek_char(C),
    C >= '0', C =< '9',
    get_char(C),
    char_code(C, D),
    collect_digits(Ds).

collect_digits([]) :-
    peek_char(C),
    (C < '0' ; C > '9').

% 空白スキップ
skip_whitespace :-
    peek_char(' '),
    get_char(_),
    skip_whitespace.

skip_whitespace :-
    peek_char(C),
    C \= ' '.

% EOFチェック付きトークン読み取り
next_token(Token) :-
    skip_whitespace,
    (at_end_of_stream ->
        Token = eof
    ;   parse_number(Token)
    ).
""")

# パーサーテスト
test_input = "  123   456  "
runtime.io_manager.set_input_stream(StringStream(test_input))

# トークンを順次解析
token1 = runtime.query("next_token(T1)")  # '123'
token2 = runtime.query("next_token(T2)")  # '456'  
token3 = runtime.query("next_token(T3)")  # 'eof'
```

### 6.4 エラーハンドリングパターン

```python
def safe_peek_char(runtime):
    """安全なpeek_char操作"""
    try:
        # ストリームサポート確認
        stream = runtime.io_manager.get_input_stream()
        if not stream.supports_peek_operations():
            print("Peek operations not supported")
            return None
        
        # peek操作実行
        result = runtime.query("peek_char(X)")
        if result:
            return result[0][Variable("X")]
        else:
            print("Peek operation failed")
            return None
            
    except StreamOperationError as e:
        print(f"Stream operation error: {e}")
        return None
    except PrologError as e:
        print(f"Prolog error: {e}")
        return None

# 使用例
char = safe_peek_char(runtime)
if char:
    print(f"Next character: {char}")
```

---

## 7. 移行ガイド

### 7.1 既存コードからの移行

**移行前:**
```python
# ブロッキング読み取り
runtime = Runtime()
result = runtime.query("get_char(X)")  # 入力待ちで停止
```

**移行後:**
```python
# 非ブロッキング確認後の読み取り
runtime = Runtime()

# まず入力の有無を確認
if not runtime.query("at_end_of_stream"):
    # 入力があることを確認してから読み取り
    result = runtime.query("get_char(X)")
else:
    print("No input available")
```

### 7.2 段階的移行戦略

**Phase 1: 基本機能導入**
```python
# 既存コードは変更せず、新機能のみ追加
runtime = Runtime()

# 新機能をオプションで使用
try:
    peek_result = runtime.query("peek_char(X)")
    # peek成功時の処理
except PrologError:
    # フォールバック: 既存の方法を使用
    result = runtime.query("get_char(X)")
```

**Phase 2: 徐々に置き換え**
```python
def smart_char_read(runtime):
    """スマートな文字読み取り"""
    # 可能ならpeekを使用
    if runtime.io_manager.get_input_stream().supports_peek_operations():
        peek_result = runtime.query("peek_char(X)")
        if peek_result:
            # 必要に応じて実際に読み取り
            return runtime.query("get_char(Y)")
    
    # フォールバック
    return runtime.query("get_char(Z)")
```

**Phase 3: 完全移行**
```python
from pyprolog.runtime.interpreter import Runtime
from pyprolog.config.stream_config import StreamConfiguration, create_stream_with_config

# 全てのコードで新機能を活用
runtime = Runtime()

# 設定で新機能を有効化
config = StreamConfiguration(enable_peek_operations=True)
stream = create_stream_with_config("console", config)
runtime.io_manager.set_input_stream(stream)

# 新しいパターンで実装
result = safe_peek_and_read(runtime)
```

---

## 8. トラブルシューティング

### 8.1 よくある問題と解決策

**問題1: "Stream does not support peek_char" エラー**

**原因:** ストリームがpeek操作をサポートしていない

**解決策:**
```python
# ストリームサポート確認
stream = runtime.io_manager.get_input_stream()
if stream.supports_peek_operations():
    result = runtime.query("peek_char(X)")
else:
    # サポートするストリームに置き換え
    new_stream = StringStream(existing_data)
    runtime.io_manager.set_input_stream(new_stream)
```

**問題2: peek_charが常に同じ文字を返す**

**原因:** peek_charの正常な動作（位置を変更しないため）

**解決策:**
```python
# 意図した動作の場合
char = runtime.query("peek_char(X)")  # 同じ文字
char = runtime.query("peek_char(Y)")  # 同じ文字

# 次の文字を取得したい場合
runtime.query("get_char(_)")  # 現在の文字を消費
next_char = runtime.query("peek_char(Z)")  # 次の文字
```

**問題3: at_end_of_streamが期待通りに動作しない**

**原因:** バッファリングまたは状態の不整合

**解決策:**
```python
# ストリーム状態確認
stream = runtime.io_manager.get_input_stream()
status = stream.get_stream_status()

print(f"At EOF: {status.at_eof}")
print(f"Has data: {status.has_data_available}")
print(f"Buffer position: {status.buffer_position}")

# 状態リフレッシュ（必要に応じて）
runtime.query("peek_char(_)")  # バッファ状態更新
```

**問題4: パフォーマンスの低下**

**原因:** 頻繁なpeek操作やバッファ効率の問題

**解決策:**
```python
# バッファサイズ調整
config = StreamConfiguration(default_buffer_size=4096)
stream = create_stream_with_config("console", config)

# 不要なpeek操作の削減
# 悪い例
for i in range(1000):
    runtime.query("peek_char(X)")

# 良い例
peek_result = runtime.query("peek_char(X)")
# 結果を再利用
```

### 8.2 デバッグ支援

**ログ出力の有効化:**
```python
import logging
logging.getLogger('pyprolog.runtime.io_streams').setLevel(logging.DEBUG)

# 詳細なストリーム操作ログが出力される
```

**ストリーム状態の監視:**
```python
def monitor_stream_operations(runtime):
    """ストリーム操作の監視"""
    stream = runtime.io_manager.get_input_stream()
    
    if hasattr(stream, 'get_performance_metrics'):
        metrics = stream.get_performance_metrics()
        print(f"Peek operations: {metrics['peek_count']}")
        print(f"Average response time: {metrics['avg_response_time']}")
```

**テスト環境での確認:**
```python
def test_peek_functionality():
    """peek機能の動作確認"""
    test_cases = [
        ("empty", ""),
        ("single", "x"),
        ("multi", "hello"),
        ("unicode", "こんにちは")
    ]
    
    for name, data in test_cases:
        stream = StringStream(data)
        runtime = Runtime()
        runtime.io_manager.set_input_stream(stream)
        
        print(f"Testing {name}: {data}")
        
        # peek操作
        try:
            peek_result = runtime.query("peek_char(X)")
            print(f"  Peek result: {peek_result}")
        except Exception as e:
            print(f"  Peek error: {e}")
        
        # EOF確認
        try:
            eof_result = runtime.query("at_end_of_stream")
            print(f"  EOF status: {len(eof_result) > 0}")
        except Exception as e:
            print(f"  EOF error: {e}")
```

---

**作成者**: Claude Code  
**日時**: 2025年8月6日  
**バージョン**: 1.0