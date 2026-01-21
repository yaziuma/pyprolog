# PyProlog - Advanced Prolog Interpreter in Python

[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://www.python.org/)
[![Tests](https://img.shields.io/badge/Tests-351%20Passing-green.svg)](#testing)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Unified Input](https://img.shields.io/badge/Unified%20Input%20System-Active-brightgreen.svg)](#unified-input-system)

PyPrologは、Pythonで実装された拡張性の高いPrologインタープリタです。**統一入力システム**、**日本語変数名サポート**、および**高度な開発ツール**を備え、`uv` を利用した効率的な開発環境を提供します。

**2025年9月更新**: 統一入力システム（Unified Input System）の実装が完了しました。継続実行機能により、対話的プログラムの応答性が向上しています。

## 主な特徴

### 言語サポート
- **日本語変数名・ファンクター名のサポート**: `患者診断(症状, 年齢, 結果)` のような日本語記述が可能
- **Unicode文字対応**: 多言語文字の使用が可能
- **包括的な演算子サポート**: 70種類以上の算術、比較、論理、制御演算子を実装

### 開発ツール
- **`prolog_explain`**: クエリの推論過程を可視化（テキスト/ツリー/JSON形式）
- **`prolog_search`**: 大規模知識ベースの検索機能
- **`prolog_validate`**: 静的解析によるコード品質チェック

### 実用機能
- **統一入力システム**: InputHandlerインターフェースによる入力処理の統合管理
- **継続実行**: 中断・再開可能な処理フローの実現
- **スレッドセーフI/O**: 複数同時対話セッションのサポート
- **標準的な組み込み述語**: 40種類以上の標準述語（`listing/0`, `listing/1`, `export_facts/2` 等）を実装
- **知識ベース管理**: 述語一覧表示、データのエクスポート機能
- **自動型変換**: 数値文字列の自動判定および変換機能
- **CLIインターフェース**: インタラクティブREPLおよびバッチ処理に対応
- **拡張I/O機能**: ファイル入出力、ストリーム処理、入力待ち検知
- **メタ述語**: `findall/3`、動的述語操作をサポート

## プロジェクト状況

**2025年9月14日 - 統一入力システム完全実装 (v0.7.0)**

- **統一入力システム**: InputHandlerインターフェースによる入力処理の統一
- **継続実行**: スレッドスタックフレーム保持による処理の中断・再開
- **テスト**: 既存および新規テストケースによる動作検証済み
- **後方互換性**: 既存APIとの完全な互換性を維持

**2025年8月27日 - 知識ベース管理機能追加 (v0.6.0)**

- **知識ベース表示**: `listing/0`, `listing/1` によるルール表示
- **データエクスポート**: `export_facts/2` によるCSV/JSON/TSV形式出力
- **多言語対応**: 日本語述語名・変数名の表示・エクスポート

**2025年8月21日 - 入力システム強化 (v0.5.0)**

- **型変換**: `atom_number/2` による型変換
- **自動入力変換**: `read_line/1`, `get_char/1` における数値自動判定
- **複数入力対応**: 繰り返し入力およびバリデーション処理のサポート
- **IOシステム統合**: ストリーム処理との統合

## クイックスタート

### 動作確認手順

```bash
# 1. リポジトリのクローン
git clone <repository-url>
cd pyprolog

# 2. 依存関係のインストール
uv sync

# 3. Prolog クエリの実行
uvx python -m pyprolog.cli.prolog tests/data/puzzle1.prolog

# 4. 日本語医療診断システムの実行例
uvx python -c "
from pyprolog.runtime.interpreter import Runtime
r = Runtime()
r.consult('tests/data/medical_diagnosis_kb_japanese.pl')
solutions = r.query('患者診断([発熱, 咳], 30, [], [], Result).')
print(f'診断結果: {solutions}')
"
```

### インタラクティブREPLの使用

```bash
# REPLの起動
uvx python -m pyprolog.cli.interactive_repl

# 実行例
?- 年齢 = 25, 年齢 > 20.
年齢 = 25.

?- append([a, b], [c, d], リスト).
リスト = [a, b, c, d].
```

## 開発ツールの使用方法

### prolog_explain: 推論過程の可視化
```python
from pyprolog.tools.explain_tool import ExplainTool
tool = ExplainTool(runtime)
result = tool.explain("member(X, [1, 2, 3])", format="tree")
print(result)
```

### prolog_search: 知識ベース検索
```python
from pyprolog.tools.search_tool import SearchTool
tool = SearchTool(runtime)
results = tool.search("patient", search_type="predicate")
```

### prolog_validate: 静的解析
```python
from pyprolog.tools.validate_tool import ValidateTool
tool = ValidateTool(runtime)
issues = tool.validate(check_type="all")
```

### 統一入力システム: InputHandlerの実装
```python
from pyprolog.runtime.interpreter import Runtime
from pyprolog.runtime.unified_input_system import InputHandler, InputEvent

class AdvancedInputHandler(InputHandler):
    def handle_input_request(self, event: InputEvent):
        # 入力要求の処理ロジックを実装
        if event.input_type == "line":
            return get_input_from_gui()
        elif event.input_type == "char":
            return get_single_char()
        return None

runtime = Runtime()
runtime.io_manager.set_input_handler(AdvancedInputHandler())
runtime.io_manager.enable_threading()
```

## インストール・セットアップ

### 前提条件
- Python 3.8以上
- `uv`パッケージマネージャー

### uv のインストール

```bash
# macOS / Linux
curl -LsSf https://astral.sh/uv/install.sh | sh
# Windows
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
```

詳細は [uv 公式ドキュメント](https://astral.sh/uv) を参照してください。

## プロジェクトのセットアップ

### プロジェクト初期化 (オプション)

```bash
uv init
```

### Python バージョン管理

```bash
# バージョンの指定
uv python pin 3.10
```

### 仮想環境の作成と有効化

```bash
# 作成
uv venv

# 有効化 (macOS / Linux)
source .venv/bin/activate
# 有効化 (Windows)
.\.venv\Scripts\activate
```

## 依存関係の管理

`pyproject.toml` を使用した依存関係管理を推奨します。

```bash
# 依存関係の同期
uv sync

# パッケージの追加
uv add requests

# 開発用依存関係の追加
uv add --dev pytest ruff
```

## REPL の実行

```bash
uvx python -m pyprolog.cli.prolog tests/data/puzzle1.prolog
```

## 主要機能詳細

### 組み込み述語
- **基本I/O**: `write/1`, `nl/0`, `tab/1`, `get_char/1`, `read_line/1` 等
- **知識ベース管理**: `listing/0`, `export_facts/2` 等
- **型チェック**: `var/1`, `atom/1`, `number/1` 等
- **リスト操作**: `member/2`, `append/3` 等
- **メタ述語**: `findall/3`, `asserta/1` 等
- **演算子**: 算術、比較、論理演算子をサポート

### 日本語サポート
Unicode対応により、日本語を含む多言語での記述が可能です。

### パフォーマンス
- 大規模知識ベースに対応したインデックス機能
- 遅延評価によるメモリ効率化
- 並行処理のサポート

詳細は `docs/pyprolog_実装済み機能・述語リスト.md` を参照してください。

## テストと品質管理

### テストの実行

```bash
# 全テスト実行
uvx pytest --cov=pyprolog tests
```

### コード品質管理

```bash
# リンティングとフォーマット
uvx ruff check .
uvx ruff format .
```

## ライブラリとしての利用

### インストール

```bash
uv add pieprolog
```

### 使用例

```python
from pyprolog import Scanner, Parser, Runtime

def main():
    source = '''
    location(computer, office).
    isoffice(X) :- location(computer, X).
    '''
    tokens = Scanner(source).tokenize()
    rules = Parser(tokens).parse_rules()
    runtime = Runtime(rules)
    
    # クエリ実行
    goal = Parser(Scanner('location(X, office).').tokenize()).parse_terms()
    for item in runtime.execute(goal):
        print(f"Solution: {item}")

if __name__ == "__main__":
    main()
```

詳細は `docs/python_api_reference.md` を参照してください。

## コントリビューション

バグ報告、機能要望、プルリクエストを歓迎します。

1. Issueの確認
2. リポジトリのフォークおよびブランチ作成
3. 開発、テスト、品質チェック
4. プルリクエストの作成

## ドキュメント

- [`CLAUDE.md`](CLAUDE.md): 開発者ガイド
- [`docs/入力待ち検知ガイド.md`](docs/入力待ち検知ガイド.md): 入力システムガイド
- [`docs/pyprolog_実装済み機能・述語リスト.md`](docs/pyprolog_実装済み機能・述語リスト.md): 機能・述語リスト
- [`docs/python_api_reference.md`](docs/python_api_reference.md): Python API リファレンス

## ライセンス

MIT License - 詳細は [LICENSE](LICENSE) ファイルを参照してください。

## 作者・保守者

本プロジェクトは Claude Code の協力により開発・保守されています。