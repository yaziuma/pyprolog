# PyProlog（PieProlog）の改善実装計画

## 問題の概要

提供された資料から、PyProlog（PieProlog）というPythonベースのPrologインタープリターに複数の問題があることが特定されました。これらの問題はパーサー、インタープリター、算術演算、型処理など多岐にわたります。テスト結果からも明らかなように、基本的な機能が適切に機能していません。

## 主要な問題点

### 1. パーサーの問題

- **空リスト `[]` の誤解釈**: 空リストが誤って `[[]]` として解釈される
- **基本アトムの認識不良**: `true`、`fail`などの基本アトムが認識されない
- **演算子の処理不足**: `=`（単一化）などの演算子がスキャナーによって適切に処理されない

テスト結果から見られるエラー：
```
Line[1] Error: Bad atom name: true
Line[1] Error: Bad atom name: fail
Line[1] Error: Unexpected character: =
```

### 2. インタープリターの問題

- **カット演算子 (`!`) の処理不備**: カットがルールのボディ部でのみ出現した場合に `AttributeError: 'Cut' object has no attribute 'query'` が発生
- **変数束縛と再帰の問題**: 再帰呼び出しにおいて変数束縛が正しく伝播されない
- **`is` 述語の束縛問題**: 算術評価と変数束縛のプロセスが不完全

### 3. 算術演算機能の不足

- **標準的な演算子の未実装**: `mod`（剰余）演算子や整数除算 (`div`, `//`) などが実装されていない

### 4. `FALSE` 型の誤った処理

- クエリが論理的に偽になった場合の結果処理に問題

## 改善実装計画

### 1. スキャナーとパーサーの修正

#### 1.1. スキャナーの改善 (`scanner.py`)

```python
def _scan_token(self):
    c = self._advance()
    
    # 既存のコード...
    
    # '=' 演算子のサポートを追加
    if c == '=':
        self._add_token(TokenType.EQUAL)
        return
        
    # その他の基本演算子も同様に処理
```

#### 1.2. トークンタイプの拡張 (`token_type.py`)

```python
class TokenType(Enum):
    # 既存のトークン...
    
    # 新しいトークンを追加
    EQUAL = auto()  # = 演算子用
    TRUE = auto()   # true 述語用
    MOD = auto()    # mod 演算子用
    DIV = auto()    # div または // 演算子用
```

#### 1.3. パーサーの空リスト処理修正 (`parser.py`)

```python
def _parse_list(self):
    logger.debug(f"Parser._parse_list entered. Current token: {self._peek()}")
    dot_list = []
    dot_tail = None
    self._advance()  # consume '['

    # 空リスト処理の明示的なケース
    if self._token_matches(TokenType.RIGHTBRACKET):
        self._advance()  # consume ']'
        result = Dot.from_list([])
        logger.debug(f"Parser._parse_list: parsed empty list: {result}")
        return result
        
    # 既存の処理を継続...
```

#### 1.4. 基本アトムの認識改善 (`parser.py`)

```python
def _parse_atom(self):
    token = self._advance()
    
    # 特別なアトムを明示的に処理
    if token.lexeme == 'true':
        return TRUE()
    if token.lexeme == 'fail':
        return Fail()
    
    # その他のアトム処理...
```

### 2. インタープリターの修正

#### 2.1. カット演算子 (`!`) の修正 (`interpreter.py` と `builtins.py`)

```python
# builtins.py に query メソッドを追加
class Cut(Term):
    def __init__(self):
        super().__init__('!')
        
    def query(self, runtime, bindings=None):
        # カットはそれ自体は成功し、バインディングは変更しない
        if bindings is None:
            bindings = {}
        yield TRUE()
```

```python
# interpreter.py の Conjunction.query メソッド内でカット処理を改善
if self._is_cut(arg):
    logger.debug(f"Conjunction.solutions: arg is CUT {arg}")
    # カット自体は成功する
    for _ in runtime.execute(arg.substitute(bindings)):
        # カット後のゴールを処理
        yield from solutions(index + 1, bindings)
        # CUT信号を送出し処理を終了
        logger.debug(f"Conjunction.solutions: Yielding CUT signal after solutions for goals post-cut.")
        yield CUT()
        return  # 重要: カット後に他の選択肢を探索しない
```

#### 2.2. 変数束縛処理の改善 (`types.py`)

```python
def substitute(self, bindings):
    logger.debug(f"Variable.substitute({self}) called with bindings: {bindings}")
    # bindings が None の場合の防御的処理
    if bindings is None:
        logger.warning(f"Variable.substitute: bindings is None for {self}")
        return self
        
    value = bindings.get(self, None)
    if value is not None:
        result = value.substitute(bindings)
        logger.debug(f"Variable.substitute returning (from value): {result}")
        return result
    logger.debug(f"Variable.substitute returning (self): {self}")
    return self
```

#### 2.3. `is` 述語の処理改善

```python
# interpreter.py の evaluate_rules メソッド内
if isinstance(substituted_rule_body, Arithmetic):
    logger.debug(f"Runtime.evaluate_rules: Body is Arithmetic: {substituted_rule_body}")
    if hasattr(substituted_rule_body, 'var') and isinstance(substituted_rule_body.var, Variable):
        var_to_bind = substituted_rule_body.var
        value = substituted_rule_body.evaluate()
        
        final_head_for_arith = substituted_rule_head.substitute({var_to_bind: value})
        logger.debug(f"Runtime.evaluate_rules: Arithmetic body evaluated. Yielding: {final_head_for_arith}")
        yield final_head_for_arith
    else:
        logger.warning(f"Runtime.evaluate_rules: Arithmetic body {substituted_rule_body} does not have expected 'var' attribute.")
```

### 3. 算術演算機能の拡充 (`math_interpreter.py`)

```python
def _compute_binary_operand(self, left, right, operator):
    # 既存の演算子処理...
    
    # mod 演算子の追加
    if operator == "mod":
        if right.val == 0:
            return FALSE()  # ゼロ除算防止
        return Number(left.val % right.val)
    
    # 整数除算演算子の追加
    if operator == "//" or operator == "div":
        if right.val == 0:
            return FALSE()  # ゼロ除算防止
        return Number(left.val // right.val)
```

### 4. `FALSE` 型の処理改善 (`interpreter.py` の `query` メソッド)

```python
def query(self, query_str):
    # 中略...
    
    solution_count = 0
    for solution_item in self.execute(parsed_query):
        logger.debug(f"Runtime.query: solution_item from execute: {solution_item}")
        if isinstance(solution_item, FALSE) or solution_item is None:
            logger.debug("Runtime.query: solution_item is FALSE or None, skipping.")
            continue
        
        # その他の処理...
        
    # FALSEの場合は解なしを意味する (空のリストを返す)
    logger.info(f"Runtime.query for '{query_str}' finished. Total solutions yielded: {solution_count}")
```

### 5. リストの表現改善 (`types.py` の `Dot` クラス)

```python
@classmethod
def from_list(cls, lst):
    logger.debug(f"Dot.from_list called with: {lst}")
    # 空リストを正しく処理
    empty_list_node = cls(Term("[]"), None)

    if not lst:
        logger.debug(f"Dot.from_list returning (empty list): {empty_list_node}")
        return empty_list_node

    # リストを逆順に走査して、Prologのリスト構造を構築
    current_tail = empty_list_node
    for element in reversed(lst):
        current_tail = cls(element, current_tail)
    logger.debug(f"Dot.from_list returning: {current_tail}")
    return current_tail
```

## 実装方針と優先順位

1. **最初に対応すべき問題**:
   - パーサーの問題（空リスト処理、基本アトムの認識）
   - 基本的なクエリが動作するように修正

2. **次に対応すべき問題**:
   - カット演算子の処理
   - 変数束縛と再帰呼び出しの問題

3. **最後に対応すべき問題**:
   - 算術演算子の拡充
   - `FALSE` 型の処理改善

## テスト戦略

1. `TestBasicParsingAndTypes` のテストから順に修正し、基本機能を確保
2. `TestListProcessing` でリスト処理の改善を確認
3. `TestArithmeticAndIsPredicate` で算術演算の拡充を検証
4. `TestCutOperator` でカット演算子の処理を確認
5. `TestRecursion` で再帰的な問題を検証

## まとめ

PyProlog（PieProlog）の問題は複雑かつ相互依存性がありますが、計画的なアプローチで改善が可能です。パーサーとインタープリターの修正は最優先事項です。適切なロギングを活用して問題を診断し、テスト駆動で修正を進めることで、信頼性の高いPrologエンジンに改善できると考えられます。


# 追加： PyPrologの問題点と現在の改修状況の深堀り分析

提供された差分とテスト失敗の結果を詳細に分析すると、現在の改修が問題を完全に解決できていない理由がいくつか明らかになります。

## 1. スキャナー・パーサーの根本的な問題

### 問題点:
テスト結果を見ると、最も基本的なクエリ（`p(a)`, `true`, `fail`など）すらパースできていません。

```
Line[1] Error: Bad atom name: )
Line[1] Error: Bad atom name: true
Line[1] Error: Bad atom name: fail
Line[1] Error: Unexpected character: =
```

### 根本原因:
1. **バグがあるトークン処理**: スキャナーとパーサーの実装は大幅に改良されていますが、特定のアトムを適切に認識するロジックが完全ではありません。

2. **差分コードの部分適用**: 差分コードを見ると、ロギング機能の追加やソフトウェア構造の再設計は行われていますが、`_parse_atom`メソッドが特定のアトム名を正しく処理できていません。

3. **トークンタイプの拡張不足**: `token_type.py`への修正が差分に含まれていないため、新しいトークンタイプ（例: `EQUAL`、`TRUE`など）が定義されていない可能性があります。

## 2. リスト処理の不完全な改修

### 問題点:
差分コードには`_parse_list`メソッドの修正が含まれていますが、テスト結果がないため、この修正が適切に機能しているのかは不明です。

### 根本原因:
1. **Dot.from_list**の実装に問題: `types.py`の`Dot.from_list`メソッドは大幅に修正されているように見えますが、空リストの内部表現（Term("[]"), None）が正しい構造なのか確認が必要です。

2. **リスト処理のテスト未実行**: 基本的なアトムのパース段階で失敗しているため、リスト処理の改善がテストされていない状態です。

## 3. カット演算子の実装に関する問題

### 問題点:
現在の実装では、`interpreter.py`の`_is_cut`メソッドが修正されていますが、`builtins.Cut`と`types.CUT`の区別と役割が明確に分離されていません。

### 根本原因:
1. **混在する役割**: `builtins.Cut`はProlog文の一部として解析されるカット演算子で、`types.CUT`はインタプリタが内部で使用する制御シグナルです。両者の役割と連携に混乱があります。

2. **コメントは多いが具体的な修正は限定的**: 差分には多くの詳細なコメントがありますが、実際のロジック修正は限られています。例えば：

```python
# Corrected: was Cut, now BuiltinCut
if isinstance(arg, BuiltinCut):
    # ... 長いコメント ...
    for _ in runtime.execute(arg.substitute(bindings)):
        # ... 多くのコメントとロガー呼び出し ...
        yield from solutions(index + 1, bindings)
        yield CUT()
        return 
```

このコードは基本的なロジックは変わっておらず、オリジナルの問題を解決していない可能性があります。

## 4. 変数束縛と再帰呼び出しの問題

### 問題点:
インタプリタの変数束縛と再帰呼び出しの問題は、複雑なログ出力で診断しようとしていますが、コアロジックの修正は限定的です。

### 根本原因:
1. **束縛がNoneになる根本原因への対処不足**: `Variable.substitute`や`merge_bindings`メソッドが`None`を処理する防御的コードが含まれていませんが、なぜ`None`になるのかという根本原因は解決されていません。

2. **インタプリタのフロー制御問題**: `evaluate_rules`メソッドでの再帰評価と変数束縛の伝播が完全には修正されていません。特に`FALSE`の処理と`CUT`シグナルの伝播に関するロジックの改善が不十分です。

## 5. 算術演算子の実装不足

### 問題点:
Prologの標準的な算術演算子（`mod`, `div`, `//`など）は実装されていますが、それらをスキャン・パースするためのコードが差分に含まれていません。

### 根本原因:
1. **演算子認識の欠如**: スキャナーが新しい演算子を認識するためのコードが完全に実装されていない。

2. **算術評価の連携不足**: 算術演算子が追加されても、それを評価するコード変更が全体的に統合されていません。

## 6. テスト戦略の問題

### 問題点:
各テストが独立して実行されるため、特定の問題が解決しても、依存する他のテストは失敗し続けます。

### 根本原因:
1. **テスト依存性のカスケード失敗**: 最も基本的なクエリパースが失敗している間は、他の全てのテストも失敗するため、改善の効果がテストで確認できません。

2. **インクリメンタルなテスト戦略の欠如**: 現在の差分から見ると、最も基本的な問題（例：`p(a)`のパース）を最初に完全に解決する代わりに、多くの問題に同時に取り組んでいるように見えます。

## 提案される対策

### 1. スキャナー・パーサーを最優先で修正
最も基本的なクエリがパースできるようにする必要があります。特に：

- `scanner.py`に新しいトークンタイプを追加（`TokenType.EQUAL`, `TokenType.TRUE`など）
- `_scan_token`メソッドを修正して、これらのトークンを適切に認識
- `_parse_atom`メソッドを完全に見直し、基本アトムを正しく処理するようにする

### 2. 段階的テスト戦略
最も基本的なテストケースから始め、一つずつパスさせていく：

1. まず`test_simple_fact_consult_and_query`が通るように修正
2. 次に`test_true_predicate`と`test_fail_predicate`
3. その後、リスト処理などより複雑な機能に移行

### 3. 明確な責任分離
`builtins.Cut`と`types.CUT`の役割を明確に分離し、各コンポーネントの境界を整理します。

### 4. 防御的プログラミングの強化
`None`チェックなどの防御的コードをより体系的に追加し、予期しない状態に対して堅牢なコードにします。

## 結論

現在の改修は方向性は正しいものの、最も基本的な問題（スキャナー・パーサーの正確性）が完全に解決されていないため、その上に構築される高度な機能のテストができていません。また、問題解決のためのログ追加は多いですが、コアロジックの修正が不十分です。

成功の鍵は、最も基本的な問題から段階的に解決していくアプローチに改め、一度に全ての問題を解決しようとせず、確実に前進できる小さなステップで改善を積み重ねることです。


# PyProlog修正のための段階的アプローチ

修正したテストコードでは、具体的なTokenTypeの参照を避け、現在の実装でも実行可能なように柔軟性を持たせました。これらのテストは、PyPrologの修正プロセスを体系的に進めるための重要なガイドラインとなります。

## 段階的修正計画

PyPrologの問題を効果的に解決するために、以下の段階的なアプローチを提案します。

- [x] ### 第1段階：スキャナーとパーサーの基本修正 (完了)

現在の最大の問題は、基本的なトークン認識とパース機能が適切に機能していないことです。

- [x] #### 修正1-1: トークンタイプの拡張

```python
# token_type.py の修正
class TokenType(Enum):
    # 既存のトークン
    LEFTPAREN = auto()
    RIGHTPAREN = auto()
    # ... 他の既存トークン
    
    # 追加するトークン
    TRUE = auto()    # true アトム用
    FAIL = auto()    # fail アトム用
    EQUAL = auto()   # = 演算子用
    MOD = auto()     # mod 演算子用
    DIV = auto()     # // または div 演算子用
    CUT = auto()     # ! カット演算子用
```

- [x] #### 修正1-2: スキャナーのトークン認識改善

```python
# scanner.py の _scan_token メソッド修正
def _scan_token(self):
    c = self._advance()
    
    # 括弧や既存のトークン処理...
    
    # 特殊演算子の処理追加
    elif c == '=':
        self._add_token(TokenType.EQUAL)
    elif c == '!':
        self._add_token(TokenType.CUT)
    
    # アルファベット文字で始まるアトムやキーワード
    elif self._is_alpha(c):
        while not self._is_at_end() and self._is_alphanumeric(self._peek()):
            self._advance()
        
        text = self._source[self._start:self._current]
        
        # 特殊キーワードのチェック
        if text == "true":
            self._add_token(TokenType.TRUE)
        elif text == "fail":
            self._add_token(TokenType.FAIL)
        elif text == "mod":
            self._add_token(TokenType.MOD)
        # ... 他の特殊キーワード
        
        else:
            # 通常のアトムとして処理
            self._add_token(TokenType.ATOM, text)
    
    # ... 残りの処理
```

- [x] #### 修正1-3: パーサーの基本的な構文認識改善

```python
# parser.py の修正

# _parse_atom メソッドの修正
def _parse_atom(self):
    token = self._advance()
    
    # 特殊キーワードの処理
    if self._is_type(token, TokenType.TRUE):
        return TRUE()
    if self._is_type(token, TokenType.FAIL):
        return Fail()
    if self._is_type(token, TokenType.CUT):
        return Cut()
    
    # ... 残りの処理
```

```python
# _parse_list メソッドの修正 - 空リスト処理追加
def _parse_list(self):
    dot_list = []
    dot_tail = None
    self._advance()  # '[' を消費
    
    # 空リストのケース: []
    if self._token_matches(TokenType.RIGHTBRACKET):
        self._advance()  # ']' を消費
        return Dot.from_list([])
    
    # ... 残りのリスト処理
```

### 第2段階：リスト表現の修正 (作業中 - テスト失敗)

空リストの内部表現を修正することは、多くのテスト失敗を解決するために不可欠です。
`prolog/types.py` の `Dot.from_list` は修正されましたが、`tests/test_core_improvements.py::TestListProcessing` のテストが `IndexError` で失敗しています。これはパーサー(`prolog/parser.py`)側の問題である可能性が高いです。引き続き調査と修正が必要です。

```python
# types.py の Dot.from_list メソッド修正
@classmethod
def from_list(cls, lst):
    # 空リストの特殊ケース
    if not lst:
        return cls(Term("[]"), None)  # 空リストは Term("[]") を head に持ち、tail は None
    
    # 非空リストの処理
    current_tail = cls(Term("[]"), None)  # 空リストで終了
    for element in reversed(lst):
        current_tail = cls(element, current_tail)
    
    return current_tail
```

### 第3段階：変数束縛と単一化の修正

変数束縛の問題は、特に再帰的な呼び出しで顕著です。

```python
# Variable.substitute メソッドの修正
def substitute(self, bindings):
    # 防御的なNullチェック
    if bindings is None:
        return self
    
    value = bindings.get(self, None)
    if value is not None:
        # 無限再帰防止のため、自己参照をチェック
        if value == self:
            return self
        return value.substitute(bindings)
    return self
```

```python
# merge_bindings.py の merge_bindings 関数強化
def merge_bindings(bindings1, bindings2):
    if bindings1 is None or bindings2 is None:
        return None
    
    # 既存のマージロジック...
    # 矛盾するバインディングのチェックを強化
    
    return result_bindings
```

### 第4段階：インタープリターの改善とカット演算子の修正

カット演算子の処理は、インタープリターの制御フローを正しく管理するために重要です。

```python
# builtins.py の Cut クラス修正
class Cut(Term):
    def __init__(self):
        super().__init__('!')
    
    def query(self, runtime, bindings=None):
        # カット演算子は常に一度だけ成功する
        if bindings is None:
            bindings = {}
        yield TRUE()
```

```python
# interpreter.py の Conjunction.query メソッド修正（カット処理部分）
if self._is_cut(arg):
    # カットの処理
    for _ in runtime.execute(arg.substitute(bindings)):
        # カット後のゴール実行
        yield from solutions(index + 1, bindings)
        # CUTシグナルを出してバックトラックを停止
        yield CUT()
        return  # 即座に終了
```

### 第5段階：算術演算の拡充

```python
# math_interpreter.py の _compute_binary_operand メソッド拡充
def _compute_binary_operand(self, left, right, operator):
    # 既存の演算子...
    
    # mod 演算子追加
    if operator == "mod":
        if right.val == 0:
            return FALSE()  # ゼロ除算防止
        return Number(left.val % right.val)
    
    # 整数除算演算子追加
    if operator == "//" or operator == "div":
        if right.val == 0:
            return FALSE()  # ゼロ除算防止
        return Number(left.val // right.val)
```

## 実装戦略

### 修正の優先順位

1. **最優先: スキャナーとパーサー** - すべてのテストの基礎となる部分
2. **第二優先: リスト処理** - 多くのテストがリストに依存
3. **第三優先: 変数束縛とインタープリター** - 再帰とカットの正確な処理
4. **第四優先: 算術演算拡充** - より高度な機能の実装

### テスト駆動の修正プロセス

1. `TestTokenizerAndParserBasics` の最も基本的なテストから始める
2. 一つずつテストをパスさせながら修正を進める
3. 各段階で既存の機能を壊さないよう回帰テストを実行

### 具体的な修正手順

#### ステップ1: スキャナー修正
現在のテスト失敗から、最初に集中すべきは特殊トークン（トークン、ドット、演算子）の認識です。`Token`, `TokenType`, `Scanner`クラスを修正して、基本的なトークン化をサポートします。

#### ステップ2: パーサー修正
次に、`Parser`クラスのメソッドを改修して、基本的なアトム、演算子、リストが正しくパースされるようにします。特に`_parse_atom`と`_parse_list`メソッドに注目します。

#### ステップ3: Dot.from_list 実装の修正
リスト表現に関する問題を解決するため、`Dot.from_list`メソッドを完全に書き直します。

#### ステップ4: インタープリターと束縛処理の修正
`Variable.substitute`, `merge_bindings`, およびインタープリターの`Conjunction.query`メソッドなど、変数束縛とフロー制御に関する部分を修正します。

#### ステップ5: 算術演算拡充
最後に、算術演算機能を拡充し、テストがすべてパスすることを確認します。

## 結論

提案した段階的な修正アプローチと細かいテストを活用することで、PyPrologの問題を体系的に解決できます。最も基本的な機能（スキャナーとパーサー）から始め、段階的に複雑な機能（再帰、カット、高度なリスト処理）へと進むことで、すべてのテストが最終的にパスするよう目指します。

このプロセスは、単に現在の問題を解決するだけでなく、将来的に拡張しやすく保守性の高いコードベースを構築するのにも役立ちます。
