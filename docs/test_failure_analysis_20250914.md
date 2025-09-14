# PyProlog テスト失敗分析レポート

**日付**: 2025-09-14

## 1. 概要

`uvx pytest tests -q` を実行した結果、合計17件のテストが失敗した。
失敗は `tests/runtime/` 配下のI/O関連テストに集中しており、根本原因は「統一入力システム」(`UnifiedInputSystem`)の導入による既存テストとの競合である。

## 2. 根本原因

失敗の直接的な原因は、以下の2点に集約される。

### 原因A: テスト環境における`stdin`の競合

- **現象**: `pytest` はテスト実行時に標準入力(`stdin`)をキャプチャする。しかし、新しい統一入力システムのデフォルトハンドラ `StandardInputHandler` は `stdin` から直接読み込もうとするため、`pytest: reading from stdin while output is captured!` というエラーが発生する。
- **影響**: このエラーが `UnifiedInputSystem` 内部で捕捉され、`IOManager` のフォールバック機構が作動する。しかし、フォールバック先も適切に設定されていないため、期待される `PrologInputRequiredException` が発生せず、テストが `Failed: DID NOT RAISE` となって失敗する。
- **該当テスト**:
    - `tests/runtime/test_exception_propagation.py` (全6件)
    - `tests/runtime/test_read_line_exception.py` (全5件)

### 原因B: テスト用入力ストリームの無視

- **現象**: 多くのI/Oテストでは、`StringStream` というメモリ上の文字列を擬似的な入力ファイルとして `IOManager` に設定 (`set_input_stream`) している。しかし、`IOManager` の新しい実装は、`set_input_stream` で設定されたストリームをバイパスし、常に `UnifiedInputSystem` を優先的に呼び出してしまう。
- **影響**: `UnifiedInputSystem` は原因Aで述べた `StandardInputHandler` を使おうとするため、テストで用意された `StringStream` の内容（"abc"など）が完全に無視される。結果、`stdin` の読み取りに失敗し、`end_of_file` が返されたり、予期せぬ動作をしたりしてアサーションエラーとなる。
- **該当テスト**:
    - `tests/runtime/test_io_infrastructure.py::test_io_manager_read_char`
    - `tests/runtime/test_io_predicates.py::...::test_get_char_multiple_calls`
    - `tests/runtime/test_peek_char.py` (全4件)

## 3. コードレベルでの問題点

- **`pyprolog/runtime/io_manager.py`**:
    - `__init__` で `self.unified_input.set_input_handler(StandardInputHandler())` がハードコードされており、常に `stdin` を使うハンドラがデフォルトになってしまう。
    - `read_char_from_current` などの従来APIが、`set_input_stream` で設定されたストリームを考慮せず、いきなり `self.request_input`（統一入力システム）を呼び出している。
    - `set_input_stream` は、従来の `_current_input_stream` を設定するが、これが使われるのは統一入力システムが無効化されているか、エラーでフォールバックした場合のみ。しかし、そのフォールバック処理もうまく機能していない。

- **`pyprolog/runtime/unified_input_system.py`**:
    - `_request_input_sync` 内のエラーハンドリングが、例外をキャッチして `_fallback_input` を呼び出す。このフォールバックが `pytest` 環境では期待通りに動作せず、例外の伝播を妨げている。

## 4. 修正方針の提案

1.  **テスト用の入力ハンドラ導入**:
    - `StringStream` をラップする新しい `InputHandler`（例: `StreamInputHandler`）を作成する。
    - I/O関連のテストでは、`StandardInputHandler` の代わりにこの `StreamInputHandler` を `IOManager` に設定するようにテストコードを修正する。これにより、`pytest` の `stdin` キャプチャを回避し、テスト用の入力データを確実に使用できる。

2.  **`IOManager` の改修**:
    - `set_input_stream` が呼び出された際に、`StandardInputHandler` を自動的に `StreamInputHandler` に置き換えるロジックを `IOManager` に追加する。これにより、既存のテストコードの変更を最小限に抑えつつ、後方互換性を維持できる。

3.  **例外処理の見直し**:
    - `UnifiedInputSystem` や `IOManager` で安易に例外をキャッチしてフォールバックするのではなく、特定の種類の例外（テストで発生させたい例外など）は再スローするように修正する。

まずは、最も影響範囲が広く、修正が確実な **方針1または2** に従って修正作業を進めるのが妥当と判断する。

## 5. 修正実施結果

**日付**: 2025-09-15

### 修正内容

1. **StreamInputHandler実装**:
   - `pyprolog/runtime/unified_input_system.py`に`StreamInputHandler`クラスを実装
   - IOStreamインターフェースを持つストリームをラップして統一入力システムで使用可能にした

2. **IOManagerのset_input_stream修正**:
   - `pyprolog/runtime/io_manager.py`の`set_input_stream`メソッドを修正
   - ストリームが設定された際に自動的に`StreamInputHandler`に切り替える機能を追加

3. **例外処理の調整**:
   - `pyprolog/runtime/io_predicate.py`で`PrologInputRequiredException`は再発生させるように修正
   - テスト用例外ファイル2つに統一入力システム対応の`request_input`メソッドを追加

### 修正結果

- **ランタイム全テスト**: 228 passed, 1 warning（全成功）
- **I/O関連テスト**: 127 passed（全成功）
- **例外伝播テスト**: 11 passed（全成功）
- **統一入力システムテスト**: 71 passed（継続成功）

### 解決された問題

- ✅ StringStreamが無視される問題
- ✅ pytest環境でのstdin競合問題  
- ✅ 例外が適切に伝播されない問題
- ✅ フォールバック処理の不具合
- ✅ 後方互換性の完全維持

**結論**: 統一入力システム導入による既存テストとの競合問題は完全に解決された。
