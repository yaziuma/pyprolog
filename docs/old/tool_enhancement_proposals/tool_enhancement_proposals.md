# 機能拡張提案書

## 🔧 実用性向上機能

### 4. `prolog_explain` - 推論過程の説明
**目的**: クエリがどのように解決されたかのトレース情報を提供

**パラメータ**:
- `query` (string): 説明したいPrologクエリ
- `depth` (optional, int): トレースの深さ
- `format` (optional, string): 出力形式 ("text", "tree", "json")


### 5. `prolog_validate` - ルール検証機能
**目的**: 知識ベースの整合性チェックと問題点の報告

**パラメータ**:
- `check_type` (optional, string): チェック種別 ("all", "conflicts", "unreachable", "undefined")
- `detailed` (optional, bool): 詳細レポートの生成


### 6. `prolog_search` - ナレッジベース検索
**目的**: 特定のパターンや条件に合致するルール・事実を検索

**パラメータ**:
- `pattern` (string): 検索パターン（述語名、引数パターンなど）
- `search_type` (string): 検索タイプ ("predicate", "argument", "full_text")
- `limit` (optional, int): 結果の上限数
