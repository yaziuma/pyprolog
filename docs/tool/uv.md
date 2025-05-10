### Python の管理

- `uv python install`: Python のバージョンをインストールします。
- `uv python list`: 利用可能な Python のバージョンを表示します。
- `uv python find`: インストール済みの Python のバージョンを検索します。
- `uv python pin`: 現在のプロジェクトで使用する Python のバージョンを固定します。
- `uv python uninstall`: Python のバージョンをアンインストールします。

### スクリプトの実行と依存関係の管理

- `uv run`: スクリプトを実行します。
- `uv add --script`: スクリプトに依存関係を追加します。
- `uv remove --script`: スクリプトから依存関係を削除します。

### プロジェクト管理

- `uv init`: 新しい Python プロジェクトを作成します。
- `uv add`: プロジェクトに依存関係を追加します。
- `uv remove`: プロジェクトから依存関係を削除します。
- `uv sync`: プロジェクトの依存関係を環境と同期します。
- `uv lock`: プロジェクトの依存関係のロックファイルを作成します。
- `uv run`: プロジェクト環境でコマンドを実行します。
- `uv tree`: プロジェクトの依存関係ツリーを表示します。
- `uv build`: プロジェクトを配布用アーカイブにビルドします。
- `uv publish`: プロジェクトをパッケージインデックスに公開します。

### ツールの管理

- `uvx` / `uv tool run`: 一時的な環境でツールを実行します。
- `uv tool install`: ツールをユーザー全体にインストールします。
- `uv tool uninstall`: ツールをアンインストールします。
- `uv tool list`: インストール済みのツールを一覧表示します。
- `uv tool update-shell`: ツールの実行ファイルを含むようにシェルを更新します。

### 仮想環境とパッケージ管理 (pip インターフェース)

- `uv venv`: 新しい仮想環境を作成します。
- `uv pip install`: 現在の環境にパッケージをインストールします。
- `uv pip show`: インストール済みパッケージの詳細を表示します。
- `uv pip freeze`: インストール済みのパッケージとそのバージョンを一覧表示します。
- `uv pip check`: 現在の環境に互換性のあるパッケージがあるか確認します。
- `uv pip list`: インストール済みのパッケージを一覧表示します。
- `uv pip uninstall`: パッケージをアンインストールします。
- `uv pip tree`: 環境の依存関係ツリーを表示します。
- `uv pip compile`: 要求事項をロックファイルにコンパイルします。
- `uv pip sync`: 環境をロックファイルと同期します。

### キャッシュ管理

- `uv cache clean`: キャッシュエントリを削除します。
- `uv cache prune`: 古いキャッシュエントリを削除します。
- `uv cache dir`: uv キャッシュディレクトリのパスを表示します。

### ディレクトリパスの表示

- `uv tool dir`: uv ツールディレクトリのパスを表示します。
- `uv python dir`: uv でインストールされた Python バージョンのパスを表示します。

### uv 自体のアップデート

- `uv self update`: uv を最新バージョンにアップデートします。
