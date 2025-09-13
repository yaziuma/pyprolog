# 統一入力システムテスト仕様書

## 1. テスト概要

### 1.1 目的と範囲
統一入力システム（Phase 1）の品質保証を目的とする実装前テスト（TDD）仕様書。
設計ドキュメントに基づき、実装の正確性と設計整合性を保証する。

> **用語**: 詳細な定義は[用語集](./glossary.md)を参照

**テスト対象コンポーネント:**
- IOPredicate基底クラス（テンプレートメソッドパターン）
- UnifiedInputSystem（中央制御・InputHandlerルーティング）
- ThreadingController（真の継続実行）
- IOManager統合（後方互換性）
- Runtime統合（全コンポーネント統合）

**品質指標:** カバレッジ90%以上、100+テストケース、実行時間30秒以内

## 2. テスト実装構成

### 2.1 テストファイル配置
```
tests/unified_input/
├── README.md                        # テスト実行ガイド
├── test_io_predicate_base.py        # IOPredicate基底クラステスト
├── test_unified_input_system.py     # UnifiedInputSystem/ThreadingControllerテスト
├── test_io_manager_integration.py   # IOManager統合テスト
└── test_integration.py              # エンドツーエンド統合テスト
```

**詳細実行ガイド:** [tests/unified_input/README.md](../../tests/unified_input/README.md)

### 2.2 テスト仕様とコード対応

| テスト分類 | 主要検証項目 | 実装ファイル |
|------------|-------------|-------------|
| **IOPredicate基底クラス** | テンプレートメソッド、引数検証、入力変換 | [test_io_predicate_base.py](../../tests/unified_input/test_io_predicate_base.py) |
| **ThreadingController** | スレッド間通信、ブロッキング、真の継続実行 | [test_unified_input_system.py](../../tests/unified_input/test_unified_input_system.py) |
| **UnifiedInputSystem** | モード切り替え、フォールバック、統計情報 | [test_unified_input_system.py](../../tests/unified_input/test_unified_input_system.py) |
| **IOManager統合** | 新旧API共存、後方互換性、エラーハンドリング | [test_io_manager_integration.py](../../tests/unified_input/test_io_manager_integration.py) |
| **Runtime統合** | コンポーネント統合、複雑シナリオ、パフォーマンス | [test_integration.py](../../tests/unified_input/test_integration.py) |

## 3. 重要テストケース仕様

### 3.1 真の継続実行検証
**テストケース:** `TestThreadedExecution::test_threaded_execution_with_delay`  
**検証内容:** スレッドブロッキングによるスタックフレーム保持とシームレス実行再開  
**実装:** [test_integration.py#L200-L240](../../tests/unified_input/test_integration.py)

### 3.2 後方互換性保証
**テストケース:** `TestIOManagerLegacyAPI::test_*_from_current_unified`  
**検証内容:** 既存API（read_*_from_current）の統一入力システム経由実行  
**実装:** [test_io_manager_integration.py#L400-L450](../../tests/unified_input/test_io_manager_integration.py)

### 3.3 エラーハンドリング
**テストケース:** `TestErrorHandling::test_*_error_*`  
**検証内容:** InputHandlerエラー時のフォールバック、回復処理  
**実装:** [test_integration.py#L300-L350](../../tests/unified_input/test_integration.py)

### 3.4 スレッド安全性
**テストケース:** `TestThreadedExecution::test_concurrent_predicate_execution`  
**検証内容:** 並行実行時の競合状態、デッドロック防止  
**実装:** [test_integration.py#L250-L300](../../tests/unified_input/test_integration.py)

## 4. テスト設計原則

### 4.1 実装前テスト（TDD）
- 設計ドキュメントに基づく事前テスト実装
- 実装時の即座なフィードバック提供
- テストがAPIの仕様書として機能

### 4.2 モック戦略
- 外部依存（Runtime、LogicInterpreter等）はモック化
- 各コンポーネントの単体動作に集中
- 統合テストで実際の組み合わせを検証

### 4.3 異常系カバレッジ
**目標:** 異常系50%以上カバレッジ
- InputHandlerエラー時の適切な処理
- スレッド同期エラー時の回復
- タイムアウト制御の動作確認

## 5. テスト実行と品質保証

### 5.1 基本実行コマンド
```bash
# 全テスト実行
uvx pytest tests/unified_input/ -q

# カバレッジ付き実行  
uvx pytest tests/unified_input/ --cov=pyprolog.runtime --cov-report=html

# 特定コンポーネントテスト
uvx pytest tests/unified_input/test_io_predicate_base.py -v
```

### 5.2 品質保証基準
- **機能テスト:** 全テストケース成功
- **カバレッジ:** コード行カバレッジ90%以上  
- **パフォーマンス:** 全テスト実行30秒以内
- **メモリ効率:** 10MB以内のメモリ増加

### 5.3 CI/CD統合
```yaml
# 継続的テスト実行
uvx pytest tests/unified_input/ --cov --cov-report=xml
```

## 6. 実装時の注意点

### 6.1 テスト用モック置き換え
実装完了後、テスト内のモッククラスを実際のクラスに置き換え：
```python
# テスト用（現在）
from tests.unified_input.test_io_predicate_base import IOPredicate

# 実装後
from pyprolog.runtime.io_predicate import IOPredicate
```

### 6.2 タイムアウト値調整
テスト用短縮値（5秒）を実用値（300秒）に調整

### 6.3 パフォーマンス要件
- 100回述語実行: 1秒以内
- 1000回実行時メモリ増加: 10MB以内
- スレッド切り替えオーバーヘッド: 1ms以内

このテスト仕様書により、統一入力システムの実装品質が保証され、設計ドキュメントとの整合性が確認されます。