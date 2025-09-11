# 入出力述語の共通処理統合

## 現在の問題

入出力述語に重複する処理が多数存在：

1. **引数検証**: 全ての述語で類似の引数数チェック
2. **EOF処理**: `end_of_file`原子への変換
3. **数値変換**: 文字列から数値への変換ロジック
4. **統一化処理**: Prologの統一化パターン
5. **IOManager呼び出し**: 各述語で個別にIOManager呼び出し

## 提案する親クラス設計

### IOPredicate親クラス

```python
class IOPredicate(BuiltinPredicate):
    """入出力述語の共通基底クラス"""
    
    def __init__(self, *args):
        super().__init__(*args)
        self._validate_arguments()
    
    def _validate_arguments(self):
        """引数数検証（サブクラスでオーバーライド）"""
        expected_args = self._get_expected_arg_count()
        if len(self.args) != expected_args:
            raise PrologError(
                f"{self._get_predicate_name()} expects {expected_args} argument(s), "
                f"got {len(self.args)}"
            )
    
    def _get_expected_arg_count(self) -> int:
        """期待する引数数（サブクラスで実装）"""
        raise NotImplementedError
    
    def _get_predicate_name(self) -> str:
        """述語名（サブクラスで実装）"""
        raise NotImplementedError
    
    def _get_input_type(self) -> str:
        """入力タイプ（統一入力システム用）"""
        raise NotImplementedError
    
    def execute(
        self, runtime: "Runtime", env: BindingEnvironment
    ) -> Iterator[BindingEnvironment]:
        """共通実行フロー"""
        # 1. 統一入力システム経由で入力取得
        input_value = self._request_input(runtime)
        
        # 2. Prologターム変換
        target_term = self._convert_to_prolog_term(input_value)
        
        # 3. 統一化実行
        yield from self._unify_with_argument(runtime, env, target_term)
    
    def _request_input(self, runtime: "Runtime") -> str:
        """統一入力システム経由での入力要求"""
        return runtime.io_manager.request_input(
            input_type=self._get_input_type(),
            predicate_name=self._get_predicate_name(),
            prompt=self._get_prompt()
        )
    
    def _get_prompt(self) -> str:
        """プロンプト文字列（サブクラスでオーバーライド可能）"""
        return f"{self._get_predicate_name()}: "
    
    def _convert_to_prolog_term(self, input_value: str) -> PrologType:
        """入力値のPrologターム変換（サブクラスで実装）"""
        raise NotImplementedError
    
    def _unify_with_argument(
        self, 
        runtime: "Runtime", 
        env: BindingEnvironment, 
        target_term: PrologType
    ) -> Iterator[BindingEnvironment]:
        """引数との統一化（共通処理）"""
        prolog_arg = self.args[0]  # 通常、最初の引数が対象
        unified, next_env = runtime.logic_interpreter.unify(
            prolog_arg, target_term, env
        )
        if unified:
            yield next_env
    
    def _handle_eof(self) -> Atom:
        """EOF処理（共通）"""
        return Atom("end_of_file")
    
    def _try_convert_to_number(self, value: str) -> Optional[PrologType]:
        """数値変換試行（共通ユーティリティ）"""
        number_value = try_convert_atom_to_number(value)
        if number_value is not None:
            return Number(number_value)
        return None
```

## 具体的な述語実装

### GetCharPredicate（簡略化版）

```python
class GetCharPredicate(IOPredicate):
    """get_char/1述語 - 統合版"""
    
    def _get_expected_arg_count(self) -> int:
        return 1
    
    def _get_predicate_name(self) -> str:
        return "get_char"
    
    def _get_input_type(self) -> str:
        return "char"
    
    def _convert_to_prolog_term(self, input_value: str) -> PrologType:
        """文字入力のPrologターム変換"""
        if input_value == "":  # EOF
            return self._handle_eof()
        elif len(input_value) == 1:
            # 単一文字: 数字なら数値、それ以外は原子
            if input_value.isdigit():
                return Number(int(input_value))
            else:
                return Atom(input_value)
        else:
            # 複数文字の場合は最初の文字のみ
            char = input_value[0]
            return Number(int(char)) if char.isdigit() else Atom(char)
```

### ReadLinePredicate（簡略化版）

```python
class ReadLinePredicate(IOPredicate):
    """read_line/1述語 - 統合版"""
    
    def _get_expected_arg_count(self) -> int:
        return 1
    
    def _get_predicate_name(self) -> str:
        return "read_line"
    
    def _get_input_type(self) -> str:
        return "line"
    
    def _convert_to_prolog_term(self, input_value: str) -> PrologType:
        """行入力のPrologターム変換"""
        if input_value is None:  # EOF
            return self._handle_eof()
        
        # 数値変換を試行、失敗時は原子
        number_term = self._try_convert_to_number(input_value)
        return number_term if number_term else Atom(input_value)
```

### PeekCharPredicate（簡略化版）

```python
class PeekCharPredicate(IOPredicate):
    """peek_char/1述語 - 統合版"""
    
    def _get_expected_arg_count(self) -> int:
        return 1
    
    def _get_predicate_name(self) -> str:
        return "peek_char"
    
    def _get_input_type(self) -> str:
        return "peek_char"
    
    def _convert_to_prolog_term(self, input_value: str) -> PrologType:
        """覗き見文字のPrologターム変換"""
        if input_value == "":
            return self._handle_eof()
        return Atom(input_value)
    
    def _request_input(self, runtime: "Runtime") -> str:
        """peek_char特有の入力要求"""
        # peek_charは非破壊的読み取り
        return runtime.io_manager.request_input(
            input_type=self._get_input_type(),
            predicate_name=self._get_predicate_name(),
            non_destructive=True  # 追加パラメータ
        )
```

## 統合の利点

### 1. コード削減
- **従来**: 各述語で100+行の重複コード
- **統合後**: 各述語10-20行で実装完了

### 2. 保守性向上
- 共通ロジックの修正が1箇所で完結
- 新しい入出力述語の追加が容易

### 3. 統一入力システム対応
- 全ての入出力述語が自動的に統一入力システム対応
- 真の継続実行が透過的に適用

### 4. エラーハンドリング統一
- 引数検証エラーメッセージの統一
- EOF処理の一貫性

## マイグレーション戦略

### Phase 1: IOPredicate基底クラス追加
```python
# 既存のBuiltinPredicateに加えて新規追加
class IOPredicate(BuiltinPredicate):
    # 共通処理実装
```

### Phase 2: 段階的移行
```python
# 既存クラスを一つずつ統合版に移行
class GetCharPredicate(IOPredicate):  # 変更
    # 簡略化実装

class ReadLinePredicate(IOPredicate):  # 変更  
    # 簡略化実装
```

### Phase 3: 従来コード削除
```python
# 統合完了後、重複コードを削除
# テスト実行で互換性確認
```

## 既存コードへの影響

**変更必要な箇所:**
- 入出力述語クラス定義のみ（約4-5クラス）

**変更不要な箇所:**
- 述語の外部API（完全互換）
- 利用者コード（無修正で動作）
- テストコード（既存テスト継続実行）

この統合により、入出力述語の実装が大幅に簡素化され、統一入力システムへの移行も自然に実現できます。