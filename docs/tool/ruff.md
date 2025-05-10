Ruff は、非常に高速な Python リンターおよびコードフォーマッターです。Rust で書かれており、既存のリンター（Flake8 など）やフォーマッター（Black など）よりも 10〜100 倍高速に動作することを目指しています。

## Ruff の主な使い方

Ruff は主にコマンドラインツールとして使用され、コードの検査（lint）、整形（format）以外にも、ルールの説明、設定オプションの表示、対応リンターの一覧表示、キャッシュのクリア、言語サーバーの実行、コード分析、バージョン表示などの機能があります。

### インストール

`uv`（推奨）、`pip`、または`pipx`を使用して Ruff をインストールできます。

```shell
# uv を使用する場合
uvx ruff check  # 現在のディレクトリ内のすべてのファイルを検査
uvx ruff format # 現在のディレクトリ内のすべてのファイルを整形

# または uv でインストール
uv pip install ruff

# pip を使用する場合
pip install ruff

# pipx を使用する場合
pipx install ruff
```

### コードの検査 (Linting)

以下のコマンドで Ruff をリンターとして実行できます。

```shell
ruff check                               # 現在のディレクトリ（およびサブディレクトリ）の全ファイルを検査
ruff check path/to/code/                 # 指定したディレクトリ（およびサブディレクトリ）の全ファイルを検査
ruff check path/to/code/*.py             # 指定したディレクトリ内の全`.py`ファイルを検査
ruff check path/to/code/to/file.py       # 指定したファイルを検査
ruff check @arguments.txt                # ファイルから引数を読み込んで検査
```

### コードの整形 (Formatting)

以下のコマンドで Ruff をフォーマッターとして実行できます。

```shell
ruff format                               # 現在のディレクトリ（およびサブディレクトリ）の全ファイルを整形
ruff format path/to/code/                 # 指定したディレクトリ（およびサブディレクトリ）の全ファイルを整形
ruff format path/to/code/*.py             # 指定したディレクトリ内の全`.py`ファイルを整形
ruff format path/to/code/to/file.py       # 指定したファイルを整形
ruff format @arguments.txt                # ファイルから引数を読み込んで整形
```

### その他のコマンド

Ruff には、検査と整形以外にもいくつかの便利なコマンドがあります。

```shell
ruff rule LINT_CODE                      # 特定のルール (例: E501) の説明を表示
ruff rule --all                          # すべてのルールの説明を表示
ruff config                              # 利用可能な設定オプションを一覧表示または説明
ruff linter                              # サポートされているすべてのアップストリームリンターを一覧表示
ruff clean                               # 現在のディレクトリおよびサブディレクトリ内のキャッシュをクリア
ruff server                              # 言語サーバーを実行
ruff analyze                             # Python ソースコードの分析を実行
ruff version                             # Ruff のバージョンを表示
ruff help <command>                      # 特定のサブコマンドのヘルプを表示
```

### グローバルオプション

以下のオプションは、すべての Ruff コマンドで使用できます。

- `-h`, `--help`: ヘルプメッセージを表示します。
- `-V`, `--version`: Ruff のバージョンを表示します。

### ログレベル

- `-v`, `--verbose`: 詳細なログを有効にします。
- `-q`, `--quiet`: 診断結果のみを表示し、それ以外のログは表示しません。
- `-s`, `--silent`: すべてのログを無効にします（ただし、診断結果が検出された場合はステータスコード "1" で終了します）。

### 設定オプション

- `--config <CONFIG_OPTION>`: TOML 設定ファイル（`pyproject.toml` または `ruff.toml`）へのパス、または特定の設定オプションを上書きする TOML の `<KEY> = <VALUE>` ペアを指定します。このオプションによる個々の設定の上書きは、`--config` で指定された設定ファイルを含むすべての設定ファイルよりも常に優先されます。
- `--isolated`: すべての設定ファイルを無視します。
