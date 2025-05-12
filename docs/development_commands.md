# 開発コマンドガイド

このドキュメントは、`pyprolog` ライブラリの改修とテストを行う際に使用する主なコマンドをまとめたものです。コマンドの実行には `uv` を使用します。

## 2. リンティングとフォーマット

コードの品質を保つために、`Ruff` を使用してリンティングとフォーマットを行います。

### 2.1. リンティング

以下のコマンドで、プロジェクト全体のソースコードに対してリンティングを実行します。

```bash
uvx ruff check .
```

### 2.2. フォーマット

以下のコマンドで、プロジェクト全体のソースコードをフォーマットします。

```bash
uvx ruff format .
```

## 3. テストの実行

改修したコードが正しく動作することを確認するために、単体テストを実行します。テストは `pytest` フレームワークで記述・実行されます。

以下のコマンドで、`tests` ディレクトリ配下のすべてのテストを実行します。

```bash
uvx pytest
```

特定のテストファイルを実行する場合は、以下のように指定します。

```bash
uvx pytest tests/test_core_improvements.py
```

特定のテストケース（クラス）やテストメソッドを実行する場合は、以下のように指定します。

```bash
uvx pytest tests/test_core_improvements.py::TestCoreImprovements
uvx pytest tests/test_core_improvements.py::TestCoreImprovements::test_parse_empty_list
```

キーワードでテストをフィルタリングすることも可能です。

```bash
uvx pytest -k "parse_empty_list"
```

## 4. 改修からテストまでの一般的な流れ

1.  **コードの改修:**

    - `prolog/` ディレクトリ内の関連する Python ファイル（例: [`parser.py`](prolog/parser.py:1), [`interpreter.py`](prolog/interpreter.py:1) など）を編集します。
    - 必要に応じて、[`tests/test_core_improvements.py`](tests/test_core_improvements.py:1) などのテストコードを修正または追加します。

2.  **リンティングとフォーマット:**

    ```bash
    uvx ruff format .
    uvx ruff check .
    ```

    エラーや警告が表示された場合は修正します。

3.  **テストの実行:**
    ```bash
    uvx pytest
    ```
    すべてのテストが成功することを確認します。失敗したテストがある場合は、コードを修正し再度テストを実行します。

この手順を繰り返すことで、品質を維持しながら効率的に開発を進めることができます。
