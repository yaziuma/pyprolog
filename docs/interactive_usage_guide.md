# PyProlog 対話型システム使用ガイド

## 概要

PyPrologには、ユーザーが対話的にPrologクエリを実行できるシステムが追加されました。このガイドでは、対話型システムの使用方法について説明します。

## 起動方法

### 1. 基本的な起動

```bash
python interactive_prolog.py
```

空のPrologセッションが開始されます。

### 2. ファイルを読み込んで起動

```bash
python interactive_prolog.py -f sample_usage/family.pl
```

指定したPrologファイルを読み込んでセッションを開始します。

### 3. デモモードで起動

```bash
python interactive_prolog.py --demo
```

あらかじめ用意されたデモデータでセッションを開始します。

## 対話コマンド

### システムコマンド

| コマンド | 説明 |
|---------|------|
| `:help` | ヘルプメッセージを表示 |
| `:quit` または `:exit` | システムを終了 |
| `:load <ファイル>` | Prologファイルを読み込み |
| `:reload` | 現在のファイルを再読み込み |
| `:show_rules` | 現在読み込まれているルールを表示 |
| `:clear` | 現在のルールをクリア |
| `:status` | システム状態を表示 |

### Prologクエリ

通常のPrologクエリを入力できます：

```prolog
likes(mary, X).
parent(X, Y).
append([1,2], [3,4], L).
X is 2 + 3.
```

## 使用例

### 1. 基本的な使用例

```
Prolog> :load sample_usage/family.pl
ファイル 'sample_usage/family.pl' を読み込みました

Prolog> parent(X, Y).
2 件の解が見つかりました:
   1. X = tom, Y = bob
   2. X = tom, Y = liz

Prolog> :show_rules
現在のルール (3 件):
   1. parent(tom, bob).
   2. parent(tom, liz).
   3. grandparent(X, Z) :- parent(X, Y), parent(Y, Z).
```

### 2. 算術演算の例

```
Prolog> X is 5 + 3.
1 件の解が見つかりました:
   1. X = 8

Prolog> X is 10 * 2, Y is X / 4.
1 件の解が見つかりました:
   1. X = 20, Y = 5
```

### 3. リスト操作の例

```
Prolog> member(X, [1, 2, 3, 4, 5]).
5 件の解が見つかりました:
   1. X = 1
   2. X = 2
   3. X = 3
   4. X = 4
   5. X = 5

Prolog> append([a, b], [c, d], L).
1 件の解が見つかりました:
   1. L = [a, b, c, d]
```

## エラー処理

システムは以下のエラーを適切に処理します：

- **構文エラー**: 不正なProlog構文
- **ファイルエラー**: 存在しないファイルの読み込み
- **実行時エラー**: クエリ実行中のエラー

エラーが発生した場合、詳細なエラーメッセージが表示され、セッションは継続されます。

## デモデータ

デモモード（`--demo`）では以下のデータが利用できます：

```prolog
% 家族関係
parent(tom, bob).
parent(tom, liz).
parent(bob, ann).
parent(bob, pat).
parent(pat, jim).

% ルール
grandparent(X, Z) :- parent(X, Y), parent(Y, Z).

% 好み関係
likes(mary, food).
likes(mary, wine).
likes(john, wine).
likes(john, mary).

% 幸せのルール
happy(X) :- likes(X, wine).
```

### デモクエリ例

```
Prolog> parent(X, Y).
Prolog> grandparent(X, Y).
Prolog> happy(X).
Prolog> likes(mary, X).
```

## 技術的詳細

### アーキテクチャ

- **SimplePrologInteractive**: メインの対話クラス
- **Runtime**: Prologランタイムエンジン
- **Parser/Scanner**: 構文解析システム

### 拡張性

新しい対話コマンドは`SimplePrologInteractive._handle_command()`メソッドに追加できます。

### カスタマイズ

- カラー設定: `colorama`を使用
- 履歴管理: セッション履歴を自動記録
- エラー処理: 詳細なエラーメッセージ

## トラブルシューティング

### 一般的な問題

1. **モジュールが見つからない**
   ```
   ModuleNotFoundError: No module named 'prolog'
   ```
   → プロジェクトルートディレクトリから実行してください

2. **ファイルが見つからない**
   ```
   ファイル 'xxx.pl' が見つかりません
   ```
   → ファイルパスを確認してください

3. **構文エラー**
   ```
   Prologエラー: Unexpected token
   ```
   → Prolog構文を確認してください

### デバッグ方法

1. `:status` コマンドでシステム状態を確認
2. `:show_rules` で読み込まれたルールを確認
3. より詳細なエラー情報が必要な場合は、Pythonの例外を確認

## 今後の拡張予定

- [ ] タブ補完機能
- [ ] より高度な履歴管理
- [ ] 設定ファイルサポート
- [ ] プロファイリング機能
- [ ] デバッガー統合

## 関連ファイル

- `interactive_prolog.py` - メインエントリーポイント
- `prolog/cli/simple_interactive.py` - 対話システム実装
- `sample_usage/` - サンプルファイル群