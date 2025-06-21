# PyProlog ファンクター名日本語対応 詳細設計書

## 📋 設計概要

### 目的

PyProlog において、述語名（ファンクター名）の日本語対応を実現し、完全な日本語 Prolog プログラムの実行を可能にする。

### 対象範囲

```prolog
% 実現したい記述
親(太郎, 花子).
男性(太郎).
女性(花子).
父親(X, Y) :- 親(X, Y), 男性(X).

% 現在（変数のみ対応）
parent(太郎, 花子).  % ファンクター名は英語のまま
```

### 設計方針

1. **既存アーキテクチャとの互換性維持**
2. **段階的実装による安全性確保**
3. **性能への影響最小化**
4. **拡張性を考慮した設計**

---

## 🏗️ アーキテクチャ設計

### システム全体図

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   入力ソース     │    │  内部表現処理    │    │   出力結果      │
│                 │    │                 │    │                 │
│ 親(太郎, 花子)   │───▶│ F1(V1, V2)      │───▶│ 親(太郎, 花子)   │
│ 男性(太郎)       │    │ F2(V1)          │    │ 男性(太郎)       │
│ 父親(X,Y):-...   │    │ F3(X,Y):-...    │    │ 父親(X,Y):-...   │
└─────────────────┘    └─────────────────┘    └─────────────────┘
        │                        │                        ▲
        ▼                        │                        │
┌─────────────────┐              │              ┌─────────────────┐
│ FunctorMapper   │              │              │ 出力時復元処理   │
│                 │              ▼              │                 │
│ 親 ←→ F1        │    ┌─────────────────┐    │ F1 → 親          │
│ 男性 ←→ F2      │    │ Parser/Runtime  │    │ V1 → 太郎        │
│ 父親 ←→ F3      │    │ (既存処理)       │    │                 │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

### コンポーネント構成

```
pyprolog/
├── util/
│   ├── variable_mapper.py      # 既存：変数名マッピング
│   └── functor_mapper.py       # 新規：ファンクター名マッピング
├── parser/
│   ├── scanner.py              # 修正：日本語ファンクター対応
│   └── parser.py               # 修正：マッピング統合
└── runtime/
    └── interpreter.py          # 修正：出力時復元処理
```

---

## 📝 詳細仕様

### 1. FunctorMapper クラス設計

#### 1.1 基本インターフェース

```python
class FunctorMapper:
    """ファンクター名の日本語⇔英語マッピング管理"""

    def __init__(self):
        self._japanese_to_english: Dict[str, str] = {}
        self._english_to_japanese: Dict[str, str] = {}
        self._next_functor_index: int = 1

    def map_japanese_to_english(self, japanese_functor: str) -> str:
        """日本語ファンクター名を英語に変換"""

    def map_english_to_japanese(self, english_functor: str) -> str:
        """英語ファンクター名を日本語に復元"""

    def is_japanese_functor(self, name: str) -> bool:
        """日本語ファンクター名かどうかを判定"""

    def clear_mapping(self):
        """マッピング情報をクリア"""

    def get_all_mappings(self) -> Tuple[Dict[str, str], Dict[str, str]]:
        """全マッピング情報を取得"""
```

#### 1.2 日本語判定ロジック

```python
def is_japanese_functor(self, name: str) -> bool:
    """
    日本語ファンクター名の判定条件：
    1. ひらがな、カタカナ、漢字を含む
    2. 英数字、アンダースコアとの組み合わせ可
    3. 変数名判定とは区別（大文字開始でも日本語文字があればファンクター）
    """
    if not name:
        return False

    # 日本語文字が含まれているかチェック
    japanese_chars = re.search(r'[ぁ-ゟ゠-ヿ一-鿿]', name)
    return japanese_chars is not None
```

#### 1.3 マッピング生成ロジック

```python
def _generate_english_functor(self) -> str:
    """
    英語ファンクター名生成：F1, F2, F3, ...
    重複回避のためのインデックス管理
    """
    while True:
        functor_name = f"F{self._next_functor_index}"
        if functor_name not in self._english_to_japanese:
            self._next_functor_index += 1
            return functor_name
        self._next_functor_index += 1

def map_japanese_to_english(self, japanese_functor: str) -> str:
    """日本語→英語マッピング（キャッシュ機能付き）"""
    if not self.is_japanese_functor(japanese_functor):
        return japanese_functor  # 日本語でない場合はそのまま返す

    if japanese_functor in self._japanese_to_english:
        return self._japanese_to_english[japanese_functor]

    # 新規マッピング作成
    english_functor = self._generate_english_functor()
    self._japanese_to_english[japanese_functor] = english_functor
    self._english_to_japanese[english_functor] = japanese_functor

    return english_functor
```

### 2. Scanner の修正設計

#### 2.1 コンストラクタ修正

```python
class Scanner:
    def __init__(
        self,
        source: str,
        report: Callable[[int, str], None] = default_error_handler,
        variable_mapper: Optional[VariableMapper] = None,
        functor_mapper: Optional[FunctorMapper] = None,  # 追加
    ):
        # 既存の初期化処理
        self._functor_mapper = functor_mapper  # 追加
```

#### 2.2 識別子処理の修正

```python
def _identifier(self):
    """識別子のスキャン（ファンクター対応版）"""
    while self._peek().isalnum() or self._peek() == "_" or \
          self._contains_japanese_char(self._source[self._start : self._current + 1]):
        self._advance()

    text = self._source[self._start : self._current]
    literal_override = None

    # キーワードチェック（既存）
    token_type = self._keywords.get(text)

    if token_type is None:
        # 演算子キーワードチェック（既存）
        if text in self._operator_symbols:
            token_type = self._operator_symbols[text]

        # 日本語ファンクター処理（新規）
        elif self._functor_mapper and self._functor_mapper.is_japanese_functor(text):
            token_type = TokenType.ATOM
            literal_override = self._functor_mapper.map_japanese_to_english(text)
            logger.debug(f"Mapped Japanese functor '{text}' to '{literal_override}'")

        # 日本語変数処理（既存）
        elif self._variable_mapper and self._variable_mapper.is_japanese_variable(text):
            token_type = TokenType.VARIABLE
            literal_override = self._variable_mapper.map_japanese_to_english(text)

        # 英語識別子処理（既存）
        elif text[0].isupper() or text[0] == "_":
            token_type = TokenType.VARIABLE
        else:
            token_type = TokenType.ATOM

    # トークン生成
    if literal_override is not None:
        self._add_token(token_type, literal_override=literal_override)
    else:
        self._add_token(token_type)
```

#### 2.3 日本語文字検出ヘルパー

```python
def _contains_japanese_char(self, text: str) -> bool:
    """文字列に日本語文字が含まれているかチェック"""
    return bool(re.search(r'[ぁ-ゟ゠-ヿ一-鿿]', text))
```

### 3. Parser の修正設計

#### 3.1 コンストラクタ修正

```python
class Parser:
    def __init__(
        self,
        tokens: List[Token],
        error_handler: Callable[[Token, str], None] = default_error_handler,
        variable_mapper: Optional[VariableMapper] = None,
        functor_mapper: Optional[FunctorMapper] = None,  # 追加
    ):
        # 既存の初期化処理
        self._functor_mapper = functor_mapper  # 追加
```

#### 3.2 項解析の修正

```python
def _parse_primary(self):
    """基本要素の解析（ファンクター対応版）"""
    if self._match(TokenType.ATOM, ...):
        token = self._previous()
        atom_name = token.literal if token.literal else token.lexeme

        # ファンクター名の処理
        functor_atom = Atom(atom_name)  # literal を使用（英語変換済み）

        if self._match(TokenType.LEFTPAREN):
            # 複合項の処理（既存）
            args = []
            # ... 引数解析処理 ...
            return Term(functor_atom, args)
        else:
            return functor_atom

    # その他の処理（既存）
```

### 4. Runtime の修正設計

#### 4.1 コンストラクタ修正

```python
class Runtime:
    def __init__(
        self,
        rules: Optional[List[Union[Rule, Fact]]] = None,
        variable_mapper: Optional[VariableMapper] = None,
        functor_mapper: Optional[FunctorMapper] = None,  # 追加
    ):
        # 既存の初期化処理
        self.functor_mapper = functor_mapper if functor_mapper is not None else FunctorMapper()
```

#### 4.2 クエリ処理の修正

```python
def query(self, query_string: str) -> List[Dict[Variable, Any]]:
    """クエリ実行（ファンクター復元対応版）"""
    logger.debug(f"QUERY: Executing query: {query_string}")
    solutions = []

    try:
        # クエリの解析（ファンクターマッピング適用）
        if not query_string.strip().endswith("."):
            query_string += "."

        tokens = Scanner(
            query_string,
            variable_mapper=self.variable_mapper,
            functor_mapper=self.functor_mapper  # 追加
        ).scan_tokens()

        parsed_structures = Parser(
            tokens,
            variable_mapper=self.variable_mapper,
            functor_mapper=self.functor_mapper  # 追加
        ).parse()

        # ... 既存のクエリ処理 ...

        # 結果の復元処理
        for i, env_solution in enumerate(self.execute(query_goal, initial_env)):
            result = {}
            for var_name_str in query_vars_names:
                var_obj = Variable(var_name_str)
                value_fully_dereferenced = self.logic_interpreter.deep_dereference_term(
                    var_obj, env_solution
                )

                # 変数名とファンクター名の両方を日本語に復元
                original_var_name = self.variable_mapper.map_english_to_japanese(var_obj.name)
                display_var_obj = Variable(original_var_name)

                # 値内のファンクター名も日本語に復元
                result[display_var_obj] = self._convert_all_to_japanese(value_fully_dereferenced)

            solutions.append(result)

    except Exception as e:
        # エラー処理（既存）

    return solutions
```

#### 4.3 日本語復元処理

```python
def _convert_all_to_japanese(self, term: Any) -> Any:
    """項内の変数名とファンクター名を日本語に復元"""
    if isinstance(term, Variable):
        # 変数名の復元
        return Variable(self.variable_mapper.map_english_to_japanese(term.name))

    elif isinstance(term, Term):
        # ファンクター名の復元
        original_functor_name = self.functor_mapper.map_english_to_japanese(
            term.functor.name if isinstance(term.functor, Atom) else str(term.functor)
        )

        # 引数の再帰的復元
        new_args = [self._convert_all_to_japanese(arg) for arg in term.args]

        # 復元されたファンクター名でTermを再構築
        return Term(Atom(original_functor_name), new_args)

    elif isinstance(term, list):
        # リストの要素を再帰的に復元
        return [self._convert_all_to_japanese(item) for item in term]

    # その他の型はそのまま返す
    return term
```

#### 4.4 ルール追加処理の修正

```python
def add_rule(self, rule_string: str) -> bool:
    """ルール追加（ファンクターマッピング対応版）"""
    try:
        if not rule_string.strip().endswith("."):
            rule_string += "."

        tokens = Scanner(
            rule_string,
            variable_mapper=self.variable_mapper,
            functor_mapper=self.functor_mapper  # 追加
        ).scan_tokens()

        parsed_items = Parser(
            tokens,
            variable_mapper=self.variable_mapper,
            functor_mapper=self.functor_mapper  # 追加
        ).parse()

        # ... 既存の処理 ...

    except Exception as e:
        logger.error(f"Failed to add rule: {e}", exc_info=True)
        return False
```

---

## 🔧 実装手順

### Phase 1: 基盤実装（Week 1-2）

#### Step 1.1: FunctorMapper 実装

```python
# pyprolog/util/functor_mapper.py
# - 基本クラス構造の実装
# - 日本語判定ロジック
# - マッピング生成・管理機能
# - テストケース作成
```

#### Step 1.2: 単体テスト作成

```python
# tests/util/test_functor_mapper.py
def test_japanese_functor_detection():
    """日本語ファンクター判定のテスト"""

def test_functor_mapping_generation():
    """マッピング生成のテスト"""

def test_mapping_consistency():
    """マッピングの一貫性テスト"""
```

### Phase 2: Scanner 統合（Week 2-3）

#### Step 2.1: Scanner 修正

```python
# pyprolog/parser/scanner.py
# - コンストラクタにfunctor_mapper追加
# - _identifier()メソッドの修正
# - 日本語文字検出ヘルパーメソッド追加
```

#### Step 2.2: 統合テスト

```python
# tests/parser/test_scanner_functor.py
def test_japanese_functor_scanning():
    """日本語ファンクターのスキャンテスト"""

def test_mixed_japanese_english():
    """日英混在のスキャンテスト"""
```

### Phase 3: Parser 統合（Week 3-4）

#### Step 3.1: Parser 修正

```python
# pyprolog/parser/parser.py
# - コンストラクタ修正
# - _parse_primary()メソッドの修正
```

#### Step 3.2: 構文解析テスト

```python
# tests/parser/test_parser_functor.py
def test_japanese_fact_parsing():
    """日本語ファクトの解析テスト"""

def test_japanese_rule_parsing():
    """日本語ルールの解析テスト"""
```

### Phase 4: Runtime 統合（Week 4-5）

#### Step 4.1: Runtime 修正

```python
# pyprolog/runtime/interpreter.py
# - コンストラクタ修正
# - query()メソッドの修正
# - 日本語復元処理の実装
```

#### Step 4.2: エンドツーエンドテスト

```python
# tests/integration/test_japanese_functor.py
def test_complete_japanese_program():
    """完全な日本語プログラムのテスト"""
```

### Phase 5: 最適化・安定化（Week 5-6）

#### Step 5.1: 性能最適化

- マッピング処理の高速化
- メモリ使用量の最適化
- キャッシュ機構の改善

#### Step 5.2: エラーハンドリング強化

- 日本語ファンクター関連のエラーメッセージ改善
- 部分的失敗時の回復処理

---

## 🧪 テスト戦略

### 1. 単体テスト

#### FunctorMapper テスト

```python
class TestFunctorMapper:
    def test_japanese_functor_identification(self):
        """日本語ファンクター識別テスト"""
        mapper = FunctorMapper()

        # 日本語ファンクター
        assert mapper.is_japanese_functor("親")
        assert mapper.is_japanese_functor("男性")
        assert mapper.is_japanese_functor("疾患名")
        assert mapper.is_japanese_functor("test親")  # 混在

        # 英語ファンクター
        assert not mapper.is_japanese_functor("parent")
        assert not mapper.is_japanese_functor("male")
        assert not mapper.is_japanese_functor("X")  # 変数

    def test_mapping_generation(self):
        """マッピング生成テスト"""
        mapper = FunctorMapper()

        # 初回マッピング
        assert mapper.map_japanese_to_english("親") == "F1"
        assert mapper.map_japanese_to_english("男性") == "F2"

        # 重複チェック
        assert mapper.map_japanese_to_english("親") == "F1"  # 同じ結果

        # 逆マッピング
        assert mapper.map_english_to_japanese("F1") == "親"
        assert mapper.map_english_to_japanese("F2") == "男性"

    def test_non_japanese_passthrough(self):
        """非日本語のパススルーテスト"""
        mapper = FunctorMapper()

        # 英語はそのまま通す
        assert mapper.map_japanese_to_english("parent") == "parent"
        assert mapper.map_english_to_japanese("parent") == "parent"
```

### 2. 統合テスト

#### Scanner + FunctorMapper テスト

```python
class TestScannerFunctorIntegration:
    def test_japanese_functor_tokenization(self):
        """日本語ファンクターのトークン化テスト"""
        functor_mapper = FunctorMapper()
        scanner = Scanner("親(太郎, 花子).", functor_mapper=functor_mapper)
        tokens = scanner.scan_tokens()

        # 期待されるトークン
        assert tokens[0].token_type == TokenType.ATOM
        assert tokens[0].lexeme == "親"
        assert tokens[0].literal == "F1"  # マッピング済み
```

#### Parser + FunctorMapper テスト

```python
class TestParserFunctorIntegration:
    def test_japanese_fact_parsing(self):
        """日本語ファクトの解析テスト"""
        functor_mapper = FunctorMapper()
        variable_mapper = VariableMapper()

        source = "親(太郎, 花子)."
        scanner = Scanner(source, variable_mapper=variable_mapper, functor_mapper=functor_mapper)
        tokens = scanner.scan_tokens()
        parser = Parser(tokens, variable_mapper=variable_mapper, functor_mapper=functor_mapper)
        results = parser.parse()

        assert len(results) == 1
        fact = results[0]
        assert isinstance(fact, Fact)
        assert fact.head.functor.name == "F1"  # 内部的には英語
        assert len(fact.head.args) == 2
```

### 3. エンドツーエンドテスト

#### 完全な日本語プログラムテスト

```python
class TestCompleteJapaneseProgram:
    def test_japanese_family_relations(self):
        """日本語家族関係プログラムテスト"""
        runtime = Runtime()

        # ルール追加
        runtime.add_rule("親(太郎, 花子).")
        runtime.add_rule("親(太郎, 次郎).")
        runtime.add_rule("男性(太郎).")
        runtime.add_rule("男性(次郎).")
        runtime.add_rule("女性(花子).")
        runtime.add_rule("父親(X, Y) :- 親(X, Y), 男性(X).")

        # クエリ実行
        results = runtime.query("父親(太郎, 誰).")

        # 結果検証
        assert len(results) == 2
        # 結果が日本語で返ることを確認
        for result in results:
            for var, value in result.items():
                assert isinstance(var.name, str)  # 日本語変数名
                # 値も日本語ファンクターを含むことを確認
```

### 4. 性能テスト

#### マッピング性能テスト

```python
class TestFunctorMappingPerformance:
    def test_large_scale_mapping(self):
        """大規模マッピングの性能テスト"""
        mapper = FunctorMapper()

        # 1000個の日本語ファンクターをマッピング
        import time
        start_time = time.time()

        for i in range(1000):
            japanese_name = f"述語{i}"
            english_name = mapper.map_japanese_to_english(japanese_name)
            recovered_name = mapper.map_english_to_japanese(english_name)
            assert recovered_name == japanese_name

        end_time = time.time()

        # 1秒以内で完了することを確認
        assert end_time - start_time < 1.0
```

---

## 🚀 期待される効果

### 1. 機能的効果

#### Before（現在）

```prolog
% エラーになる
親(太郎, 花子).

% 仕方なく英語で記述
parent(太郎, 花子).  % 変数のみ日本語
```

#### After（実装後）

```prolog
% 完全に日本語で記述可能
親(太郎, 花子).
男性(太郎).
女性(花子).
父親(X, Y) :- 親(X, Y), 男性(X).

% クエリも日本語
?- 父親(太郎, 誰).
```

### 2. 教育的効果

#### 理解の促進

- **自然言語に近い記述**: 論理構造の理解が容易
- **母語での学習**: 概念理解の敷居を下げる
- **直感的な操作**: プログラミング初学者への配慮

#### 学習効率の向上

- **認知負荷の軽減**: 英語翻訳の手間を削減
- **エラー理解**: 日本語エラーメッセージでの理解促進
- **デバッグ効率**: 日本語での思考とコードの一致

### 3. 実用的効果

#### ドメイン特化記述

```prolog
% 医療診断システム
疾患(風邪).
症状(発熱).
疾患症状(風邪, 発熱, 0.8).
診断(患者, 疾患) :- 症状(患者, 症状), 疾患症状(疾患, 症状, 確率), 確率 > 0.7.

% 法務システム
法律(民法).
条文(民法, 第1条).
適用条件(民法, 第1条, 私権行使).
```

---

## 📚 参考資料と関連仕様

### 関連する既存実装

- `pyprolog/util/variable_mapper.py` - 変数名マッピングの参考実装
- `pyprolog/parser/scanner.py` - トークン化処理の拡張ベース
- `pyprolog/parser/parser.py` - 構文解析への統合箇所
