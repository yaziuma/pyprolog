# Prologインタープリタ：実行時インタラクション機能 概要設計

## 1. 概要

Prologプログラム実行中にユーザとの対話的入出力を可能にする機能を設計します。標準的なProlog I/O述語を実装し、現在の出力専用システムを双方向通信システムに拡張します。

## 2. 主要な拡張項目

### 2.1 新規実装予定述語

#### 基本入力述語
- `read/1` - Prolog項をユーザから読み取り
- `get_char/1` - 1文字を読み取り
- `get_code/1` - 文字コードを読み取り
- `read_term/2` - オプション付きで項を読み取り

#### 基本出力述語（拡張）
- `put_char/1` - 1文字を出力
- `put_code/1` - 文字コードから1文字を出力
- `format/2` - フォーマット指定付き出力

#### ストリーム管理述語
- `current_input/1` - 現在の入力ストリームを取得
- `current_output/1` - 現在の出力ストリームを取得
- `set_input/1` - 入力ストリームを設定
- `set_output/1` - 出力ストリームを設定

#### 対話支援述語
- `prompt/2` - プロンプト表示と入力
- `ask_user/2` - yes/no質問

## 3. アーキテクチャ設計

### 3.1 ストリーム抽象化層

```python
# prolog/runtime/io_streams.py
class IOStream(ABC):
    @abstractmethod
    def read_char(self) -> str:
        pass
    
    @abstractmethod
    def write_char(self, char: str):
        pass
    
    @abstractmethod
    def read_term(self) -> PrologType:
        pass
    
    @abstractmethod
    def write_term(self, term: PrologType):
        pass

class ConsoleStream(IOStream):
    """標準入出力ストリーム"""
    def read_char(self) -> str:
        return input()[:1] if input() else '\n'
    
    def read_term(self) -> PrologType:
        # Scanner/Parserを使ってProlog項をパース
        pass

class FileStream(IOStream):
    """ファイルストリーム"""
    pass

class StringStream(IOStream):
    """文字列ストリーム（テスト用）"""
    pass
```

### 3.2 IOマネージャー

```python
# prolog/runtime/io_manager.py
class IOManager:
    def __init__(self):
        self.input_stream = ConsoleStream()
        self.output_stream = ConsoleStream()
        self.streams = {}  # ストリーム登録
    
    def read_term(self) -> PrologType:
        return self.input_stream.read_term()
    
    def write_term(self, term: PrologType):
        self.output_stream.write_term(term)
    
    def set_input_stream(self, stream: IOStream):
        self.input_stream = stream
    
    def set_output_stream(self, stream: IOStream):
        self.output_stream = stream
```

### 3.3 Runtime統合

```python
# prolog/runtime/interpreter.py（修正）
class Runtime:
    def __init__(self, rules=None):
        # 既存の初期化
        self.io_manager = IOManager()  # 新規追加
    
    def _create_io_evaluator(self, op_info: OperatorInfo):
        """IO演算子の評価器（拡張）"""
        def evaluator(args, env):
            if op_info.symbol == "read":
                # read/1の実装
                if len(args) != 1:
                    raise PrologError("read/1 requires exactly 1 argument")
                
                try:
                    term = self.io_manager.read_term()
                    unified, new_env = self.logic_interpreter.unify(args[0], term, env)
                    if unified:
                        yield new_env
                except Exception as e:
                    logger.error(f"Read error: {e}")
            
            elif op_info.symbol == "get_char":
                # get_char/1の実装
                if len(args) != 1:
                    raise PrologError("get_char/1 requires exactly 1 argument")
                
                try:
                    char = self.io_manager.input_stream.read_char()
                    char_atom = Atom(char)
                    unified, new_env = self.logic_interpreter.unify(args[0], char_atom, env)
                    if unified:
                        yield new_env
                except Exception as e:
                    logger.error(f"Get char error: {e}")
            
            # 他のIO述語の実装...
        
        return evaluator
```

## 4. 新規述語の詳細設計

### 4.1 read/1

```prolog
% 使用例
?- read(X).
|: hello(world).
X = hello(world).

?- read(Term), write(Term).
|: [1,2,3].
[1,2,3]
Term = [1,2,3].
```

**実装ポイント：**
- ユーザ入力をScanner/Parserでパース
- 不正な構文の場合はエラーハンドリング
- EOF処理

### 4.2 get_char/1

```prolog
% 使用例
?- get_char(C).
|: a
C = a.

?- get_char(C1), get_char(C2).
|: ab
C1 = a, C2 = b.
```

**実装ポイント：**
- バッファリング管理
- 特殊文字（改行、EOF等）の処理

### 4.3 prompt/2

```prolog
% 使用例
?- prompt('Enter your name: ', Name).
Enter your name: |: john
Name = john.

?- prompt('Continue? (y/n): ', Answer), Answer = y.
Continue? (y/n): |: y
Answer = y.
```

**実装ポイント：**
- プロンプト表示
- レスポンス読み取り
- 型変換（必要に応じて）

## 5. エラーハンドリング

### 5.1 例外型定義

```python
# prolog/core/errors.py（拡張）
class IOError(PrologError):
    pass

class ReadError(IOError):
    pass

class WriteError(IOError):
    pass

class StreamError(IOError):
    pass
```

### 5.2 エラー処理方針

- **構文エラー**: 再入力を促す
- **EOF**: 専用のアトム `end_of_file` を返す
- **ストリームエラー**: 例外をthrow
- **タイムアウト**: オプションでサポート

## 6. テスト設計

### 6.1 単体テスト

```python
# tests/runtime/test_interactive_io.py
class TestInteractiveIO:
    def test_read_simple_atom(self):
        """基本的なアトムの読み取りテスト"""
        pass
    
    def test_read_complex_term(self):
        """複合項の読み取りテスト"""
        pass
    
    def test_get_char(self):
        """文字読み取りテスト"""
        pass
    
    def test_prompt_interaction(self):
        """プロンプト対話テスト"""
        pass
```

### 6.2 統合テスト

```python
# tests/integration/test_interactive_session.py
class TestInteractiveSession:
    def test_calculator_program(self):
        """対話的計算機プログラムのテスト"""
        pass
    
    def test_question_answer_system(self):
        """質問応答システムのテスト"""
        pass
```

## 7. 実装スケジュール

### フェーズ1：基盤整備（2週間）
- IOStream抽象化層の実装
- IOManagerの基本機能
- Runtime統合

### フェーズ2：基本入力述語（1週間）
- `read/1`の実装
- `get_char/1`の実装
- 基本テストの作成

### フェーズ3：拡張機能（1週間）
- `prompt/2`の実装
- フォーマット出力の拡張
- エラーハンドリング強化

### フェーズ4：テスト・最適化（1週間）
- 包括的なテストスイート
- パフォーマンス最適化
- ドキュメント整備

## 8. 使用例シナリオ

### 8.1 対話的計算機

```prolog
calculator :-
    write('Simple Calculator'), nl,
    write('Enter expression (or quit to exit): '),
    read(Input),
    ( Input = quit -> 
        write('Goodbye!'), nl
    ; 
        Result is Input,
        write('Result: '), write(Result), nl,
        calculator
    ).
```

### 8.2 質問応答システム

```prolog
expert_system :-
    prompt('What is your problem? ', Problem),
    diagnose(Problem, Solution),
    write('Suggested solution: '), write(Solution), nl.

diagnose(computer_slow, 'Restart your computer').
diagnose(internet_down, 'Check your network connection').
diagnose(_, 'Contact technical support').
```

