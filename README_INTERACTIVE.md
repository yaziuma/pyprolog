# PyProlog 対話型システム

PyProlog の対話型システムは、ユーザーがリアルタイムで Prolog クエリを実行できる強力なツールです。

## 🚀 クイックスタート

### 基本的な起動

```bash
uv run interactive_prolog.py
```

### デモモードで起動

```bash
uv run interactive_prolog.py --demo
```

### Prolog ファイルを読み込んで起動

```bash
uv run interactive_prolog.py -f sample_usage/family.pl
```

## 📋 主な機能

### ✨ リアルタイムクエリ実行

- Prolog クエリを入力して即座に結果を確認
- 複数の解がある場合は全て表示
- 変数バインディングの詳細表示

### 🎮 対話コマンド

| コマンド           | 機能                     |
| ------------------ | ------------------------ |
| `:help`            | ヘルプメッセージ表示     |
| `:quit` / `:exit`  | システム終了             |
| `:load <ファイル>` | Prolog ファイル読み込み  |
| `:reload`          | 現在のファイル再読み込み |
| `:show_rules`      | 読み込み済みルール表示   |
| `:clear`           | ルールクリア             |
| `:status`          | システム状態表示         |

### 🎨 視覚的表示

- カラー出力による見やすい結果表示
- エラーメッセージの分かりやすい表示
- 成功/警告/情報メッセージの色分け

## 💡 使用例

### 基本的なクエリ

```prolog
Prolog> parent(tom, X).
2 件の解が見つかりました:
   1. X = bob
   2. X = liz
```

### 複合クエリ

```prolog
Prolog> grandparent(X, Y).
3 件の解が見つかりました:
   1. X = tom, Y = ann
   2. X = tom, Y = pat
   3. X = bob, Y = jim
```

### 算術演算

```prolog
Prolog> X is 5 + 3 * 2.
1 件の解が見つかりました:
   1. X = 11
```

### リスト操作

```prolog
Prolog> member(X, [a, b, c]).
3 件の解が見つかりました:
   1. X = a
   2. X = b
   3. X = c
```

## 📚 デモデータ

デモモード（`--demo`）には以下のデータが含まれています：

### 家族関係

```prolog
parent(tom, bob).
parent(tom, liz).
parent(bob, ann).
parent(bob, pat).
parent(pat, jim).
grandparent(X, Z) :- parent(X, Y), parent(Y, Z).
```

### 好み関係

```prolog
likes(mary, food).
likes(mary, wine).
likes(john, wine).
likes(john, mary).
happy(X) :- likes(X, wine).
```

### 推奨クエリ

```prolog
parent(X, Y).          # 親子関係を表示
grandparent(X, Y).     # 祖父母関係を表示
happy(X).              # 幸せな人を表示
likes(mary, X).        # maryが好きなものを表示
```

## 🛠️ セットアップ

### 必要な依存関係

```bash
pip install colorama
```

### プロジェクト構造

```
pyprolog/
├── interactive_prolog.py          # メインエントリーポイント
├── prolog/
│   ├── cli/
│   │   └── simple_interactive.py  # 対話システム実装
│   ├── runtime/
│   │   └── interpreter.py         # Prologランタイム
│   └── parser/
│       ├── parser.py              # 構文解析器
│       └── scanner.py             # 字句解析器
├── sample_usage/                  # サンプルファイル
└── docs/
    └── interactive_usage_guide.md # 詳細ガイド
```

## 🎯 高度な使用方法

### セッション管理

- システムは自動的にクエリ履歴を記録
- セッション終了時に統計情報を表示

### ファイル操作

```bash
# セッション中にファイルを読み込み
Prolog> :load new_rules.pl

# 現在のルールを確認
Prolog> :show_rules

# システム状態を確認
Prolog> :status
```

### エラー処理

システムは以下のエラーを適切に処理します：

- 構文エラー（不正な Prolog 構文）
- ファイルエラー（存在しないファイル）
- 実行時エラー（クエリ実行中の問題）

## 🔧 トラブルシューティング

### よくある問題

#### 1. モジュールが見つからない

```
ModuleNotFoundError: No module named 'prolog'
```

**解決方法**: プロジェクトルートディレクトリから実行してください

#### 2. ファイルが見つからない

```
ファイル 'xxx.pl' が見つかりません
```

**解決方法**: ファイルパスを確認してください

#### 3. 構文エラー

```
Prologエラー: Unexpected token
```

**解決方法**: Prolog 構文を確認してください

### デバッグ方法

1. `:status` でシステム状態を確認
2. `:show_rules` で読み込まれたルールを確認
3. より詳細な情報が必要な場合は、ログメッセージを参照

## 🎮 インタラクティブな学習

### Prolog 初心者向け

1. デモモードで起動: `python interactive_prolog.py --demo`
2. 基本クエリから始める: `parent(X, Y).`
3. ルールを理解する: `grandparent(X, Y).`
4. 条件付きクエリを試す: `happy(X).`

### 上級ユーザー向け

- 独自の Prolog ファイルを作成
- 複雑なルールシステムを構築
- パフォーマンステストの実行

## 📈 パフォーマンス

### 最適化のヒント

- 大きなファイルは分割して読み込み
- 複雑なクエリは段階的に構築
- `:clear` で不要なルールを削除

### 制限事項

- メモリ使用量はルール数に比例
- 深い再帰は時間がかかる場合がある

## 🔮 今後の拡張予定

## 📝 ライセンス

このプロジェクトは、PyProlog メインプロジェクトと同じライセンスの下で配布されます。

## 🤝 貢献

バグ報告、機能要求、プルリクエストを歓迎します！

---

**📞 サポート**

- ドキュメント: `docs/interactive_usage_guide.md`
- サンプル: `sample_usage/` ディレクトリ
- 問題報告: GitHub の Issue トラッカー

**🎉 楽しい Prolog プログラミングを！**
