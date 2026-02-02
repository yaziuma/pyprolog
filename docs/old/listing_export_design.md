# pyprologライブラリ改善提案 - 概要設計書

## 機能概要

pyprologに標準Prolog互換の知識ベース出力機能とデータエクスポート機能を追加する。

## 実装対象機能

### 1. 標準Prolog述語
- **listing/0**: 全知識ベース内容の出力
- **listing/1**: 指定述語の出力

### 2. 独自拡張述語
- **export_facts/2**: 事実データの外部形式エクスポート（CSV/JSON/TSV対応）

## アーキテクチャ設計

### コンポーネント構成
```
pyprolog/
├── runtime/
│   ├── builtins.py          # ListingPredicate, ExportFactsPredicate追加
│   └── interpreter.py       # Runtime機能拡張
├── util/
│   └── formatters.py        # 新規: 出力フォーマット処理
└── io/
    └── export_manager.py    # 新規: ファイル出力管理
```

### 実装方針

**1. 組み込み述語拡張**
- `BuiltinPredicate`継承の新述語クラス実装
- Runtime.rulesへの直接アクセスによる効率的な処理
- IOManager連携による標準出力制御

**2. フォーマッター設計**
- `PrologFormatter`: Prolog形式出力
- `DataExporter`: 構造化データ出力（CSV/JSON/TSV）
- 拡張可能なフォーマット追加アーキテクチャ

**3. エラーハンドリング**
- 述語指定の妥当性検証
- ファイル出力権限・パス検証
- フォーマット変換例外処理

## API設計

### Python API
```python
# 知識ベース参照
runtime.get_all_rules()
runtime.get_rules_by_predicate(name, arity)

# エクスポート機能  
runtime.export_facts(predicate, format, filepath)
```

### Prolog述語API
```prolog
listing.                             % 全出力
listing(predicate/arity).           % 述語別出力
export_facts(predicate/arity, file). % エクスポート
```

## 実装優先順位

1. **Phase 1**: `listing/0`, `listing/1` 基本機能
2. **Phase 2**: `export_facts/2` CSV対応  
3. **Phase 3**: JSON/TSV形式拡張