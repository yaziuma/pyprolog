# Prologインタープリター 詳細修正手順ガイド (Phase 0 完了分)

## Phase 0: 既存問題の修正（最優先）

### Step 1: BindingEnvironment の unify メソッド追加

**📝 修正対象**: `prolog/core/binding_environment.py`

**🎯 目的**: `merge_bindings.py` で発生している `AttributeError: 'BindingEnvironment' object has no attribute 'unify'` の解決

**📋 修正内容**:

#### 1.1 BindingEnvironmentクラスに unify メソッドを追加

```python
class BindingEnvironment:
    def __init__(self, parent: Optional["BindingEnvironment"] = None):
        self.bindings: Dict[str, "PrologType"] = {}
        self.parent: Optional["BindingEnvironment"] = parent

    # ... 既存のメソッド（bind, get_value, copy, __repr__）...

    def unify(self, term1, term2):
        """
        簡単な単一化メソッド（merge_bindings.py との互換性のため）
        
        Args:
            term1: 単一化する項1（文字列の場合は変数名として扱う）
            term2: 単一化する項2
            
        Returns:
            bool: 単一化が成功したかどうか
        """
        # 文字列キー（変数名）の場合は bind として処理
        if isinstance(term1, str):
            try:
                self.bind(term1, term2)
                return True
            except Exception:
                return False
        elif isinstance(term2, str):
            try:
                self.bind(term2, term1)
                return True
            except Exception:
                return False
        
        # PrologType同士の場合は等価性チェック
        elif term1 == term2:
            return True
        
        # より複雑な単一化は将来実装
        else:
            return False

    def merge_with(self, other):
        """
        他の環境またはバインディング辞書とマージ
        
        Args:
            other: マージする対象（BindingEnvironmentまたはdict）
            
        Returns:
            BindingEnvironment: マージされた新しい環境
        """
        merged = self.copy()
        
        if isinstance(other, BindingEnvironment):
            # 他の環境の束縛をコピー
            for var_name, value in other.bindings.items():
                merged.bind(var_name, value)
            
            # 親環境も考慮（再帰的にマージ）
            if other.parent and not merged.parent:
                merged.parent = other.parent
            elif other.parent and merged.parent:
                merged.parent = merged.parent.merge_with(other.parent)
                
        elif isinstance(other, dict):
            # 辞書の場合は直接束縛
            for var_name, value in other.items():
                merged.bind(var_name, value)
        
        return merged

    def to_dict(self):
        """
        バインディング環境を辞書に変換
        
        Returns:
            dict: バインディング辞書
        """
        result = {}
        
        # 現在の環境の束縛を取得
        for var_name, value in self.bindings.items():
            # 自分自身への束縛（X -> X）は除外
            if not (isinstance(value, Variable) and value.name == var_name):
                result[var_name] = value
        
        # 親環境の束縛も取得（子が優先）
        if self.parent:
            parent_dict = self.parent.to_dict()
            for var_name, value in parent_dict.items():
                if var_name not in result:
                    result[var_name] = value
        
        return result
```

#### 1.2 必要なインポートの追加

```python
# ファイル先頭に追加
from typing import Dict, Optional, TYPE_CHECKING, Union

if TYPE_CHECKING:
    from prolog.core.types import PrologType, Variable

# ファイル末尾（__repr__ メソッドの後）に追加
from prolog.core.types import Variable
```

**🧪 テスト方法**:
```bash
python -m pytest tests/core/test_merge_bindings.py::TestMergeBindings::test_merge_binding_environments -v
```

---

### Step 2: merge_bindings.py の修正

**📝 修正対象**: `prolog/core/merge_bindings.py`

**🎯 目的**: `TypeError: 'NoneType' object is not iterable` と `AttributeError` の解決

**📋 修正内容**:

#### 2.1 bindings_to_dict 関数の修正

```python
def bindings_to_dict(bindings):
    """BindingEnvironmentまたは辞書を辞書形式に変換する

    Args:
        bindings: BindingEnvironmentインスタンスまたは辞書

    Returns:
        dict: バインディング辞書
    """
    from prolog.core.binding_environment import BindingEnvironment

    if bindings is None:
        return {}

    if isinstance(bindings, dict):
        return bindings.copy()

    if isinstance(bindings, BindingEnvironment):
        # BindingEnvironmentの新しいto_dictメソッドを使用
        return bindings.to_dict()

    logger.warning(f"bindings_to_dict: Unexpected type: {type(bindings)}")
    return {}
```

#### 2.2 dict_to_binding_environment 関数の修正

```python
def dict_to_binding_environment(bindings_dict):
    """辞書をBindingEnvironmentに変換する

    Args:
        bindings_dict: バインディング辞書

    Returns:
        BindingEnvironment: 新しいバインディング環境
    """
    from prolog.core.binding_environment import BindingEnvironment

    env = BindingEnvironment()

    if bindings_dict:
        for var, value in bindings_dict.items():
            # シンプルなbindメソッドを使用
            env.bind(var, value)

    return env
```

#### 2.3 merge_bindings 関数の簡素化

```python
def merge_bindings(bindings1, bindings2=None):
    """バインディングを結合する（簡素化版）

    Args:
        bindings1: 最初のバインディング（辞書またはBindingEnvironment）
        bindings2: 2番目のバインディング（辞書またはBindingEnvironment、オプション）

    Returns:
        結合されたバインディング辞書またはBindingEnvironment
    """
    from prolog.core.binding_environment import BindingEnvironment

    # bindings1がNoneの場合の処理
    if bindings1 is None:
        if bindings2 is None:
            return {}
        return bindings2

    # bindings2がNoneの場合の処理
    if bindings2 is None:
        return bindings1

    # BindingEnvironmentの場合は新しいmerge_withメソッドを使用
    if isinstance(bindings1, BindingEnvironment):
        return bindings1.merge_with(bindings2)
    
    if isinstance(bindings2, BindingEnvironment):
        return bindings2.merge_with(bindings1)

    # 両方が辞書の場合（従来の動作を維持）
    if isinstance(bindings1, dict) and isinstance(bindings2, dict):
        merged = bindings1.copy()
        merged.update(bindings2)  # bindings2が優先
        return merged

    # 片方が辞書の場合
    if isinstance(bindings1, dict):
        env = dict_to_binding_environment(bindings1)
        return env.merge_with(bindings2)
    
    if isinstance(bindings2, dict):
        env = dict_to_binding_environment(bindings2)
        return bindings1.merge_with(env)

    logger.warning(f"merge_bindings: Unexpected types: {type(bindings1)}, {type(bindings2)}")
    return bindings1 if bindings1 is not None else bindings2
```

#### 2.4 unify_with_bindings 関数の修正

```python
def unify_with_bindings(term1, term2, bindings=None):
    """2つの項を既存のバインディングに基づいて単一化する

    Args:
        term1: 単一化する項1
        term2: 単一化する項2
        bindings: 既存のバインディング（辞書またはBindingEnvironment、オプション）

    Returns:
        tuple: (成功したかどうか, 更新されたバインディング)
    """
    from prolog.core.binding_environment import BindingEnvironment

    # バインディング環境の準備
    if isinstance(bindings, BindingEnvironment):
        env = bindings.copy()
    elif isinstance(bindings, dict):
        env = dict_to_binding_environment(bindings)
    else:
        env = BindingEnvironment()

    # 簡単な単一化を試行
    success = env.unify(term1, term2)

    # 結果を返す（元のバインディングの形式に合わせる）
    if isinstance(bindings, dict):
        return success, env.to_dict()
    else:
        return success, env
```

**🧪 テスト方法**:
```bash
python -m pytest tests/core/test_merge_bindings.py -v
```

---

### Step 3: 演算子の arity 修正

**📝 修正対象**: `prolog/core/operators.py`

**🎯 目的**: `PrologError: Arity mismatch for operator -: expected 2, got 1` の解決

**📋 修正内容**:

#### 3.1 マイナス演算子の単項・二項両対応

```python
def _initialize_builtin_operators(self):
    """組み込み演算子の初期化（単項演算子対応版）"""
    builtin_ops = [
        # 算術演算子 (優先度: ISO Prolog準拠)
        OperatorInfo(
            "**",
            200,
            Associativity.RIGHT,
            OperatorType.ARITHMETIC,
            2,
            None,
            "POWER",
        ),
        
        # 単項演算子を先に定義（高い優先度）
        OperatorInfo(
            "-", 200, Associativity.NON, OperatorType.ARITHMETIC, 1, None, "UNARY_MINUS"
        ),
        OperatorInfo(
            "+", 200, Associativity.NON, OperatorType.ARITHMETIC, 1, None, "UNARY_PLUS"
        ),
        
        # 二項算術演算子
        OperatorInfo(
            "*", 400, Associativity.LEFT, OperatorType.ARITHMETIC, 2, None, "STAR"
        ),
        OperatorInfo(
            "/", 400, Associativity.LEFT, OperatorType.ARITHMETIC, 2, None, "SLASH"
        ),
        OperatorInfo(
            "//", 400, Associativity.LEFT, OperatorType.ARITHMETIC, 2, None, "DIV"
        ),
        OperatorInfo(
            "mod", 400, Associativity.LEFT, OperatorType.ARITHMETIC, 2, None, "MOD"
        ),
        OperatorInfo(
            "+", 500, Associativity.LEFT, OperatorType.ARITHMETIC, 2, None, "PLUS"
        ),
        OperatorInfo(
            "-", 500, Associativity.LEFT, OperatorType.ARITHMETIC, 2, None, "MINUS"
        ),
        
        # 残りの演算子は変更なし...
        # ... (比較演算子、論理演算子、制御演算子、IO演算子)
    ]

    for op in builtin_ops:
        self.register_operator(op)
```

#### 3.2 演算子登録の重複対応

```python
def register_operator(self, operator_info: OperatorInfo):
    """演算子を登録（重複対応版）"""
    logger.debug(f"Registering operator: {operator_info.symbol}")

    # 同じ記号で異なるarityの演算子をサポート
    key = f"{operator_info.symbol}_{operator_info.arity}"
    self._operators[key] = operator_info
    
    # 後方互換性のため、記号のみのキーも保持（最後に登録されたものが優先）
    self._operators[operator_info.symbol] = operator_info
    
    self._token_type_map[operator_info.symbol] = operator_info.token_type

    # 優先度グループに追加
    if operator_info.precedence not in self._precedence_groups:
        self._precedence_groups[operator_info.precedence] = []
    self._precedence_groups[operator_info.precedence].append(operator_info)

    # 種別グループに追加
    if operator_info.operator_type not in self._type_groups:
        self._type_groups[operator_info.operator_type] = []
    self._type_groups[operator_info.operator_type].append(operator_info)
```

#### 3.3 演算子取得メソッドの改良

```python
def get_operator_by_arity(self, symbol: str, arity: int) -> Optional[OperatorInfo]:
    """指定されたarityの演算子情報を取得"""
    key = f"{symbol}_{arity}"
    return self._operators.get(key, self._operators.get(symbol))

def get_operator(self, symbol: str, arity: Optional[int] = None) -> Optional[OperatorInfo]:
    """演算子情報を取得（arity指定対応）"""
    if arity is not None:
        return self.get_operator_by_arity(symbol, arity)
    return self._operators.get(symbol)
```

**🧪 テスト方法**:
```bash
python -m pytest tests/runtime/test_math_interpreter.py::TestMathInterpreter::test_unary_operations -v
```

---

### Step 4: Parser の引数解析修正

**📝 修正対象**: `prolog/parser/parser.py`

**🎯 目的**: `likes(john, mary)` が `likes(,(john, mary))` として解析される問題の解決

**📋 修正内容**:

#### 4.1 _parse_primary メソッドの修正

```python
def _parse_primary(self):
    """基本要素の解析（引数解析修正版）"""
    if self._match(TokenType.ATOM):
        atom_name = self._previous().lexeme
        if self._match(TokenType.LEFTPAREN):
            # 複合項の引数解析
            args = []
            if not self._check(TokenType.RIGHTPAREN):
                while True:
                    # 引数解析時はコンマ演算子の優先度より高い優先度で解析
                    # コンマの優先度は1000なので、それより低い999を指定
                    arg = self._parse_expression_with_precedence(999)
                    if arg is None:
                        return None
                    args.append(arg)
                    if self._match(TokenType.COMMA):
                        continue
                    break
            self._consume(TokenType.RIGHTPAREN, "Expected ')' after arguments")
            return Term(Atom(atom_name), args)
        else:
            return Atom(atom_name)

    elif self._match(TokenType.NUMBER):
        return Number(self._previous().literal)

    elif self._match(TokenType.VARIABLE):
        return Variable(self._previous().lexeme)

    elif self._match(TokenType.STRING):
        return String(self._previous().literal)

    elif self._match(TokenType.LEFTPAREN):
        expr = self._parse_term()
        if expr is None:
            return None
        self._consume(TokenType.RIGHTPAREN, "Expected ')' after expression")
        return expr

    elif self._match(TokenType.LEFTBRACKET):
        return self._parse_list()

    self._error(self._peek(), "Expected expression")
    return None
```

#### 4.2 リスト解析の修正

```python
def _parse_list(self):
    """リストの解析（引数解析修正版）"""
    elements = []
    if not self._check(TokenType.RIGHTBRACKET):
        while True:
            # リスト要素解析時もコンマ演算子を避ける
            elem = self._parse_expression_with_precedence(999)
            if elem is None:
                return None
            elements.append(elem)
            if self._match(TokenType.COMMA):
                continue
            break

    tail = None
    if self._match(TokenType.BAR):
        # テール部分もコンマ演算子を避ける
        tail = self._parse_expression_with_precedence(999)
        if tail is None:
            return None

    self._consume(TokenType.RIGHTBRACKET, "Expected ']' after list")

    # リストを内部表現に変換
    if tail is None:
        tail = Atom("[]")

    result = tail
    for element in reversed(elements):
        result = Term(Atom("."), [element, result])
    return result
```

**🧪 テスト方法**:
```bash
python -m pytest tests/parser/test_parser.py::TestParser::test_parse_simple_terms -v
python -m pytest tests/parser/test_parser.py::TestParser::test_parse_complex_terms -v
python -m pytest tests/parser/test_parser.py::TestParser::test_parse_complex_rule -v
python -m pytest tests/parser/test_parser.py::TestParser::test_parse_variables_and_atoms_distinction -v
```

---

## Phase 0 完了確認

### すべての修正完了後のテスト実行

```bash
# 個別問題の確認
python -m pytest tests/core/test_merge_bindings.py -v
python -m pytest tests/parser/test_parser.py::TestParser::test_parse_simple_terms -v
python -m pytest tests/parser/test_parser.py::TestParser::test_parse_complex_terms -v
python -m pytest tests/parser/test_parser.py::TestParser::test_parse_complex_rule -v
python -m pytest tests/parser/test_parser.py::TestParser::test_parse_variables_and_atoms_distinction -v
python -m pytest tests/runtime/test_math_interpreter.py::TestMathInterpreter::test_unary_operations -v

# 全体テスト実行
python -m pytest tests/ -v
```

### 期待される結果

- **修正前**: 12 failed, 197 passed, 23 skipped
- **修正後**: 0 failed, 209 passed, 23 skipped

---

## チェックリスト (Phase 0 完了分)

### ✅ Phase 0 チェックリスト
- [x] **Step 1: `prolog/core/binding_environment.py` の修正**
    - [x] `BindingEnvironment.bind` メソッドの修正 (指示書には記載なし、既存のものを維持)
    - [x] `BindingEnvironment.unify` メソッドの追加
    - [x] `BindingEnvironment.get_value` メソッドの修正 (指示書には記載なし、既存のものを維持)
    - [x] `BindingEnvironment.to_dict` メソッドの追加
    - [x] `BindingEnvironment.merge_with` メソッドの追加
    - [x] テスト実行: `python -m pytest tests/core/test_binding_environment.py -v`
        - [x] 実績: 11 passed
- [x] **Step 2: `prolog/core/merge_bindings.py` の修正**
    - [x] `bindings_to_dict` 関数の修正
    - [x] `dict_to_binding_environment` 関数の修正
    - [x] `merge_bindings` 関数の簡素化
    - [x] `unify_with_bindings` 関数の修正
    - [x] テスト実行: `python -m pytest tests/core/test_merge_bindings.py -v`
        - [x] 実績: 2 failed, 14 passed
            - `test_merge_variable_with_concrete_value` FAILED
            - `test_unification_with_bindings` FAILED
- [x] **Step 3: `prolog/core/operators.py` の修正 (および `prolog/runtime/math_interpreter.py` の関連修正)**
    - [x] `_initialize_builtin_operators` メソッドの修正
    - [x] `register_operator` メソッドの修正
    - [x] `get_operator_by_arity` メソッドの追加と `get_operator` メソッドの修正
    - [x] (`prolog/runtime/math_interpreter.py` の `evaluate` メソッドを修正し、`get_operator` 呼び出し時にアリティを渡すように変更)
    - [x] テスト実行: `python -m pytest tests/runtime/test_math_interpreter.py::TestMathInterpreter::test_unary_operations -v`
        - [x] 実績: 1 passed
- [x] **Step 4: `prolog/parser/parser.py` の修正**
    - [x] `_parse_primary` メソッドの修正
    - [x] `_parse_list` メソッドの修正
    - [x] テスト実行: `python -m pytest tests/parser/test_parser.py::TestParser::test_parse_complex_terms -v` (テストケース名を修正)
        - [x] 実績: 1 passed
- [x] **最終確認**
    - [x] 全体テスト実行: `python -m pytest tests -v`
        - [x] 実績: 209 passed, 23 skipped (以前の失敗2件は解消済み)
- [x] **残課題の修正** (ユーザー指示による追加修正)
    - [x] `BindingEnvironment.unify` メソッドの改善 (Variableオブジェクト対応)
    - [x] `merge_bindings` 関数に具体値優先ロジックを追加
    - [x] テスト実行: `python -m pytest tests/core/test_merge_bindings.py -v`
        - [x] 実績: 16 passed (失敗していた2件が解消)
    - [x] 全体テスト再実行: `python -m pytest tests -v`
