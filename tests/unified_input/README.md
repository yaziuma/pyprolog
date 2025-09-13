# 統一入力システムテスト

pyprologの統一入力システム改修用のテストスイートです。

## テスト構成

### 1. IOPredicate基底クラステスト (`test_io_predicate_base.py`)
- IOPredicate基底クラスのテンプレートメソッドパターンをテスト
- 引数検証、入力変換、統一化処理の共通機能をテスト
- get_char/1, read_line/1述語の具象実装をテスト

**主要テストケース:**
- 引数数検証（正常/異常）
- プロンプト文字列生成
- EOF処理
- 数値変換（成功/失敗）
- Prologターム変換（文字/行入力）
- 統一入力システム呼び出し
- 引数との統一化
- execute()テンプレートメソッド
- エラー時の述語失敗

### 2. UnifiedInputSystem/ThreadingControllerテスト (`test_unified_input_system.py`)
- UnifiedInputSystemの中央制御機能をテスト
- ThreadingControllerのスレッド間通信をテスト
- シングル/マルチスレッドモード切り替えをテスト

**主要テストケース:**
- ThreadingController有効化/無効化
- 入力要求のブロッキング処理
- InputHandlerエラー時の処理
- 複数入力要求の順次処理
- UnifiedInputSystem統計情報収集
- フォールバック機能
- 並行入力要求（スレッド安全性）

### 3. IOManager統合テスト (`test_io_manager_integration.py`)
- 統一入力システムと既存IOManagerの統合をテスト
- 完全な後方互換性維持をテスト
- 新旧API共存をテスト

**主要テストケース:**
- 新API（request_input）の動作
- 従来API（read_*_from_current）の互換性
- 統一入力システム有効/無効切り替え
- フォールバックストリーム使用
- エラーハンドリングとフォールバック
- ストリーム管理API
- 統計情報収集

### 4. 統合テスト (`test_integration.py`)
- 全コンポーネントの統合動作をテスト
- Runtime統合をテスト
- 真の継続実行をテスト

**主要テストケース:**
- IOPredicate + UnifiedInputSystem統合
- シングル/マルチスレッドモード一貫性
- スレッド化実行（遅延あり）
- 複数述語並行実行
- エラーハンドリング統合
- 複雑なシナリオ（混在述語シーケンス）

## テスト実行

### 全テスト実行
```bash
# 統一入力システムテストのみ実行
uvx pytest tests/unified_input/ -q

# 詳細出力付き
uvx pytest tests/unified_input/ -v -s

# カバレッジ付き
uvx pytest tests/unified_input/ --cov=pyprolog.runtime --cov-report=html
```

### 個別テスト実行
```bash
# IOPredicate基底クラステストのみ
uvx pytest tests/unified_input/test_io_predicate_base.py -v

# UnifiedInputSystemテストのみ
uvx pytest tests/unified_input/test_unified_input_system.py -v

# IOManager統合テストのみ  
uvx pytest tests/unified_input/test_io_manager_integration.py -v

# 統合テストのみ
uvx pytest tests/unified_input/test_integration.py -v
```

### 特定テストケース実行
```bash
# IOPredicate基底クラスの引数検証テスト
uvx pytest tests/unified_input/test_io_predicate_base.py::TestIOPredicateBase::test_argument_validation_success -v

# ThreadingControllerの有効化テスト
uvx pytest tests/unified_input/test_unified_input_system.py::TestThreadingController::test_enable_disable -v

# スレッド化実行テスト
uvx pytest tests/unified_input/test_integration.py::TestThreadedExecution::test_threaded_execution_with_delay -v
```

## テスト設計原則

### 1. 実装前テスト（TDD）
- 設計ドキュメントに基づいてテストを先行実装
- 実際の実装時に即座にフィードバック取得
- テストがAPIの仕様書として機能

### 2. モック使用戦略
- 外部依存（Runtime、Logic Interpreter等）はモック化
- テスト対象コンポーネントの単体動作に集中
- 統合テストでは実際の組み合わせをテスト

### 3. スレッド安全性テスト
- マルチスレッド環境での動作確認
- 並行実行時の競合状態検出
- デッドロック防止確認

### 4. エラーハンドリングテスト
- 異常系シナリオの網羅
- エラー回復機能の検証
- フォールバック機能の動作確認

### 5. 後方互換性テスト
- 既存APIの継続動作保証
- 新旧API共存確認
- 段階的移行シナリオ検証

## 実装時の注意点

### 1. テスト用モッククラス
各テストファイルには実装前のモッククラスが含まれています：
- `BuiltinPredicate`, `PrologType`, `Atom`, `Number`
- `IOPredicate`, `UnifiedInputSystem`, `ThreadingController`
- `IOManager`, `Runtime`

実際の実装時は、これらのモックを実際のクラスに置き換えてください。

### 2. インポートの修正
実装完了後、以下のインポートを実際のモジュールに変更：
```python
# テスト用（現在）
from tests.unified_input.test_io_predicate_base import IOPredicate

# 実装後
from pyprolog.runtime.io_predicate import IOPredicate
```

### 3. タイムアウト値調整
テスト用に短いタイムアウト値（5秒等）を使用しています。
実装時は実用的な値（300秒等）に調整してください。

## テスト品質指標

- **テストカバレッジ**: 90%以上
- **テストケース数**: 100+件
- **実行時間**: 30秒以内
- **並行テスト**: 4スレッド対応
- **エラーケースカバレッジ**: 異常系50%以上

このテストスイートにより、統一入力システムの品質と動作保証が確保されます。