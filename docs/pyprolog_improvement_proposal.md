# pyprologライブラリ改善提案 - 事実・ルール出力機能拡張

## 改善概要

標準Prolog述語 `listing/0`, `listing/1` および事実データエクスポート機能をpyprologに追加する。

## 背景・動機

### 現在の問題
- pyprologには知識ベース内容を確認する標準的な方法がない
- 外部システムとの連携でデータエクスポートが困難

### 期待効果
- **デバッグ機能強化**: 知識ベース状態の可視化
- **外部連携改善**: データエクスポート機能

## 提案機能仕様

### 1. listing/0 述語
```prolog
?- listing.
% 知識ベース内のすべての事実・ルールを出力
person(alice, 28).
person(bob, 35).
parent(X, Y) :- father(X, Y).
```

**実装詳細:**
- Runtime.rulesの全内容をPrologフォーマットで出力
- IOManagerを通じたストリーム出力
- コメント付きフォーマット対応

### 2. listing/1 述語
```prolog
?- listing(person/2).
% person/2 述語のみ出力
person(alice, 28).
person(bob, 35).
```

**実装詳細:**
- 述語名/アリティ指定での絞り込み出力
- 複数述語の一括指定対応: `listing([person/2, parent/2])`

### 3. export_facts/2 述語（独自拡張）
```prolog
?- export_facts(person/2, 'persons.csv').
% CSV形式でエクスポート
true.
```

**実装詳細:**
- フォーマット: CSV, JSON, TSV対応
- フィールド名解決: コメント解析または自動生成
- エラーハンドリング

## 実装アーキテクチャ

### 1. 新規組み込み述語クラス
```python
# pyprolog/runtime/builtins.py に追加
class ListingPredicate(BuiltinPredicate):
    def execute(self, args, env, runtime):
        # listing/0, listing/1 の実装
        
class ExportFactsPredicate(BuiltinPredicate):  
    def execute(self, args, env, runtime):
        # export_facts/2 の実装
```

### 2. フォーマッター機能
```python
# pyprolog/util/formatters.py (新規)
class PrologFormatter:
    def format_rules(self, rules: List[Rule]) -> str
    def format_as_csv(self, facts: List[Fact]) -> str
    def format_as_json(self, facts: List[Fact]) -> str
```

### 3. Runtime拡張
```python
# pyprolog/runtime/interpreter.py 修正
class Runtime:
    def get_rules_by_predicate(self, predicate: str, arity: int) -> List[Rule]
    def export_facts(self, predicate: str, format: str, filepath: str) -> bool
```

## API仕様

### Python API
```python
runtime = Runtime()
runtime.consult("facts.pl")

# 全ルール取得
all_rules = runtime.get_all_rules()

# 述語別ルール取得  
person_rules = runtime.get_rules_by_predicate("person", 2)

# エクスポート
runtime.export_facts("person", "csv", "output.csv")
```

### Prolog述語API
```prolog
listing.                    % 全ルール出力
listing(person/2).         % 指定述語出力
export_facts(person/2, 'data.csv').  % CSV出力
export_facts(person/2, json('data.json')).  % JSON出力
```
