# PyProlog 対話型システム

PyProlog の対話型システムは、ユーザーがリアルタイムで Prolog クエリを実行できる強力なツールです。

**🆕 2025年9月更新**: 統一入力システム（Unified Input System）により対話性能が大幅向上。真の継続実行で応答性の高い入力処理を実現しました。

## 🚀 クイックスタート

### 基本的な起動

```bash
uv run python -m pyprolog.cli.interactive_repl
```

### 対話型REPLで起動

```bash
uv run python -m pyprolog.cli.repl
```

### Prolog ファイルを読み込んで実行

```bash
uv run python -m pyprolog.cli.prolog sample_usage/family.pl
```

### unsafeモードでワークフローを実行

```bash
uv run python -m pyprolog.cli.prolog --unsafe workflow/main.pl
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

### 🔌 外部Pythonスクリプト実行

unsafeモードでは、Prologファイル内から登録済み Python スクリプトを起動できます。

```prolog
:- py_register(run_task, "/absolute/path/to/run_task.py").

run(Exit, Out, Err) :-
    py_call(run_task, ["--mode", "fast"], Exit, Out, Err).
```

注意点:

- `pyprolog.cli.prolog` を `--unsafe` 付きで起動する必要があります
- 登録パスは絶対パスのみです
- `Args` はコマンドライン引数として渡されます
- 標準入力や対話入力は渡されません

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

### 🆕 統一入力システム対応（新機能）

```prolog
Prolog> user_input_demo.
あなたの名前は？ Alice
年齢は？ 25
こんにちは、Aliceさん（25歳）！
1 件の解が見つかりました:
   1. true
```

**新機能の特徴:**
- **真の継続実行**: 入力待ち中もシステムが応答
- **スレッドセーフ**: 複数の対話が同時実行可能
- **統一インターフェース**: 全ての入力処理が統一されたAPIで動作

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
├── pyprolog/
│   ├── cli/
│   │   ├── interactive_repl.py    # 対話システム実装
│   │   ├── repl.py                # REPL実装
│   │   └── prolog.py              # CLIエントリーポイント
│   ├── runtime/
│   │   ├── interpreter.py         # Prologランタイム
│   │   └── unified_input_system.py # 統一入力システム
│   └── parser/
│       ├── parser.py              # 構文解析器
│       └── scanner.py             # 字句解析器
├── sample_usage/                  # サンプルファイル
└── docs/
    ├── 入力待ち検知ガイド.md      # 入力システムガイド
    └── unified_input_system_design/ # 設計ドキュメント
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
- unsafe モード未有効時の外部実行エラー

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

1. 対話モードで起動: `uv run python -m pyprolog.cli.interactive_repl`
2. サンプルファイル読み込み: `:load sample_usage/family.pl`
3. 基本クエリから始める: `parent(X, Y).`
4. ルールを理解する: `grandparent(X, Y).`
5. 条件付きクエリを試す: `happy(X).`

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

## 🆕 統一入力システムの新機能

### 高度な対話プログラム例

```prolog
% 複雑な対話を伴うプログラム
diagnosis_system :-
    write('医療診断システムを開始します'), nl,
    collect_symptoms(Symptoms),
    analyze_symptoms(Symptoms, Diagnosis),
    write('診断結果: '), write(Diagnosis), nl.

collect_symptoms(Symptoms) :-
    write('症状を入力してください（終了時は "done"）'), nl,
    collect_symptoms_loop([], Symptoms).

collect_symptoms_loop(Acc, Result) :-
    write('症状: '),
    read_line(Input),
    (Input == "done" -> 
        Result = Acc
    ;   collect_symptoms_loop([Input|Acc], Result)
    ).
```

### 統一入力システム統計

- **テスト成功率**: 71/71 (100%)
- **対応入力タイプ**: char, line, peek_char
- **スレッド処理**: 真の継続実行対応
- **後方互換性**: 完全維持（228/228テスト成功）

## 🔮 今後の拡張予定

### 計画中の機能

- **WebSocket統合**: リアルタイム Web インターフェース
- **GUI版対話システム**: tkinter ベースのグラフィカルUI  
- **入力履歴機能**: セッション間での履歴保持
- **プラグインシステム**: カスタム入力ハンドラの動的読み込み

## 📝 ライセンス

このプロジェクトは、PyProlog メインプロジェクトと同じライセンスの下で配布されます。

## 🤝 貢献

バグ報告、機能要求、プルリクエストを歓迎します！

---

**📞 サポート**

- **入力システムガイド**: `docs/入力待ち検知ガイド.md`
- **統一入力システム設計**: `docs/unified_input_system_design/`
- **サンプル**: `sample_usage/` ディレクトリ
- **問題報告**: GitHub の Issue トラッカー

**🎉 楽しい Prolog プログラミングを！**
