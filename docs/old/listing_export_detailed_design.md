# pyprologライブラリ改善提案 - 詳細設計書

## 1. 概要

本設計書では、`listing/0`, `listing/1`, `export_facts/2`述語の具体的な実装詳細を定義する。現行のpyprologアーキテクチャに基づいて、既存パターンに準拠した実装を行う。

## 2. 現行アーキテクチャ分析

### 2.1 組み込み述語の実装パターン
- **基底クラス**: `BuiltinPredicate`クラスを継承
- **実行メソッド**: `execute(runtime, env) -> Iterator[BindingEnvironment]`
- **登録場所**: `runtime/interpreter.py`のRuntimeクラス内で条件分岐による動的マッピング

### 2.2 既存の類似述語
- **findall/3**: テンプレート収集とリスト構築の参考
- **write/1**: IOManager経由の出力処理の参考
- **retract/1**: Runtime.rulesへの直接アクセスの参考

## 3. 実装仕様

### 3.1 listing/0述語

#### クラス設計
```python
class ListingPredicate(BuiltinPredicate):
    def __init__(self):
        super().__init__()
    
    def execute(self, runtime: "Runtime", env: BindingEnvironment) -> Iterator[BindingEnvironment]:
        """全知識ベースの内容を標準Prolog形式で出力"""
```

#### 実装アルゴリズム
1. **Runtime.rules**から全ルール・事実を取得
2. **PrologFormatter**を使用してProlog構文で整形
3. **IOManager**経由で標準出力へ書き出し
4. 成功時に元の環境を返却

### 3.2 listing/1述語

#### クラス設計  
```python
class ListingWithPredicatePredicate(BuiltinPredicate):
    def __init__(self, predicate_spec: PrologType):
        super().__init__(predicate_spec)
    
    def execute(self, runtime: "Runtime", env: BindingEnvironment) -> Iterator[BindingEnvironment]:
        """指定述語の内容のみを出力"""
```

#### 実装アルゴリズム
1. 引数から述語名/アリティを抽出（例: `person/2`）
2. 述語指定の妥当性検証
3. **Runtime.rules**から該当述語をフィルタリング  
4. 整形・出力・環境返却

### 3.3 export_facts/2述語

#### クラス設計
```python
class ExportFactsPredicate(BuiltinPredicate):
    def __init__(self, predicate_spec: PrologType, file_spec: PrologType):
        super().__init__(predicate_spec, file_spec)
    
    def execute(self, runtime: "Runtime", env: BindingEnvironment) -> Iterator[BindingEnvironment]:
        """事実データのエクスポート"""
```

#### 実装アルゴリズム
1. 述語名/アリティ抽出
2. ファイルパス・フォーマット解析
3. 該当事実の抽出（`isinstance(rule, Fact)`フィルタ）
4. **DataExporter**による形式変換・ファイル出力

## 4. 支援クラス設計

### 4.1 PrologFormatter（新規作成）

#### 配置場所
```
pyprolog/util/formatters.py
```

#### クラス仕様
```python
class PrologFormatter:
    @staticmethod
    def format_fact(fact: Fact) -> str:
        """事実をProlog構文文字列に変換"""
        
    @staticmethod  
    def format_rule(rule: Rule) -> str:
        """ルールをProlog構文文字列に変換"""
        
    @staticmethod
    def format_rules_list(rules: List[Union[Rule, Fact]]) -> str:
        """ルール・事実リストの一括変換"""
```

#### 実装詳細
- **Term表現**: ファンクター(引数1, 引数2, ...)
- **変数名**: 日本語変数名の適切な復元（VariableMapper連携）
- **コメント**: 各述語の前にコメント行付加

### 4.2 DataExporter（新規作成）

#### 配置場所
```
pyprolog/io/export_manager.py
```

#### クラス仕様
```python
class DataExporter:
    def __init__(self, runtime: "Runtime"):
        self.runtime = runtime
        
    def export_to_csv(self, facts: List[Fact], filepath: str) -> bool:
        """CSV形式エクスポート"""
        
    def export_to_json(self, facts: List[Fact], filepath: str) -> bool:
        """JSON形式エクスポート"""
        
    def export_to_tsv(self, facts: List[Fact], filepath: str) -> bool:
        """TSV形式エクスポート"""
```

#### CSV形式仕様
```csv
functor,arg1,arg2,arg3
person,alice,28,
person,bob,35,
```

#### JSON形式仕様
```json
[
  {"functor": "person", "args": ["alice", 28]},
  {"functor": "person", "args": ["bob", 35]}
]
```

## 5. Runtime統合

### 5.1 述語登録
`runtime/interpreter.py`のexecuteメソッドに以下を追加:

```python
elif functor_name == "listing" and len(processed_goal.args) == 0:
    listing_pred = ListingPredicate()
    for item in listing_pred.execute(self, env):
        yield item
elif functor_name == "listing" and len(processed_goal.args) == 1:
    listing_pred = ListingWithPredicatePredicate(processed_goal.args[0])
    for item in listing_pred.execute(self, env):
        yield item  
elif functor_name == "export_facts" and len(processed_goal.args) == 2:
    export_pred = ExportFactsPredicate(processed_goal.args[0], processed_goal.args[1])
    for item in export_pred.execute(self, env):
        yield item
```

### 5.2 インポート追加
```python
from pyprolog.runtime.builtins import (
    # 既存インポート...
    ListingPredicate,
    ListingWithPredicatePredicate, 
    ExportFactsPredicate,
)
```

## 6. エラーハンドリング

### 6.1 述語指定エラー
- **型エラー**: 述語指定が`functor/arity`形式でない場合
- **アリティエラー**: 負の数値や非整数の場合

### 6.2 ファイル操作エラー  
- **権限エラー**: 書き込み権限なし
- **パスエラー**: 無効なディレクトリパス
- **フォーマットエラー**: 未対応のエクスポート形式

### 6.3 エラー処理パターン
```python
try:
    # ファイル操作
    with open(filepath, 'w') as f:
        # 書き込み処理
    yield env  # 成功時のみ
except (IOError, OSError) as e:
    logger.error(f"File operation failed: {e}")
    return  # 失敗時は何もyieldしない
```

## 7. テスト設計

### 7.1 テストファイル配置
```
tests/runtime/test_listing_predicates.py
tests/integration/test_export_functionality.py
```

### 7.2 テストケース
1. **listing/0**: 全述語出力の検証
2. **listing/1**: 特定述語フィルタの検証  
3. **export_facts/2**: CSV/JSON出力の検証
4. **エラーケース**: 無効な引数での失敗検証

## 8. 実装優先順位と段階的リリース

### Phase 1: 基本機能
- `ListingPredicate` (listing/0)
- `PrologFormatter` 基本機能
- 基本的な統合テスト

### Phase 2: 述語指定機能  
- `ListingWithPredicatePredicate` (listing/1)
- 述語パーシング・バリデーション機能

### Phase 3: エクスポート機能
- `ExportFactsPredicate` (export_facts/2)
- `DataExporter` 全フォーマット対応
- 包括的エラーハンドリング

## 9. 互換性とメンテナンス

### 9.1 標準Prolog互換性
- SWI-Prolog、GNU Prologとの出力形式互換性
- 標準的なPredicateIndicator (`functor/arity`) サポート

### 9.2 拡張性
- 新フォーマット追加のためのプラガブル設計
- カスタムフォーマッタの登録機能

### 9.3 パフォーマンス
- 大規模知識ベースでのメモリ効率
- ストリーミング書き込みによるスケーラビリティ