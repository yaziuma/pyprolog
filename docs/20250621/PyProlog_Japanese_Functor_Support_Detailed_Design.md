# PyProlog ファンクター名日本語対応 詳細設計書（修正版）

## 📋 修正概要

### 主な修正点

1. **Unicode文字全般への対応拡張**
2. **既存ファンクター名との衝突回避機能**
3. **より安全な命名スキーム**

---

## 🏗️ 修正されたアーキテクチャ設計

### 1. FunctorMapper クラス設計（修正版）

#### 1.1 基本インターフェース（拡張）

```python
class FunctorMapper:
    """ファンクター名の非ASCII⇔英語マッピング管理"""

    def __init__(self, existing_functors: Optional[Set[str]] = None):
        self._non_ascii_to_english: Dict[str, str] = {}
        self._english_to_non_ascii: Dict[str, str] = {}
        self._next_functor_index: int = 1
        self._existing_functors: Set[str] = existing_functors or set()
        
    def register_existing_functors(self, functors: Set[str]):
        """既存ファンクター名を登録（衝突回避用）"""
        
    def map_non_ascii_to_english(self, functor: str) -> str:
        """非ASCII文字を含むファンクター名を英語に変換"""
        
    def map_english_to_non_ascii(self, english_functor: str) -> str:
        """英語ファンクター名を元の形に復元"""
        
    def needs_mapping(self, name: str) -> bool:
        """マッピングが必要かどうかを判定"""
```

#### 1.2 非ASCII文字判定ロジック（拡張）

```python
def needs_mapping(self, name: str) -> bool:
    """
    マッピングが必要な文字の判定条件：
    1. ASCII範囲外の文字を含む（Unicode全般）
    2. Prolog識別子として安全でない文字を含む
    3. 既存の英語ファンクターでない
    """
    if not name:
        return False
    
    # ASCII範囲外の文字が含まれているかチェック
    has_non_ascii = any(ord(char) > 127 for char in name)
    
    # Prolog識別子として問題のある文字をチェック
    unsafe_chars = re.search(r'[^\w]', name)  # 英数字・アンダースコア以外
    
    # ただし、既に登録済みの英語ファンクターは除外
    if name in self._existing_functors and not has_non_ascii:
        return False
        
    return has_non_ascii or bool(unsafe_chars)
```

#### 1.3 安全な命名スキーム（修正）

```python
def _generate_safe_english_functor(self) -> str:
    """
    安全な英語ファンクター名生成：
    - プレフィックス: MAPPED_ （衝突回避）
    - 形式: MAPPED_F1, MAPPED_F2, ...
    - 既存ファンクターとの衝突チェック
    """
    while True:
        # より安全なプレフィックスを使用
        candidate = f"MAPPED_F{self._next_functor_index}"
        
        # 既存ファンクターとの衝突チェック
        if (candidate not in self._english_to_non_ascii and 
            candidate not in self._existing_functors):
            self._next_functor_index += 1
            return candidate
            
        self._next_functor_index += 1

def map_non_ascii_to_english(self, functor: str) -> str:
    """非ASCII→英語マッピング（安全性強化版）"""
    if not self.needs_mapping(functor):
        return functor  # マッピング不要な場合はそのまま返す

    if functor in self._non_ascii_to_english:
        return self._non_ascii_to_english[functor]

    # 新規マッピング作成（安全性チェック付き）
    english_functor = self._generate_safe_english_functor()
    self._non_ascii_to_english[functor] = english_functor
    self._english_to_non_ascii[english_functor] = functor

    return english_functor
```

#### 1.4 既存ファンクター名の収集機能

```python
def _extract_functors_from_rules(self, rules: List[Union[Rule, Fact]]) -> Set[str]:
    """ルールから既存のファンクター名を抽出"""
    functors = set()
    
    for rule in rules:
        if isinstance(rule, Fact):
            functors.add(self._extract_functor_name(rule.head))
            functors.update(self._extract_functors_from_term(rule.head))
        elif isinstance(rule, Rule):
            functors.add(self._extract_functor_name(rule.head))
            functors.update(self._extract_functors_from_term(rule.head))
            functors.update(self._extract_functors_from_term(rule.body))
    
    return functors

def _extract_functor_name(self, term) -> str:
    """項からファンクター名を抽出"""
    if isinstance(term, Term):
        return term.functor.name if isinstance(term.functor, Atom) else str(term.functor)
    elif isinstance(term, Atom):
        return term.name
    return ""

def _extract_functors_from_term(self, term) -> Set[str]:
    """項から再帰的にファンクター名を抽出"""
    functors = set()
    
    if isinstance(term, Term):
        functor_name = self._extract_functor_name(term)
        if functor_name:
            functors.add(functor_name)
        
        # 引数も再帰的にチェック
        for arg in term.args:
            functors.update(self._extract_functors_from_term(arg))
            
    elif isinstance(term, list):
        for item in term:
            functors.update(self._extract_functors_from_term(item))
    
    return functors
```

### 2. Scanner の修正設計（拡張対応）

#### 2.1 識別子処理の修正（Unicode対応）

```python
def _identifier(self):
    """識別子のスキャン（Unicode対応版）"""
    # Unicode文字を含む識別子をサポート
    while (self._peek().isalnum() or 
           self._peek() == "_" or 
           ord(self._peek()) > 127 or  # 非ASCII文字
           self._is_valid_identifier_char(self._peek())):
        self._advance()

    text = self._source[self._start : self._current]
    literal_override = None

    # キーワードチェック（既存）
    token_type = self._keywords.get(text)

    if token_type is None:
        # 演算子キーワードチェック（既存）
        if text in self._operator_symbols:
            token_type = self._operator_symbols[text]

        # 非ASCIIファンクター処理（新規）
        elif self._functor_mapper and self._functor_mapper.needs_mapping(text):
            token_type = TokenType.ATOM
            literal_override = self._functor_mapper.map_non_ascii_to_english(text)
            logger.debug(f"Mapped non-ASCII functor '{text}' to '{literal_override}'")

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

def _is_valid_identifier_char(self, char: str) -> bool:
    """識別子として有効な文字かチェック"""
    if not char:
        return False
    
    # 基本的な制御文字や区切り文字は除外
    invalid_chars = set('()[]{}.,;:!|"\'`~@#$%^&*+-=<>?/\\')
    return char not in invalid_chars and not char.isspace()
```

### 3. Runtime の修正設計（衝突回避対応）

#### 3.1 初期化時の既存ファンクター登録

```python
class Runtime:
    def __init__(
        self,
        rules: Optional[List[Union[Rule, Fact]]] = None,
        variable_mapper: Optional[VariableMapper] = None,
        functor_mapper: Optional[FunctorMapper] = None,
    ):
        self.rules: List[Union[Rule, Fact]] = rules if rules is not None else []
        self.variable_mapper = variable_mapper if variable_mapper is not None else VariableMapper()
        
        # 既存ルールからファンクター名を抽出
        existing_functors = self._extract_existing_functors()
        self.functor_mapper = functor_mapper if functor_mapper is not None else FunctorMapper(existing_functors)
        
        # 既にマッパーが提供されている場合は、既存ファンクターを登録
        if functor_mapper is not None:
            self.functor_mapper.register_existing_functors(existing_functors)
```

#### 3.2 動的ルール追加時の衝突チェック

```python
def add_rule(self, rule_string: str) -> bool:
    """ルール追加（衝突チェック対応版）"""
    try:
        # まず仮解析して新しいファンクターを確認
        temp_functors = self._extract_functors_from_string(rule_string)
        
        # 新しいファンクターを既存リストに登録
        self.functor_mapper.register_existing_functors(temp_functors)
        
        # 通常の解析処理
        if not rule_string.strip().endswith("."):
            rule_string += "."

        tokens = Scanner(
            rule_string,
            variable_mapper=self.variable_mapper,
            functor_mapper=self.functor_mapper
        ).scan_tokens()

        parsed_items = Parser(
            tokens,
            variable_mapper=self.variable_mapper,
            functor_mapper=self.functor_mapper
        ).parse()

        # ルール追加処理（既存）
        # ...

    except Exception as e:
        logger.error(f"Failed to add rule: {e}", exc_info=True)
        return False
```

---

## 🧪 修正されたテスト戦略

### 1. Unicode文字対応テスト

```python
class TestUnicodeFunctorMapping:
    def test_various_unicode_functors(self):
        """様々なUnicode文字のテスト"""
        mapper = FunctorMapper()
        
        # 日本語
        assert mapper.needs_mapping("親")
        assert mapper.needs_mapping("疾患名")
        
        # 全角英数字
        assert mapper.needs_mapping("ＰＡＲＥＮＴ")
        assert mapper.needs_mapping("ｔｅｓｔ１")
        
        # その他のUnicode
        assert mapper.needs_mapping("café")  # フランス語
        assert mapper.needs_mapping("α")     # ギリシャ文字
        assert mapper.needs_mapping("родитель")  # キリル文字
        
        # ASCII文字（マッピング不要）
        assert not mapper.needs_mapping("parent")
        assert not mapper.needs_mapping("test123")
```

### 2. 衝突回避テスト

```python
class TestFunctorCollisionAvoidance:
    def test_existing_functor_collision(self):
        """既存ファンクターとの衝突回避テスト"""
        # 既存ファンクターを含むマッパー
        existing = {"F1", "F2", "MAPPED_F1", "parent"}
        mapper = FunctorMapper(existing)
        
        # 日本語ファンクターのマッピング
        mapped1 = mapper.map_non_ascii_to_english("親")
        mapped2 = mapper.map_non_ascii_to_english("子")
        
        # 既存ファンクターと衝突しないことを確認
        assert mapped1 not in existing
        assert mapped2 not in existing
        assert mapped1 != mapped2
        
        # プレフィックスパターンの確認
        assert mapped1.startswith("MAPPED_F")
        assert mapped2.startswith("MAPPED_F")
```

### 3. 既存プログラムとの互換性テスト

```python
class TestBackwardCompatibility:
    def test_mixed_ascii_unicode_program(self):
        """ASCII/Unicode混在プログラムのテスト"""
        runtime = Runtime()
        
        # 既存の英語ルール
        runtime.add_rule("parent(tom, bob).")
        runtime.add_rule("male(tom).")
        
        # 新しい日本語ルール
        runtime.add_rule("親(太郎, 花子).")
        runtime.add_rule("男性(太郎).")
        
        # 混在ルール
        runtime.add_rule("父親(X, Y) :- parent(X, Y), 男性(X).")
        runtime.add_rule("father(X, Y) :- 親(X, Y), male(X).")
        
        # クエリ実行
        results1 = runtime.query("父親(太郎, 誰).")
        results2 = runtime.query("father(tom, who).")
        
        # 両方が正常に動作することを確認
        assert len(results1) > 0
        assert len(results2) > 0
```

---

## 📊 期待される改善効果

### 1. 拡張された対応範囲

- **多言語対応**: 日本語以外の言語での記述も可能
- **全角文字対応**: 日本語環境でよく使われる全角英数字もサポート
- **特殊文字対応**: 数学記号などの専門的な記述も可能

### 2. 安全性の向上

- **衝突回避**: 既存プログラムとの互換性を保持
- **動的対応**: 実行時のファンクター追加にも対応
- **エラー回復**: 衝突検出時の適切な処理

### 3. 実用性の向上

- **段階的移行**: 既存プログラムを壊さずに新機能を追加
- **混在環境**: ASCII/Unicode混在環境での安定動作
- **拡張性**: 将来的な言語サポート拡張への対応

この修正により、より包括的で安全なファンクター名マッピング機能が実現されます。